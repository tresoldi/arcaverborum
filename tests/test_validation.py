import pandas as pd

from arcaverborum.schema import ColumnTracking, DatasetMetadata, ReferenceVersions
from arcaverborum.validation import ValidationAccumulator


def _make_forms(n: int, cognacy_frac: float = 0.0) -> pd.DataFrame:
    df = pd.DataFrame({
        "Glottocode": ["abcd1234"] * n,
        "Concepticon_ID": ["123"] * n,
        "Cognacy": pd.NA,
        "Segments": ["a b c"] * n,
        "Alignment": pd.NA,
        "Morpheme_Index": pd.NA,
        "Segment_Slice": pd.NA,
        "Comment": pd.NA,
        "Loan": pd.NA,
    })
    cog_count = int(n * cognacy_frac)
    if cog_count:
        df.loc[:cog_count - 1, "Cognacy"] = "cog_1"
    return df


def _make_meta(dataset: str, has_cognates: bool = False) -> DatasetMetadata:
    return DatasetMetadata(
        dataset, "T", "C", "U", "L", "W", None, None, 10, 2, 3, has_cognates
    )


def _make_refs(dataset: str) -> ReferenceVersions:
    return ReferenceVersions(dataset, "v4.8", "v3.1", None)


def _make_ct(dataset: str, has_cognates: bool = False) -> ColumnTracking:
    return ColumnTracking(dataset, ("ID", "Value"), has_cognates)


def test_empty_accumulator():
    v = ValidationAccumulator()
    report = v.generate_report()
    assert report["summary"]["total_datasets"] == 0
    assert report["summary"]["total_forms"] == 0


def test_single_dataset():
    v = ValidationAccumulator()
    forms = _make_forms(10, cognacy_frac=0.5)
    v.update(
        "ds1", forms,
        pd.DataFrame({"ID": ["l1", "l2"]}),
        pd.DataFrame({"ID": ["p1", "p2", "p3"]}),
        _make_meta("ds1", has_cognates=True),
        _make_refs("ds1"),
        "@article{...", _make_ct("ds1", True),
    )
    assert v.datasets_processed == 1
    assert v.total_forms == 10
    assert v.datasets_with_cognates == 1
    assert v.forms_with_cognacy == 5


def test_two_datasets():
    v = ValidationAccumulator()
    for name in ("a", "b"):
        v.update(
            name, _make_forms(5),
            pd.DataFrame({"ID": [f"{name}_l"]}),
            pd.DataFrame({"ID": [f"{name}_p"]}),
            _make_meta(name), _make_refs(name), "", _make_ct(name),
        )
    assert v.datasets_processed == 2
    assert v.total_forms == 10


def test_report_quality():
    v = ValidationAccumulator()
    v.update(
        "ds", _make_forms(100, 0.3),
        pd.DataFrame({"ID": ["l"]}),
        pd.DataFrame({"ID": ["p"]}),
        _make_meta("ds"), _make_refs("ds"), "", _make_ct("ds"),
    )
    report = v.generate_report()
    assert report["data_quality"]["glottocode_coverage_percent"] == 100.0
    assert report["data_quality"]["forms_with_cognate_data_percent"] == 30.0
