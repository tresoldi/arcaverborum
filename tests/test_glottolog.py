"""Tests for arcaverborum.glottolog module."""

from arcaverborum.glottolog import GlottologEntry, resolve_language


def _make_glottolog():
    entries = {
        "stan1293": GlottologEntry(
            glottocode="stan1293", name="English", iso639p3="eng",
            macroarea="Eurasia", latitude=51.0, longitude=-1.0,
            family="Indo-European",
        ),
        "stan1290": GlottologEntry(
            glottocode="stan1290", name="French", iso639p3="fra",
            macroarea="Eurasia", latitude=48.0, longitude=2.0,
            family="Indo-European",
        ),
    }
    entries["iso:eng"] = entries["stan1293"]
    entries["iso:fra"] = entries["stan1290"]
    return entries


def test_resolve_by_glottocode():
    g = _make_glottolog()
    entry = resolve_language("stan1293", "", g)
    assert entry is not None
    assert entry.name == "English"
    assert entry.family == "Indo-European"


def test_resolve_by_iso():
    g = _make_glottolog()
    entry = resolve_language("", "fra", g)
    assert entry is not None
    assert entry.glottocode == "stan1290"


def test_resolve_unknown():
    g = _make_glottolog()
    entry = resolve_language("xxxx1234", "zzz", g)
    assert entry is None


def test_resolve_prefers_glottocode():
    g = _make_glottolog()
    entry = resolve_language("stan1293", "fra", g)
    assert entry is not None
    assert entry.name == "English"
