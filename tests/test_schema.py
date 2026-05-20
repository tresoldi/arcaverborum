import pandas as pd

from arcaverborum.schema import (
    OUTPUT_SCHEMA,
    ColumnSchema,
    ColumnTracking,
    DatasetMetadata,
    DatasetResult,
    ReferenceVersions,
)


def test_output_schema_types():
    assert isinstance(OUTPUT_SCHEMA, ColumnSchema)
    assert isinstance(OUTPUT_SCHEMA.forms_output, tuple)
    assert isinstance(OUTPUT_SCHEMA.languages, tuple)
    assert isinstance(OUTPUT_SCHEMA.parameters, tuple)


def test_forms_output_columns():
    cols = OUTPUT_SCHEMA.forms_output
    assert "ID" in cols
    assert "Dataset" in cols
    assert "Language_ID" in cols
    assert "Parameter_ID" in cols
    assert "Cognacy" in cols


def test_dataset_metadata():
    meta = DatasetMetadata(
        dataset="test", title="Test", citation="cite", url="http://x",
        license="CC-BY", cldf_module="Wordlist", repository_version="v1",
        python_version="3.11", form_count=10, language_count=2,
        parameter_count=3, has_cognates=True,
    )
    d = meta.to_dict()
    assert d["Dataset"] == "test"
    assert d["Has_Cognates"] is True
    assert d["Form_Count"] == 10


def test_reference_versions():
    ref = ReferenceVersions(
        dataset="test", glottolog_version="v4.8",
        concepticon_version="v3.1", clts_version=None,
    )
    d = ref.to_dict()
    assert d["Glottolog_Version"] == "v4.8"
    assert d["CLTS_Version"] is None


def test_column_tracking():
    ct = ColumnTracking(
        dataset="test",
        forms_columns_present=("ID", "Value", "Form"),
        has_cognates=False,
    )
    d = ct.to_dict()
    assert d["has_cognates"] is False
    assert "ID" in d["forms_columns_present"]


def test_dataset_result():
    result = DatasetResult(
        forms=pd.DataFrame({"ID": ["a"]}),
        languages=pd.DataFrame({"ID": ["l1"]}),
        parameters=pd.DataFrame({"ID": ["p1"]}),
        metadata=DatasetMetadata(
            "t", "t", "c", "u", "l", "w", None, None, 1, 1, 1, False
        ),
        references=ReferenceVersions("t", None, None, None),
        bibtex="",
        column_tracking=ColumnTracking("t", (), False),
    )
    assert len(result.forms) == 1
    assert len(result.languages) == 1
