"""Streaming extraction of translations and etymologies from kaikki.org JSONL."""

from __future__ import annotations

import gzip
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WiktTranslation:
    english_word: str
    pos: str
    sense: str
    target_word: str
    target_lang: str
    target_lang_code: str
    roman: str
    alt: str
    tags: tuple[str, ...]
    raw_tags: tuple[str, ...]
    note: str


@dataclass(frozen=True, slots=True)
class WiktEtymology:
    kind: str
    source_lang_code: str
    target_lang_code: str
    word: str
    proto_word: str
    entry_lang_code: str
    entry_word: str


ETYMOLOGY_TEMPLATE_NAMES = frozenset({"inh", "bor", "der"})


def stream_entries(path: Path) -> Iterator[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract_translations(entry: dict) -> Iterator[WiktTranslation]:
    word = entry.get("word", "")
    pos = entry.get("pos", "")
    if not word:
        return

    for tr in entry.get("translations", []):
        target_word = tr.get("word", "")
        lang_code = tr.get("lang_code") or tr.get("code", "")
        if not target_word or not lang_code:
            continue

        yield WiktTranslation(
            english_word=word,
            pos=pos,
            sense=tr.get("sense", ""),
            target_word=target_word,
            target_lang=tr.get("lang", ""),
            target_lang_code=lang_code,
            roman=tr.get("roman", ""),
            alt=tr.get("alt", ""),
            tags=tuple(tr.get("tags", ())),
            raw_tags=tuple(tr.get("raw_tags", ())),
            note=tr.get("note", ""),
        )


def extract_etymologies(entry: dict) -> Iterator[WiktEtymology]:
    lang_code = entry.get("lang_code", "")
    word = entry.get("word", "")

    for tmpl in entry.get("etymology_templates", []):
        name = tmpl.get("name", "")
        if name not in ETYMOLOGY_TEMPLATE_NAMES:
            continue
        args = tmpl.get("args", {})
        source_lang = args.get("2", "")
        etym_word = args.get("3", "")
        if not source_lang or not etym_word:
            continue
        yield WiktEtymology(
            kind=name,
            source_lang_code=source_lang,
            target_lang_code=args.get("1", "") or lang_code,
            word=etym_word,
            proto_word="",
            entry_lang_code=lang_code,
            entry_word=word,
        )

    for desc in entry.get("descendants", []):
        yield from _walk_descendants(desc, proto_lang_code=lang_code, proto_word=word)


def _walk_descendants(
    node: dict,
    proto_lang_code: str,
    proto_word: str,
) -> Iterator[WiktEtymology]:
    lc = node.get("lang_code", "")
    w = node.get("word", "")
    if lc and w:
        yield WiktEtymology(
            kind="desc",
            source_lang_code=proto_lang_code,
            target_lang_code=lc,
            word=w,
            proto_word=proto_word,
            entry_lang_code=proto_lang_code,
            entry_word=proto_word,
        )
    for child in node.get("descendants", []):
        yield from _walk_descendants(child, proto_lang_code, proto_word)
