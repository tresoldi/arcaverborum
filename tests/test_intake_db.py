"""The SQLite intake store must reproduce the DataFrame path exactly."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from arcaverborum import tracking
from arcaverborum.catalog import build_catalog
from arcaverborum.glottolog import GlottologEntry
from arcaverborum.intake_db import IntakeDB, build_intake_db
from arcaverborum.variety import (
    _INTAKE_USECOLS,
    FALLBACK_SOURCE,
    _load_intake_for_glottocodes,
    build_one,
    register,
)


def _glottolog() -> dict[str, GlottologEntry]:
    return {
        gc: GlottologEntry(glottocode=gc, name=name, iso639p3="", macroarea="Eurasia",
                           latitude=0.0, longitude=0.0, family="Testic")
        for gc, name in (("abcd1234", "A"), ("efgh5678", "B"))
    }


def _row(i, ds, gc, lang, form, **kw):
    base = {"ID": f"{ds}_{i}", "Dataset": ds, "Language_ID": lang, "Glottocode": gc,
            "Parameter_ID": f"{ds}_p{i % 3}", "Concepticon_Gloss": "",
            "Value": form, "Form": form, "Segments": " ".join(form),
            "Cognacy": "", "Alignment": "", "Loan": "", "Doubt": "", "Source": "",
            "Cognate_Detection_Method": "", "Comment": "", "Cognate_Source": "",
            "Morpheme_Index": "", "Segment_Slice": "", "Extra": "ignored"}
    base.update(kw)
    return base


def _setup(tmp_path: Path):
    # Interleaved rows, a padded/upper-case glottocode, a multi-line value,
    # and a GLED-only variety, spread over two files.
    f1 = pd.DataFrame([
        _row(1, "alpha", "abcd1234", "a1", "zeta"),
        _row(2, "alpha", " ABCD1234 ", "a2", "beta", Comment="line1\nline2"),
        _row(3, FALLBACK_SOURCE, "efgh5678", "g1", "mizu"),
        _row(4, "alpha", "abcd1234", "a1", "alfa", Cognacy="c1", Alignment="a l f a"),
    ])
    f2 = pd.DataFrame([_row(5, "wikt", "abcd1234", "w1", "omega"),
                       _row(6, "alpha", "abcd1234", "a1", "late", Segments="")])
    f2 = f2[list(reversed(f2.columns))]  # different column order per file
    paths = [tmp_path / "f1.csv", tmp_path / "f2.csv"]
    f1.to_csv(paths[0], index=False)
    f2.to_csv(paths[1], index=False)
    langs = tmp_path / "languages.csv"
    pd.DataFrame([
        {"ID": "a1", "Dataset": "alpha", "Name": "A", "Glottocode": "abcd1234"},
        {"ID": "g1", "Dataset": FALLBACK_SOURCE, "Name": "B", "Glottocode": "efgh5678"},
    ]).to_csv(langs, index=False)
    catalog = build_catalog(langs, glottolog=_glottolog(), overrides_path=tmp_path / "none.csv")
    return paths, catalog


def test_build_one_db_matches_dataframe(tmp_path: Path):
    paths, catalog = _setup(tmp_path)
    db_path = tmp_path / "intake.sqlite"
    build_intake_db(paths, db_path, _INTAKE_USECOLS)
    db = IntakeDB(db_path)
    assert db.is_current(paths)
    df = _load_intake_for_glottocodes(paths, {"abcd1234", "efgh5678"})

    cases = [("abcd1234", "alpha", ""), ("abcd1234", "wikt", ""),
             ("efgh5678", "alpha", ""), ("abcd1234", "alpha", "a1")]
    for gc, src, lang in cases:
        outs = []
        for name, intake in (("df", df), ("db", db)):
            root = tmp_path / name
            register(av_id=gc, varieties_root=root, transcription_source=src,
                     glottocode=gc, forms_score=0.5, tier="silver",
                     source_language_id=lang, overwrite=True)
            build_one(av_id=gc, varieties_root=root, intake_forms=intake, catalog=catalog)
            outs.append((root / gc / "generated" / "forms.csv").read_bytes())
        assert outs[0] == outs[1], (gc, src, lang)


def test_slice_hashes_db_match_files(tmp_path: Path):
    paths, _ = _setup(tmp_path)
    db_path = tmp_path / "intake.sqlite"
    build_intake_db(paths, db_path, _INTAKE_USECOLS)
    db = IntakeDB(db_path)
    pi = {"alpha_p1": ("1234", "WATER")}
    want = tracking.compute_slice_hashes_from_files(paths, pi)
    assert tracking.compute_slice_hashes_from_db(db, pi) == want
    keys = set(want) | {("nope0000", "alpha")}
    assert tracking.compute_slice_hashes_from_db(db, pi, keys=keys) == want


def test_stale_db_detected(tmp_path: Path):
    paths, _ = _setup(tmp_path)
    db_path = tmp_path / "intake.sqlite"
    build_intake_db(paths, db_path, _INTAKE_USECOLS)
    paths[1].write_text(paths[1].read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert not IntakeDB(db_path).is_current(paths)


def test_corrupt_db_is_rebuilt(tmp_path: Path):
    from arcaverborum.variety import open_intake_db

    paths, _ = _setup(tmp_path)
    db_path = tmp_path / "intake.sqlite"
    db_path.write_bytes(b"not a database")
    db = open_intake_db(db_path, paths)
    assert db.is_current(paths) and db.rows == 6


def test_non_string_dataset_matches_nothing(tmp_path: Path):
    paths, _ = _setup(tmp_path)
    db_path = tmp_path / "intake.sqlite"
    build_intake_db(paths, db_path, _INTAKE_USECOLS)
    db = IntakeDB(db_path)
    assert len(db.slice("abcd1234", "alpha")) == 4
    assert db.slice("abcd1234", 123).empty and db.slice("abcd1234", None).empty


def test_reviewed_member_union_keeps_order_and_fails_on_missing_member(tmp_path):
    import pytest
    import yaml

    from arcaverborum.variety import _slice_component

    paths, catalog = _setup(tmp_path)
    frame = pd.read_csv(paths[0], dtype=str, keep_default_na=False)
    frame.loc[frame.ID == 'alpha_4', ['Glottocode', 'Language_ID']] = ['efgh5678', 'dialect']
    frame.to_csv(paths[0], index=False)
    store = tmp_path / 'intake.sqlite'
    build_intake_db(paths, store, _INTAKE_USECOLS)
    db = IntakeDB(store)
    try:
        union = db.slice_many(['abcd1234', 'efgh5678'], 'alpha')
        assert union.ID.tolist() == ['alpha_1', 'alpha_2', 'alpha_4', 'alpha_6']
        root = tmp_path / 'varieties'
        register(av_id='abcd1234', varieties_root=root, transcription_source='alpha',
                 glottocode='abcd1234', forms_score=0.5, tier='bronze')
        config_path = root / 'abcd1234/config.yaml'
        config = yaml.safe_load(config_path.read_text())
        config['sources'].update(source_glottocodes=[' abcd1234 ', ' efgh5678 '],
                                 source_language_ids=['a1', 'dialect'])
        config_path.write_text(yaml.safe_dump(config))
        build_one('abcd1234', root, db, catalog)
        out = pd.read_csv(root / 'abcd1234/generated/forms.csv')
        assert out.source_form_id.tolist() == ['alpha_1', 'alpha_4', 'alpha_6']
        hashes = {('abcd1234', 'alpha'): 'a', ('efgh5678', 'alpha'): 'b'}
        first = _slice_component(config, 'abcd1234', hashes)
        hashes[('efgh5678', 'alpha')] = 'changed'
        assert _slice_component(config, 'abcd1234', hashes) != first
        config['sources']['source_language_ids'].append('disappeared')
        config_path.write_text(yaml.safe_dump(config))
        with pytest.raises(ValueError, match='members disappeared'):
            build_one('abcd1234', root, db, catalog)
    finally:
        db.close()
