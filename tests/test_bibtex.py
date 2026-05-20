import pandas as pd

from arcaverborum.bibtex import load_bibtex, prefix_bibtex_file, prefix_bibtex_keys


class TestPrefixBibtexKeys:
    def test_single_key(self):
        assert prefix_bibtex_keys("smith2020", "ds") == "ds_smith2020"

    def test_multiple_keys(self):
        assert prefix_bibtex_keys("a;b;c", "ds") == "ds_a;ds_b;ds_c"

    def test_empty_string(self):
        assert prefix_bibtex_keys("", "ds") == ""

    def test_na(self):
        result = prefix_bibtex_keys(pd.NA, "ds")
        assert pd.isna(result)

    def test_keys_with_spaces(self):
        assert prefix_bibtex_keys("a ; b", "ds") == "ds_a;ds_b"


class TestPrefixBibtexFile:
    def test_single_entry(self):
        bib = '@article{smith2020,\n  title = {Test}\n}'
        result = prefix_bibtex_file(bib, "ds")
        assert "@article{ds_smith2020," in result

    def test_multiple_entries(self):
        bib = (
            "@article{a,\n  title = {A}\n}\n\n"
            "@book{b,\n  title = {B}\n}"
        )
        result = prefix_bibtex_file(bib, "ds")
        assert "@article{ds_a," in result
        assert "@book{ds_b," in result

    def test_preserves_content(self):
        bib = '@article{key,\n  author = {John Doe},\n  year = {2024}\n}'
        result = prefix_bibtex_file(bib, "ds")
        assert "John Doe" in result
        assert "2024" in result


class TestLoadBibtex:
    def test_existing_file(self, minimal_dataset_path):
        content = load_bibtex(minimal_dataset_path / "sources.bib")
        assert "src1" in content
        assert "src2" in content

    def test_missing_file(self, tmp_path):
        assert load_bibtex(tmp_path / "nonexistent.bib") == ""
