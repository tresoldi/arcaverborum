import csv
import gzip
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "collection_release", Path(__file__).parents[1] / "scripts/build_collection_release.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def prepare(root):
    aggregate = root / "output/aggregate"
    aggregate.mkdir(parents=True)
    for name, rows in {
        "forms.csv": [dict(av_id="test", source_form_id="native", Segments_Source="source",
                           transcription_source="source")],
        "metadata.csv": [dict(Dataset="source", Title="Source title", License="", Citation="Citation")],
        "varieties.csv": [dict(av_id="test")],
    }.items():
        with (aggregate / name).open("w") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (root / "datasets.csv").write_text("NAME\nsource\n")
    data = root / "src/arcaverborum/data"
    data.mkdir(parents=True)
    (data / "concepts.csv").write_text("concept_id\ntest\n")
    variety = root / "varieties/test"
    variety.mkdir(parents=True)
    (variety / "config.yaml").write_text("av_id: test\n")
    catalog = root / "web/data/catalog.json.gz"
    catalog.parent.mkdir(parents=True)
    with gzip.open(catalog, "wt") as handle:
        json.dump(dict(languages=[dict(av_id="test", forms=1, transcription_source="source")]), handle)
    return aggregate


def test_archive_is_reproducible_and_missing_terms_are_explicit(tmp_path):
    prepare(tmp_path)
    a, b = tmp_path / "release-a", tmp_path / "release-b"
    first = module.build(tmp_path, a, "2026-11-02", True)
    second = module.build(tmp_path, b, "2026-11-02", True)
    assert first == second
    assert (a / "arca-all-accepted-2026-11-02.tar.gz").read_bytes() == (
        b / "arca-all-accepted-2026-11-02.tar.gz").read_bytes()
    assert first["source_terms"][0]["terms_status"] == "missing_declaration"
    assert first["lexical_constructions"] == 1
    with pytest.raises(FileExistsError):
        module.build(tmp_path, a, "2026-11-02")


def test_empty_data_and_missing_source_attribution_fail(tmp_path):
    aggregate = prepare(tmp_path)
    forms = aggregate / "forms.csv"
    original = forms.read_text()
    forms.write_text(original.splitlines()[0] + "\n")
    with pytest.raises(ValueError, match="empty"):
        module.build(tmp_path, tmp_path / "empty", "2026-11-02")
    forms.write_text(original)
    (aggregate / "metadata.csv").write_text("Dataset,License\nother,CC-BY\n")
    with pytest.raises(ValueError, match="attribution"):
        module.build(tmp_path, tmp_path / "missing", "2026-11-02")


def test_archive_verification_rejects_a_changed_payload(tmp_path):
    prepare(tmp_path)
    output = tmp_path / "release"
    manifest = module.build(tmp_path, output, "2026-11-02", True)
    expected = {row["path"]: row["sha256"] for row in manifest["files"]}
    expected.update({"manifest.json": module.sha(output / "manifest.json"),
                     "RELEASE_README.txt": module.sha(output / "RELEASE_README.txt")})
    expected["datasets.csv"] = "changed"
    with pytest.raises(ValueError, match="changed during packaging"):
        module.verify_archive(output / "arca-all-accepted-2026-11-02.tar.gz", expected)
