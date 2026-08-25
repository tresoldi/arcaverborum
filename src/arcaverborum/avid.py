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

from pathlib import Path

from arcaverborum.idscheme import (
    build_codes,
    code_for,
    load_codes,
    slugify_name,
    write_codes,
)

DATA_DIR = Path(__file__).parent / "data"
FAMILY_CODES_CSV = DATA_DIR / "family_codes.csv"

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

def build_family_codes(
    families: list[str],
    seed: dict[str, str] | None = None,
) -> dict[str, str]:
    """Assign a unique 3-char code to each family name."""
    return build_codes(families, SEED_FAMILY_CODES if seed is None else seed)


def load_family_codes(path: Path = FAMILY_CODES_CSV) -> dict[str, str]:
    return load_codes(path, "family", "code")


def write_family_codes(codes: dict[str, str], path: Path = FAMILY_CODES_CSV) -> None:
    write_codes(codes, path, "family", "code")


def family_code_for(family: str, codes: dict[str, str]) -> str:
    return code_for(family, codes)


def mint_av_id(
    name: str,
    family: str,
    family_codes: dict[str, str],
    taken: set[str],
    glottocode: str = "",
) -> str:
    """Mint one fresh, non-colliding av_id for a single variety."""
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
    """Map each variety's Glottocode to a proposed av_id."""
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
