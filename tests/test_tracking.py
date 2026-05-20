"""Tests for content-based build tracking (skip-if-unchanged)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from arcaverborum import tracking


def _intake(rows: list[dict]) -> pd.DataFrame:
    """Build an intake-like frame the way cmd_update does (fillna + _glottocode_lc)."""
    df = pd.DataFrame(rows).fillna("")
    df["_glottocode_lc"] = df["Glottocode"].astype(str).str.strip().str.lower()
    return df


_PARAM_INDEX = {"alpha_water": ("1234", "WATER"), "alpha_fire": ("5678", "FIRE")}

_BASE_ROWS = [
    {"ID": "a1", "Dataset": "alpha", "Glottocode": "abcd1234",
     "Parameter_ID": "alpha_water", "Concepticon_Gloss": "WATER",
     "Value": "wata", "Form": "wata", "Segments": "w a t a"},
    {"ID": "a2", "Dataset": "alpha", "Glottocode": "abcd1234",
     "Parameter_ID": "alpha_fire", "Concepticon_Gloss": "FIRE",
     "Value": "pir", "Form": "pir", "Segments": "p i r"},
    {"ID": "b1", "Dataset": "beta", "Glottocode": "abcd1234",
     "Parameter_ID": "alpha_water", "Concepticon_Gloss": "WATER",
     "Value": "wata", "Form": "wata", "Segments": ""},
]


def test_recipe_hash_is_stable_nonempty():
    assert tracking.recipe_hash() == tracking.recipe_hash()
    assert len(tracking.recipe_hash()) == 16


def test_config_component_ignores_noise_fields():
    base = {"glottocode": "abcd1234", "name": "Test",
            "sources": {"transcription": "alpha", "cognates": "alpha"},
            "scoring": {"forms_score": 0.8, "tier": "bronze"}}
    noisy = dict(base, extensions={"forms": True}, notes="x",
                 registered_on="2026-05-20", pinned=True, macroarea="Eurasia")
    assert tracking.config_component(base) == tracking.config_component(noisy)


def test_config_component_reacts_to_source_and_scoring():
    base = {"sources": {"transcription": "alpha"}, "scoring": {"forms_score": 0.8}}
    diff_src = {"sources": {"transcription": "beta"}, "scoring": {"forms_score": 0.8}}
    diff_score = {"sources": {"transcription": "alpha"}, "scoring": {"forms_score": 0.9}}
    assert tracking.config_component(base) != tracking.config_component(diff_src)
    assert tracking.config_component(base) != tracking.config_component(diff_score)


def test_custom_component_reacts_to_content(tmp_path: Path):
    custom = tmp_path / "custom"
    custom.mkdir()
    before = tracking.custom_component(custom)  # all absent
    (custom / "cognates.csv").write_text("form_id,Cognacy\na1,7\n", encoding="utf-8")
    after = tracking.custom_component(custom)
    assert before != after
    (custom / "cognates.csv").write_text("form_id,Cognacy\na1,8\n", encoding="utf-8")
    assert tracking.custom_component(custom) != after


def test_slice_hash_per_variety_and_source():
    hashes = tracking.compute_intake_slice_hashes(_intake(_BASE_ROWS), _PARAM_INDEX)
    # Keyed by (glottocode_lc, Dataset): alpha and beta slices are distinct.
    assert ("abcd1234", "alpha") in hashes
    assert ("abcd1234", "beta") in hashes
    assert hashes[("abcd1234", "alpha")] != hashes[("abcd1234", "beta")]


def test_slice_hash_order_independent():
    forward = tracking.compute_intake_slice_hashes(_intake(_BASE_ROWS), _PARAM_INDEX)
    reversed_ = tracking.compute_intake_slice_hashes(
        _intake(list(reversed(_BASE_ROWS))), _PARAM_INDEX
    )
    assert forward[("abcd1234", "alpha")] == reversed_[("abcd1234", "alpha")]


def test_slice_hash_reacts_to_content_change():
    base = tracking.compute_intake_slice_hashes(_intake(_BASE_ROWS), _PARAM_INDEX)
    changed_rows = [dict(r) for r in _BASE_ROWS]
    changed_rows[0]["Segments"] = "w a t aː"
    changed = tracking.compute_intake_slice_hashes(_intake(changed_rows), _PARAM_INDEX)
    assert base[("abcd1234", "alpha")] != changed[("abcd1234", "alpha")]
    # the untouched beta slice is unaffected
    assert base[("abcd1234", "beta")] == changed[("abcd1234", "beta")]


def test_slice_hash_reacts_to_concept_resolution():
    """A parameters_raw.csv change that remaps a used concept changes the slice."""
    base = tracking.compute_intake_slice_hashes(_intake(_BASE_ROWS), _PARAM_INDEX)
    remapped = dict(_PARAM_INDEX, alpha_water=("9999", "AQUA"))
    changed = tracking.compute_intake_slice_hashes(_intake(_BASE_ROWS), remapped)
    assert base[("abcd1234", "alpha")] != changed[("abcd1234", "alpha")]


def test_manifest_roundtrip_and_freshness(tmp_path: Path):
    gen = tmp_path / "generated"
    forms = gen / "forms.csv"
    digest, components = tracking.fingerprint("c", "u", "s", "r")

    # No output yet → not fresh.
    assert tracking.is_fresh(gen, digest, forms) is False

    gen.mkdir()
    forms.write_text("av_id\n", encoding="utf-8")
    tracking.write_manifest(gen, digest, components, n_forms=2)

    # Same fingerprint → fresh; different fingerprint → stale.
    assert tracking.is_fresh(gen, digest, forms) is True
    other, _ = tracking.fingerprint("c", "u", "s", "DIFFERENT")
    assert tracking.is_fresh(gen, other, forms) is False

    loaded = tracking.load_manifest(gen)
    assert loaded["fingerprint"] == digest
    assert loaded["n_forms"] == 2
    assert loaded["components"] == components
