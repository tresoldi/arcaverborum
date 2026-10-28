"""Existing namespace expansion preserves evidence and rolls back failed writes."""

import csv
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "expand_source_intake", Path(__file__).parents[1] / "scripts/expand_source_intake.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def pair(tmp_path):
    target, stage = tmp_path / "active", tmp_path / "stage"
    target.mkdir()
    stage.mkdir()
    for path, expanded in [(target, False), (stage, True)]:
        for name in module.TABLES:
            with (path / name).open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["ID", "Dataset", "Value"])
                writer.writeheader()
                if path == target:
                    writer.writerow(dict(ID="other", Dataset="other", Value="a, b\nsecond line"))
                writer.writerow(dict(ID="old", Dataset="source", Value="unchanged"))
                if expanded:
                    writer.writerow(dict(ID="new", Dataset="source", Value="new evidence"))
        with (path / "metadata.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "Dataset",
                    "License",
                    "Citation",
                    "Repository_Version",
                    "Form_Count",
                    "Language_Count",
                    "Parameter_Count",
                ],
            )
            writer.writeheader()
            if path == target:
                writer.writerow(dict(Dataset="other", Citation="other\nquoted, citation"))
                handle.write("\n")
            writer.writerow(
                dict(
                    Dataset="source",
                    License="CC-BY",
                    Citation="original citation",
                    Repository_Version="frozen",
                    Form_Count=2 if expanded else 1,
                    Language_Count=2 if expanded else 1,
                    Parameter_Count=2 if expanded else 1,
                )
            )
        (path / "sources.bib").write_text("@misc{source,title={Original}}\n")
    return stage, target


def snapshot(path):
    return {p.name: p.read_bytes() for p in path.iterdir()}


def test_additions_preserve_earlier_bytes_and_quoted_metadata(tmp_path):
    stage, target = pair(tmp_path)
    before = snapshot(target)
    assert module.expand_intake(stage, target, "source", expected_forms=1)["forms.csv"] == 1
    assert snapshot(target) == before
    module.expand_intake(stage, target, "source", expected_forms=1, write=True)
    for name in module.TABLES:
        assert (target / name).read_bytes().startswith(before[name])
    oldprefix = before["metadata.csv"].split(b"source,", 1)[0]
    assert (target / "metadata.csv").read_bytes().startswith(oldprefix)
    assert (target / "sources.bib").read_bytes() == before["sources.bib"]
    assert module.scoped(target / "forms.csv", "source")[1][-1]["Value"] == "new evidence"


@pytest.mark.parametrize(
    "file,old,new",
    [
        ("forms.csv", "unchanged", "altered"),
        ("metadata.csv", "CC-BY", "unknown"),
        ("metadata.csv", "frozen", "moving"),
        ("sources.bib", "Original", "Changed"),
    ],
)
def test_changed_evidence_citation_or_license_is_rejected_before_writes(tmp_path, file, old, new):
    stage, target = pair(tmp_path)
    before = snapshot(target)
    p = stage / file
    p.write_text(p.read_text().replace(old, new))
    with pytest.raises(ValueError):
        module.expand_intake(stage, target, "source", expected_forms=1, write=True)
    assert snapshot(target) == before


def test_failed_replacement_rolls_back_all_tables(tmp_path, monkeypatch):
    stage, target = pair(tmp_path)
    before = snapshot(target)
    original = module.os.replace

    def fail(source, destination):
        if Path(source).name == "languages.csv":
            raise OSError("simulated")
        return original(source, destination)

    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError, match="simulated"):
        module.expand_intake(stage, target, "source", expected_forms=1, write=True)
    assert snapshot(target) == before


def test_wrong_baseline_count_cannot_repeat_expansion(tmp_path):
    stage, target = pair(tmp_path)
    with pytest.raises(ValueError, match="original form count"):
        module.expand_intake(stage, target, "source", expected_forms=2, write=True)
