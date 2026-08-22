"""Build the Arca Verborum Core dataset release.

Reads the CORE slice of the aggregate and emits a self-contained, versioned
release directory: a CLDF-compatible Wordlist (component tables + metadata JSON
+ sources.bib) that is ALSO a set of plain CSVs, plus a datasheet and a
provenance manifest. Written without any pycldf/cldfbench dependency.

See docs/RELEASE_SPECIFICATION.md. Entry point: ``build_release``.
"""

from __future__ import annotations

import csv
import json
import shutil
from datetime import date
from pathlib import Path

from arcaverborum.packet import load_core_concepts

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_CSV = PROJECT_ROOT / "datasets.csv"

RELEASE_TITLE = "Arca Verborum Core"

# CLDF Wordlist term URLs for the columns we map (others stay plain).
CLDF = "http://cldf.clld.org/v1.0/terms.rdf#"
_PROP = {
    # FormTable
    "ID": CLDF + "id", "Language_ID": CLDF + "languageReference",
    "Parameter_ID": CLDF + "parameterReference", "Form": CLDF + "form",
    "Segments": CLDF + "segments", "Value": CLDF + "value",
    "Comment": CLDF + "comment", "Source": CLDF + "source",
    # LanguageTable
    "Name": CLDF + "name", "Glottocode": CLDF + "glottocode",
    "Macroarea": CLDF + "macroarea",
    # ParameterTable
    "Concepticon_ID": CLDF + "concepticonReference",
    # CognateTable
    "Form_ID": CLDF + "formReference", "Cognateset_ID": CLDF + "cognatesetReference",
    "Alignment": CLDF + "alignment", "Cognate_Detection_Method": CLDF + "cognateDetectionMethod",
    "Doubt": CLDF + "doubt",
}


def load_core_datasets(path: Path = DATASETS_CSV) -> set[str]:
    """CORE-flagged dataset names (CRLF-tolerant)."""
    out: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            name = (r.get("NAME") or "").strip()
            if name and (r.get("CORE") or "").replace("\r", "").strip().upper() == "TRUE":
                out.add(name)
    return out


def load_source_metadata(metadata_csv: Path) -> dict[str, dict]:
    """Dataset -> {Title, Citation, URL, License, Repository_Version} (proper CSV parse)."""
    meta: dict[str, dict] = {}
    if not metadata_csv.exists():
        return meta
    with metadata_csv.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ds = (r.get("Dataset") or "").strip()
            if ds:
                meta[ds] = {k: (r.get(k) or "").strip() for k in
                            ("Title", "Citation", "URL", "License", "Repository_Version")}
    return meta


# ---- FormTable / CognateTable output columns ----

_FORM_COLUMNS = [
    "ID", "Language_ID", "Parameter_ID", "Glottocode", "Variety_Name",
    "concept_label", "Concepticon_ID", "Value", "Form", "Segments", "Segments_Source",
    "Cognacy", "canonical_cognate_id", "Doubt", "Cognate_Detection_Method",
    "Loan", "Comment", "is_core_concept", "License",
    "transcription_source", "cognate_source", "source_form_id",
    "Source", "quality_score", "tier",
]
_COGNATE_COLUMNS = [
    "ID", "Form_ID", "Cognateset_ID", "Cognate_Detection_Method",
    "Alignment", "Segment_Slice", "Morpheme_Index", "Doubt",
]
_LANGUAGE_COLUMNS = [
    "ID", "Name", "Glottocode", "Family", "Macroarea", "tier",
    "forms_score", "cognates_score",
]
_PARAMETER_COLUMNS = [
    "ID", "Name", "Concepticon_ID", "pos", "semantic_field", "is_core",
]


def _write_forms_and_cognates(agg_forms: Path, out_dir: Path, core_datasets: set[str],
                              core_concepts: set[str], licenses: dict[str, dict]) -> dict:
    """Stream the aggregate, emit forms.csv + cognates.csv (CORE only). Returns stats."""
    langs_used: set[str] = set()
    concepts_used: set[str] = set()
    datasets_used: set[str] = set()
    per_dataset = {}          # dataset -> form count
    n_forms = 0
    n_cognate_rows = 0
    cognatesets: set[str] = set()
    counters: dict[str, int] = {}

    fpath = out_dir / "forms.csv"
    cpath = out_dir / "cognates.csv"
    with agg_forms.open(encoding="utf-8") as fin, \
            fpath.open("w", encoding="utf-8", newline="") as ff, \
            cpath.open("w", encoding="utf-8", newline="") as fc:
        reader = csv.DictReader(fin)
        fw = csv.DictWriter(ff, fieldnames=_FORM_COLUMNS)
        cw = csv.DictWriter(fc, fieldnames=_COGNATE_COLUMNS)
        fw.writeheader()
        cw.writeheader()
        for row in reader:
            ts = row.get("transcription_source", "")
            if ts not in core_datasets:
                continue
            av = row["av_id"]
            i = counters.get(av, 0)
            counters[av] = i + 1
            form_id = f"{av}-{i:05d}"
            cid = (row.get("concept_id") or "").strip()

            n_forms += 1
            langs_used.add(av)
            if cid:
                concepts_used.add(cid)
            datasets_used.add(ts)
            per_dataset[ts] = per_dataset.get(ts, 0) + 1

            out = {
                "ID": form_id,
                "Language_ID": av,
                "Parameter_ID": cid,
                "Glottocode": row.get("Glottocode", ""),
                "Variety_Name": row.get("Variety_Name", ""),
                "concept_label": row.get("concept_label", ""),
                "Concepticon_ID": row.get("Concepticon_ID", ""),
                "Value": row.get("Value", ""),
                "Form": row.get("Form", ""),
                "Segments": row.get("Segments", ""),
                "Segments_Source": row.get("Segments_Source", ""),
                "Cognacy": row.get("Cognacy", ""),
                "canonical_cognate_id": row.get("canonical_cognate_id", ""),
                "Doubt": row.get("Doubt", ""),
                "Cognate_Detection_Method": row.get("Cognate_Detection_Method", ""),
                "Loan": row.get("Loan", ""),
                "Comment": row.get("Comment", ""),
                "is_core_concept": "true" if cid in core_concepts else "false",
                "License": licenses.get(ts, {}).get("License", ""),
                "transcription_source": ts,
                "cognate_source": row.get("cognate_source", ""),
                "source_form_id": row.get("source_form_id", ""),
                "Source": row.get("bibtex_key", ""),
                "quality_score": row.get("quality_score", ""),
                "tier": row.get("tier", ""),
            }
            fw.writerow(out)

            cognacy = (row.get("Cognacy") or "").strip()
            if cognacy:
                cset = (row.get("canonical_cognate_id") or "").strip() or cognacy
                cognatesets.add(cset)
                n_cognate_rows += 1
                cw.writerow({
                    "ID": f"{form_id}-c",
                    "Form_ID": form_id,
                    "Cognateset_ID": cset,
                    "Cognate_Detection_Method": row.get("Cognate_Detection_Method", ""),
                    "Alignment": row.get("Alignment", ""),
                    "Segment_Slice": row.get("Segment_Slice", ""),
                    "Morpheme_Index": row.get("Morpheme_Index", ""),
                    "Doubt": row.get("Doubt", ""),
                })
    return {
        "n_forms": n_forms, "langs_used": langs_used, "concepts_used": concepts_used,
        "datasets_used": datasets_used, "per_dataset": per_dataset,
        "n_cognate_rows": n_cognate_rows, "n_cognatesets": len(cognatesets),
    }


def _write_languages(agg_varieties: Path, out_dir: Path, core_datasets: set[str],
                     langs_used: set[str]) -> int:
    n = 0
    with agg_varieties.open(encoding="utf-8") as fin, \
            (out_dir / "languages.csv").open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        w = csv.DictWriter(fout, fieldnames=_LANGUAGE_COLUMNS)
        w.writeheader()
        for row in reader:
            if row["av_id"] not in langs_used:
                continue
            w.writerow({
                "ID": row["av_id"], "Name": row.get("Name", ""),
                "Glottocode": row.get("Glottocode", ""), "Family": row.get("Family", ""),
                "Macroarea": row.get("Macroarea", ""), "tier": row.get("tier", ""),
                "forms_score": row.get("forms_score", ""),
                "cognates_score": row.get("cognates_score", ""),
            })
            n += 1
    return n


def _write_parameters(agg_parameters: Path, out_dir: Path, concepts_used: set[str],
                      core_concepts: set[str]) -> int:
    n = 0
    with agg_parameters.open(encoding="utf-8") as fin, \
            (out_dir / "parameters.csv").open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        w = csv.DictWriter(fout, fieldnames=_PARAMETER_COLUMNS)
        w.writeheader()
        for row in reader:
            cid = row["concept_id"]
            if cid not in concepts_used:
                continue
            w.writerow({
                "ID": cid, "Name": row.get("label", ""),
                "Concepticon_ID": row.get("concepticon_id", ""),
                "pos": row.get("pos", ""), "semantic_field": row.get("semantic_field", ""),
                "is_core": "true" if cid in core_concepts else "false",
            })
            n += 1
    return n


def _cldf_columns(names: list[str]) -> list:
    cols = []
    for name in names:
        col = {"name": name}
        if name in _PROP:
            col["propertyUrl"] = _PROP[name]
        cols.append(col)
    return cols


def _write_cldf_metadata(out_dir: Path, version: str) -> None:
    meta = {
        "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
        "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#Wordlist",
        "dc:title": RELEASE_TITLE,
        "dc:description": "Basic-vocabulary lexical dataset for computational historical "
                          "linguistics; one accepted construction per variety across 13 "
                          "curated CORE families. See README.md.",
        "dcat:version": version,
        "dc:license": "Per-source; see the License column of forms.csv and README.md "
                      "(mostly CC-BY-4.0; grollemundbantu is CC-BY-NC-4.0).",
        "dc:source": "sources.bib",
        "tables": [
            {"url": "forms.csv",
             "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#FormTable",
             "tableSchema": {"columns": _cldf_columns(_FORM_COLUMNS), "primaryKey": ["ID"],
                             "foreignKeys": [
                                 {"columnReference": ["Language_ID"],
                                  "reference": {"resource": "languages.csv", "columnReference": ["ID"]}},
                                 {"columnReference": ["Parameter_ID"],
                                  "reference": {"resource": "parameters.csv", "columnReference": ["ID"]}},
                             ]}},
            {"url": "languages.csv",
             "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#LanguageTable",
             "tableSchema": {"columns": _cldf_columns(_LANGUAGE_COLUMNS), "primaryKey": ["ID"]}},
            {"url": "parameters.csv",
             "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#ParameterTable",
             "tableSchema": {"columns": _cldf_columns(_PARAMETER_COLUMNS), "primaryKey": ["ID"]}},
            {"url": "cognates.csv",
             "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#CognateTable",
             "tableSchema": {"columns": _cldf_columns(_COGNATE_COLUMNS), "primaryKey": ["ID"],
                             "foreignKeys": [
                                 {"columnReference": ["Form_ID"],
                                  "reference": {"resource": "forms.csv", "columnReference": ["ID"]}},
                             ]}},
        ],
    }
    (out_dir / "cldf-metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_manifest(out_dir: Path, version: str, stats: dict, n_langs: int,
                    n_params: int, licenses: dict[str, dict], build_date: str,
                    merkmal_version: str) -> None:
    sources = []
    for ds in sorted(stats["datasets_used"]):
        m = licenses.get(ds, {})
        sources.append({
            "dataset": ds, "forms": stats["per_dataset"].get(ds, 0),
            "license": m.get("License", ""), "version": m.get("Repository_Version", ""),
            "url": m.get("URL", ""),
        })
    lic_summary = sorted({s["license"] for s in sources if s["license"]})
    manifest = {
        "title": RELEASE_TITLE, "version": version, "build_date": build_date,
        "merkmal_version": merkmal_version,
        "counts": {
            "forms": stats["n_forms"], "languages": n_langs, "parameters": n_params,
            "cognate_rows": stats["n_cognate_rows"], "cognatesets": stats["n_cognatesets"],
        },
        "license_summary": lic_summary,
        "sources": sources,
    }
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_datasheet(out_dir: Path, version: str, stats: dict, n_langs: int,
                     n_params: int, licenses: dict[str, dict], build_date: str,
                     merkmal_version: str, n_core_concepts: int) -> None:
    lines = [
        f"# {RELEASE_TITLE} v{version}",
        "",
        "A basic-vocabulary lexical dataset for computational historical linguistics.",
        "For each language variety, Arca provides one accepted construction from a single",
        "curated source, with per-form provenance and quality scoring. This release covers",
        "the 13 curated CORE families (one source per family).",
        "",
        "## Contents",
        "",
        f"- **{stats['n_forms']:,} forms** across **{n_langs} varieties** and "
        f"**{n_params} concepts**.",
        f"- **{stats['n_cognate_rows']:,} cognate-coded forms** in "
        f"**{stats['n_cognatesets']:,} cognate sets**.",
        f"- A frozen **basic-vocabulary core of {n_core_concepts} concepts** "
        "(the `is_core_concept` flag on forms / `is_core` on parameters) — the concepts "
        "attested across ≥7 of the 13 CORE families.",
        "",
        "## Files",
        "",
        "CLDF Wordlist (`cldf-metadata.json`) that is also plain CSV:",
        "",
        "| File | Role |",
        "|---|---|",
        "| `forms.csv` | forms (FormTable) — `is_core_concept`, per-source `License` |",
        "| `languages.csv` | varieties (LanguageTable) |",
        "| `parameters.csv` | concepts (ParameterTable) |",
        "| `cognates.csv` | cognate judgements (CognateTable) |",
        "| `sources.bib` | BibTeX for all sources |",
        "| `cldf-metadata.json` | CLDF Wordlist metadata |",
        "| `MANIFEST.json` | machine-readable provenance |",
        "",
        "## Sources, attribution & licensing",
        "",
        "This dataset aggregates the following curated sources; **each retains its own",
        "license**, recorded per row in the `License` column. Attribution is required.",
        "",
        "| Dataset | Forms | License | Version |",
        "|---|---|---|---|",
    ]
    for ds in sorted(stats["datasets_used"]):
        m = licenses.get(ds, {})
        lines.append(f"| {ds} | {stats['per_dataset'].get(ds, 0):,} | "
                     f"{m.get('License', '') or '—'} | {m.get('Repository_Version', '') or '—'} |")
    lics = sorted({licenses.get(ds, {}).get('License', '') for ds in stats['datasets_used']} - {""})
    lines += [
        "",
        "**License summary:** " + ", ".join(lics) + ".",
        "",
        "> Note: **grollemundbantu (Bantu) is CC-BY-NC-4.0** (NonCommercial). This release",
        "> therefore contains NonCommercial material; commercial reuse must exclude those",
        "> rows (filter `License`). All other sources are CC-BY-4.0.",
        "",
        "Arca Verborum code is MIT-licensed.",
        "",
        "## Quality tiers",
        "",
        "Each variety carries a `tier` (gold/silver/bronze/copper) reflecting source",
        "quality, transcription cleanliness, concept mapping, and cognate quality. Filter",
        "by `tier`, `quality_score`, and `Segments_Source` rather than treating any subset",
        "as canonical vs provisional.",
        "",
        "## Provenance",
        "",
        f"- Build date: {build_date}",
        f"- merkmal (phonology) version: {merkmal_version}",
        f"- Arca Verborum Core version: {version}",
        "- Per-source repository versions: see `MANIFEST.json` / the table above.",
        "",
        "## Citation",
        "",
        "See `CITATION.cff` in the Arca Verborum repository, and cite the underlying",
        "sources (`sources.bib`) as required by their licenses.",
        "",
    ]
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def build_release(aggregate_dir: Path, out_root: Path, version: str,
                  datasets_csv: Path = DATASETS_CSV,
                  metadata_csv: Path | None = None) -> dict:
    """Build the release into out_root/arca-verborum-core-<version>/. Returns stats."""
    agg_forms = aggregate_dir / "forms.csv"
    if not agg_forms.exists():
        raise FileNotFoundError(f"Aggregate not found at {agg_forms}; run `build.py aggregate` first.")
    if metadata_csv is None:
        metadata_csv = PROJECT_ROOT / "intake" / "lexibank" / "metadata.csv"

    try:
        import merkmal
        merkmal_version = str(getattr(merkmal, "__version__", "?"))
    except Exception:
        merkmal_version = "?"

    core_datasets = load_core_datasets(datasets_csv)
    core_concepts = load_core_concepts()
    licenses = load_source_metadata(metadata_csv)
    build_date = date.today().isoformat()

    out_dir = out_root / f"arca-verborum-core-{version}"
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = _write_forms_and_cognates(agg_forms, out_dir, core_datasets, core_concepts, licenses)
    n_langs = _write_languages(aggregate_dir / "varieties.csv", out_dir, core_datasets,
                               stats["langs_used"])
    n_params = _write_parameters(aggregate_dir / "parameters.csv", out_dir,
                                 stats["concepts_used"], core_concepts)

    bib = aggregate_dir / "sources.bib"
    if bib.exists():
        shutil.copyfile(bib, out_dir / "sources.bib")

    _write_cldf_metadata(out_dir, version)
    _write_manifest(out_dir, version, stats, n_langs, n_params, licenses, build_date, merkmal_version)
    _write_datasheet(out_dir, version, stats, n_langs, n_params, licenses, build_date,
                     merkmal_version, len(core_concepts))

    return {
        "out_dir": str(out_dir), "version": version, "forms": stats["n_forms"],
        "languages": n_langs, "parameters": n_params,
        "cognate_rows": stats["n_cognate_rows"], "cognatesets": stats["n_cognatesets"],
        "datasets": sorted(stats["datasets_used"]),
    }
