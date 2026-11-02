import copy
import csv
import json

import pytest

from arcaverborum.review_workspace import (
    packet_from_csv,
    render_workspace,
    scope_comparability,
    validate_decisions,
)


def fixture(tmp_path):
    row = dict(case_id="case", language="</script><script>bad()</script>", source="source", member="lect",
               basis="written", a="bag", b="witch", definition_a="container", definition_b="witch",
               original_records_a=json.dumps([dict(source_form_id="native-a", Value="antaruxa")]),
               original_records_b=json.dumps([dict(source_form_id="native-b", Value="antaruxa")]),
               native_senses_a="[]", native_senses_b="[]")
    path = tmp_path / "worksheet.csv"
    with path.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    packet = packet_from_csv(path)
    decision = dict(case_id="case", case_sha256=packet["cases"][0]["case_sha256"],
                    reviewer="Reviewer", reviewer_type="model_assisted", decision="mapping_error",
                    evidence_locator="original dictionary, entry123", rationale="BAG/HAG confusion",
                    record_scopes=[dict(source_form_id="native-a", edition="edition1", evidence_locator="p3")])
    return packet, dict(schema=1, packet_sha256=packet["packet_sha256"], decisions=[decision])


def test_local_export_does_not_claim_human_gold(tmp_path):
    packet, submission = fixture(tmp_path)
    assert validate_decisions(packet, submission) == dict(decisions=1, human_expert_gold=0,
                                                         automatic_lexical_changes=0)
    submission["decisions"][0]["reviewer_type"] = "human"
    assert validate_decisions(packet, submission)["human_expert_gold"] == 0


@pytest.mark.parametrize("mutation", ["packet", "case", "record", "reviewer", "locator", "duplicate"])
def test_export_rejects_stale_or_unfounded_decisions(tmp_path, mutation):
    packet, submission = fixture(tmp_path)
    decision = submission["decisions"][0]
    if mutation == "packet":
        packet["cases"][0]["original_records_a"] = "[]"
    elif mutation == "case":
        decision["case_sha256"] = "stale"
    elif mutation == "record":
        decision["record_scopes"][0]["source_form_id"] = "invented"
    elif mutation == "reviewer":
        decision["reviewer"] = ""
    elif mutation == "locator":
        decision["record_scopes"][0]["evidence_locator"] = ""
    else:
        submission["decisions"].append(copy.deepcopy(decision))
    with pytest.raises(ValueError):
        validate_decisions(packet, submission)


def test_native_text_cannot_break_out_of_embedded_json(tmp_path):
    packet, _ = fixture(tmp_path)
    html = render_workspace(packet)
    assert "</script><script>bad()" not in html
    assert "\\u003c/script>" in html


def test_shared_publication_is_not_a_complete_witness_scope():
    assert scope_comparability(dict(original_publication="book"), dict(original_publication="book")) == "unknown"
    assert scope_comparability(dict(field_collection="a"), dict(field_collection="b")) == "different_scope"
    a = dict(field_collection="collection", local_variety="lect", historical_stage="modern",
             reading_convention="author1", edition="first")
    b = dict(a, edition="reprint")
    assert scope_comparability(a, b) == "matched_scope"
    b["reading_convention"] = "different transcription"
    assert scope_comparability(a, b) == "different_scope"
