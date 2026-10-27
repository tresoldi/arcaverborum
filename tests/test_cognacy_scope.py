"""Only reviewed exact snapshots can reinterpret meaning-local raw labels."""

import csv
import hashlib

import pandas as pd
import pytest

from arcaverborum.sources import cognacy_scope


def test_snapshot_guard_and_raw_qualifiers_are_retained(tmp_path, monkeypatch):
    forms = pd.DataFrame([dict(ID="a", Cognacy="1?", Comment="original")])
    cognates = pd.DataFrame([dict(Form_ID="a", Cognateset_ID="hand-1")])
    forms.to_csv(tmp_path / "forms.csv", index=False)
    cognates.to_csv(tmp_path / "cognates.csv", index=False)
    policy = dict(
        dataset="source",
        policy="structured_only",
        forms_sha256=hashlib.sha256((tmp_path / "forms.csv").read_bytes()).hexdigest(),
        cognates_sha256=hashlib.sha256((tmp_path / "cognates.csv").read_bytes()).hexdigest(),
    )
    path = tmp_path / "policies.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(policy))
        writer.writeheader()
        writer.writerow(policy)
    monkeypatch.setattr(cognacy_scope, "POLICIES", path)
    result = cognacy_scope.apply_policy(forms, cognates, "source", tmp_path)
    assert result.iloc[0].Cognacy == "" and forms.iloc[0].Cognacy == "1?"
    assert "1?" in result.iloc[0].Comment and result.iloc[0].Comment.startswith("original; ")
    (tmp_path / "cognates.csv").write_text("changed")
    with pytest.raises(ValueError, match="snapshot changed"):
        cognacy_scope.apply_policy(forms, cognates, "source", tmp_path)
