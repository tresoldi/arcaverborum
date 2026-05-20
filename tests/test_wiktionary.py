"""Tests for the Wiktionary pipeline modules."""

import gzip
import json

from arcaverborum.sources.wiktionary.cognates import CognateBuilder
from arcaverborum.sources.wiktionary.extract import (
    WiktEtymology,
    extract_etymologies,
    extract_translations,
    stream_entries,
)
from arcaverborum.sources.wiktionary.langmap import (
    ISO639_1_TO_3,
    PROTO_TO_GLOTTOCODE,
    build_lang_mapper,
)
from arcaverborum.sources.wiktionary.parameters import make_parameter_id, make_parameter_name, slugify

# === parameters.py ===

class TestSlugify:
    def test_ascii(self):
        assert slugify("water") == "water"

    def test_accented(self):
        assert slugify("café") == "cafe"

    def test_spaces(self):
        assert slugify("ice cream") == "ice_cream"

    def test_special_chars(self):
        assert slugify("don't") == "don_t"

    def test_empty(self):
        assert slugify("") == "unknown"


class TestMakeParameterId:
    def test_basic(self):
        pid = make_parameter_id("water", "noun", "clear liquid")
        assert pid.startswith("wikt_water_noun_")
        assert len(pid) == len("wikt_water_noun_") + 8

    def test_different_senses_different_ids(self):
        pid1 = make_parameter_id("bank", "noun", "financial institution")
        pid2 = make_parameter_id("bank", "noun", "edge of river")
        assert pid1 != pid2

    def test_same_sense_same_id(self):
        a = make_parameter_id("water", "noun", "H2O")
        b = make_parameter_id("water", "noun", "H2O")
        assert a == b


class TestMakeParameterName:
    def test_with_sense(self):
        assert make_parameter_name("water", "noun", "liquid") == "water (noun): liquid"

    def test_without_sense(self):
        assert make_parameter_name("water", "noun", "") == "water (noun)"


# === langmap.py ===

class TestLangmap:
    def test_iso639_1_table_completeness(self):
        assert "en" in ISO639_1_TO_3
        assert "fr" in ISO639_1_TO_3
        assert "zh" in ISO639_1_TO_3
        assert len(ISO639_1_TO_3) >= 180

    def test_proto_table(self):
        assert "ine-pro" in PROTO_TO_GLOTTOCODE
        assert "gem-pro" in PROTO_TO_GLOTTOCODE
        assert len(PROTO_TO_GLOTTOCODE) >= 30

    def test_mapper_iso3(self):
        mapper = build_lang_mapper()
        m = mapper("fra", "French")
        assert m.iso639p3 == "fra"

    def test_mapper_iso1(self):
        mapper = build_lang_mapper()
        m = mapper("fr", "French")
        assert m.iso639p3 == "fra"

    def test_mapper_proto(self):
        mapper = build_lang_mapper()
        m = mapper("ine-pro", "Proto-Indo-European")
        assert m.glottocode == "indo1319"

    def test_mapper_unknown(self):
        mapper = build_lang_mapper()
        m = mapper("zzz-x-weird", "Unknown")
        assert m.iso639p3 == ""
        assert m.glottocode == ""


# === extract.py ===

class TestExtractTranslations:
    def test_basic_entry(self):
        entry = {
            "word": "water", "lang_code": "en", "pos": "noun",
            "translations": [
                {"word": "eau", "lang": "French", "lang_code": "fr", "sense": "liquid"},
                {"word": "Wasser", "lang": "German", "lang_code": "de", "sense": "liquid"},
            ],
        }
        trs = list(extract_translations(entry))
        assert len(trs) == 2
        assert trs[0].target_word == "eau"
        assert trs[0].target_lang_code == "fr"
        assert trs[0].sense == "liquid"

    def test_skips_empty_word(self):
        entry = {
            "word": "test", "lang_code": "en", "pos": "noun",
            "translations": [{"word": "", "lang_code": "fr", "sense": "s"}],
        }
        assert list(extract_translations(entry)) == []

    def test_skips_missing_lang_code(self):
        entry = {
            "word": "test", "lang_code": "en", "pos": "noun",
            "translations": [{"word": "mot", "sense": "s"}],
        }
        assert list(extract_translations(entry)) == []

    def test_tags_captured(self):
        entry = {
            "word": "test", "lang_code": "en", "pos": "noun",
            "translations": [
                {"word": "mot", "lang_code": "fr", "sense": "s",
                 "tags": ["archaic", "masculine"], "raw_tags": ["Northern"]},
            ],
        }
        trs = list(extract_translations(entry))
        assert trs[0].tags == ("archaic", "masculine")
        assert trs[0].raw_tags == ("Northern",)


class TestExtractEtymologies:
    def test_inh_template(self):
        entry = {
            "word": "water", "lang_code": "en",
            "etymology_templates": [
                {"name": "inh", "args": {"1": "en", "2": "enm", "3": "water"}},
            ],
        }
        etyms = list(extract_etymologies(entry))
        assert len(etyms) == 1
        assert etyms[0].kind == "inh"
        assert etyms[0].source_lang_code == "enm"
        assert etyms[0].word == "water"

    def test_descendants(self):
        entry = {
            "word": "watōr", "lang_code": "gem-pro",
            "descendants": [
                {"lang": "English", "lang_code": "en", "word": "water"},
                {"lang": "German", "lang_code": "de", "word": "Wasser"},
            ],
        }
        etyms = list(extract_etymologies(entry))
        assert len(etyms) == 2
        assert all(e.kind == "desc" for e in etyms)
        langs = {e.target_lang_code for e in etyms}
        assert langs == {"en", "de"}

    def test_nested_descendants(self):
        entry = {
            "word": "watōr", "lang_code": "gem-pro",
            "descendants": [
                {"lang": "Old English", "lang_code": "ang", "word": "wæter",
                 "descendants": [
                     {"lang": "English", "lang_code": "en", "word": "water"},
                 ]},
            ],
        }
        etyms = list(extract_etymologies(entry))
        assert len(etyms) == 2

    def test_skips_non_etymology_templates(self):
        entry = {
            "word": "test", "lang_code": "en",
            "etymology_templates": [
                {"name": "cog", "args": {"1": "en", "2": "la", "3": "testum"}},
            ],
        }
        assert list(extract_etymologies(entry)) == []


class TestStreamEntries:
    def test_gzip(self, tmp_path):
        path = tmp_path / "test.jsonl.gz"
        with gzip.open(path, "wt") as f:
            f.write(json.dumps({"word": "test"}) + "\n")
            f.write(json.dumps({"word": "fire"}) + "\n")
        entries = list(stream_entries(path))
        assert len(entries) == 2
        assert entries[0]["word"] == "test"

    def test_plain(self, tmp_path):
        path = tmp_path / "test.jsonl"
        path.write_text(json.dumps({"word": "test"}) + "\n")
        entries = list(stream_entries(path))
        assert len(entries) == 1


# === cognates.py ===

class TestCognateBuilder:
    def test_descendants_cognate_set(self):
        cb = CognateBuilder()
        cb.add_etymology(WiktEtymology("desc", "gem-pro", "en", "water", "watōr", "gem-pro", "watōr"))
        cb.add_etymology(WiktEtymology("desc", "gem-pro", "de", "Wasser", "watōr", "gem-pro", "watōr"))
        cb.finalize()

        en_cog = cb.get_cognate_ids("en", "water")
        de_cog = cb.get_cognate_ids("de", "Wasser")
        assert "wikt_gem-pro_watōr" in en_cog
        assert "wikt_gem-pro_watōr" in de_cog

    def test_no_match(self):
        cb = CognateBuilder()
        cb.finalize()
        assert cb.get_cognate_ids("xx", "nothing") == ""

    def test_loan_from_bor(self):
        cb = CognateBuilder()
        cb.add_etymology(WiktEtymology("bor", "fr", "en", "restaurant", "", "en", "restaurant"))
        assert cb.is_loan("en", "restaurant") is True

    def test_inherited_not_loan(self):
        cb = CognateBuilder()
        cb.add_etymology(WiktEtymology("inh", "enm", "en", "water", "", "en", "water"))
        assert cb.is_loan("en", "water") is False

    def test_multiple_cognate_sets(self):
        cb = CognateBuilder()
        cb.add_etymology(WiktEtymology("inh", "enm", "en", "water", "", "en", "water"))
        cb.add_etymology(WiktEtymology("desc", "gem-pro", "en", "water", "watōr", "gem-pro", "watōr"))
        cb.finalize()
        cog = cb.get_cognate_ids("en", "water")
        assert ";" in cog

    def test_finalize_required(self):
        cb = CognateBuilder()
        cb.add_etymology(WiktEtymology("desc", "gem-pro", "en", "water", "watōr", "gem-pro", "watōr"))
        assert cb.get_cognate_ids("en", "water") == ""
