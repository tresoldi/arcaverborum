"""Citation locators and secondary intake metadata survive aggregation."""
import csv
import hashlib
from pathlib import Path

from arcaverborum.aggregate import write_metadata, write_sources_bib
from arcaverborum.sources.wiktionary.provenance import write_provenance


def test_cldf_page_locators_resolve_base_key_from_extra_intake(tmp_path: Path):
    primary = tmp_path / 'primary.bib'
    primary.write_text('@book{lex_Author, title={Primary}}\n')
    extra = tmp_path / 'extra.bib'
    extra.write_text('@book{other_Genetti, title={Grammar}}\n\n@book{unused, title={Other}}\n')
    refs = {'lex_Author[12-15]', 'other_Genetti[130]', 'other_Genetti[523]'}
    assert write_sources_bib(primary, refs, tmp_path, [extra]) == 2
    text = (tmp_path / 'sources.bib').read_text()
    assert 'lex_Author,' in text and 'other_Genetti,' in text and 'unused' not in text
    assert 'other_Genetti[130]' in refs  # resolving never rewrites form provenance


def test_snapshot_citation_is_exported_without_inventing_dump_date_or_license(tmp_path: Path):
    extra = tmp_path / 'wiktionary'
    extra.mkdir()
    dump = tmp_path / 'dump.gz'
    dump.write_bytes(b'example snapshot')
    write_provenance(extra, dump, dict(forms=2, languages=1, parameters=2))
    metadata = extra / 'metadata.csv'
    row = next(csv.DictReader(metadata.open()))
    assert row['Repository_Version'] == 'sha256:' + hashlib.sha256(dump.read_bytes()).hexdigest()
    assert not row['License']
    text = (extra / 'sources.bib').read_text()
    assert 'Original dump date' in text and 'year =' not in text
    assert write_metadata(tmp_path / 'missing.csv', {'wiktionary'}, tmp_path, [metadata]) == 1
    assert next(csv.DictReader((tmp_path / 'metadata.csv').open()))['Form_Count'] == '2'
    assert write_sources_bib(tmp_path / 'missing.bib', {'wiktionary_kaikki2026'}, tmp_path,
                             [extra / 'sources.bib']) == 1
