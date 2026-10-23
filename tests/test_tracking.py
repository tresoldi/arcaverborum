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


def test_slice_hash_follows_intake_order():
    # build_one emits rows in intake order, so reordering changes the output
    # and must change the hash.
    forward = tracking.compute_intake_slice_hashes(_intake(_BASE_ROWS), _PARAM_INDEX)
    reversed_ = tracking.compute_intake_slice_hashes(
        _intake(list(reversed(_BASE_ROWS))), _PARAM_INDEX
    )
    assert forward[("abcd1234", "alpha")] != reversed_[("abcd1234", "alpha")]
    assert forward[("abcd1234", "beta")] == reversed_[("abcd1234", "beta")]


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


def test_slice_component_tracks_gled_when_fallback_possible():
    from arcaverborum.variety import FALLBACK_SOURCE, _slice_component

    hashes = {("abcd1234", "alpha"): "p:3", ("abcd1234", FALLBACK_SOURCE): "g:5"}
    changed = {**hashes, ("abcd1234", FALLBACK_SOURCE): "g:6"}
    cfg = {"sources": {"transcription": "alpha"}}
    # A non-empty primary slice and no Language_ID filter: GLED cannot be used.
    assert _slice_component(cfg, "ABCD1234", hashes) == "p:3"
    assert _slice_component(cfg, "abcd1234", changed) == "p:3"
    # An empty primary slice falls back to GLED, so GLED is tracked.
    empty = {k: v for k, v in hashes.items() if k[1] != "alpha"}
    empty_changed = {k: v for k, v in changed.items() if k[1] != "alpha"}
    assert _slice_component(cfg, "abcd1234", empty) != _slice_component(cfg, "abcd1234", empty_changed)
    # A Language_ID filter may empty the primary slice: GLED is tracked too.
    cfg_lid = {"sources": {"transcription": "alpha", "source_language_id": "x"}}
    assert _slice_component(cfg_lid, "abcd1234", hashes) != _slice_component(cfg_lid, "abcd1234", changed)
    # A GLED-sourced variety tracks its slice once.
    cfg_gled = {"sources": {"transcription": FALLBACK_SOURCE}}
    assert _slice_component(cfg_gled, "abcd1234", hashes) == "g:5"


def test_write_manifest_is_atomic(tmp_path, monkeypatch):
    import json as _json

    gen = tmp_path / "generated"
    tracking.write_manifest(gen, "old", {"config": "c"}, 1)
    before = tracking.manifest_path(gen).read_text(encoding="utf-8")

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(_json, "dumps", boom)
    try:
        tracking.write_manifest(gen, "new", {"config": "c"}, 2)
    except OSError:
        pass
    monkeypatch.undo()
    assert tracking.manifest_path(gen).read_text(encoding="utf-8") == before
    assert [p.name for p in gen.iterdir()] == [tracking.MANIFEST_NAME]


def test_atomic_path_keeps_old_file_on_failure(tmp_path):
    from arcaverborum.fsutil import atomic_path

    target = tmp_path / "forms.csv"
    target.write_text("old\n", encoding="utf-8")
    try:
        with atomic_path(target) as tmp:
            tmp.write_text("half", encoding="utf-8")
            raise RuntimeError("interrupted")
    except RuntimeError:
        pass
    assert target.read_text(encoding="utf-8") == "old\n"
    assert [p.name for p in tmp_path.iterdir()] == ["forms.csv"]
    with atomic_path(target) as tmp:
        tmp.write_text("new\n", encoding="utf-8")
    assert target.read_text(encoding="utf-8") == "new\n"
    assert oct(target.stat().st_mode & 0o777) != oct(0o600)


def test_recipe_hash_flags_merkmal_without_utf8proc(monkeypatch):
    import merkmal

    full = tracking.recipe_hash()
    monkeypatch.setattr(merkmal, "HAVE_UTF8PROC", False, raising=False)
    assert tracking.recipe_hash() != full
    monkeypatch.setattr(merkmal, "HAVE_UTF8PROC", True, raising=False)
    assert tracking.recipe_hash() == full
