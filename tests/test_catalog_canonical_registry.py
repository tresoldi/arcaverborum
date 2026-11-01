"""A source-specific dialect sharing a Glottocode cannot displace its parent."""

import csv

import pytest

from arcaverborum.catalog import load_avid_registry


@pytest.mark.parametrize("reverse", [False, True])
def test_canonical_registry_is_independent_of_dialect_row_order(tmp_path, reverse):
    rows = [
        dict(av_id="ine-sursilvan", glottocode="surs1244", in_glottolog="true"),
        dict(av_id="ine-tuatschin", glottocode="surs1244", in_glottolog="false"),
    ]
    path = tmp_path / "varieties.csv"
    with path.open("w") as h:
        writer = csv.DictWriter(h, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(list(reversed(rows)) if reverse else rows)
    assert load_avid_registry(path) == {"surs1244": "ine-sursilvan"}
