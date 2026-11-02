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


def test_cached_memberships_use_exact_native_form_and_retain_multiple_judgments(monkeypatch):
    monkeypatch.setattr(cognacy_scope, "emission_memberships", lambda *args: (
        {"s-a": ["s-meaning1-1", "s-meaning1-2"], "s-b": ["s-meaning2-1"]},
        {"s-a": "1", "s-b": "1", "s-unknown": "3"}))
    forms = pd.DataFrame([
        dict(ID="s-a", Cognacy="s_1;s-meaning1-1;s-meaning1-2", Form="a", Segments="a", Comment="native"),
        dict(ID="s-b", Cognacy="s_1;s-meaning2-1", Form="b", Segments="b", Comment="native"),
        dict(ID="s-unknown", Cognacy="s_3", Form="x", Segments="", Comment="unknown source class"),
    ])
    result = cognacy_scope.apply_emission_policy(forms, "s")
    assert list(result.Cognacy) == ["s-meaning1-1;s-meaning1-2", "s-meaning2-1", ""]
    assert list(result.Form) == list(forms.Form) and list(result.Segments) == list(forms.Segments)
    assert '"raw_cognacy": "1"' in result.iloc[0].Comment
    assert forms.iloc[0].Cognacy.startswith("s_1;")
    # Applying the policy to already-clean input makes no further changes.
    assert cognacy_scope.apply_emission_policy(result, "s").equals(result)
    forms.loc[0, "Cognacy"] = "unreviewed-override"
    with pytest.raises(ValueError, match="differs"):
        cognacy_scope.apply_emission_policy(forms, "s")


def test_emission_rejects_source_snapshot_drift(tmp_path):
    source = tmp_path / "s/cldf"
    source.mkdir(parents=True)
    forms = source / "forms.csv"
    forms.write_text("ID,Cognacy\na,1\n")
    cognates = source / "cognates.csv"
    cognates.write_text("ID,Form_ID,Cognateset_ID\nj,a,meaning1-1\n")
    policy = tmp_path / "policies.csv"
    policy.write_text("dataset,emission_guard,forms_sha256,cognates_sha256\n" +
                      "s,true," + hashlib.sha256(forms.read_bytes()).hexdigest() + "," +
                      hashlib.sha256(cognates.read_bytes()).hexdigest() + "\n")
    assert cognacy_scope.emission_memberships("s", policy, tmp_path)[0] == {"s_a": ["s_meaning1-1"]}
    forms.write_text("changed")
    cognacy_scope.emission_memberships.cache_clear()
    with pytest.raises(ValueError, match="snapshot changed"):
        cognacy_scope.emission_memberships("s", policy, tmp_path)
