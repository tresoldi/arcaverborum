"""Add reviewed rows to an existing namespace without changing earlier evidence.

Stage the complete expanded namespace outside intake first. Existing form,
language and parameter rows must match exactly. Only metadata counts may change;
license, source version, citation and bibliography must remain unchanged.
Default validates without writing; replacements are prepared with rollback links.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ("forms.csv", "languages.csv", "parameters_raw.csv")
COUNTS = {"Form_Count", "Language_Count", "Parameter_Count"}


def scoped(path, dataset):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [r for r in reader if r["Dataset"] == dataset]
        return reader.fieldnames, rows


def replace_metadata(raw, fields, dataset, replacement):
    # csv.reader.line_num includes physical lines inside quoted fields. Preserve
    # every byte outside the selected source record, including its neighbors.
    lines = raw.splitlines(keepends=True)
    reader = csv.DictReader(io.StringIO(raw.decode(), newline=""))
    previous = 1
    found = []
    for row in reader:
        end = reader.line_num
        if row["Dataset"] == dataset:
            found.append((previous, end))
        previous = end
    if len(found) != 1:
        raise ValueError("Expected one existing metadata record")
    start, end = found[0]
    while start < end and not lines[start].strip():
        start += 1
    newline = "\r\n" if lines[end - 1].endswith(b"\r\n") else "\n"
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator=newline)
    writer.writerow(replacement)
    return b"".join(lines[:start]) + out.getvalue().encode() + b"".join(lines[end:])


def expand_intake(staged, target, dataset, *, expected_forms, write=False):
    if staged.resolve() == target.resolve() or target.resolve() in staged.resolve().parents:
        raise ValueError("Stage outside active intake")
    additions = {}
    old_counts = {}
    for name in TABLES:
        fields, old = scoped(target / name, dataset)
        newfields, new = scoped(staged / name, dataset)
        with (staged / name).open() as handle:
            if any(r["Dataset"] != dataset for r in csv.DictReader(handle)):
                raise ValueError("Stage must contain one reviewed namespace")
        if fields != newfields or not old or not new:
            raise ValueError("Missing source or schema mismatch: " + name)
        oldby = {r["ID"]: r for r in old}
        newby = {r["ID"]: r for r in new}
        if len(oldby) != len(old) or len(newby) != len(new):
            raise ValueError("Duplicate identity in " + name)
        if any(newby.get(key) != row for key, row in oldby.items()):
            raise ValueError("Earlier evidence changed or removed: " + name)
        additions[name] = (fields, [r for r in new if r["ID"] not in oldby])
        old_counts[name] = len(old)
    if old_counts["forms.csv"] != expected_forms:
        raise ValueError("Expected original form count does not match")
    fields, oldmeta = scoped(target / "metadata.csv", dataset)
    newfields, newmeta = scoped(staged / "metadata.csv", dataset)
    if fields != newfields or len(oldmeta) != 1 or len(newmeta) != 1:
        raise ValueError("Expected one source metadata record")
    oldmeta, newmeta = oldmeta[0], newmeta[0]
    if any(oldmeta[k] != newmeta[k] for k in fields if k not in COUNTS):
        raise ValueError("Source citation, license or version changed")
    for filename, key in [
        ("forms.csv", "Form_Count"),
        ("languages.csv", "Language_Count"),
        ("parameters_raw.csv", "Parameter_Count"),
    ]:
        if int(newmeta[key]) != old_counts[filename] + len(additions[filename][1]):
            raise ValueError("Expanded metadata count mismatch")
    bib = (staged / "sources.bib").read_bytes().strip()
    if not bib or bib not in (target / "sources.bib").read_bytes():
        raise ValueError("Bibliography changed; requires a different migration")
    result = {name: len(rows) for name, (_, rows) in additions.items()}
    if not write:
        return result
    names = (*TABLES, "metadata.csv")
    with tempfile.TemporaryDirectory(prefix=".expand-", dir=target.parent) as temporary:
        work = Path(temporary)
        for name in names:
            os.link(target / name, work / ("old-" + name))
            if name == "metadata.csv":
                (work / name).write_bytes(replace_metadata((target / name).read_bytes(), fields, dataset, newmeta))
            else:
                columns, rows = additions[name]
                shutil.copyfile(target / name, work / name)
                with (work / name).open("a", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
                    handle.write("\n")
                    writer.writerows(rows)
        committed = []
        try:
            for name in names:
                os.replace(work / name, target / name)
                committed.append(name)
        except BaseException:
            for name in committed:
                os.replace(work / ("old-" + name), target / name)
            raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", type=Path, required=True)
    parser.add_argument("--target", type=Path, default=ROOT / "intake/lexibank")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--expected-old-forms", type=int, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(
        expand_intake(args.staged, args.target, args.dataset, expected_forms=args.expected_old_forms, write=args.write)
    )


if __name__ == "__main__":
    main()
