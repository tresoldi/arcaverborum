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


def test_aggregate_aligns_optional_fields_by_name_for_older_generated_slices(tmp_path):
    import yaml

    from arcaverborum.aggregate import aggregate_all
    from arcaverborum.forms_schema import FORMS_OUT_FIELDS
    root = tmp_path / 'varieties'
    for aid, old in [('a', False), ('b', True)]:
        folder = root / aid
        (folder / 'generated').mkdir(parents=True)
        (folder / 'config.yaml').write_text(yaml.safe_dump(dict(av_id=aid, name=aid,
            sources=dict(transcription='source', cognates='source'), scoring={})))
        fields = [k for k in FORMS_OUT_FIELDS if not old or k not in (
            'raw_ipa', 'pronunciation_tags', 'source_pronunciation_id')]
        row = dict.fromkeys(fields, '')
        row.update(av_id=aid, Form='a', concept_id='phy-water', transcription_source='source',
                   cognate_source='source', source_form_id=aid, Cognacy='source_hand-1', bibtex_key='book')
        with (folder / 'generated/forms.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
    intake = tmp_path / 'intake'
    intake.mkdir()
    (intake / 'metadata.csv').write_text('Dataset,Title\nsource,Example\n')
    (intake / 'sources.bib').write_text('@book{book, title={Example}}\n')
    out = tmp_path / 'aggregate'
    aggregate_all(root, intake, out)
    records = list(csv.DictReader((out / 'forms.csv').open()))
    assert len(records)==2 and all(r['Cognacy']=='source_hand-1' for r in records)
    assert all(r['raw_ipa']=='' and r['source_form_id']==r['av_id'] for r in records)
