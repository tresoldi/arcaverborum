"""Glottolog data loading and Glottocode resolution."""

from __future__ import annotations

import csv
import io
import urllib.request
from dataclasses import dataclass
from pathlib import Path

GLOTTOLOG_CSV_URL = "https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/languages.csv"
RAW_CACHE = Path("raw/glottolog/languages.csv")


@dataclass(frozen=True, slots=True)
class GlottologEntry:
    glottocode: str
    name: str
    iso639p3: str
    macroarea: str
    latitude: float | None
    longitude: float | None
    family: str


def load_glottolog(source: str | Path | None = None) -> dict[str, GlottologEntry]:
    """Load Glottolog data into a lookup dict.

    Resolution order: explicit `source` arg → `raw/glottolog/languages.csv`
    cache → URL download. Keys are both raw glottocodes (e.g. "abaz1241")
    and "iso:{code}" (e.g. "iso:abq").

    Dialect-level entries are included: they use their own coordinates/name
    where available, falling back to their parent language for family,
    macroarea, and missing fields.
    """
    if source and Path(source).exists():
        data = Path(source).read_text(encoding="utf-8")
    elif RAW_CACHE.exists():
        data = RAW_CACHE.read_text(encoding="utf-8")
    else:
        url = str(source) if source and str(source).startswith("http") else GLOTTOLOG_CSV_URL
        data = urllib.request.urlopen(url, timeout=30).read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(data))
    rows = list(reader)

    family_names = {r["ID"]: r["Name"] for r in rows if r.get("Level") == "family"}

    index: dict[str, GlottologEntry] = {}
    dialect_rows = []

    for r in rows:
        level = r.get("Level", "")
        if level == "dialect":
            dialect_rows.append(r)
            continue
        if level != "language":
            continue

        gc = r.get("Glottocode", r.get("ID", "")).strip()
        iso = r.get("ISO639P3code", "").strip()
        name = r.get("Name", "").strip()
        macro = r.get("Macroarea", "").strip()
        lat_s = r.get("Latitude", "").strip()
        lon_s = r.get("Longitude", "").strip()
        fam_id = r.get("Family_ID", "").strip()
        is_isolate = r.get("Is_Isolate", "").strip() == "true"

        lat = float(lat_s) if lat_s else None
        lon = float(lon_s) if lon_s else None
        family = family_names.get(fam_id, name if is_isolate else "")

        entry = GlottologEntry(gc, name, iso, macro, lat, lon, family)
        if gc:
            index[gc] = entry
        if iso:
            index[f"iso:{iso}"] = entry

    for r in dialect_rows:
        gc = r.get("Glottocode", r.get("ID", "")).strip()
        if not gc or gc in index:
            continue
        parent_id = r.get("Language_ID", "").strip()
        parent = index.get(parent_id)
        if not parent:
            continue

        iso = r.get("ISO639P3code", "").strip()
        name = r.get("Name", "").strip() or parent.name
        lat_s = r.get("Latitude", "").strip()
        lon_s = r.get("Longitude", "").strip()
        lat = float(lat_s) if lat_s else parent.latitude
        lon = float(lon_s) if lon_s else parent.longitude
        macro = r.get("Macroarea", "").strip() or parent.macroarea

        entry = GlottologEntry(gc, name, iso, macro, lat, lon, parent.family)
        index[gc] = entry
        if iso:
            iso_key = f"iso:{iso}"
            if iso_key not in index:
                index[iso_key] = entry

    return index


def resolve_language(
    glottocode: str,
    iso_code: str,
    glottolog: dict[str, GlottologEntry],
) -> GlottologEntry | None:
    """Resolve a language to a GlottologEntry via fallback chain: Glottocode → ISO."""
    if glottocode and glottocode in glottolog:
        return glottolog[glottocode]
    if iso_code:
        key = f"iso:{iso_code}"
        if key in glottolog:
            return glottolog[key]
    return None
