"""Opportunity ranking must count additive supported gaps, not raw spelling."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "coverage_opportunities", Path(__file__).parents[1] / "scripts/rank_coverage_opportunities.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_missing_core_potential_excludes_supported_slots_and_separates_spelling():
    target = dict(
        av_id="und-test",
        name="Test",
        macroarea="South America",
        glottocode="xxxx1234",
        primary="gled",
        supported={"phy-water"},
    )
    forms = [
        dict(Parameter_ID="water", Form="agua", Value="agua", Segments="a g w a"),
        dict(Parameter_ID="sun", Form="orthography", Value="orthography", Segments=""),
        dict(Parameter_ID="moon", Form="luna", Value="luna", Segments="l u n a"),
    ]
    params = {"water": "1", "sun": "2", "moon": "3"}
    concepts = {"1": "phy-water", "2": "phy-sun", "3": "phy-moon"}
    row = module.opportunity(target, "other", "member", forms, params, concepts, set(concepts.values()), {}, {})
    assert row["additive_source_core_potential"] == 1
    assert row["orthographic_core_potential"] == 1
    assert row["supplied_concepts"] == "phy-moon"
    assert row["orthographic_concepts"] == "phy-sun"
    assert "citation_or_license_incomplete" in row["blockers"]
    # A local authored sense overrides the raw intake mapping for dictionary discovery.
    revised = module.opportunity(
        target, "other", "member", forms, params, concepts, set(concepts.values()), {("other", "moon"): "phy-water"}, {}
    )
    assert revised["additive_source_core_potential"] == 0
    assert revised["orthographic_core_potential"] == 1


def test_profiles_count_as_supported_but_resegmented_spelling_does_not():
    forms = [
        dict(concept_id="a", Segments_Source="source"),
        dict(concept_id="b", Segments_Source="profile"),
        dict(concept_id="c", Segments_Source="resegmented"),
    ]
    assert module.baseline(forms, {"a", "b", "c"}) == ({"a", "b", "c"}, {"a", "b"})
    south = dict(
        macroarea="South America",
        additive_source_core_potential=1,
        orthographic_core_potential=0,
        av_id="a",
        source="x",
        source_language_id="m",
    )
    north = {**south, "macroarea": "North America", "additive_source_core_potential": 20}
    assert module.rank_key(south) < module.rank_key(north)


def test_recording_buttons_are_not_profile_opportunities():
    target = dict(av_id="test", name="Test", macroarea="North America", glottocode="test1234",
                  primary="gled", supported=set())
    forms = [dict(Parameter_ID="water", Form="►", Value="►", Segments="")]
    assert module.opportunity(target, "mixezoqueanvoices", "member", forms,
                              {"water": "1"}, {"1": "phy-water"}, {"phy-water"}, {}, {}) is None
