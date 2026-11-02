"""Build deterministic All accepted release candidates with per-source terms.

This is a packaging audit, not a new blanket license or permission assessment.
Archive bytes are streamed; existing destinations are never overwritten.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
import tarfile
from collections import Counter
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(sys.maxsize)


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024**2), b""):
            result.update(block)
    return result.hexdigest()


def runtime():
    packages = {}
    for name in ("arcaverborum", "merkmal", "numpy", "pandas", "PyYAML", "requests",
                 "infomap", "igraph", "leidenalg"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    import merkmal

    return dict(python=sys.version, packages=packages, merkmal_have_utf8proc=merkmal.HAVE_UTF8PROC)


def verify_archive(path, expected):
    """Stream-check every member; a partial/stale or extra payload cannot be sealed."""
    seen = set()
    with tarfile.open(path, mode="r|gz") as archive:
        for member in archive:
            if not member.isfile() or member.name not in expected or member.name in seen:
                raise ValueError("Unexpected or duplicate release member: " + member.name)
            seen.add(member.name)
            handle = archive.extractfile(member)
            if hashlib.file_digest(handle, "sha256").hexdigest() != expected[member.name]:
                raise ValueError("Release member changed during packaging: " + member.name)
    if seen != set(expected):
        raise ValueError("Incomplete release archive")


def build(root, output, date, archive=False):
    output.mkdir(parents=True, exist_ok=False)
    aggregate = root / "output/aggregate"
    counts, evidence, sources = Counter(), Counter(), Counter()
    with (aggregate / "forms.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            if not row["av_id"] or not row["source_form_id"]:
                raise ValueError("Release record lacks stable variety/source identity")
            counts[row["av_id"]] += 1
            evidence[row["Segments_Source"]] += 1
            sources[row["transcription_source"]] += 1
    if not counts:
        raise ValueError("Refusing an empty collection release")
    catalog_path = root / "web/data/catalog.json.gz"
    with gzip.open(catalog_path, "rt") as handle:
        catalog = json.load(handle)
    accepted = {row["av_id"]: row for row in catalog["languages"]}
    if not set(counts).issubset(accepted):
        raise ValueError("Aggregate includes a construction outside the public accepted catalog")
    if any(counts[av] != int(row["forms"]) for av, row in accepted.items()):
        raise ValueError("Accepted catalog is stale relative to aggregate forms")
    recording_files, recordings = [], 0
    for av, row in accepted.items():
        n = int(row.get("recordings", 0))
        if n:
            path = root / "varieties" / av / "generated/recordings.csv"
            with path.open(newline="") as handle:
                if sum(1 for _ in csv.DictReader(handle)) != n:
                    raise ValueError("Recording catalog differs from accepted original recording rows")
            recording_files.append(path)
            recordings += n
        if not counts[av] and not n:
            raise ValueError("Refusing an empty accepted construction without recordings")
        sources.setdefault(row["transcription_source"], 0)
    with (aggregate / "metadata.csv").open(newline="") as handle:
        metadata = {r["Dataset"]: r for r in csv.DictReader(handle)}
    missing = set(sources) - set(metadata)
    if missing:
        raise ValueError(f"Missing source attribution: {sorted(missing)}")
    tables = ("forms.csv", "varieties.csv", "parameters.csv", "metadata.csv", "sources.bib")
    paths = [aggregate / name for name in tables
             if (aggregate / name).exists()]
    paths += [root / "datasets.csv", catalog_path, *recording_files]
    data = root / "src/arcaverborum/data"
    paths += [p for p in data.rglob("*") if p.is_file()]
    paths += list((root / "src").rglob("*.py"))
    paths += list((root / "scripts").glob("*.py"))
    paths += [root / name for name in ("build.py", "pyproject.toml", "uv.lock", "ONBOARDING.md", "CONTEXT.md",
                                     "CITATION.cff", "LICENSE")
              if (root / name).exists()]
    for av in sorted(accepted):
        directory = root / "varieties" / av
        if not (directory / "config.yaml").exists():
            raise ValueError(f"Missing accepted construction recipe: {av}")
        paths += [directory / "config.yaml"]
        paths += [p for p in directory.rglob("*") if p.is_file()
                  and ("custom" in p.relative_to(directory).parts or p.name == "recipe.yaml")]
    paths = sorted(set(paths), key=lambda p: str(p.relative_to(root)))
    files = [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in paths]
    source_terms = [{"source": s, "accepted_records": sources[s], "title": metadata[s].get("Title", ""),
                     "citation": metadata[s].get("Citation", ""), "url": metadata[s].get("URL", ""),
                     "license": metadata[s].get("License", ""),
                     "upstream_version": metadata[s].get("Repository_Version", ""),
                     "terms_status": "declared_not_reaudited" if metadata[s].get("License") else "missing_declaration"}
                    for s in sorted(sources)]
    manifest = dict(schema=1, collection="All accepted", release_candidate=date,
                    accepted_constructions=len(accepted), lexical_constructions=sum(n > 0 for n in counts.values()),
                    recording_only_constructions=sum(not counts[av] for av in accepted), recordings=recordings,
                    records=sum(counts.values()),
                    runtime=runtime(),
                    evidence_counts=dict(evidence), source_terms=source_terms, files=files,
                    qualification="Constructions are not independent living languages; source namespaces and "
                    "bibliography keys do not establish independent fieldwork. Source-specific cognacy is "
                    "not colexification. WordNet candidate/association/typed links remain distinct.",
                    licensing="Per-source declarations are retained, not replaced by a blanket license. "
                    "Missing or restrictive terms require review before a separately redistributed release.",
                    evidence="source means supplied/upstream-converted, not certified IPA; profile means "
                    "reviewed source-specific conversion; resegmented and unclean retain limitations.")
    encoded = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (output / "manifest.json").write_text(encoded)
    readme = output / "RELEASE_README.txt"
    readme.write_text(
        f"Arca Verborum — All accepted, {date} (release candidate)\n\n"
        "This dated whole-collection candidate is distinct from the historical Core release and "
        "from the earlier project version in the archived root CITATION.cff. No new version DOI "
        "is asserted. Cite this candidate by date and archive SHA256, together with the original "
        "sources used in your selection.\n\n"
        "Per-source attribution, versions and declared terms are in manifest.json and "
        "output/aggregate/metadata.csv; bibliography is in output/aggregate/sources.bib. "
        "The code license does not replace underlying data terms. Missing/restrictive terms "
        "require review before separate redistribution.\n\n"
        "Accepted constructions include recording-only entries; neither construction count nor "
        "source namespaces measure independent living languages or field collections. Supplied "
        "segments can be upstream conversions; written evidence and ASJP-derived reductions retain "
        "their limitations. Typed WordNet links do not remap native senses. Source cognacy "
        "is distinct from colexification.\n\n"
        "The archive freezes accepted analytic inputs and recipes. Reacquiring source documents "
        "or rebuilding compiled dependencies can require additional permissions and platform work. "
        "Every packaged input is hashed; archive ordering and metadata are deterministic.\n")
    if archive:
        dest = output / f"arca-all-accepted-{date}.tar.gz"
        with dest.open("wb") as raw, gzip.GzipFile(fileobj=raw, filename="", mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|") as tar:
                for path in paths + [output / "manifest.json", readme]:
                    name = path.name if path.parent == output else str(path.relative_to(root))
                    info = tar.gettarinfo(str(path), arcname=name)
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ""
                    info.mode = 0o644
                    with path.open("rb") as handle:
                        tar.addfile(info, handle)
        expected = {row["path"]: row["sha256"] for row in files}
        expected.update({"manifest.json": sha(output / "manifest.json"), "RELEASE_README.txt": sha(readme)})
        verify_archive(dest, expected)
        (output / "archive-sha256.txt").write_text(sha(dest) + "  " + dest.name + "\n")
        (output / "complete.json").write_text(json.dumps(dict(
            schema=1, verified_members=len(expected), manifest_sha256=sha(output / "manifest.json"),
            archive_sha256=sha(dest), archive_bytes=dest.stat().st_size,
            archive_filename=dest.name), indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--archive", action="store_true")
    a = p.parse_args()
    result = build(a.root, a.output, a.date, a.archive)
    keys = ("collection", "accepted_constructions", "lexical_constructions", "records", "evidence_counts")
    print(json.dumps({k: result[k] for k in keys}, indent=2))
