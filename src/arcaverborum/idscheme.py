"""Generic <code>-<slug> ID scheme shared by avid and concepts modules."""

from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

UNDETERMINED_CODE = "und"

_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def ascii_fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    no_marks = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_marks.lower()


def slugify_name(name: str, fallback: str = "") -> str:
    """Lowercased, ASCII-folded, hyphen-joined slug."""
    folded = ascii_fold(name)
    out: list[str] = []
    prev_hyphen = False
    for ch in folded:
        if ch.isalnum():
            out.append(ch)
            prev_hyphen = False
        elif not prev_hyphen:
            out.append("-")
            prev_hyphen = True
    slug = "".join(out).strip("-")
    return slug or ascii_fold(fallback).strip("-") or "unnamed"


def derive_code(name: str, used: set[str]) -> str:
    """Deterministic 3-char code from a name, avoiding ``used``."""
    letters = [c for c in ascii_fold(name) if c.isalpha()]
    base = "".join(letters[:3])
    base = (base + "xxx")[:3] if len(base) < 3 else base

    if base not in used:
        return base

    for i in (2, 1, 0):
        for c in _LETTERS:
            cand = base[:i] + c + base[i + 1:]
            if cand not in used:
                return cand
    for a in _LETTERS:
        for b in _LETTERS:
            for c in _LETTERS:
                cand = a + b + c
                if cand not in used:
                    return cand
    raise RuntimeError("exhausted 3-letter code space")


def build_codes(
    names: list[str],
    seed: dict[str, str],
    undetermined: str = UNDETERMINED_CODE,
) -> dict[str, str]:
    """Assign a unique 3-char code to each name, seeded entries first."""
    codes: dict[str, str] = {}
    used: set[str] = {undetermined}

    ordered: list[str] = []
    seen: set[str] = set()
    for n in names:
        n = n.strip()
        if n and n not in seen:
            seen.add(n)
            ordered.append(n)

    for n, code in seed.items():
        if n in seen and n not in codes:
            if code in used:
                code = derive_code(n, used)
            codes[n] = code
            used.add(code)

    for n in ordered:
        if n in codes:
            continue
        code = derive_code(n, used)
        codes[n] = code
        used.add(code)

    return codes


def code_for(name: str, codes: dict[str, str], undetermined: str = UNDETERMINED_CODE) -> str:
    name = (name or "").strip()
    return codes.get(name, undetermined) if name else undetermined


def load_codes(path: Path, name_col: str, code_col: str) -> dict[str, str]:
    codes: dict[str, str] = {}
    if not path.exists():
        return codes
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = (row.get(name_col) or "").strip()
            c = (row.get(code_col) or "").strip()
            if n and c:
                codes[n] = c
    return codes


def write_codes(codes: dict[str, str], path: Path, name_col: str, code_col: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([name_col, code_col])
        for n in sorted(codes):
            w.writerow([n, codes[n]])
