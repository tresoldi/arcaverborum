"""av_id assignment: family-prefixed, human-readable variety IDs.

Scheme (decided 2026-05): ``<family_code>-<name_slug>[-<n>]``

* ``family_code`` — a stable 3-char code for the variety's TOP-LEVEL
  Glottolog family. Codes live in a committed, curatable registry
  (``data/family_codes.csv``); a small seed of conventional codes
  (ISO 639-5 where it fits Glottolog's naming) keeps the big families
  recognizable, the rest are auto-derived. Only the *coarse, stable*
  genealogical dimension goes in the key — subfamily/genus/area stay
  as columns, so the ID survives Glottolog reclassifications.
* ``name_slug`` — the lowercased, ASCII-folded language name.
* ``-<n>`` — appended only to break collisions, in Glottocode order, so
  the first claimant keeps the bare slug.

IDs are **assigned once and frozen**: the ``varieties/`` tree plus the
committed registry are the source of truth. Later Glottolog name/family
drift is flagged, never silently re-keyed.
"""

from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
FAMILY_CODES_CSV = DATA_DIR / "family_codes.csv"

# Code used when a variety has no resolved family.
UNDETERMINED_CODE = "und"

# Conventional codes for high-recognition families, keyed by EXACT Glottolog
# family name. Seeded from ISO 639-5 where it lines up with Glottolog's
# taxonomy. Everything else is auto-derived; curate freely in
# data/family_codes.csv.
SEED_FAMILY_CODES: dict[str, str] = {
    "Indo-European": "ine",
    "Sino-Tibetan": "sit",
    "Afro-Asiatic": "afa",
    "Austronesian": "map",
    "Austroasiatic": "aav",
    "Dravidian": "dra",
    "Turkic": "trk",
    "Uralic": "urj",
    "Tai-Kadai": "tai",
    "Tupian": "tup",
    "Pama-Nyungan": "pny",
    "Japonic": "jpx",
    "Hmong-Mien": "hmx",
    "Quechuan": "qwe",
}

_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _ascii_fold(text: str) -> str:
    """Lowercase, strip diacritics, keep ASCII letters/digits only."""
    nfkd = unicodedata.normalize("NFKD", text)
    no_marks = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_marks.lower()


def slugify_name(name: str, fallback: str = "") -> str:
    """Lowercased, ASCII-folded, hyphen-joined slug of a language name.

    Non-alphanumeric runs collapse to a single hyphen. Empty results fall
    back to ``fallback`` (typically the Glottocode).
    """
    folded = _ascii_fold(name)
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
    return slug or _ascii_fold(fallback).strip("-") or "unnamed"


def _derive_family_code(name: str, used: set[str]) -> str:
    """Deterministic 3-char code from a family name, avoiding ``used``.

    Preference: first three ASCII letters of the name. On collision,
    cycle the 3rd then 2nd character through a-z; finally scan all
    letter triples. Letters only (no digits) for readability.
    """
    letters = [c for c in _ascii_fold(name) if c.isalpha()]
    base = "".join(letters[:3])
    base = (base + "xxx")[:3] if len(base) < 3 else base

    if base not in used:
        return base

    for i in (2, 1, 0):  # vary 3rd, then 2nd, then 1st char
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
    raise RuntimeError("exhausted 3-letter family code space")


def build_family_codes(
    families: list[str],
    seed: dict[str, str] | None = None,
) -> dict[str, str]:
    """Assign a unique 3-char code to each family name.

    ``families`` is processed in the order given (dedup preserves first
    appearance), so callers control who claims the clean first-three
    code on collision — pass families biggest-first to favour the
    largest. Seeded families are assigned first. Blank family names are
    skipped (they map to ``UNDETERMINED_CODE`` at lookup time).
    """
    seed = SEED_FAMILY_CODES if seed is None else seed
    codes: dict[str, str] = {}
    used: set[str] = {UNDETERMINED_CODE}

    ordered: list[str] = []
    seen: set[str] = set()
    for fam in families:
        fam = fam.strip()
        if fam and fam not in seen:
            seen.add(fam)
            ordered.append(fam)

    for fam, code in seed.items():
        if fam in seen and fam not in codes:
            if code in used:
                code = _derive_family_code(fam, used)
            codes[fam] = code
            used.add(code)

    for fam in ordered:
        if fam in codes:
            continue
        code = _derive_family_code(fam, used)
        codes[fam] = code
        used.add(code)

    return codes


def load_family_codes(path: Path = FAMILY_CODES_CSV) -> dict[str, str]:
    codes: dict[str, str] = {}
    if not path.exists():
        return codes
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fam = (row.get("family") or "").strip()
            code = (row.get("code") or "").strip()
            if fam and code:
                codes[fam] = code
    return codes


def write_family_codes(codes: dict[str, str], path: Path = FAMILY_CODES_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["family", "code"])
        for fam in sorted(codes):
            w.writerow([fam, codes[fam]])


def family_code_for(family: str, codes: dict[str, str]) -> str:
    return codes.get(family.strip(), UNDETERMINED_CODE) if family.strip() else UNDETERMINED_CODE


def mint_av_id(
    name: str,
    family: str,
    family_codes: dict[str, str],
    taken: set[str],
    glottocode: str = "",
) -> str:
    """Mint one fresh, non-colliding av_id for a single variety.

    Used when a Glottocode appears that the frozen registry doesn't yet
    cover. ``taken`` is the set of av_ids already in use; the result is
    not added to it (caller decides).
    """
    code = family_code_for(family, family_codes)
    slug = slugify_name(name, fallback=glottocode)
    base = f"{code}-{slug}"
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


def assign_av_ids(
    varieties: list[dict[str, str]],
    family_codes: dict[str, str],
) -> dict[str, str]:
    """Map each variety's Glottocode to a proposed av_id.

    ``varieties`` items need ``glottocode``, ``name``, ``family``. The
    bare ``family_code-name_slug`` goes to the lowest Glottocode among
    collisions; later claimants get ``-2``, ``-3`` … so assignment is
    order-independent and stable. Returns ``{glottocode: av_id}``.
    """
    # Group by the (family_code, slug) stem, claimants in Glottocode order.
    stems: dict[tuple[str, str], list[str]] = {}
    meta: dict[str, dict[str, str]] = {}
    for v in varieties:
        gc = v["glottocode"].strip().lower()
        if not gc:
            continue
        meta[gc] = v
        code = family_code_for(v.get("family", ""), family_codes)
        slug = slugify_name(v.get("name", ""), fallback=gc)
        stems.setdefault((code, slug), []).append(gc)

    out: dict[str, str] = {}
    for (code, slug), gcs in stems.items():
        for n, gc in enumerate(sorted(gcs)):
            suffix = "" if n == 0 else f"-{n + 1}"
            out[gc] = f"{code}-{slug}{suffix}"
    return out
