"""Curation machinery: scaffold per-variety authority recipes and packets.

Emits two files per variety (see ``docs/CURATION_MACHINERY.md``):

* ``recipe.yaml`` — the authority recipe: a structured, descriptive-first record
  of the accepted construction. ENFORCED fields name build mechanisms
  (``config.sources`` and ``custom/*``); all others are advisory.
* ``PACKET.md`` — the human-readable curation packet.

The scaffolder is descriptive only: it reads the variety's ``config.yaml`` and
its built ``generated/forms.csv`` plus the frozen basic-vocabulary core, and
writes files a curator (human or agent) then edits. It changes no build output.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CONCEPT_CORE_CSV = DATA_DIR / "concept_core.csv"
DATASETS_CSV = Path(__file__).resolve().parents[2] / "datasets.csv"


def load_core_concepts(path: Path = CONCEPT_CORE_CSV) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as f:
        return {r["concept_id"] for r in csv.DictReader(f)}


def load_expert_datasets(path: Path = DATASETS_CSV) -> set[str]:
    """Names of datasets whose ExpertCognates flag is TRUE (CRLF-tolerant)."""
    if not path.exists():
        return set()
    out: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            name = (r.get("NAME") or "").strip()
            if name and (r.get("ExpertCognates") or "").strip().replace("\r", "").upper() == "TRUE":
                out.add(name)
    return out


def diagnose(generated_forms: Path, core_concepts: set[str]) -> dict:
    """Compute per-variety diagnostics from a built generated/forms.csv."""
    n = 0
    seg: Counter = Counter()
    concepts: set[str] = set()
    core_hit: set[str] = set()
    with_cid = 0
    with_cognacy = 0
    with_loan = 0
    tsrc: Counter = Counter()
    csrc: Counter = Counter()
    with generated_forms.open(encoding="utf-8") as f:
        for x in csv.DictReader(f):
            n += 1
            seg[x.get("Segments_Source", "")] += 1
            cid = (x.get("concept_id") or "").strip()
            if cid:
                with_cid += 1
                concepts.add(cid)
                if cid in core_concepts:
                    core_hit.add(cid)
            if (x.get("Cognacy") or "").strip():
                with_cognacy += 1
            if (x.get("Loan") or "").strip():
                with_loan += 1
            if (x.get("transcription_source") or "").strip():
                tsrc[x["transcription_source"]] += 1
            if (x.get("cognate_source") or "").strip():
                csrc[x["cognate_source"]] += 1
    return {
        "n_forms": n,
        "seg": seg,
        "n_concepts": len(concepts),
        "with_cid": with_cid,
        "core_hit": len(core_hit),
        "core_total": len(core_concepts),
        "with_cognacy": with_cognacy,
        "with_loan": with_loan,
        "transcription_sources": tsrc,
        "cognate_sources": csrc,
    }


def _pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "n/a"


def _transcription_strategy(vd_custom: Path) -> tuple[str, str, str]:
    """(strategy, profile-ref, overrides-ref) from which custom files have rows."""
    prof = vd_custom / "profile.tsv"
    over = vd_custom / "transcriptions.csv"
    has_prof = prof.exists() and prof.stat().st_size > 0
    has_over = over.exists() and over.stat().st_size > 0
    profile_ref = "custom/profile.tsv" if has_prof else "none"
    over_ref = "custom/transcriptions.csv" if has_over else "none"
    if has_prof and has_over:
        strat = "mixed"
    elif has_prof:
        strat = "profile"
    elif has_over:
        strat = "override"
    else:
        strat = "source"
    return strat, profile_ref, over_ref


def build_recipe_yaml(av_id: str, config: dict, diag: dict, expert_datasets: set[str],
                      strat: str, profile_ref: str, over_ref: str,
                      concept_map_used: bool) -> str:
    name = config.get("name", "")
    sources = config.get("sources", {}) or {}
    scoring = config.get("scoring", {}) or {}
    tsrc = sources.get("transcription", "")
    csrc = sources.get("cognates", "")
    method = "expert" if (csrc in expert_datasets and diag["with_cognacy"]) else (
        "source" if diag["with_cognacy"] else "none")
    mapping = "corrected" if concept_map_used else "source"
    loan_pct = _pct(diag["with_loan"], diag["n_forms"])
    clean = diag["seg"].get("source", 0) + diag["seg"].get("profile", 0)
    seg_note = (f"{clean}/{diag['n_forms']} forms clean "
                f"(source {diag['seg'].get('source', 0)}, profile {diag['seg'].get('profile', 0)}, "
                f"resegmented {diag['seg'].get('resegmented', 0)}, unclean {diag['seg'].get('unclean', 0)}).")
    concept_note = f"{diag['with_cid']}/{diag['n_forms']} forms mapped; {diag['n_concepts']} distinct concepts."
    cognacy_note = f"{_pct(diag['with_cognacy'], diag['n_forms'])} of forms carry Cognacy."
    lines = [
        f"# Authority recipe for {av_id} — see docs/CURATION_MACHINERY.md",
        "# Descriptive companion to config.yaml + custom/*. ENFORCED fields name build",
        "# mechanisms; all others are advisory. Scaffolded by `build.py packet`; edit freely.",
        f"av_id: {av_id}",
        f"name: {_yv(name)}",
        "review:",
        "  status: draft",
        '  reviewer: ""',
        '  date: ""',
        "quality:                     # advisory mirror of config.scoring",
        f"  tier: {scoring.get('tier', '')}",
        f"  forms_score: {scoring.get('forms_score', '')}",
        f"  cognates_score: {scoring.get('cognates_score', '')}",
        f"  pinned: {str(bool(config.get('pinned', False))).lower()}",
        "construction:",
        "  summary: >",
        f"    {name} basic vocabulary from {tsrc or 'the selected source'}"
        + (f" (cognacy from {csrc})" if csrc and csrc != tsrc else "")
        + ". Scaffolded from the current build; review and refine.",
        "  lexical_base:",
        f"    source: {tsrc}            # ENFORCED -> config.sources.transcription",
        '    rationale: ""             # advisory: why this source over the alternatives',
        "  transcription:",
        f"    strategy: {strat}",
        f"    profile: {profile_ref}    # ENFORCED (extensions.profile)",
        f"    overrides: {over_ref}     # ENFORCED (extensions.transcriptions)",
        f"    notes: {_yv(seg_note)}",
        "  concepts:",
        f"    mapping: {mapping}        # ENFORCED via custom/concept_map.csv when corrected",
        f"    core_coverage: {diag['core_hit']}/{diag['core_total']}",
        f"    notes: {_yv(concept_note)}",
        "  cognates:",
        f"    source: {csrc}            # ENFORCED -> config.sources.cognates",
        f"    method: {method}          # expert|computed|manual|hybrid|source|none",
        "    computed: none            # method metadata block when computed",
        f"    notes: {_yv(cognacy_note)}",
        "  loans:",
        "    handling: source",
        f"    annotated: {loan_pct}",
        '    notes: ""',
        "candidates:                  # advisory: other sources considered + verdict",
        "  []",
        "provenance:",
        f"  bibliography: [{tsrc}]      # advisory; bibtex keys resolve in output sources.bib",
        "tradeoffs:",
        '  gains: ""',
        '  known_losses: ""',
        'notes: ""                     # advisory free-form',
        "",
    ]
    return "\n".join(lines)


def _yv(s: str) -> str:
    """Minimal YAML scalar quoting for values that may contain colons/quotes."""
    s = str(s).replace("\n", " ").strip()
    if s == "":
        return '""'
    if any(c in s for c in ':#') or s[0] in "!&*?|>%@`\"'":
        return '"' + s.replace('"', '\\"') + '"'
    return s


def build_packet_md(av_id: str, config: dict, diag: dict) -> str:
    name = config.get("name", "")
    sources = config.get("sources", {}) or {}
    scoring = config.get("scoring", {}) or {}
    tsrc = sources.get("transcription", "")
    csrc = sources.get("cognates", "")
    n = diag["n_forms"]
    rows = [
        f"# Curation Packet — {name} (`{av_id}`)",
        "",
        f"- **Family / macroarea:** {config.get('family', '')} / {config.get('macroarea', '')}"
        f" · **Glottocode:** {config.get('glottocode', '') or '—'}",
        f"- **Accepted source:** {tsrc}"
        + (f" (transcription); {csrc} (cognates)" if csrc and csrc != tsrc else " (transcription + cognates)")
        + f" · **Tier:** {scoring.get('tier', '')} · **Pinned:** {'yes' if config.get('pinned') else 'no'}",
        "- **Review status:** draft (scaffolded)",
        "",
        "## 1. Current accepted construction",
        "",
        f"{name} is built from **{tsrc}**"
        + (f", with cognates from **{csrc}**" if csrc and csrc != tsrc else "")
        + ". Scaffolded from the current build — review and refine `recipe.yaml`.",
        "",
        "## 2. Coverage & quality (from the current build)",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Forms | {n} |",
        f"| Distinct concepts | {diag['n_concepts']} |",
        f"| `concept_id` mapped | {diag['with_cid']} / {n} ({_pct(diag['with_cid'], n)}) |",
        f"| **Basic-vocab core coverage** | **{diag['core_hit']} / {diag['core_total']}** |",
        f"| Segments source/profile-clean | {diag['seg'].get('source', 0) + diag['seg'].get('profile', 0)} / {n} |",
        f"| Segments unclean | {diag['seg'].get('unclean', 0)} / {n} |",
        f"| Forms with Cognacy | {diag['with_cognacy']} / {n} ({_pct(diag['with_cognacy'], n)}) |",
        "",
        "## 3. Candidate sources",
        "",
        "_To be filled: other sources considered, coverage, verdict, and reason._",
        "",
        "## 4. Transcription",
        "",
        f"Segment status — source: {diag['seg'].get('source', 0)}, profile: {diag['seg'].get('profile', 0)}, "
        f"resegmented: {diag['seg'].get('resegmented', 0)}, unclean: {diag['seg'].get('unclean', 0)}.",
        "",
        "## 5. Concepts",
        "",
        f"{_pct(diag['with_cid'], n)} `concept_id` coverage; {diag['core_hit']} of "
        f"{diag['core_total']} basic-vocabulary core concepts present.",
        "",
        "## 6. Cognates",
        "",
        f"{_pct(diag['with_cognacy'], n)} of forms carry Cognacy from {csrc or tsrc}. "
        "Computed cognates, if added later, must pass the evaluation gate and be recorded "
        "with method metadata (see workflow spec).",
        "",
        "## 7. Recommended recipe & follow-up",
        "",
        "_To be filled: keep as-is, or the concrete improvement and whether its gain "
        "justifies departing from the single-source construction._",
        "",
        "## 8. Gains / losses vs alternatives",
        "",
        "_To be filled._",
        "",
    ]
    return "\n".join(rows)


def scaffold_packet(av_id: str, variety_root: Path, core_concepts: set[str],
                    expert_datasets: set[str], overwrite: bool = False) -> dict:
    """Write recipe.yaml + PACKET.md for one variety. Returns a status dict."""
    import yaml

    config_path = variety_root / "config.yaml"
    if not config_path.exists():
        return {"av_id": av_id, "status": "no-config"}
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    generated = variety_root / "generated" / "forms.csv"
    if not generated.exists():
        return {"av_id": av_id, "status": "not-built"}

    diag = diagnose(generated, core_concepts)
    strat, profile_ref, over_ref = _transcription_strategy(variety_root / "custom")
    cmap = variety_root / "custom" / "concept_map.csv"
    concept_map_used = cmap.exists() and cmap.stat().st_size > 0

    recipe_path = variety_root / "recipe.yaml"
    packet_path = variety_root / "PACKET.md"
    if (recipe_path.exists() or packet_path.exists()) and not overwrite:
        return {"av_id": av_id, "status": "exists", "diag": diag}

    recipe_path.write_text(
        build_recipe_yaml(av_id, config, diag, expert_datasets, strat, profile_ref,
                          over_ref, concept_map_used),
        encoding="utf-8",
    )
    packet_path.write_text(build_packet_md(av_id, config, diag), encoding="utf-8")
    return {"av_id": av_id, "status": "written", "diag": diag}
