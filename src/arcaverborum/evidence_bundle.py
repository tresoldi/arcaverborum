"""Export framework ``evidence_bundle`` JSON from the committed web snapshot.

The research web snapshot (``web/data/manifest.json``, ``catalog.json.gz`` and the
family shards) is the only complete accepted-output copy tracked in git, so this
exporter reads it rather than ``output/aggregate`` (absent in a fresh checkout).
Every shard is checked against its manifest SHA-256 and the hashes are recorded
in the bundle, which makes an export reproducible from a commit.

Three outputs are written, deliberately partitioned (see docs/EVIDENCE_BUNDLE.md):

* ``evidence_bundle.json`` -- lawful ``D``: Evidence, FormObs, SenseObs, provisional
  lect-state candidates and retained cross-source conflicts. It carries no cognacy,
  alignment, loan judgment, proto-form or starred form.
* ``door2_cognacy.json`` -- source cognacy (and loan flags / free-text source notes)
  as named Door-2 hypotheses (CONSTITUTION 11.2), keyed to FormObs ids.
* ``sealed/sealed_gold_proto.json`` -- reconstructions (proto-variety rows, rows
  with a ``source_reported_reconstruction`` reading basis, starred forms), withheld
  for hide-the-witness evaluation only.

``validate_bundle`` fails closed if anything from the second or third partition
leaks into the first.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from arcaverborum.historical_evidence import BASES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).resolve().parent / "data"
SOURCE_CLASS_TABLE = DATA_DIR / "evidence_source_classes.csv"
CONSTRUCTION_KINDS = DATA_DIR / "construction_kinds.csv"

SCHEMA_VERSION = "0.1.0"
EXPORTER = "arcaverborum.evidence_bundle"
SIGMA_SCALE = "arca_coarse_ordinal_v0"
DEFAULT_FAMILY = "Indo-European"
#: Latest documentation year (catalog first/last_documented) for a historical stage.
HISTORICAL_STAGE_MAX_YEAR = 1500
#: Last documentation at or before this year makes ``by_documentation`` modality written.
WRITTEN_MODALITY_MAX_YEAR = 1900
STAGE_NAME_RE = re.compile(r"^(Old|Middle|Early(?! Modern)|Ancient|Classical)\b")
PROTO_NAME_RE = re.compile(r"(^Proto-|-proto-)")
#: A star directly before a letter, at a word start: the reconstruction / unattested mark.
STARRED_TOKEN_RE = re.compile(r"(?:^|(?<=[\s(\[{,;/\"'“‘]))\*(?=[^\W\d_]|\()")
RECONSTRUCTION_BASIS = "source_reported_reconstruction"
EXCLUDE_CLASS = "EXCLUDE_SEALED_GOLD"
READING_LABELS = ("Historical reading evidence", "Reading evidence")

#: Keys that must never occur anywhere inside an evidence bundle.
FORBIDDEN_KEYS = {
    "Cognacy", "cognacy", "cognate_sets", "cognate_set", "cognateset_id", "Cognateset_ID",
    "canonical_cognate_id", "Alignment", "alignment", "Morpheme_Index", "Segment_Slice",
    "cognate_source", "Cognate_Detection_Method", "cognate_evidence_source", "Loan", "loan",
    "proto_form", "reconstruction", "PIE", "etymon", "etymon_id",
}

# --------------------------------------------------------------------------- licences

_LICENCES = {
    "https://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
    "CC-BY-4.0": "CC-BY-4.0",
    "https://creativecommons.org/licenses/by-sa/4.0/": "CC-BY-SA-4.0",
    "https://creativecommons.org/licenses/by-nc/4.0/": "CC-BY-NC-4.0",
    "https://creativecommons.org/licenses/by-nc-sa/4.0/": "CC-BY-NC-SA-4.0",
    "https://creativecommons.org/licenses/by-nc-nd/4.0/": "CC-BY-NC-ND-4.0",
    "https://www.gnu.org/licenses/gpl-3.0.html": "GPL-3.0",
    "http://www.opensource.org/licenses/GPL-3.0": "GPL-3.0",
}
#: Sources with no recorded row licence whose upstream terms are documented.
_PRESUMED = {
    "wiktionary": (
        "CC-BY-SA-4.0",
        "Arca records no licence for its frozen English Wiktionary/Kaikki snapshot. English "
        "Wiktionary text is published under CC BY-SA 4.0 (dual GFDL); treated as share-alike "
        "until the snapshot's terms are recorded.",
    ),
}
LICENCE_FLAGS = ("nc", "sa", "nd", "gpl", "unrecorded", "presumed")


def classify_licence(raw: str, source: str) -> dict:
    """Normalize a row licence and derive reuse flags (never invents terms silently)."""
    raw = (raw or "").strip()
    spdx = _LICENCES.get(raw)
    note = ""
    presumed = False
    if spdx is None and source in _PRESUMED:
        spdx, note = _PRESUMED[source]
        presumed = True
    flags = {
        "nc": bool(spdx and "-NC" in spdx),
        "sa": bool(spdx and "-SA" in spdx),
        "nd": bool(spdx and "-ND" in spdx),
        "gpl": bool(spdx and spdx.startswith("GPL")),
        "unrecorded": spdx is None,
        "presumed": presumed,
    }
    out = {"raw": raw, "spdx": spdx, "flags": flags}
    if note:
        out["note"] = note
    if spdx and spdx.startswith("GPL"):
        out["note"] = "GPL-3.0 data component; see docs/RVID_DATA_LICENSE.md and web/data/RVID_NOTICE.txt."
    return out


def licence_excluded(lic: dict, exclusions: set[str]) -> bool:
    """True when a licence matches an ``--exclude-licence`` term (flag or SPDX id)."""
    if not exclusions:
        return False
    if any(lic["flags"].get(flag) for flag in exclusions if flag in LICENCE_FLAGS):
        return True
    return bool(lic["spdx"]) and lic["spdx"].lower() in exclusions


# --------------------------------------------------------------------------- ids

def stable_id(prefix: str, *parts: str, n: int = 24) -> str:
    """Deterministic ID: ``<prefix>-`` + truncated SHA-256 of unit-separated parts."""
    payload = "\x1f".join(["arcaverborum", prefix, *[str(p) for p in parts]])
    return f"{prefix}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:n]}"


def evidence_key(row: dict) -> tuple[str, ...]:
    if row["source_form_id"]:
        return ("v1", row["transcription_source"], row["source_form_id"],
                row.get("source_pronunciation_id", ""), row["av_id"])
    # No source form id: fall back to the source content (flagged in meta.id_basis).
    return ("v1-content", row["transcription_source"], row["av_id"], row["Value"], row["Form"],
            row.get("raw_ipa", ""), row.get("source_parameter_id", ""))


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_id(obj: dict, prefix: str) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(canonical_json(obj).encode('utf-8')).hexdigest()}"


# --------------------------------------------------------------------------- snapshot

@dataclass
class Snapshot:
    web_data: Path
    manifest: dict
    manifest_sha256: str
    catalog: dict
    languages: dict[str, dict] = field(default_factory=dict)
    sources: dict[str, dict] = field(default_factory=dict)
    shards_read: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, web_data: Path) -> Snapshot:
        web_data = Path(web_data)
        manifest_bytes = (web_data / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        cat_path = web_data / Path(manifest["catalog"]["url"]).name
        cat_bytes = cat_path.read_bytes()
        if hashlib.sha256(cat_bytes).hexdigest() != manifest["catalog"]["sha256"]:
            raise ValueError(f"Catalog hash mismatch: {cat_path}")
        catalog = json.loads(gzip.decompress(cat_bytes))
        snap = cls(web_data, manifest, hashlib.sha256(manifest_bytes).hexdigest(), catalog)
        snap.languages = {lang["av_id"]: lang for lang in catalog["languages"]}
        snap.sources = {src["Dataset"]: src for src in catalog["sources"]}
        return snap

    def family_of(self, av_id: str) -> str:
        return self.languages[av_id]["Family"] or "Unclassified"

    def rows(self, family: str):
        meta = self.manifest["shards"][family]
        path = self.web_data / Path(meta["url"]).name
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != meta["sha256"]:
            raise ValueError(f"Shard hash mismatch for {family}: {path}")
        self.shards_read[family] = meta["sha256"]
        fields = self.manifest["fields"]
        for values in json.loads(gzip.decompress(data)):
            yield dict(zip(fields, values, strict=True))

    def record(self) -> dict:
        return {
            "kind": "arcaverborum_web_snapshot",
            "manifest_sha256": self.manifest_sha256,
            "build_date": self.manifest.get("build_date"),
            "counts": self.manifest.get("counts"),
            "catalog_sha256": self.manifest["catalog"]["sha256"],
            "aggregate_source_files": self.manifest.get("source_files", {}),
            "shards": dict(sorted(self.shards_read.items())),
        }


# --------------------------------------------------------------------------- source classes

def load_source_class_table(path: Path = SOURCE_CLASS_TABLE) -> list[dict]:
    with Path(path).open(encoding="utf-8") as f:
        rules = list(csv.DictReader(f))
    seen = set()
    for rule in rules:
        key = (rule["source"], rule["segments_source"], rule["reading_basis"])
        if key in seen:
            raise ValueError(f"Duplicate source-class rule {key}")
        seen.add(key)
        if rule["reading_basis"] not in BASES | {"*", "(none)"}:
            raise ValueError(f"Unknown reading basis in source-class rule {key}")
    return rules


def classify_source(rules: list[dict], source: str, segments_source: str, reading_basis: str) -> dict:
    """Most specific rule wins: reading basis (4) > source (2) > segments source (1)."""
    rb = reading_basis or "(none)"
    best, best_score = [], -1
    for rule in rules:
        score = 0
        for key, value, weight in (("reading_basis", rb, 4), ("source", source, 2),
                                   ("segments_source", segments_source, 1)):
            if rule[key] == value:
                score += weight
            elif rule[key] != "*":
                score = -1
                break
        if score > best_score:
            best, best_score = [rule], score
        elif score == best_score and score >= 0:
            best.append(rule)
    if len(best) != 1:
        raise ValueError(f"Ambiguous or missing source-class rule for {(source, segments_source, rb)}")
    return best[0]


# --------------------------------------------------------------------------- row parsing

def parse_comment(comment: str) -> tuple[dict, str]:
    """Split Arca's appended reading-evidence JSON from the source's own note."""
    comment = comment or ""
    evidence: dict = {}
    spans = []
    decoder = json.JSONDecoder()
    for label in READING_LABELS:
        start = 0
        while (i := comment.find(label + ": {", start)) >= 0:
            j = i + len(label) + 2
            try:
                obj, end = decoder.raw_decode(comment, j)
            except json.JSONDecodeError:
                break
            if not evidence:
                evidence = dict(obj, rule_label=label)
            spans.append((i, end))
            start = end
    note = comment
    for i, end in sorted(spans, reverse=True):
        note = note[:i] + note[end:]
    note = re.sub(r"(;\s*)+", "; ", note).strip(" ;")
    return evidence, note


def _year(value) -> int | None:
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def has_star(text: str) -> bool:
    return "*" in (text or "")


def has_starred_token(text: str) -> bool:
    return bool(STARRED_TOKEN_RE.search(text or ""))


def proto_varieties(snapshot: Snapshot, star_share: dict[str, float] | None = None) -> dict[str, str]:
    """Proto/reconstruction varieties, with the reason each was identified."""
    out = {}
    if CONSTRUCTION_KINDS.exists():
        with CONSTRUCTION_KINDS.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["construction_kind"] == "reconstruction":
                    out[row["av_id"]] = "construction_kind=reconstruction"
    for av_id, lang in snapshot.languages.items():
        if av_id not in out and (PROTO_NAME_RE.search(av_id) or PROTO_NAME_RE.search(lang["Name"])):
            out[av_id] = "proto name"
    for av_id, share in (star_share or {}).items():
        if av_id not in out and share > 0.5:
            out[av_id] = f"majority starred forms ({share:.2f})"
    return out


def _reading_rule_present(av_id: str, varieties_dir: Path) -> bool:
    # Only *historical* reading rules: custom/reading_evidence.csv documents modern readings.
    return (varieties_dir / av_id / "custom" / "historical_evidence.csv").exists()


def default_varieties(snapshot: Snapshot, varieties_dir: Path, family: str = DEFAULT_FAMILY) -> dict[str, list[str]]:
    """Derive the ancient/historical-stage set of a family from tracked data.

    A variety is selected when it has a reviewed historical reading rule, a catalog
    documentation date at or before ``HISTORICAL_STAGE_MAX_YEAR``, or a stage
    name (Old/Middle/Early/Ancient/Classical/Archaic). Proto varieties are not
    selected (they only ever reach the sealed gold file).
    """
    protos = proto_varieties(snapshot)
    out = {}
    for av_id, lang in sorted(snapshot.languages.items()):
        if lang["Family"] != family or av_id in protos:
            continue
        reasons = []
        if _reading_rule_present(av_id, varieties_dir):
            reasons.append("reading_rule")
        years = [y for y in (_year(lang.get("first_documented")), _year(lang.get("last_documented")))
                 if y is not None]
        if years and min(years) <= HISTORICAL_STAGE_MAX_YEAR:
            reasons.append(f"documented<={HISTORICAL_STAGE_MAX_YEAR}")
        if STAGE_NAME_RE.search(lang["Name"]):
            reasons.append("stage_name")
        if reasons:
            out[av_id] = reasons
    return out


# --------------------------------------------------------------------------- profiles

class ProfileIndex:
    """Resolve the profile behind a ``profile`` row and the FLAG notes it applied."""

    def __init__(self, varieties_dir: Path):
        self.varieties_dir = Path(varieties_dir)
        self._cache: dict[tuple[str, str], dict | None] = {}

    def _load(self, av_id: str, source: str) -> dict | None:
        from arcaverborum.phonology import load_profile

        custom = self.varieties_dir / av_id / "custom"
        config_path = self.varieties_dir / av_id / "config.yaml"
        primary = ""
        if config_path.exists():
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            primary = ((config.get("sources") or {}).get("transcription")) or ""
        path = None
        if source == primary and (custom / "profile.tsv").exists():
            path = custom / "profile.tsv"
        elif (custom / "supplements.csv").exists():
            with (custom / "supplements.csv").open(encoding="utf-8") as f:
                files = {r.get("profile_file", "") for r in csv.DictReader(f) if r.get("source") == source}
            files.discard("")
            if len(files) == 1:
                path = custom / "supplement_profiles" / files.pop()
        if path is None or not path.exists():
            return None
        flags = {}
        with path.open(encoding="utf-8") as f:
            f.readline()
            for line in f:
                cols = line.rstrip("\n").split("\t")
                if len(cols) >= 3 and "FLAG" in cols[2] and cols[0]:
                    flags[unicodedata.normalize("NFC", cols[0])] = (cols[1].strip(), cols[2].strip())
        rel = path.relative_to(self.varieties_dir.parent) if path.is_relative_to(self.varieties_dir.parent) else path
        return {
            "path": str(rel),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "profile": load_profile(path),
            "flags": flags,
        }

    def steps(self, row: dict) -> tuple[list[str], dict]:
        from arcaverborum.phonology import apply_profile

        key = (row["av_id"], row["transcription_source"])
        if key not in self._cache:
            self._cache[key] = self._load(*key)
        prof = self._cache[key]
        if prof is None:
            return [f"profile:{row['av_id']}/{row['transcription_source']}@unresolved"], {"profile_resolved": False}
        steps = [f"profile:{prof['path']}@sha256:{prof['sha256'][:16]}"]
        form = unicodedata.normalize("NFC", row["Form"] or row["Value"])
        for grapheme, (ipa, note) in sorted(prof["flags"].items()):
            if grapheme in form:
                steps.append(f"flag:{grapheme}→{ipa or '∅'} ({note})")
        replay, _ = apply_profile(row["Form"] or row["Value"], prof["profile"])
        replay_ok = replay == row["Segments"]
        if not replay_ok and row["Value"] != row["Form"]:
            replay_ok = apply_profile(row["Value"], prof["profile"])[0] == row["Segments"]
        return steps, {"profile_resolved": True, "profile_replay_matches_snapshot": replay_ok}


# --------------------------------------------------------------------------- sigma

_SEG_LEVEL = {"source": 1, "profile": 2, "resegmented": 4, "unclean": 4, "": 5}
_BASIS_LEVEL = {
    "": 1, "source_reported_pronunciation": 1, "source_reported_phonemic_citation": 1,
    "upstream_profile_conversion": 2, "profile_inferred_broad_reading": 3,
    "unspecified_historical_reading": 3, "source_reported_historical_reading": 3,
    "automatic_transcription_conversion": 4, "orthographic_transcription_only": 5,
}
SIGMA_LABELS = {
    1: "supplied_transcription",
    2: "derived_by_reviewed_conversion",
    3: "historical_or_lemma_reading",
    4: "mechanical_or_unvalidated",
    5: "no_segment_hypothesis",
}


def sigma_for(segments_source: str, segments: str, reading_basis: str, rule: dict, gled_dependence: str) -> dict:
    seg_level = _SEG_LEVEL.get(segments_source, 4) if segments else 5
    components = {
        "segments_source": seg_level,
        "reading_basis": _BASIS_LEVEL.get(reading_basis or "", 3),
        "source_class_floor": int(rule["sigma_floor"] or 1),
    }
    if gled_dependence and gled_dependence != "none":
        components["asjp_dependence"] = 3
    level = max(components.values())
    return {
        "scale": SIGMA_SCALE,
        "level": level,
        "label": SIGMA_LABELS[level],
        "components": components,
        "provenance_missing": False,
    }


# --------------------------------------------------------------------------- export

@dataclass
class ExportOptions:
    av_ids: list[str] | None = None
    exclude_licence: set[str] = field(default_factory=set)
    gold_scope: str = "family"  # selected | family | all
    web_data: Path = PROJECT_ROOT / "web" / "data"
    varieties_dir: Path = PROJECT_ROOT / "varieties"
    source_class_table: Path = SOURCE_CLASS_TABLE


def _code_pin() -> dict:
    pin = {"exporter": EXPORTER, "schema_version": SCHEMA_VERSION}
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        pin["git_sha"] = sha
    except (OSError, subprocess.CalledProcessError):
        pin["git_sha"] = None
    return pin


def _modality(rule: dict, lang: dict) -> str:
    if rule["modality"] != "by_documentation":
        return rule["modality"]
    last = _year(lang.get("last_documented"))
    return "written_document" if last is not None and last <= WRITTEN_MODALITY_MAX_YEAR else "spoken"


def _gold_entry(row: dict, reason: str, reading: dict, lic: dict, lang: dict) -> dict:
    sets = _cognate_set_ids(row)
    return {
        "gold_id": stable_id("av-gold", *evidence_key(row)),
        "reason": reason,
        "av_id": row["av_id"],
        "variety_name": row["Variety_Name"],
        "glottocode": row["Glottocode"],
        "family": lang.get("Family", ""),
        "source_id": row["transcription_source"],
        "source_form_id": row["source_form_id"],
        "value": row["Value"],
        "form": row["Form"],
        "segments": row["Segments"],
        "segments_source": row["Segments_Source"],
        "concept_id": row["concept_id"],
        "concepticon_id": row["Concepticon_ID"],
        "source_gloss": row["source_gloss"],
        "reading_basis": reading.get("reading_basis"),
        "language_stage": reading.get("language_stage"),
        "cognate_source": row["cognate_source"] if sets else "",
        "cognate_set_ids": [f"{row['cognate_source']}:{s}" for s in sets],
        "licence": lic,
    }


def _cognate_set_ids(row: dict) -> list[str]:
    raw = row.get("cognate_sets") or ""
    ids: list[str] = []
    if raw.startswith("["):
        try:
            ids = [str(x) for x in json.loads(raw) if str(x)]
        except json.JSONDecodeError:
            ids = []
    if not ids and row.get("Cognacy"):
        ids = [x.strip() for x in re.split(r"[,;]", row["Cognacy"]) if x.strip()]
    return ids


def export(options: ExportOptions) -> dict:
    """Build the three partitions in memory. Returns a dict of JSON-ready objects."""
    snap = Snapshot.load(options.web_data)
    rules = load_source_class_table(options.source_class_table)
    profiles = ProfileIndex(options.varieties_dir)
    exclusions = {e.strip().lower() for e in options.exclude_licence if e.strip()}

    if options.av_ids:
        unknown = [a for a in options.av_ids if a not in snap.languages]
        if unknown:
            raise KeyError(f"Unknown av_id(s) in snapshot: {', '.join(unknown)}")
        selection = {a: ["requested"] for a in options.av_ids}
        selection_rule = "explicit av_ids"
    else:
        selection = default_varieties(snap, options.varieties_dir)
        selection_rule = (
            f"{DEFAULT_FAMILY} varieties with a reviewed historical reading rule "
            f"(custom/historical_evidence.csv), or catalog first/last_documented <= {HISTORICAL_STAGE_MAX_YEAR}, or a "
            f"stage name ({STAGE_NAME_RE.pattern}); proto varieties excluded"
        )

    families = sorted({snap.family_of(a) for a in selection})
    if options.gold_scope == "all":
        families = sorted(snap.manifest["shards"])
    totals: Counter = Counter()
    starred: Counter = Counter()
    for fam in families:  # first streaming pass: star share per variety (proto detection)
        for row in snap.rows(fam):
            totals[row["av_id"]] += 1
            starred[row["av_id"]] += row["Value"].lstrip().startswith("*")
    star_share = {a: starred[a] / n for a, n in totals.items() if n}
    protos = proto_varieties(snap, star_share)

    gold_families = set(snap.family_of(a) for a in selection)
    evidence, form_obs, sense_obs = [], [], []
    gold, notes, loans = [], [], []
    memberships: dict[tuple[str, str], dict] = {}
    lect_states: dict[tuple[str, str], dict] = {}
    by_concept: dict[tuple[str, str], list] = defaultdict(list)
    seen_evidence: dict[tuple, dict] = {}
    seen_form_obs: set[str] = set()
    report = Counter()
    licence_counts: dict[str, Counter] = {"evidence": Counter(), "excluded": Counter(), "gold": Counter(),
                                          "door2": Counter()}
    reading_missing: dict[str, Counter] = defaultdict(Counter)
    excluded_varieties = {}

    for fam in families:
        for row in snap.rows(fam):
            av_id = row["av_id"]
            lang = snap.languages.get(av_id, {})
            selected = av_id in selection
            is_proto = av_id in protos
            gold_candidate = is_proto and (
                options.gold_scope == "all"
                or (options.gold_scope == "family" and lang.get("Family") in gold_families)
                or selected
            )
            if not selected and not gold_candidate:
                continue
            reading, note = parse_comment(row["Comment"])
            basis = reading.get("reading_basis", "")
            lic = classify_licence(row["License"], row["transcription_source"])
            if licence_excluded(lic, exclusions):
                licence_counts["excluded"][lic["spdx"] or "unrecorded"] += 1
                report["rows_excluded_by_licence"] += 1
                continue

            reason = None
            if is_proto:
                reason = "proto_variety"
                if selected:
                    excluded_varieties[av_id] = protos[av_id]
            elif basis == RECONSTRUCTION_BASIS:
                reason = "reconstruction_reading_basis"
            elif has_star(row["Value"]) or has_star(row["Form"]):
                reason = "starred_form"
            if reason:
                gold.append(_gold_entry(row, reason, reading, lic, lang))
                licence_counts["gold"][lic["spdx"] or "unrecorded"] += 1
                report[f"gold_{reason}"] += 1
                continue
            if not selected:
                continue

            rule = classify_source(rules, row["transcription_source"], row["Segments_Source"], basis)
            if rule["source_class"] == EXCLUDE_CLASS:  # defensive: table-driven exclusion
                gold.append(_gold_entry(row, "excluded_source_class", reading, lic, lang))
                continue

            key = evidence_key(row)
            ev_id = stable_id("av-ev", *key)
            src_meta = snap.sources.get(row["transcription_source"], {})
            if key in seen_evidence:
                if seen_evidence[key]["raw_string"] != row["Value"]:
                    raise ValueError(f"Evidence key collision with different raw strings: {key}")
                ev = seen_evidence[key]
            else:
                stage = reading.get("language_stage", "")
                ls_key = (av_id, stage)
                if ls_key not in lect_states:
                    lect_states[ls_key] = {
                        "lect_state_candidate_id": stable_id("av-lsc", av_id, stage),
                        "status": "provisional",
                        "provisional_variety_ref": av_id,
                        "glottocode": lang.get("Glottocode") or None,
                        "name": lang.get("Name", row["Variety_Name"]),
                        "family": lang.get("Family") or None,
                        "language_stage": stage or None,
                        "first_documented": _year(lang.get("first_documented")),
                        "last_documented": _year(lang.get("last_documented")),
                        "identity_level": lang.get("identity_level") or None,
                        "selection_reasons": selection[av_id],
                        "sources": [],
                        "note": "Catalog variety projected as a lect-state candidate; variety is not "
                                "lect-state (CONSTITUTION 3.5). Dates are catalog documentation bounds, "
                                "not per-form attestation dates.",
                    }
                if row["transcription_source"] not in lect_states[ls_key]["sources"]:
                    lect_states[ls_key]["sources"].append(row["transcription_source"])
                if not basis:
                    reading_missing[av_id][row["transcription_source"]] += 1
                ev_meta = {
                    "av_id": av_id,
                    "glottocode": row["Glottocode"] or None,
                    "variety_name": row["Variety_Name"],
                    "lect_state_candidate_ref": lect_states[ls_key]["lect_state_candidate_id"],
                    "source_form_id": row["source_form_id"],
                    "source_language_id": row["source_language_id"],
                    "source_parameter_id": row["source_parameter_id"],
                    "source_pronunciation_id": row["source_pronunciation_id"] or None,
                    "source_form": row["Form"],
                    "raw_ipa": row["raw_ipa"] or None,
                    "pronunciation_tags": row["pronunciation_tags"] or None,
                    "bibtex_key": row["bibtex_key"] or None,
                    "source_version": src_meta.get("Repository_Version") or None,
                    "source_url": src_meta.get("URL") or None,
                    "licence": lic,
                    "reading_basis": basis or None,
                    "reading_basis_missing": not basis,
                    "language_stage": reading.get("language_stage"),
                    "reading_authority": reading.get("authority"),
                    "reading_period": reading.get("period"),
                    "reading_notes": reading.get("notes"),
                    "reading_rule_label": reading.get("rule_label"),
                    "source_class_rule": "|".join((rule["source"], rule["segments_source"], rule["reading_basis"])),
                    "source_class_fallback": rule["source"] == "*" and rule["reading_basis"] == "*",
                    "evidence_role": row["evidence_role"] or None,
                    "representation_basis": row["representation_basis"] or None,
                    "phonological_marks": row["phonological_marks"] or None,
                    "gled_dependence": row["gled_dependence"] or None,
                    "source_note_withheld": bool(note),
                    "id_basis": key[0],
                    "arca_row_id_volatile": row["ID"],
                }
                ev = {
                    "evidence_id": ev_id,
                    "source_id": row["transcription_source"],
                    "source_class": rule["source_class"],
                    "cite": src_meta.get("Citation") or src_meta.get("Title") or None,
                    "raw_string": row["Value"],
                    "script_or_orthography": None,
                    "collector": None,
                    "date": None,
                    "modality": _modality(rule, lang),
                    "meta": ev_meta,
                }
                seen_evidence[key] = ev
                evidence.append(ev)
                licence_counts["evidence"][lic["spdx"] or "unrecorded"] += 1
                if note:
                    notes.append({"evidence_id": ev_id, "source_id": row["transcription_source"], "note": note})

            # FormObs -----------------------------------------------------------
            seg_src = row["Segments_Source"]
            segs = row["Segments"].strip()
            steps: list[str] = []
            prof_meta: dict = {}
            if seg_src == "source":
                version = src_meta.get("Repository_Version") or "unversioned"
                steps += [f"source_segments:{row['transcription_source']}@{version}",
                          "merkmal_canonicalize:descriptive@unpinned"]
            elif seg_src == "profile":
                p_steps, prof_meta = profiles.steps(row)
                steps += p_steps
            elif seg_src == "resegmented":
                steps += ["resegment:merkmal_descriptive@unpinned"]
            elif seg_src == "unclean" and segs:
                steps += [f"source_segments:{row['transcription_source']}", "validation_failed:kept_verbatim"]
            fo_id = stable_id("av-fo", ev_id, seg_src, segs, *steps)
            if fo_id not in seen_form_obs:
                seen_form_obs.add(fo_id)
                fo = {
                    "form_obs_id": fo_id,
                    "lect_state_ref": None,
                    "provisional_variety_ref": av_id,
                    "lect_state_candidate_ref": ev["meta"]["lect_state_candidate_ref"],
                    "derived_from": [ev_id],
                    "segment_hypothesis": segs.split() if segs else None,
                    "segments_status": seg_src or "none",
                    "sigma": sigma_for(seg_src, segs, basis, rule, row["gled_dependence"]),
                    "pipeline_steps": steps,
                    "blank_type": "none" if segs else "segment_hypothesis_absent",
                }
                if prof_meta:
                    fo["profile_check"] = prof_meta
                    report["profile_rows"] += 1
                    report["profile_replay_mismatch"] += not prof_meta.get("profile_replay_matches_snapshot", False)
                form_obs.append(fo)
                report[f"sigma_level_{fo['sigma']['level']}"] += 1

            # SenseObs ----------------------------------------------------------
            gloss = row["source_gloss"]
            gloss_withheld = has_starred_token(gloss)
            if gloss_withheld:
                notes.append({"evidence_id": ev_id, "source_id": row["transcription_source"],
                              "note": f"source gloss withheld from SenseObs (starred token): {gloss}"})
                report["glosses_withheld_starred"] += 1
            link = None
            if row["concept_id"]:
                link = {
                    "id": row["Concepticon_ID"] or None,
                    "weight": 1.0,
                    "role": "q",
                    "link_source": "arcaverborum_concept_map",
                    "arca_concept_id": row["concept_id"],
                    "mapping_review": row["mapping_review"] or None,
                    "mapping_note": row["mapping_note"] or None,
                }
            reviewed = (row["mapping_review"] or "").split(";")[0] not in {"", "source mapping"}
            so = {
                "sense_obs_id": stable_id("av-so", ev_id, row["source_parameter_id"], row["concept_id"], gloss),
                "form_obs_ref": fo_id,
                "gloss_raw": None if gloss_withheld else (gloss or None),
                "gloss_withheld": gloss_withheld,
                "sense_atom_ref": None,
                "concepticon_link": link,
                "sigma": {"scale": SIGMA_SCALE, "level": 2 if reviewed else 3,
                          "label": "reviewed_mapping" if reviewed else "unreviewed_source_mapping",
                          "provenance_missing": not gloss},
                "derived_from": [ev_id],
            }
            sense_obs.append(so)
            if row["concept_id"]:
                by_concept[(av_id, row["concept_id"])].append((row["transcription_source"], row["Value"], fo_id))

            # Door-2 material -----------------------------------------------------
            for set_id in _cognate_set_ids(row):
                method = row["Cognate_Detection_Method"] or "unspecified"
                h_key = (row["cognate_source"], method)
                hyp = memberships.setdefault(h_key, {"sets": defaultdict(list), "licences": Counter()})
                hyp["sets"][f"{row['cognate_source']}:{set_id}"].append({
                    "form_obs_id": fo_id,
                    "evidence_id": ev_id,
                    "doubt": (row["Doubt"] or "").lower() == "true" if row["Doubt"] else None,
                    "alignment": row["Alignment"] or None,
                    "morpheme_index": row["Morpheme_Index"] or None,
                    "segment_slice": row["Segment_Slice"] or None,
                    "canonical_cognate_id": row["canonical_cognate_id"] or None,
                })
                hyp["licences"][lic["spdx"] or "unrecorded"] += 1
                licence_counts["door2"][lic["spdx"] or "unrecorded"] += 1
            if row["Loan"] in {"true", "True"}:
                loans.append({"form_obs_id": fo_id, "evidence_id": ev_id, "source_id": row["transcription_source"],
                              "loan": True})

    conflicts = []
    for (av_id, concept), items in sorted(by_concept.items()):
        srcs = {s for s, _, _ in items}
        values = {unicodedata.normalize("NFC", v).casefold() for _, v, _ in items}
        if len(srcs) > 1 and len(values) > 1:
            refs = sorted({f for _, _, f in items})
            conflicts.append({
                "conflict_id": stable_id("av-cf", av_id, concept, *refs),
                "kind": "cross_source_divergence",
                "provisional_variety_ref": av_id,
                "arca_concept_id": concept,
                "sources": sorted(srcs),
                "form_obs_refs": refs,
                "resolution": None,
                "note": "Retained source disagreement; no projection_policy applied. Arca's preferred_source "
                        "is a display choice, not deletion (CONSTITUTION 3.5).",
            })

    bundle = {
        "schema": "evidence_bundle",
        "schema_version": SCHEMA_VERSION,
        "role": "D",
        "projection_policy": None,
        "producer": _code_pin(),
        "snapshot": snap.record(),
        "selection": {
            "rule": selection_rule,
            "varieties": {a: r for a, r in sorted(selection.items()) if a not in excluded_varieties},
            "excluded_proto_varieties": excluded_varieties,
        },
        "filters": {"exclude_licence": sorted(exclusions)},
        "conventions": {
            "ids": "docs/EVIDENCE_BUNDLE.md#stable-ids",
            "sigma_scale": SIGMA_SCALE,
            "source_class_table": "src/arcaverborum/data/evidence_source_classes.csv",
            "extension_fields": ["meta.*", "FormObs.provisional_variety_ref", "FormObs.lect_state_candidate_ref",
                                 "FormObs.segments_status", "FormObs.profile_check", "SenseObs.gloss_withheld",
                                 "concepticon_link.{role,link_source,arca_concept_id,mapping_review,mapping_note}"],
        },
        "evidence": evidence,
        "form_obs": form_obs,
        "sense_obs": sense_obs,
        "lect_state_candidates": sorted(lect_states.values(), key=lambda r: r["lect_state_candidate_id"]),
        "conflicts": conflicts,
    }
    # The content hash covers the data, snapshot pins and selection, not the code pin, so
    # re-exporting the same snapshot from a later commit keeps the id when the output is unchanged.
    bundle_id = content_id({k: v for k, v in bundle.items() if k != "producer"}, "evidence_bundle")
    bundle = {"bundle_id": bundle_id, **bundle}

    hypotheses = []
    for (source, method), hyp in sorted(memberships.items()):
        src_meta = snap.sources.get(source, {})
        hyp_id = stable_id("av-h2", source, method)
        sets = [{"set_id": sid, "members": sorted(m, key=lambda x: x["form_obs_id"])}
                for sid, m in sorted(hyp["sets"].items())]
        hypotheses.append({
            "hypothesis_id": hyp_id,
            "kind": "cognacy_partition",
            "door": 2,
            "label": f"{source} cognacy ({method})",
            "producer": source,
            "source_id": source,
            "source_version": src_meta.get("Repository_Version") or None,
            "cite": src_meta.get("Citation") or None,
            "detection_method": method,
            "prior_mass": None,
            "prior_mass_note": "Unassigned. A consumer must either declare prior mass for this named "
                               "hypothesis against its rivals or run condition_on with the taint label.",
            "taint_label": f"conditional_on:{hyp_id}",
            "licences": dict(sorted(hyp["licences"].items())),
            "partial": "Memberships restricted to the exported FormObs; sets are not closed over "
                       "unexported varieties.",
            "n_sets": len(sets),
            "n_memberships": sum(len(s["members"]) for s in sets),
            "sets": sets,
        })
    door2 = {
        "schema": "door2_hypothesis_package",
        "schema_version": SCHEMA_VERSION,
        "role": "door2_hypothesis",
        "evidence_bundle_ref": bundle_id,
        "conditioning_rule": "Expert cognacy, loan judgments and etymological notes are historical conclusions "
                             "(CONSTITUTION 1.1, 11.2). Each hypothesis enters only as a named hypothesis with "
                             "prior mass or as condition_on=H; every downstream artifact must then carry "
                             "H's taint_label and may not be used to confirm H. Never merge into D.",
        "hypotheses": hypotheses,
        "loan_annotations": {
            "hypothesis_id": stable_id("av-h2", "loan_flags"),
            "kind": "loan_flags",
            "taint_label": f"conditional_on:{stable_id('av-h2', 'loan_flags')}",
            "items": sorted(loans, key=lambda x: x["form_obs_id"]),
        },
        "source_notes": {
            "kind": "source_notes",
            "note": "Free-text source comments and withheld glosses. They may contain etymologies, "
                    "reconstructions and cognate pointers, so they are kept out of D.",
            "items": sorted(notes, key=lambda x: (x["evidence_id"], x["note"])),
        },
    }
    door2 = {"package_id": content_id(door2, "door2_package"), **door2}

    gold.sort(key=lambda g: g["gold_id"])
    sealed = {
        "schema": "sealed_gold",
        "schema_version": SCHEMA_VERSION,
        "role": "sealed_gold",
        "sealed": True,
        "use": "Hide-the-witness evaluation only. Never an inference input; read only after predictions "
               "are frozen. Entries are source-reported reconstructions or unattested (starred) forms.",
        "evidence_bundle_ref": bundle_id,
        "gold_scope": options.gold_scope,
        "proto_varieties": {a: protos[a] for a in sorted({g["av_id"] for g in gold} & set(protos))},
        "entries": gold,
    }
    sealed = {"gold_id": content_id(sealed, "sealed_gold"), **sealed}

    lic_summary = {k: dict(sorted(v.items())) for k, v in licence_counts.items()}
    flag_counts = Counter()
    for ev in evidence:
        for flag, on in ev["meta"]["licence"]["flags"].items():
            flag_counts[flag] += bool(on)
    export_report = {
        "evidence_bundle": bundle_id,
        "door2_package": door2["package_id"],
        "sealed_gold": sealed["gold_id"],
        "counts": {
            "varieties_selected": len(bundle["selection"]["varieties"]),
            "varieties_with_evidence": len({e["meta"]["av_id"] for e in evidence}),
            "evidence": len(evidence),
            "form_obs": len(form_obs),
            "sense_obs": len(sense_obs),
            "lect_state_candidates": len(bundle["lect_state_candidates"]),
            "conflicts": len(conflicts),
            "sealed_gold_entries": len(gold),
            "door2_hypotheses": len(hypotheses),
            "door2_sets": sum(h["n_sets"] for h in hypotheses),
            "door2_memberships": sum(h["n_memberships"] for h in hypotheses),
            "loan_flags": len(loans),
            "source_notes_withheld": len(notes),
            **dict(sorted(report.items())),
        },
        "licences": lic_summary,
        "evidence_licence_flags": dict(sorted(flag_counts.items())),
        "source_classes": dict(sorted(Counter(e["source_class"] for e in evidence).items())),
        "reading_rules_missing": {
            a: dict(sorted(c.items())) for a, c in sorted(reading_missing.items())
        },
        "reading_rules_missing_note": (
            "Selected varieties whose rows carry no reviewed reading rule. Rules are not inferred: the "
            "existing custom/historical_evidence.csv rows came from the AN01 reviewed identity audit, not "
            "from source metadata alone. Add rules through that review, then rebuild and re-export."
        ),
    }
    return {"bundle": bundle, "door2": door2, "sealed": sealed, "report": export_report}


# --------------------------------------------------------------------------- validation

def _walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, f"{path}.{k}"
            yield from _walk_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_keys(v, f"{path}[{i}]")


def validate_bundle(bundle: dict, proto_av_ids: set[str] | None = None) -> list[str]:
    """Return a list of contract violations (empty when the bundle is lawful D)."""
    errors = []
    for key in ("schema_version", "evidence", "form_obs", "sense_obs", "lect_state_candidates", "conflicts"):
        if key not in bundle:
            errors.append(f"missing top-level key {key}")
    if errors:
        return errors
    for key, path in _walk_keys(bundle):
        if key in FORBIDDEN_KEYS:
            errors.append(f"forbidden key {path}")
    proto_av_ids = proto_av_ids or set()
    ev_ids = set()
    for ev in bundle["evidence"]:
        for k in ("evidence_id", "source_id", "source_class", "raw_string", "modality", "meta"):
            if k not in ev:
                errors.append(f"evidence missing {k}: {ev.get('evidence_id')}")
        if ev["evidence_id"] in ev_ids:
            errors.append(f"duplicate evidence_id {ev['evidence_id']}")
        ev_ids.add(ev["evidence_id"])
        meta = ev.get("meta", {})
        for text in (ev.get("raw_string"), meta.get("source_form"), meta.get("raw_ipa")):
            if has_star(text):
                errors.append(f"starred form in evidence {ev['evidence_id']}: {text!r}")
        if meta.get("reading_basis") == RECONSTRUCTION_BASIS:
            errors.append(f"reconstruction reading basis in evidence {ev['evidence_id']}")
        if ev.get("source_class") == EXCLUDE_CLASS:
            errors.append(f"excluded source class in evidence {ev['evidence_id']}")
        if meta.get("av_id") in proto_av_ids or PROTO_NAME_RE.search(meta.get("av_id", "")):
            errors.append(f"proto variety in evidence {ev['evidence_id']}: {meta.get('av_id')}")
    fo_ids = set()
    for fo in bundle["form_obs"]:
        if fo["form_obs_id"] in fo_ids:
            errors.append(f"duplicate form_obs_id {fo['form_obs_id']}")
        fo_ids.add(fo["form_obs_id"])
        if not fo.get("lect_state_ref") and not fo.get("provisional_variety_ref"):
            errors.append(f"form_obs without lect_state_ref/provisional_variety_ref {fo['form_obs_id']}")
        ref = fo.get("provisional_variety_ref") or ""
        if ref in proto_av_ids or PROTO_NAME_RE.search(ref):
            errors.append(f"proto variety in form_obs {fo['form_obs_id']}: {ref}")
        if any(has_star(t) for t in fo.get("segment_hypothesis") or []):
            errors.append(f"starred segment in form_obs {fo['form_obs_id']}")
        if not fo.get("derived_from") or any(d not in ev_ids for d in fo["derived_from"]):
            errors.append(f"form_obs with unresolved derived_from {fo['form_obs_id']}")
        for k in ("sigma", "pipeline_steps", "blank_type"):
            if k not in fo:
                errors.append(f"form_obs missing {k}: {fo['form_obs_id']}")
    so_ids = set()
    for so in bundle["sense_obs"]:
        if so["sense_obs_id"] in so_ids:
            errors.append(f"duplicate sense_obs_id {so['sense_obs_id']}")
        so_ids.add(so["sense_obs_id"])
        if so.get("form_obs_ref") and so["form_obs_ref"] not in fo_ids:
            errors.append(f"sense_obs with unresolved form_obs_ref {so['sense_obs_id']}")
        if any(d not in ev_ids for d in so.get("derived_from", [])):
            errors.append(f"sense_obs with unresolved derived_from {so['sense_obs_id']}")
        if has_starred_token(so.get("gloss_raw") or ""):
            errors.append(f"starred token in gloss {so['sense_obs_id']}")
    return errors


def validate_door2(door2: dict, bundle: dict) -> list[str]:
    errors = []
    if door2.get("role") != "door2_hypothesis" or door2.get("evidence_bundle_ref") != bundle.get("bundle_id"):
        errors.append("door2 package role/bundle reference mismatch")
    fo_ids = {fo["form_obs_id"] for fo in bundle["form_obs"]}
    for hyp in door2.get("hypotheses", []):
        if hyp.get("door") != 2 or not hyp.get("taint_label", "").startswith("conditional_on:"):
            errors.append(f"hypothesis without Door-2 label/taint: {hyp.get('hypothesis_id')}")
        for s in hyp["sets"]:
            for m in s["members"]:
                if m["form_obs_id"] not in fo_ids:
                    errors.append(f"door2 member not in bundle: {m['form_obs_id']}")
    return errors


# --------------------------------------------------------------------------- writing

def _dump(path: Path, obj: dict) -> None:
    from arcaverborum.fsutil import write_text_atomic

    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(path, json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n")


def write_export(result: dict, out_dir: Path) -> dict[str, Path]:
    protos = set(result["sealed"]["proto_varieties"])
    errors = validate_bundle(result["bundle"], protos) + validate_door2(result["door2"], result["bundle"])
    if errors:
        raise ValueError("Evidence bundle failed validation:\n  " + "\n  ".join(errors[:50]))
    out_dir = Path(out_dir)
    paths = {
        "evidence_bundle": out_dir / "evidence_bundle.json",
        "door2": out_dir / "door2_cognacy.json",
        "sealed_gold": out_dir / "sealed" / "sealed_gold_proto.json",
        "report": out_dir / "export_report.json",
    }
    _dump(paths["evidence_bundle"], result["bundle"])
    _dump(paths["door2"], result["door2"])
    _dump(paths["sealed_gold"], result["sealed"])
    _dump(paths["report"], result["report"])
    return paths
