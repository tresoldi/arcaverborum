"""Research exports preserve evidence, membership, missingness and provenance."""
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('build_research_web',
                                             Path(__file__).resolve().parents[1] / 'scripts/build_research_web.py')
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def test_membership_is_individual_namespaced_and_deduplicated():
    assert builder.assignments({'Cognacy': 'source_1;source_2;source_1'}) == ['source_1', 'source_2']
    assert builder.assignments({'Cognacy': 'legacy_1', 'canonical_cognate_id': 'canonical_1'}) == ['canonical_1']
    assert builder.assignments({'Cognacy': ''}) == []


def test_complete_catalog_and_family_shards_preserve_research_evidence(tmp_path):
    aggregate = tmp_path / 'output/aggregate'
    data = tmp_path / 'src/arcaverborum/data'
    write_csv(data / 'concept_core.csv', [{'concept_id': 'bod-head'}])
    write_csv(data / 'varieties.csv', [dict(av_id='demo', latitude='0', longitude='0',
                                          parent_av_id='parent', iso639p3='abc', glottocode='test1234',
                                          notes='Named dialect')])
    write_csv(tmp_path / 'raw/glottolog/languages.csv',
              [dict(ID='test1234', Countries='XY', Family_ID='testfamily', Level='dialect')])
    write_csv(tmp_path / 'datasets.csv', [dict(NAME='source', CORE='TRUE')])
    write_csv(aggregate / 'metadata.csv', [dict(Dataset='source', Title='Fieldwork', License='CC-BY-4.0')])
    write_csv(aggregate / 'varieties.csv', [dict(av_id='demo', Name='Sample', Family='Family',
                                               transcription_source='source', tier='bronze')])
    write_csv(aggregate / 'parameters.csv', [dict(concept_id='bod-head', definition='Part of body')])
    write_csv(tmp_path / 'intake/lexibank/parameters_raw.csv', [dict(ID='p', Name='head (anatomy)')])
    write_csv(tmp_path / 'varieties/demo/custom/core_review.csv',
              [dict(Parameter_ID='p', decision='retain', rationale='Reviewed English sense; not native certification')])
    write_csv(tmp_path / 'intake/lexibank/languages.csv',
              [dict(ID='L', Name='Native sample label', Glottolog_Name='Catalog label')])
    write_csv(tmp_path / 'varieties/demo/generated/recordings.csv',
              [dict(av_id='demo', source_form_id='audio', source='source', raw_marker='►')])
    base = dict(source_language_id='L', av_id='demo', concept_id='bod-head', Form='a',
                Segments='a', Segments_Source='profile',
                transcription_source='source', source_form_id='one', source_parameter_id='p',
                Cognacy='source_1;source_2', Cognate_Source='expert_reference', cognate_source='source')
    write_csv(aggregate / 'forms.csv', [base, {**base, 'source_form_id': 'two', 'Segments_Source': 'unclean'},
        {**base, 'source_form_id': 'supplement', 'transcription_source': 'supplement',
         'cognate_source': 'supplement', 'Cognacy': '', 'concept_id': 'phy-water', 'Segments_Source': 'source'}])
    output = tmp_path / 'web/data'
    manifest = builder.build(tmp_path, output)
    assert manifest['counts']['forms'] == 3
    assert len(manifest['fields']) == len({f.lower() for f in manifest['fields']})
    catalog = json.loads(gzip.decompress((output / 'catalog.json.gz').read_bytes()))
    variety = catalog['languages'][0]
    assert variety['forms'] == 3
    assert variety['supported_core'] == 1  # Synonyms must not inflate concept coverage.
    assert variety['statuses'] == {'profile': 1, 'unclean': 1, 'source': 1}
    assert variety['core_metrics']['forms'] == 2
    assert variety['recordings'] == 1
    assert manifest['recordings']['records'] == 1
    assert (output / 'recordings.csv').exists()
    assert variety['core_metrics']['concept_ids'] == ['bod-head']
    assert variety['source_counts'] == {'source': 2, 'supplement': 1}
    assert variety['concept_ids'] == ['bod-head', 'phy-water']
    assert variety['parent_av_id'] == 'parent'
    assert variety['countries'] == 'XY'
    assert variety['glottolog_family_id'] == 'testfamily'
    assert variety['identity_level'] == 'dialect'
    assert 'Native sample label' in variety['aliases']
    assert variety['core_collection']
    spec = manifest['shards']['Family']
    raw = (output / Path(spec['url']).name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == spec['sha256']
    rows = [dict(zip(manifest['fields'], row)) for row in json.loads(gzip.decompress(raw))]
    assert rows[0]['cognate_evidence_source'] == 'expert_reference'
    assert json.loads(rows[0]['cognate_sets']) == ['source_1', 'source_2']
    assert rows[0]['source_gloss'] == 'head (anatomy)'
    assert rows[0]['mapping_review'] == 'retain'
    assert 'not native certification' in rows[0]['mapping_note']
    assert rows[0]['License'] == 'CC-BY-4.0'
    assert rows[1]['Segments_Source'] == 'unclean'
    assert rows[0]['preferred_source'] == 'source'
    assert rows[0]['evidence_role'] == 'configured_primary_supported'
    assert rows[1]['evidence_role'] == 'written_or_unresolved'
    assert rows[2]['preferred_source'] == ''
    assert rows[2]['evidence_role'] == 'supported_alternative'
    assert all(r['gled_dependence'] == 'none' for r in rows)
    previous_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.gz')}
    builder.build(tmp_path, output)
    assert previous_hashes == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.gz')}

    # Effective per-form overlays are applied after the guarded primary admission.
    # Export provenance must report the unmapping, not the older retained target.
    write_csv(tmp_path / 'varieties/demo/custom/primary.csv',
              [dict(source_form_id='one', mapping_decision='retain', rationale='Earlier admission')])
    write_csv(tmp_path / 'varieties/demo/custom/concept_map.csv',
              [dict(source_form_id='one', action='unmap', expected_form='a', notes='Source POS mismatch')])
    write_csv(aggregate / 'forms.csv', [{**base, 'concept_id': ''},
        {**base, 'source_form_id': 'two', 'Segments_Source': 'unclean'}])
    manifest = builder.build(tmp_path, output)
    spec = manifest['shards']['Family']
    rows = [dict(zip(manifest['fields'], row)) for row in
            json.loads(gzip.decompress((output / Path(spec['url']).name).read_bytes()))]
    assert rows[0]['concept_id'] == ''
    assert rows[0]['mapping_review'] == 'unmap'
    assert rows[0]['mapping_note'] == 'Source POS mismatch'
