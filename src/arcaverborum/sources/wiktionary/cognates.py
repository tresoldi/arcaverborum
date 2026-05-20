"""Cognate set construction from Wiktionary etymology data."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field

from .extract import WiktEtymology


def _normalize_form(word: str) -> str:
    s = word.lstrip("*")
    s = unicodedata.normalize("NFC", s).lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


@dataclass
class CognateBuilder:
    _proto_to_reflexes: dict[tuple[str, str], set[tuple[str, str]]] = field(
        default_factory=lambda: defaultdict(set)
    )
    _form_to_cognate_ids: dict[tuple[str, str], set[str]] | None = field(
        default=None, repr=False
    )
    _form_to_loan: dict[tuple[str, str], bool | None] = field(
        default_factory=dict, repr=False
    )
    _etym_count: int = field(default=0)

    @property
    def etymology_count(self) -> int:
        return self._etym_count

    @property
    def cognate_set_count(self) -> int:
        return len(self._proto_to_reflexes)

    def add_etymology(self, etym: WiktEtymology) -> None:
        self._etym_count += 1

        if etym.kind == "desc":
            proto_key = (etym.source_lang_code, _normalize_form(etym.proto_word or etym.entry_word))
            reflex = (etym.target_lang_code, _normalize_form(etym.word))
            self._proto_to_reflexes[proto_key].add(reflex)
        elif etym.kind in ("inh", "bor", "der"):
            proto_key = (etym.source_lang_code, _normalize_form(etym.word))
            reflex = (etym.target_lang_code, _normalize_form(etym.entry_word))
            self._proto_to_reflexes[proto_key].add(reflex)

            loan_key = (etym.target_lang_code, _normalize_form(etym.entry_word))
            if etym.kind == "bor":
                self._form_to_loan[loan_key] = True
            elif etym.kind == "inh" and loan_key not in self._form_to_loan:
                self._form_to_loan[loan_key] = False

    def finalize(self) -> None:
        index: dict[tuple[str, str], set[str]] = defaultdict(set)
        for (proto_lang, proto_form), reflexes in self._proto_to_reflexes.items():
            cogset_id = f"wikt_{proto_lang}_{proto_form}"
            for reflex in reflexes:
                index[reflex].add(cogset_id)
        self._form_to_cognate_ids = dict(index)

    def get_cognate_ids(self, lang_code: str, word: str) -> str:
        if self._form_to_cognate_ids is None:
            return ""
        key = (lang_code, _normalize_form(word))
        ids = self._form_to_cognate_ids.get(key)
        if not ids:
            return ""
        return ";".join(sorted(ids))

    def is_loan(self, lang_code: str, word: str) -> bool | None:
        key = (lang_code, _normalize_form(word))
        return self._form_to_loan.get(key)
