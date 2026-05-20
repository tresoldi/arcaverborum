"""Tests for concept-catalog drift auditing (arcaverborum.concept_audit)."""

from __future__ import annotations

from arcaverborum import concept_audit as audit
from arcaverborum import concepts as cc
from arcaverborum.concepticon import ConcepticonEntry


def _master():
    return {
        "1040": ConcepticonEntry(id="1040", gloss="HAIR", ontological_category="Person/Thing",
                                 semantic_field="The body", definition="the hair."),
        "1336": ConcepticonEntry(id="1336", gloss="EAT", ontological_category="Action/Process",
                                 semantic_field="Basic actions and technology"),
        "948": ConcepticonEntry(id="948", gloss="WATER", ontological_category="Person/Thing",
                                semantic_field="The physical world"),
        # 1040 was merged upstream into 9999; field of EAT drifted.
    }


def _registry():
    return [
        cc.Concept(concept_id="bod-hair", concepticon_id="1040", label="hair",
                   pos="n", semantic_field="The body"),
        cc.Concept(concept_id="act-eat", concepticon_id="1336", label="eat",
                   pos="v", semantic_field="The body"),  # field drift vs master
    ]


def test_audit_clean():
    master = _master()
    reg = [
        cc.Concept(concept_id="bod-hair", concepticon_id="1040", label="hair",
                   pos="n", semantic_field="The body"),
        cc.Concept(concept_id="act-eat", concepticon_id="1336", label="eat",
                   pos="v", semantic_field="Basic actions and technology"),
    ]
    report = audit.audit_registry({"1040", "1336"}, master, reg)
    assert report["clean"]
    assert report["new_inuse"] == []


def test_audit_detects_new_inuse_and_field_drift():
    report = audit.audit_registry({"1040", "1336", "948"}, _master(), _registry())
    assert report["new_inuse"] == ["948"]              # in intake, not in registry
    assert [c.concept_id for c, _ in report["field_drift"]] == ["act-eat"]
    assert not report["clean"]


def test_audit_detects_merged_and_dropped():
    master = _master()
    master["1040"] = ConcepticonEntry(
        id="1040", gloss="HAIR", ontological_category="Person/Thing",
        semantic_field="The body", replacement_id="9999")
    reg = [
        cc.Concept(concept_id="bod-hair", concepticon_id="1040", label="hair",
                   pos="n", semantic_field="The body"),
        cc.Concept(concept_id="zzz-gone", concepticon_id="55555", label="gone",
                   semantic_field="The body"),  # no longer in master
    ]
    report = audit.audit_registry({"1040"}, master, reg)
    assert [c.concept_id for c, _ in report["now_merged"]] == ["bod-hair"]
    assert [c.concept_id for c in report["dropped"]] == ["zzz-gone"]


def test_mint_missing_extends_without_collision():
    master = _master()
    reg = _registry()
    codes = cc.build_field_codes(["The physical world", "The body"])
    minted = audit.mint_missing(["948"], master, reg, codes)
    assert len(minted) == 1
    assert minted[0].concept_id == "phy-water"
    assert minted[0].concepticon_id == "948"
    assert minted[0].pos == "n"
    # Minted ids never collide with the existing registry.
    existing = {c.concept_id for c in reg}
    assert minted[0].concept_id not in existing
