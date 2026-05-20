"""Variety catalog: our own ID space bootstrapped from Glottolog.

av_id is the primary key for the best-of product. For Glottolog-known
varieties, av_id equals the lowercased Glottocode (e.g. "kusu1250"). For
custom entries (proto-languages, sub-Glottocode dialect distinctions,
unmapped varieties), av_id is prefixed with "x-" (e.g. "x-pie").
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path

from arcaverborum.glottolog import GlottologEntry, load_glottolog, resolve_language

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
VARIETY_OVERRIDES = DATA_DIR / "variety_overrides.csv"
VARIETIES_OUT = DATA_DIR / "varieties.csv"

VARIETY_FIELDS = (
    "av_id",
    "glottocode",
    "iso639p3",
    "name",
    "parent_av_id",
    "family",
    "macroarea",
    "latitude",
    "longitude",
    "in_glottolog",
    "notes",
)


@dataclass(slots=True)
class Variety:
    av_id: str
    glottocode: str = ""
    iso639p3: str = ""
    name: str = ""
    parent_av_id: str = ""
    family: str = ""
    macroarea: str = ""
    latitude: str = ""
    longitude: str = ""
    in_glottolog: bool = False
    notes: str = ""
    sources: set[str] = field(default_factory=set)

    def to_row(self) -> dict[str, str]:
        return {
            "av_id": self.av_id,
            "glottocode": self.glottocode,
            "iso639p3": self.iso639p3,
            "name": self.name,
            "parent_av_id": self.parent_av_id,
            "family": self.family,
            "macroarea": self.macroarea,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "in_glottolog": "true" if self.in_glottolog else "false",
            "notes": self.notes,
        }


def _from_glottolog(entry: GlottologEntry) -> Variety:
    return Variety(
        av_id=entry.glottocode.lower(),
        glottocode=entry.glottocode.lower(),
        iso639p3=entry.iso639p3,
        name=entry.name,
        family=entry.family,
        macroarea=entry.macroarea,
        latitude=str(entry.latitude) if entry.latitude is not None else "",
        longitude=str(entry.longitude) if entry.longitude is not None else "",
        in_glottolog=True,
    )


def build_catalog(
    languages_csv: Path | list[Path],
    glottolog: dict[str, GlottologEntry] | None = None,
    overrides_path: Path = VARIETY_OVERRIDES,
) -> dict[str, Variety]:
    """Build a variety catalog from one or more intake languages.csv.

    Strategy:
      1. Load Glottolog (or use the one passed in).
      2. For each Glottocode appearing in any intake, create a Variety.
      3. Apply variety_overrides.csv: insert custom entries, or override
         fields on existing ones.
      4. Track which sources (Dataset values) cover each variety.
    """
    if glottolog is None:
        glottolog = load_glottolog()

    paths = [languages_csv] if isinstance(languages_csv, (str, Path)) else list(languages_csv)

    catalog: dict[str, Variety] = {}

    for path in paths:
        path = Path(path)
        if not path.exists():
            logger.warning("Catalog: languages file missing, skipping: %s", path)
            continue
        with path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                gc = (row.get("Glottocode") or "").strip().lower()
                dataset = (row.get("Dataset") or "").strip()
                if not gc:
                    continue
                if gc not in catalog:
                    entry = glottolog.get(gc)
                    if entry is not None:
                        catalog[gc] = _from_glottolog(entry)
                    else:
                        catalog[gc] = Variety(
                            av_id=gc,
                            glottocode=gc,
                            name=(row.get("Glottolog_Name") or row.get("Name") or "").strip(),
                            family=(row.get("Family") or "").strip(),
                            macroarea=(row.get("Macroarea") or "").strip(),
                            iso639p3=(row.get("ISO639P3code") or "").strip(),
                            latitude=(row.get("Latitude") or "").strip(),
                            longitude=(row.get("Longitude") or "").strip(),
                            in_glottolog=False,
                            notes="not in Glottolog",
                        )
                catalog[gc].sources.add(dataset)

    _apply_overrides(catalog, overrides_path)

    logger.info(
        "Catalog: %d varieties (%d Glottolog-backed, %d custom)",
        len(catalog),
        sum(1 for v in catalog.values() if v.in_glottolog),
        sum(1 for v in catalog.values() if not v.in_glottolog),
    )
    return catalog


def _apply_overrides(catalog: dict[str, Variety], overrides_path: Path) -> None:
    if not overrides_path.exists():
        return
    with overrides_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            av_id = (row.get("av_id") or "").strip()
            if not av_id:
                continue
            existing = catalog.get(av_id)
            if existing is None:
                catalog[av_id] = Variety(
                    av_id=av_id,
                    glottocode=(row.get("glottocode") or "").strip().lower(),
                    iso639p3=(row.get("iso639p3") or "").strip(),
                    name=(row.get("name") or "").strip(),
                    parent_av_id=(row.get("parent_av_id") or "").strip(),
                    family=(row.get("family") or "").strip(),
                    macroarea=(row.get("macroarea") or "").strip(),
                    latitude=(row.get("latitude") or "").strip(),
                    longitude=(row.get("longitude") or "").strip(),
                    in_glottolog=(row.get("in_glottolog") or "").strip().lower() == "true",
                    notes=(row.get("notes") or "").strip(),
                )
            else:
                for f_ in ("glottocode", "iso639p3", "name", "parent_av_id",
                           "family", "macroarea", "latitude", "longitude", "notes"):
                    v = (row.get(f_) or "").strip()
                    if v:
                        setattr(existing, f_, v)


def iso_from_language_id(language_id, iso_hint="") -> str:
    """Best-effort ISO 639-3 code for a (possibly wikt_) Language_ID.

    Prefers an explicit hint, else extracts a 3-letter alpha suffix from
    a `wikt_<iso>` ID. Tolerant of NaN/None/non-str inputs.
    """
    iso = "" if iso_hint is None else str(iso_hint).strip()
    if iso and iso.lower() != "nan":
        return iso
    lid = "" if language_id is None else str(language_id)
    if lid.startswith("wikt_"):
        suffix = lid[5:]
        if len(suffix) == 3 and suffix.isalpha():
            return suffix
    return ""


def enrich_glottocodes(
    forms: "object",
    languages: "object",
    glottolog: dict[str, GlottologEntry],
):
    """Fill Glottocode/Glottolog_Name/Family/Macroarea on forms whose
    source left them blank, using languages' ISO codes (or wikt_ suffix)
    resolved via Glottolog. Operates on pandas DataFrames; returns the
    (forms, languages) pair with columns filled in place.

    Used for sources like Wiktionary that ship without Glottocodes.
    """
    import pandas as pd  # local import to keep catalog import light

    if "ISO639P3code" in languages.columns:
        iso_map = dict(zip(languages["ID"], languages["ISO639P3code"]))
    else:
        iso_map = {}

    # Resolve a Glottolog entry per Language_ID once, then map columns
    # vectorized (forms can be millions of rows — no iterrows).
    field_maps: dict[str, dict[str, str]] = {
        "Glottocode": {}, "Glottolog_Name": {}, "Family": {},
        "Macroarea": {}, "Latitude": {}, "Longitude": {},
    }
    for lid in languages["ID"]:
        iso = iso_from_language_id(str(lid), iso_map.get(lid, ""))
        entry = resolve_language("", iso, glottolog)
        if entry is None:
            continue
        field_maps["Glottocode"][lid] = entry.glottocode
        field_maps["Glottolog_Name"][lid] = entry.name
        field_maps["Family"][lid] = entry.family
        field_maps["Macroarea"][lid] = entry.macroarea
        field_maps["Latitude"][lid] = "" if entry.latitude is None else str(entry.latitude)
        field_maps["Longitude"][lid] = "" if entry.longitude is None else str(entry.longitude)

    def _norm(series):
        s = series.astype("string").fillna("").astype(str).str.strip()
        return s.where(~s.str.lower().isin(["nan", "<na>", "none"]), "")

    def _fill(df, key_col: str):
        df = df.copy()
        keys = df[key_col].astype("string").fillna("").astype(str)
        for col, mapping in field_maps.items():
            if col not in df.columns:
                df[col] = ""
            current = _norm(df[col])
            resolved = keys.map(mapping).fillna("")
            df[col] = current.where(current.ne(""), resolved)
        return df

    return _fill(forms, "Language_ID"), _fill(languages, "ID")


def write_catalog(catalog: dict[str, Variety], out_path: Path = VARIETIES_OUT) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted((v.to_row() for v in catalog.values()), key=lambda r: r["av_id"])
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=VARIETY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %d varieties to %s", len(rows), out_path)


def load_catalog(path: Path = VARIETIES_OUT) -> dict[str, Variety]:
    catalog: dict[str, Variety] = {}
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            v = Variety(
                av_id=row["av_id"],
                glottocode=row.get("glottocode", ""),
                iso639p3=row.get("iso639p3", ""),
                name=row.get("name", ""),
                parent_av_id=row.get("parent_av_id", ""),
                family=row.get("family", ""),
                macroarea=row.get("macroarea", ""),
                latitude=row.get("latitude", ""),
                longitude=row.get("longitude", ""),
                in_glottolog=row.get("in_glottolog", "false").lower() == "true",
                notes=row.get("notes", ""),
            )
            catalog[v.av_id] = v
    return catalog
