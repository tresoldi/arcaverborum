"""Scientific invariants, source dependence, bounded joins and atomic publication."""
import csv
import itertools
import json
import subprocess
import sys
from pathlib import Path

import pytest

from arcaverborum.colexification import (
    DATA,
    SCHEMA,
    Limits,
    build,
    connect,
    digest,
    identity,
    pair_status,
    publish,
    representatives,
)

ROOT = Path(__file__).resolve().parents[1]


def csv_file(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def fixture(root, rows, count=4):
    data = root / 'src/arcaverborum/data'
    concepts = [dict(concept_id=f'x-{i}', concepticon_id=str(i), label=f'Concept {i}', pos='n',
                     semantic_field='Test', definition=f'Meaning {i}', status='active', replacement_id='', notes='')
                for i in range(count)]
    csv_file(data / 'concepts.csv', concepts)
    policy_dir = data / 'colexification'
    policy_dir.mkdir()
    (policy_dir / 'policy.json').write_bytes((DATA / 'colexification/policy.json').read_bytes())
    csv_file(policy_dir / 'expansions.csv', [], ['source_concept_id', 'target_a', 'target_b',
             'source_sha256', 'target_a_sha256', 'target_b_sha256', 'rationale'])
    aggregate = root / 'output/aggregate'
    varieties = [dict(av_id=av, Glottocode=av, Name=av, Family='Family', Macroarea='Area')
                 for av in ['a', 'dialect', 'b', 'unknown']]
    csv_file(aggregate / 'varieties.csv', varieties)
    csv_file(aggregate / 'parameters.csv', concepts)
    csv_file(root / 'raw/glottolog/languages.csv', [
        dict(ID=av, Language_ID='a' if av == 'dialect' else av, Family_ID='fam', Level='language', Is_Isolate='')
        for av in ['a', 'dialect', 'b']])
    csv_file(aggregate / 'metadata.csv', [dict(Dataset=s, License='CC-BY-4.0', Repository_Version='v1')
                                         for s in ['source', 'second', 'gled']])
    csv_file(aggregate / 'forms.csv', rows)
    return concepts


def form(concept, word='ma', av='a', source='source', member=None, fid=None, param=None, **kwargs):
    row = dict(av_id=av, concept_id=f'x-{concept}', Form=word, Segments=word, Segments_Source='source',
               transcription_source=source, source_language_id=member or source + '_' + av,
               source_form_id=fid or f'{source}-{concept}', source_parameter_id=param or f'p-{concept}',
               Value=word, raw_ipa='', pronunciation_tags='', source_pronunciation_id='',
               Doubt='', Loan='', bibtex_key='ref')
    row.update(kwargs)
    return row


def run(root, rows, count=4, limits=Limits()):
    fixture(root, rows, count)
    built = build(root, limits=limits)
    db = connect(built / 'index.sqlite')
    return built, db


def test_identity_retains_tone_quantity_case_and_boundaries():
    assert identity(' a\u0303   b ') == 'ã b'
    for a, b in [('a', 'aː'), ('ma˥', 'ma˩'), ('A', 'a'), ('a b', 'ab'), ('a + b', 'a b')]:
        assert identity(a) != identity(b)


def test_source_member_and_pronunciation_scope_do_not_mix(tmp_path):
    rows = [form(0), form(1, source='second'), form(1, member='other'),
            form(1, pronunciation_tags='dialect'), form(2, word='maː')]
    _, db = run(tmp_path, rows)
    assert db.execute('SELECT COUNT(*) FROM witnesses').fetchone()[0] == 0
    assert not list(pair_status(db, 'x-0', 'x-1'))
    db.close()


def test_original_ipa_and_explicit_stress_prevent_normalization_collisions(tmp_path):
    rows = [form(0, Segments='a b', raw_ipa='ˈab'), form(1, Segments='a b', raw_ipa='aˈb'),
            form(2, Segments='a b', Value='ˈab'), form(3, Segments='a b', Value='aˈb')]
    _, db = run(tmp_path, rows)
    assert not db.execute("SELECT 1 FROM edges WHERE layer='segmented'").fetchone()
    assert db.execute("SELECT 1 FROM edges WHERE layer='written'").fetchone()
    assert not list(pair_status(db, 'x-0', 'x-2'))  # distinct comparison bases do not invent negative evidence
    db.close()


def test_supplied_homophones_need_not_have_the_same_spelling(tmp_path):
    _, db = run(tmp_path, [form(0, word='to', Segments='t uː', raw_ipa='tuː'),
                          form(1, word='two', Segments='t uː', raw_ipa='tuː')])
    assert db.execute("SELECT 1 FROM edges WHERE layer='segmented'").fetchone()
    assert not db.execute("SELECT 1 FROM edges WHERE layer='written'").fetchone()
    db.close()


def test_original_ipa_cannot_override_an_accepted_reading_correction(tmp_path):
    _, db = run(tmp_path, [form(0, Segments='a', raw_ipa='a'), form(1, Segments='aː', raw_ipa='a')])
    assert not db.execute("SELECT 1 FROM edges WHERE layer='segmented'").fetchone()
    db.close()


def test_duplicates_synonyms_and_dialects_do_not_inflate_weights(tmp_path):
    rows = [form(i, av=av) for av in ['a', 'dialect', 'b'] for i in [0, 1]]
    rows += [rows[0], rows[1], form(0, source='second'), form(1, source='second')]
    built, db = run(tmp_path, rows)
    assert db.execute("SELECT varieties,languages,families FROM edges WHERE layer='segmented'").fetchone() == (3, 2, 1)
    manifest = json.loads((built / 'public/manifest.json').read_text())
    assert manifest['stats']['duplicate_readings'] == 4  # each duplicate has two representation layers
    db.close()


def test_same_original_mapping_cannot_manufacture_a_colexification(tmp_path):
    rows = [form(0, param='same'), form(1, param='same'), form(2, fid='one'), form(3, fid='one')]
    _, db = run(tmp_path, rows)
    assert not db.execute("SELECT 1 FROM witnesses WHERE a='x-0' AND b='x-1'").fetchone()
    assert not db.execute("SELECT 1 FROM witnesses WHERE a='x-2' AND b='x-3'").fetchone()
    assert not list(pair_status(db, 'x-0', 'x-1'))
    db.close()


def test_reduced_written_doubtful_and_unmapped_are_separate(tmp_path):
    rows = [form(0, source='gled'), form(1, source='gled'),
            form(2, word='na', Segments='', Segments_Source='resegmented'),
            form(3, word='na', Segments='', Segments_Source='unclean'),
            form(0, word='skip', Doubt='?'), form(1, word='skip'), form(0, concept_id='')]
    _, db = run(tmp_path, rows)
    assert not db.execute("SELECT 1 FROM edges WHERE layer='segmented'").fetchone()
    assert db.execute("SELECT 1 FROM edges WHERE layer='reduced'").fetchone()
    assert db.execute("SELECT 1 FROM edges WHERE layer='written' AND a='x-2' AND b='x-3'").fetchone()
    db.close()


def test_three_way_status_and_comparison_denominator(tmp_path):
    rows = [form(0), form(1), form(0, av='b', word='ma'), form(1, av='b', word='pa'),
            form(0, av='unknown')]
    _, db = run(tmp_path, rows)
    result = {r[1]: r[4] for r in pair_status(db, 'x-0', 'x-1')}
    assert result == {'a': 1, 'b': 0}  # unknown variety has no comparable second concept
    opp = json.loads(db.execute("SELECT opportunities FROM edges WHERE layer='segmented'").fetchone()[0])
    assert opp['comparable_varieties'] == 2 and opp['observed_fraction'] == .5
    assert opp['no_shared_form_observed'] == 1
    db.close()


def test_cli_presence_wins_over_a_distinct_second_source(tmp_path):
    rows = [form(0), form(1), form(0, source='second', word='pa'), form(1, source='second', word='ta')]
    built, db = run(tmp_path, rows)
    db.close()
    process = subprocess.run([sys.executable, str(ROOT / 'scripts/build_colexification.py'),
                              '--pair', 'x-0', 'x-1', '--database', str(built / 'index.sqlite')],
                             capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    import io
    statuses = {r['av_id']: r['status'] for r in csv.DictReader(io.StringIO(process.stdout))}
    assert statuses['a'] == 'colexified' and statuses['unknown'] == 'unknown'


def test_unknown_classification_does_not_add_a_fake_family(tmp_path):
    _, db = run(tmp_path, [form(0), form(1), form(0, av='unknown'), form(1, av='unknown')])
    assert db.execute("SELECT varieties,languages,families FROM edges WHERE layer='segmented'").fetchone() == (2, 1, 1)
    db.close()


def test_disjunctive_expansion_is_guarded_and_separate(tmp_path):
    concepts = fixture(tmp_path, [form(2)], count=3)
    p = tmp_path / 'src/arcaverborum/data/colexification/expansions.csv'
    csv_file(p, [dict(source_concept_id='x-2', target_a='x-0', target_b='x-1',
                     source_sha256=digest(concepts[2]), target_a_sha256=digest(concepts[0]),
                     target_b_sha256=digest(concepts[1]), rationale='Explicit disjunction')])
    built = build(tmp_path)
    db = connect(built / 'index.sqlite')
    assert db.execute("SELECT COUNT(*) FROM witnesses WHERE kind='observed'").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM witnesses WHERE kind='inferred'").fetchone()[0] == 2
    assert db.execute("SELECT original_concept FROM witnesses LIMIT 1").fetchone()[0] == 'x-2'
    db.close()
    concepts[2]['definition'] = 'Changed meaning'
    csv_file(tmp_path / 'src/arcaverborum/data/concepts.csv', concepts)
    with pytest.raises(ValueError, match='Stale'):
        build(tmp_path)


def test_pathological_identity_quarantined_without_negative_evidence(tmp_path):
    built, db = run(tmp_path, [form(i) for i in range(6)], 6, Limits(identity_concepts=4))
    assert db.execute('SELECT COUNT(*) FROM witnesses').fetchone()[0] == 0
    assert db.execute('SELECT COUNT(*) FROM coverage').fetchone()[0] == 0
    assert db.execute('SELECT COUNT(*) FROM quarantine').fetchone()[0] == 2
    assert json.loads((built / 'public/x-0.json').read_text())['status'] == 'no_comparable_segmented_data'
    db.close()


def test_representatives_preserve_all_compatibility_tests(tmp_path):
    db = connect(tmp_path / 'test.sqlite')
    db.executescript(SCHEMA)
    points = list(itertools.product('abc', 'xyz'))
    for mask in range(1, 1 << len(points)):
        db.execute('DELETE FROM readings')
        selected = [p for i, p in enumerate(points) if mask & (1 << i)]
        for fid, param in selected:
            db.execute('INSERT INTO readings(sid,layer,key,cid,fid,param) VALUES(1,?,?,?,?,?)',
                       ('segmented', 'ma', 'x', fid, param))
        reps = representatives(db, 1, 'segmented', 'ma', 'x')
        assert len(reps) <= 5
        for fid, param in itertools.product('abcd', 'xyzw'):
            assert any(f != fid and p != param for f, p in selected) == any(
                r[1] != fid and r[2] != param for r in reps)
    db.close()


def test_budget_failure_leaves_no_published_or_cached_partial_build(tmp_path):
    fixture(tmp_path, [form(i) for i in range(4)])
    with pytest.raises(RuntimeError, match='witness budget'):
        build(tmp_path, limits=Limits(max_witnesses=1))
    assert not list((tmp_path / 'output/colexification').iterdir())


def test_cli_runs_under_hard_address_space_limit(tmp_path):
    fixture(tmp_path, [form(0), form(1)])
    process = subprocess.run([sys.executable, str(ROOT / 'scripts/build_colexification.py'),
                              '--root', str(tmp_path), '--memory-mb', '128'], capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert '"memory_limit_mb": 128' in process.stdout


def test_large_duplicate_identity_uses_bounded_witness_representatives(tmp_path):
    fixture(tmp_path, [form(0), form(1)])
    rows = (form(i % 2, fid=f'word-{i:05d}') for i in range(20000))
    csv_file(tmp_path / 'output/aggregate/forms.csv', rows, list(form(0)))
    process = subprocess.run([sys.executable, str(ROOT / 'scripts/build_colexification.py'),
                              '--root', str(tmp_path), '--memory-mb', '128'],
                             capture_output=True, text=True, timeout=60)
    assert process.returncode == 0, process.stderr
    built = next((tmp_path / 'output/colexification').glob('*/complete.json')).parent
    summary = json.loads((built / 'complete.json').read_text())['stats']
    assert summary['input_records'] == 20000 and summary['witnesses'] == 2


def test_corrupt_cached_publication_is_rejected(tmp_path):
    built, db = run(tmp_path, [form(0), form(1)])
    db.close()
    (built / 'public/edges.csv').write_text('corrupt\n')
    with pytest.raises(ValueError, match='Corrupt'):
        build(tmp_path)


def test_fresh_builds_reproduce_all_public_bytes(tmp_path):
    fixture(tmp_path, [form(0), form(1), form(2, word='pa')])
    first = build(tmp_path)
    second = build(tmp_path, output=tmp_path / 'reproduced')
    before = {p.name: p.read_bytes() for p in (first / 'public').iterdir()}
    after = {p.name: p.read_bytes() for p in (second / 'public').iterdir()}
    assert before == after


def test_adjacency_pages_remain_bounded(tmp_path):
    built, db = run(tmp_path, [form(i) for i in range(4)], limits=Limits(page_edges=1))
    node = json.loads((built / 'public/x-0.json').read_text())
    pages = node['layers']['segmented']['observed']['pages']
    assert len(pages) == 3
    assert all(len(json.loads((built / 'public' / spec['url']).read_text())['edges']) == 1 for spec in pages)
    db.close()


def test_publish_checks_snapshot_and_keeps_immutable_build(tmp_path):
    built, db = run(tmp_path, [form(0), form(1)])
    db.close()
    manifest = json.loads((built / 'public/manifest.json').read_text())
    web = tmp_path / 'web/data'
    web.mkdir(parents=True)
    original = {'source_files': {name: manifest['inputs'].get('output/aggregate/' + name, '')
                                for name in ['forms.csv', 'varieties.csv', 'parameters.csv']}}
    (web / 'manifest.json').write_text(json.dumps(original))
    spec = publish(tmp_path, built)
    assert (tmp_path / 'web' / spec['url']).exists()
    before = (web / 'manifest.json').read_bytes()
    with (tmp_path / 'output/aggregate/forms.csv').open('a') as handle:
        handle.write('\n')
    with pytest.raises(ValueError, match='Stale'):
        publish(tmp_path, built)
    assert (web / 'manifest.json').read_bytes() == before
