"""Dictionary fields need source-specific interpretation and sense guards."""

import csv

import pytest

from arcaverborum.sources.dictionaria import process_dictionary, source_segments


def write(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def dictionary(tmp_path, monkeypatch):
    monkeypatch.setattr("arcaverborum.sources.dictionaria.subprocess.check_output", lambda *a, **k: "a" * 40)
    from arcaverborum.sources import dictionaria

    data = tmp_path / "data"
    data.mkdir()
    (data / "dictionary_sources.csv").write_bytes((dictionaria.DATA / "dictionary_sources.csv").read_bytes())
    reviews = [r for r in dictionaria.read(dictionaria.DATA / "dictionary_senses.csv") if r["sense_id"] == "SN000071"]
    write(data / "dictionary_senses.csv", reviews)
    write(data / "concepts.csv", [dict(concept_id="phy-water", concepticon_id="948", label="water")])
    monkeypatch.setattr(dictionaria, "DATA", data)
    cldf = tmp_path / "cldf"
    cldf.mkdir()
    write(cldf / "languages.csv", [dict(ID="mue", Name="Media Lengua", Glottocode="medi1245")])
    write(
        cldf / "entries.csv",
        [
            dict(
                ID="agua",
                Language_ID="mue",
                Headword="agua",
                Part_Of_Speech="noun",
                Phonological_Representation="'awa",
                Etymology="Spanish",
            )
        ],
    )
    write(cldf / "senses.csv", [dict(ID="SN000071", Entry_ID="agua", Description="water")])
    (cldf / "cldf-metadata.json").write_text("{}")
    return cldf


def test_supplied_representation_not_headword_is_used_and_no_cognacy_or_loans_inferred(tmp_path, monkeypatch):
    cldf = dictionary(tmp_path, monkeypatch)
    forms, _, params, metadata, bib = process_dictionary("dictmedialengua", cldf)
    row = forms.iloc[0]
    assert row.Form == "agua" and row.Segments == "a w a"
    assert row.Cognacy == "" and row.Loan == ""
    assert row.ID == "dictmedialengua_SN000071"
    assert "Phonological_Representation" in row.Comment and "Spanish" in row.Comment
    assert params.iloc[0].Concepticon_ID == "948"
    assert "Stewart" in metadata["Citation"] and "Visser" not in bib
    assert metadata["Repository_Version"] == "a" * 40


def test_changed_dictionary_sense_cannot_inherit_reviewed_mapping(tmp_path, monkeypatch):
    cldf = dictionary(tmp_path, monkeypatch)
    write(cldf / "senses.csv", [dict(ID="SN000071", Entry_ID="agua", Description="irrigation")])
    with pytest.raises(ValueError, match="sense changed"):
        process_dictionary("dictmedialengua", cldf)
    assert source_segments("'a be'xa") == "a _ b e x a"
    assert source_segments("a(b)") == ""
