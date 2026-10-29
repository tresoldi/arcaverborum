"""Verify Sidaama phonemic headwords against the original explicit SFM IPA field."""

from __future__ import annotations

import hashlib
import re
import unicodedata


def phonemic_witnesses(payload: bytes, headword: str) -> list[dict[str, str]]:
    """Require every original homograph to carry the same explicit phonemic string.

    The official spelling is a separate witness field. Empty/mismatched IPA never
    licenses a reading just because the CLDF headword happens to tokenize.
    """
    result = []
    expected = unicodedata.normalize("NFC", headword)
    for block in re.split(r"(?=^\\lx )", payload.decode("utf-8-sig"), flags=re.M):
        fields = {}
        for line in block.splitlines():
            match = re.match(r"\\(\S+)\s+(.*)", line)
            if match:
                fields.setdefault(match[1], []).append(match[2].strip())
        if [unicodedata.normalize("NFC", x) for x in fields.get("lx", [])] != [expected]:
            continue
        ipa = fields.get("lx_SidIPA", [])
        if len(ipa) != 1 or unicodedata.normalize("NFC", ipa[0]) != expected:
            raise ValueError("Sidaama explicit IPA field missing or ambiguous across homographs")
        result.append(
            dict(
                headword=headword,
                source_ipa=ipa[0],
                official_orthography="; ".join(fields.get("lc_Sid", [])),
                native_sfm_sha256=hashlib.sha256(block.encode()).hexdigest(),
            )
        )
    if not result:
        raise ValueError("Sidaama original headword witness missing")
    return result
