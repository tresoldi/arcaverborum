"""Tests for the semantic-field-prefixed concept catalog (arcaverborum.concepts)."""

from __future__ import annotations

from arcaverborum import concepts as cc


def test_normalize_gloss():
    assert cc.normalize_gloss("WATER") == ("water", "")
    assert cc.normalize_gloss("BLOW (OF WIND)") == ("blow", "of wind")
    assert cc.normalize_gloss("BELOW OR UNDER") == ("below or under", "")
    assert cc.normalize_gloss("CHILD (YOUNG HUMAN)") == ("child", "young human")
    # Stripping the parenthetical would leave nothing -> keep it.
    assert cc.normalize_gloss("(someone)") == ("(someone)", "")


def test_pos_for_category():
    assert cc.pos_for_category("Person/Thing") == "n"
    assert cc.pos_for_category("Action/Process") == "v"
    assert cc.pos_for_category("Property") == "adj"
    assert cc.pos_for_category("Number") == "num"
    assert cc.pos_for_category("Classifier") == "clf"
    assert cc.pos_for_category("Other") == "x"
    assert cc.pos_for_category("") == ""


def test_field_codes_seeded_and_unique():
    fields = ["The body", "Animals", "Possession", "A Made Up Field"]
    codes = cc.build_field_codes(fields)
    assert codes["The body"] == "bod"          # seeded
    assert codes["Animals"] == "ani"           # seeded
    assert codes["Possession"] == "pss"        # seeded (not "pos")
    assert len(set(codes.values())) == len(codes)
    assert all(len(c) == 3 for c in codes.values())


def test_field_code_for_undetermined():
    codes = {"The body": "bod"}
    assert cc.field_code_for("The body", codes) == "bod"
    assert cc.field_code_for("Unknown Field", codes) == cc.UNDETERMINED_CODE
    assert cc.field_code_for("", codes) == cc.UNDETERMINED_CODE


def test_assign_basic_and_field_prefix():
    codes = {"The body": "bod", "Speech and language": "lng"}
    concepts = [
        {"concepticon_id": "1040", "gloss": "HAIR", "semantic_field": "The body"},
        {"concepticon_id": "1205", "gloss": "TONGUE (BODY PART)", "semantic_field": "The body"},
        {"concepticon_id": "1494", "gloss": "TONGUE (LANGUAGE)",
         "semantic_field": "Speech and language"},
    ]
    m = cc.assign_concept_ids(concepts, codes)
    assert m["1040"] == "bod-hair"
    # Different fields -> the homograph is separated by the prefix, no suffix.
    assert m["1205"] == "bod-tongue"
    assert m["1494"] == "lng-tongue"
    assert len(set(m.values())) == len(m)


def test_assign_within_field_qualifier_disambiguation():
    codes = {"Motion": "mot"}
    concepts = [
        {"concepticon_id": "100", "gloss": "BLOW", "semantic_field": "Motion"},
        {"concepticon_id": "200", "gloss": "BLOW (OF WIND)", "semantic_field": "Motion"},
    ]
    m = cc.assign_concept_ids(concepts, codes)
    # The unqualified one keeps the bare slug; the qualified one uses its qualifier.
    assert m["100"] == "mot-blow"
    assert m["200"] == "mot-blow-of-wind"


def test_assign_numeric_fallback_for_true_homographs():
    codes = {"The body": "bod"}
    concepts = [
        {"concepticon_id": "300", "gloss": "ARM", "semantic_field": "The body"},
        {"concepticon_id": "200", "gloss": "ARM", "semantic_field": "The body"},
    ]
    m = cc.assign_concept_ids(concepts, codes)
    # Lowest Concepticon id claims the bare slug; the other gets -2.
    assert m["200"] == "bod-arm"
    assert m["300"] == "bod-arm-2"


def test_assign_is_order_independent():
    codes = {"The body": "bod"}
    a = [
        {"concepticon_id": "300", "gloss": "ARM", "semantic_field": "The body"},
        {"concepticon_id": "200", "gloss": "ARM", "semantic_field": "The body"},
    ]
    assert cc.assign_concept_ids(a, codes) == cc.assign_concept_ids(list(reversed(a)), codes)


def test_mint_concept_id_incremental():
    codes = {"The body": "bod"}
    taken = {"bod-hair"}
    assert cc.mint_concept_id("HAIR", "The body", codes, taken) == "bod-hair-2"
    assert cc.mint_concept_id("ARM", "The body", codes, taken) == "bod-arm"
    # Qualifier preferred over numeric when the bare slug is taken.
    assert cc.mint_concept_id("HAIR (OF HEAD)", "The body", codes, taken) == "bod-hair-of-head"


def test_registry_roundtrip(tmp_path):
    path = tmp_path / "concepts.csv"
    concepts = [
        cc.Concept(concept_id="bod-hair", concepticon_id="1040", label="hair",
                   pos="n", semantic_field="The body", definition="the hair."),
        cc.Concept(concept_id="act-eat", concepticon_id="1336", label="eat",
                   pos="v", semantic_field="Basic actions and technology"),
    ]
    cc.write_concepts(concepts, path)
    loaded = cc.load_concepts(path)
    assert {c.concept_id for c in loaded} == {"bod-hair", "act-eat"}
    idx = cc.load_concept_index(path)
    assert idx["1040"] == ("bod-hair", "hair")
    assert idx["1336"] == ("act-eat", "eat")


def test_field_codes_roundtrip(tmp_path):
    codes = {"The body": "bod", "Animals": "ani"}
    path = tmp_path / "semantic_field_codes.csv"
    cc.write_field_codes(codes, path)
    assert cc.load_field_codes(path) == codes
