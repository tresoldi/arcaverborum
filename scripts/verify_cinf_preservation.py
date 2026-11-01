"""Recover the pre-CINF snapshot from Git and verify the bounded fidelity delta.

A dated execution verifier: its expected baseline hash and three repair targets
are frozen in the paper record. Family shards are streamed one row at a time.
"""

import argparse
import csv
import gzip
import hashlib
import json
import resource
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from arcaverborum.colexification import sha

BASELINE_PROJECTION = "f55281bd76fda1297146002526ebf229390fa82016c22ea7c57ece03443676b5"
TARGETS = {"sab-piaroa", "tuc-wa-ikhana", "ara-yucuna"}


def stream_array(path):
    decoder = json.JSONDecoder()
    buffer = ""
    started = False
    with gzip.open(path, "rt") as handle:
        while True:
            buffer = buffer.lstrip()
            if not started:
                if not buffer:
                    buffer = handle.read(65536)
                    if not buffer:
                        raise ValueError("Missing JSON array")
                    continue
                if not buffer.startswith("["):
                    raise ValueError("Expected JSON array")
                buffer = buffer[1:]
                started = True
                continue
            if buffer.startswith(","):
                buffer = buffer[1:]
                continue
            if buffer.startswith("]"):
                return
            try:
                row, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk = handle.read(65536)
                if not chunk:
                    raise ValueError("Incomplete JSON row") from None
                buffer += chunk
                if len(buffer) > 16 * 1024**2:
                    raise ValueError("Reference row exceeds memory budget")
                continue
            buffer = buffer[end:]
            yield row


def snapshot(root, reference, manifest, output):
    process = subprocess.Popen(
        ["git", "-c", "core.packedGitWindowSize=1m", "-c", "core.packedGitLimit=8m", "cat-file", "--batch"],
        cwd=root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    try:
        for entry in manifest["shards"].values():
            process.stdin.write((reference + ":web/" + entry["url"] + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().decode().split()
            if len(header) != 3 or header[1] != "blob":
                raise ValueError("Missing reference shard")
            size = int(header[2])
            path = output / Path(entry["url"]).name
            digest = hashlib.sha256()
            with path.open("wb") as handle:
                while size:
                    chunk = process.stdout.read(min(1024**2, size))
                    if not chunk:
                        raise ValueError("Truncated Git object")
                    size -= len(chunk)
                    handle.write(chunk)
                    digest.update(chunk)
            if process.stdout.read(1) != b"\n" or digest.hexdigest() != entry["sha256"]:
                raise ValueError("Reference shard checksum differs")
    finally:
        process.stdin.close()
        if process.wait() != 0:
            raise ValueError("Git snapshot failed")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--reference", default="f3e152877")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    manifest = json.loads(
        subprocess.check_output(
            [
                "git",
                "-c",
                "core.packedGitWindowSize=1m",
                "-c",
                "core.packedGitLimit=8m",
                "show",
                a.reference + ":web/data/manifest.json",
            ],
            cwd=a.root,
        )
    )
    families = {
        r["av_id"]: r["Family"] or "Unclassified"
        for r in csv.DictReader((a.root / "output/aggregate/varieties.csv").open())
    }
    mapping = {"Cognate_Source": "cognate_evidence_source"}
    old_hash = hashlib.sha256()
    before_native = hashlib.sha256()
    after_native = hashlib.sha256()
    counts, columns = Counter(), Counter()
    examples = []
    n = 0
    unaffected = 0
    with tempfile.TemporaryDirectory(dir=a.output.parent) as temp:
        directory = Path(temp)
        snapshot(a.root, a.reference, manifest, directory)
        readers = {}
        with (a.root / "output/aggregate/forms.csv").open() as handle:
            for row in csv.DictReader(handle):
                av = row["av_id"]
                family = families[av]
                if family not in readers:
                    readers[family] = stream_array(directory / Path(manifest["shards"][family]["url"]).name)
                old = dict(zip(manifest["fields"], next(readers[family]), strict=True))
                assert (old["av_id"], old["source_form_id"]) == (av, row["source_form_id"])
                original = {k: old[mapping.get(k, k)] for k in row}
                if av not in TARGETS:
                    unaffected += 1
                    old_hash.update(
                        json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                    )
                    for data, digest in [(original, before_native), (row, after_native)]:
                        digest.update(
                            json.dumps(
                                {k: v for k, v in data.items() if k != "quality_score"},
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode()
                            + b"\n"
                        )
                differences = {k: [original[k], v] for k, v in row.items() if original[k] != v}
                if differences:
                    assert av in TARGETS or set(differences) == {"quality_score"}
                    counts[av] += 1
                    columns.update(differences.keys())
                    if len(examples) < 40:
                        examples.append(dict(av_id=av, source_form_id=row["source_form_id"], differences=differences))
                n += 1
        assert all(next(reader, None) is None for reader in readers.values())
    assert old_hash.hexdigest() == BASELINE_PROJECTION
    assert before_native.hexdigest() == after_native.hexdigest()
    report = dict(
        records=n,
        unaffected_records=unaffected,
        reference_commit=a.reference,
        changed_by_variety=dict(counts),
        changed_fields=dict(columns),
        examples=examples,
        expected_baseline_projection=BASELINE_PROJECTION,
        baseline_projection_recovered=True,
        native_fields_outside_three_preserved=True,
        native_projection_sha256=before_native.hexdigest(),
        aggregate_sha256=sha(a.root / "output/aggregate/forms.csv"),
        script_sha256=sha(Path(__file__)),
        memory_limit_mb=256,
    )
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "examples"}, indent=2))


if __name__ == "__main__":
    main()
