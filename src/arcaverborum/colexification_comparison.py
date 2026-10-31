"""Compare frozen CLICS releases without changing Arca lexical or analytical evidence.

Reference CSV/GML is streamed into SQLite. Exact, unique Concepticon identities
are the only semantic crosswalk; CLICS4 expansions are separately measurable.
"""
from __future__ import annotations

import csv
import fcntl
import html
import io
import itertools
import json
import math
import os
import resource
import shutil
import sqlite3
import tempfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path

from arcaverborum.colexification import pair_status, read_csv, sha, verify_database

MAX_FIELD = 8 * 1024 * 1024


@contextmanager
def zipped_csv(path, member):
    csv.field_size_limit(MAX_FIELD)
    with zipfile.ZipFile(path) as archive:
        with archive.open(member) as stream:
            yield csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8', newline=''))


def gml_records(path):
    """Read only flat node/edge attributes used in the published CLICS3 GML.

    Ignore the very large provenance attributes; do not instantiate NetworkX.
    Reject unexpected nesting or truncated blocks instead of guessing.
    """
    wanted = {'id', 'label', 'Gloss', 'source', 'target', 'FamilyWeight', 'LanguageWeight', 'WordWeight'}
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith('.gml')]
        if len(names) != 1:
            raise ValueError('Expected one CLICS3 GML member')
        with archive.open(names[0]) as stream:
            record, kind = None, None
            while line := stream.readline(MAX_FIELD + 1):
                if len(line) > MAX_FIELD:
                    raise ValueError('Oversized CLICS3 GML line')
                text = line.decode('utf-8').strip()
                if text in {'node [', 'edge ['}:
                    if record is not None:
                        raise ValueError('Nested CLICS3 GML record')
                    record, kind = {}, text.split()[0]
                elif text == ']' and record is not None:
                    yield kind, record
                    record = None
                elif record is not None:
                    key, _, value = text.partition(' ')
                    if key in wanted:
                        record[key] = html.unescape(value.strip('"'))
            if record is not None:
                raise ValueError('Truncated CLICS3 GML record')


def unique_crosswalk(rows):
    groups = defaultdict(list)
    for row in rows:
        if row['status'] == 'active' and row.get('concepticon_id', '').isdigit():
            groups[row['concepticon_id']].append(row)
    return {key: values[0] for key, values in groups.items() if len(values) == 1}, {
        key: [v['concept_id'] for v in values] for key, values in groups.items() if len(values) != 1}


def overlap(a, b):
    return dict(arca=len(a), reference=len(b), shared=len(a & b), arca_only=len(a - b),
                reference_only=len(b - a), jaccard=len(a & b) / len(a | b) if a | b else None)


def verify_sources(root, cache, fetch=False):
    pin = root / 'src/arcaverborum/data/colexification/clics_sources.json'
    sources = json.loads(pin.read_text())
    cache.mkdir(parents=True, exist_ok=True)
    for spec in sources['sources']:
        path = cache / spec['path']
        if not path.exists() and fetch:
            temporary = path.with_suffix('.downloading')
            try:
                with urllib.request.urlopen(spec['url'], timeout=90) as response, temporary.open('wb') as output:
                    remaining = spec['bytes']
                    while chunk := response.read(min(65536, remaining + 1)):
                        remaining -= len(chunk)
                        if remaining < 0:
                            raise ValueError('Reference download exceeded pinned size')
                        output.write(chunk)
                if remaining != 0 or sha(temporary) != spec['sha256']:
                    raise ValueError('Reference download failed integrity check')
                temporary.rename(path)
            finally:
                temporary.unlink(missing_ok=True)
        if not path.exists() or path.stat().st_size != spec['bytes'] or sha(path) != spec['sha256']:
            raise ValueError(f'Missing or changed CLICS reference: {path}; use --fetch for missing files')
    return sources


def pair(a, b):
    if a == b:
        raise ValueError('Self-edge in reference')
    return tuple(sorted((a, b)))


def form_pair(value):
    a, b = value.split('/')
    return a.removeprefix('clics4-'), b.removeprefix('clics4-')


def rank_correlation(values):
    """Spearman's rho with average ranks for ties; no inference of causation."""
    values = list(values)
    if len(values) < 2:
        return None
    ranks = []
    for column in [0, 1]:
        counts = Counter(v[column] for v in values)
        table, offset = {}, 0
        for value, count in sorted(counts.items()):
            table[value] = offset + (count + 1) / 2
            offset += count
        ranks.append([table[v[column]] for v in values])
    mean = (len(values) + 1) / 2
    va = math.fsum((x - mean) ** 2 for x in ranks[0])
    vb = math.fsum((y - mean) ** 2 for y in ranks[1])
    covariance = math.fsum((x - mean) * (y - mean) for x, y in zip(*ranks))
    return covariance / math.sqrt(va * vb) if va and vb else None


def status_counts(positive, other_positive, other_comparable):
    return dict(confirmed=len(positive & other_positive),
                other_sampled_no_shared_form=len((positive - other_positive) & other_comparable),
                other_unknown=len(positive - other_positive - other_comparable))


def discordance_statuses(differences, comparable, ordered=False):
    """Stream a sparse list of positive discrepancies; unknown is not a zero."""
    counts = Counter(other_sampled_no_shared_form=0, other_unknown=0)
    rows = differences if ordered else sorted(differences)
    for (a, b), group in itertools.groupby(rows, key=lambda r: (r[0], r[1])):
        languages = {r[2] for r in group}
        available = comparable(a, b)
        counts['other_sampled_no_shared_form'] += len(languages & available)
        counts['other_unknown'] += len(languages - available)
    return dict(counts)


def _compare(root, cache, scratch, output, fetch=False):
    root, cache, scratch, output = map(Path, (root, cache, scratch, output))
    sources = verify_sources(root, cache, fetch)
    web = json.loads((root / 'web/data/manifest.json').read_text())
    native_manifest = root / 'web' / web['colexification']['url']
    if sha(native_manifest) != web['colexification']['sha256']:
        raise ValueError('Changed analytical manifest')
    native = json.loads(native_manifest.read_text())
    for name, expected in web.get('source_files', {}).items():
        if native['inputs'].get('output/aggregate/' + name) != expected:
            raise ValueError('Lexical and analytical snapshots differ')
    for name in ['src/arcaverborum/data/concepts.csv', 'raw/glottolog/languages.csv']:
        if sha(root / name) != native['inputs'][name]:
            raise ValueError(f'Changed comparison crosswalk input: {name}')
    crosswalk, ambiguous = unique_crosswalk(read_csv(root / 'src/arcaverborum/data/concepts.csv'))
    cid_to_icon = {v['concept_id']: k for k, v in crosswalk.items()}
    classification = {}
    for row in read_csv(root / 'raw/glottolog/languages.csv'):
        language = row.get('Language_ID') or (row['ID'] if row['Level'] == 'language' else '')
        classification[row['ID']] = language
    scratch.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(scratch).free < 256 * 1024 * 1024:
        raise RuntimeError('Insufficient comparison scratch space')
    os.environ['SQLITE_TMPDIR'] = str(scratch.resolve())
    dbpath = scratch / 'comparison.sqlite'
    dbpath.unlink(missing_ok=True)
    db = sqlite3.connect(dbpath, uri=True)
    db.execute('PRAGMA cache_size=-16384')
    db.execute('PRAGMA mmap_size=0')
    db.execute('PRAGMA temp_store=FILE')
    db.execute('PRAGMA journal_mode=OFF')
    page_size = db.execute('PRAGMA page_size').fetchone()[0]
    db.execute(f'PRAGMA max_page_count={3 * 1024**3 // page_size}')
    native_db = root / 'output/colexification' / native['build_id'] / 'index.sqlite'
    verify_database(native_db.parent)
    db.execute('ATTACH DATABASE ? AS arca', (f'file:{native_db}?mode=ro',))
    db.execute('PRAGMA arca.cache_size=-16384')
    db.executescript('''
      CREATE TABLE nodes(version TEXT, id TEXT, icon TEXT, label TEXT, original TEXT,
        PRIMARY KEY(version,id));
      CREATE TABLE edges(version TEXT,a TEXT,b TEXT,families INT,languages INT,varieties INT,
        family_weight REAL,PRIMARY KEY(version,a,b));
      CREATE TABLE forms(id TEXT PRIMARY KEY,lid TEXT,icon TEXT,derived INT,local TEXT,source TEXT,
        form TEXT,segments TEXT);
      CREATE TABLE ref_support(a TEXT,b TEXT,language TEXT,direct INT,
        PRIMARY KEY(a,b,language,direct));
      CREATE TABLE native_support(a TEXT,b TEXT,language TEXT,PRIMARY KEY(a,b,language));
    ''')
    for kind, row in gml_records(cache / 'clics3-clics3-network.gml.zip'):
        if kind == 'node':
            db.execute('INSERT INTO nodes VALUES(?,?,?,?,?)',
                       ('clics3', row['id'], row['label'], row['Gloss'], ''))
        else:
            a = db.execute("SELECT icon FROM nodes WHERE version='clics3' AND id=?", (row['source'],)).fetchone()[0]
            b = db.execute("SELECT icon FROM nodes WHERE version='clics3' AND id=?", (row['target'],)).fetchone()[0]
            a, b = pair(a, b)
            db.execute('INSERT INTO edges VALUES(?,?,?,?,?,?,?)',
                       ('clics3', a, b, int(row['FamilyWeight']), int(row['LanguageWeight']), None, None))
    with zipped_csv(cache / 'clics4-concepts.csv.zip', 'concepts.csv') as rows:
        for row in rows:
            db.execute('INSERT INTO nodes VALUES(?,?,?,?,?)', ('clics4', row['Concepticon_Gloss'],
                       row['Concepticon_ID'], row['Concepticon_Gloss'], row['Original_Concept']))
    # Tiny language/concept metadata may be indexed in memory; lexical rows stay on disk.
    icons = dict(db.execute("SELECT id,icon FROM nodes WHERE version='clics4'"))
    slug_icons = {}
    c4languages = {r['ID']: classification.get(r['Glottocode'], '')
                   for r in read_csv(cache / 'clics4-languages.csv')}
    form_count = derived_count = 0
    with zipped_csv(cache / 'clics4-forms.csv.zip', 'forms.csv') as rows:
        for row in rows:
            # The parameter table uses slug IDs, while the edge table uses Concepticon glosses.
            # Slugs are resolved through the actual concept table below, never re-created heuristically.
            if not slug_icons:
                with zipped_csv(cache / 'clics4-concepts.csv.zip', 'concepts.csv') as concepts:
                    slug_icons = {r['ID']: r['Concepticon_ID'] for r in concepts}
            db.execute('INSERT INTO forms VALUES(?,?,?,?,?,?,?,?)',
                       (row['ID'], row['Language_ID'], slug_icons[row['Parameter_ID']],
                        bool(row['ConceptInSource']), row['Local_ID'], row['Source'], row['Form'], row['Segments']))
            form_count += 1
            derived_count += bool(row['ConceptInSource'])
            if form_count % 10000 == 0:
                db.commit()
    db.commit()
    db.execute('CREATE INDEX forms_coverage ON forms(lid,icon,derived)')
    kinds = Counter()
    with zipped_csv(cache / 'clics4-colexifications.csv.zip', 'colexifications.csv') as rows:
        for row in rows:
            a, b = pair(icons[row['Source_Concept']], icons[row['Target_Concept']])
            db.execute('INSERT INTO edges VALUES(?,?,?,?,?,?,?)',
                       ('clics4', a, b, int(row['Family_Count']), int(row['Language_Count']),
                        int(row['Variety_Count']), float(row['Family_Weight'])))
            for value in row['Forms'].split():
                fa, fb = form_pair(value)
                ra = db.execute('SELECT lid,icon,derived,local FROM forms WHERE id=?', (fa,)).fetchone()
                rb = db.execute('SELECT lid,icon,derived,local FROM forms WHERE id=?', (fb,)).fetchone()
                if not ra or not rb or ra[0] != rb[0] or pair(ra[1], rb[1]) != (a, b):
                    raise ValueError('Reference witness does not agree with its edge')
                direct = reference_category(ra[2], ra[3], rb[2], rb[3]) == 'direct'
                kinds['direct_form_pairs' if direct else 'derived_or_shared_native_form_pairs'] += 1
                if ra[3] == rb[3]:
                    kinds['same_native_form_pairs'] += 1
                language = c4languages[ra[0]]
                if language:
                    db.execute('INSERT OR IGNORE INTO ref_support VALUES(?,?,?,?)', (a, b, language, direct))
    db.commit()
    # Native support is restricted to the main segmented observed layer.
    for a, b, language in db.execute('''SELECT DISTINCT w.a,w.b,v.language FROM arca.witnesses w
      JOIN arca.scopes s ON s.id=w.sid JOIN arca.varieties v ON v.av=s.av
      WHERE w.layer='segmented' AND w.kind='observed' AND v.language<>'' '''):
        if a in cid_to_icon and b in cid_to_icon:
            aa, bb = pair(cid_to_icon[a], cid_to_icon[b])
            db.execute('INSERT OR IGNORE INTO native_support VALUES(?,?,?)', (aa, bb, language))
    db.commit()
    arca_edges = {}
    for a, b, f, languages, v in db.execute(
            "SELECT a,b,families,languages,varieties FROM arca.edges "
            "WHERE layer='segmented' AND kind='observed'"):
        if a in cid_to_icon and b in cid_to_icon:
            arca_edges[pair(cid_to_icon[a], cid_to_icon[b])] = (f, languages, v)
    report = dict(schema=1, arca_build_id=native['build_id'], arca_manifest_sha256=sha(native_manifest),
                  inputs={name: sha(root / name) for name in ['src/arcaverborum/data/concepts.csv',
                                                           'raw/glottolog/languages.csv']},
                  code_sha256=sha(Path(__file__)), references=sources, excluded_ambiguous_crosswalk=ambiguous,
                  arca_unique_concepticon_ids=len(crosswalk), clics4_forms=form_count,
                  clics4_derived_forms=derived_count, clics4_witness_classification=dict(kinds), comparisons={})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix('.csv').open('w', newline='') as handle:
        fields = ['reference', 'concepticon_a', 'concepticon_b', 'arca_a', 'arca_b', 'label_a', 'label_b',
                  'common_concepts', 'arca_families', 'reference_families', 'arca_languages',
                  'reference_languages', 'arca_varieties', 'reference_varieties', 'reference_family_weight',
                  'reference_concept_expansion_a', 'reference_concept_expansion_b']
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for version in ['clics3', 'clics4']:
            nodes = {r[0]: (r[1], r[2]) for r in db.execute(
                'SELECT icon,label,original FROM nodes WHERE version=?', (version,))}
            common = set(nodes) & crosswalk.keys()
            refs = {(r[0], r[1]): r[2:] for r in db.execute(
                'SELECT a,b,families,languages,varieties,family_weight FROM edges WHERE version=?', (version,))}
            aa = {k for k in arca_edges if set(k) <= common}
            rr = {k for k in refs if set(k) <= common}
            recurrent_a = {k for k in aa if arca_edges[k][0] >= 3}
            recurrent_r = {k for k in rr if refs[k][0] >= 3}
            comparison = dict(reference_concepts=len(nodes), common_concepts=len(common),
                              full_reference_edges=len(refs), arca_edges_in_reference_universe=len(aa),
                              reference_edges_outside_common_universe=len(refs.keys() - rr),
                              arca_edges_outside_common_universe=len(arca_edges.keys() - aa),
                              three_family_overlap=overlap(recurrent_a, recurrent_r),
                              shared_edge_family_count_spearman=rank_correlation(
                                  (arca_edges[k][0], refs[k][0]) for k in aa & rr))
            if version == 'clics4':
                comparison['all_support_overlap'] = overlap(aa, rr)
                comparison['concepts_with_expansion_metadata'] = sum(bool(v[1]) for v in nodes.values())
            else:
                comparison['censoring'] = (
                    'Published CLICS3 graph contains only edges with at least three families; '
                    'unlisted edges below threshold are unknown.')
            report['comparisons'][version] = comparison
            for a, b in sorted(arca_edges.keys() | refs.keys()):
                av, rv = arca_edges.get((a, b)), refs.get((a, b))
                ca, cb = crosswalk.get(a, {}), crosswalk.get(b, {})
                writer.writerow(dict(reference=version, concepticon_a=a, concepticon_b=b,
                    arca_a=ca.get('concept_id', ''), arca_b=cb.get('concept_id', ''),
                    label_a=ca.get('label', nodes.get(a, ('',))[0]), label_b=cb.get('label', nodes.get(b, ('',))[0]),
                    common_concepts=a in common and b in common,
                    arca_families=av[0] if av else '', reference_families=rv[0] if rv else '',
                    arca_languages=av[1] if av else '', reference_languages=rv[1] if rv else '',
                    arca_varieties=av[2] if av else '', reference_varieties=rv[2] if rv else '',
                    reference_family_weight=rv[3] if rv else '',
                    reference_concept_expansion_a=nodes.get(a, ('', ''))[1],
                    reference_concept_expansion_b=nodes.get(b, ('', ''))[1]))
    # Control language and semantic universes, then exclude derived CLICS4 readings.
    shared_languages = set(c4languages.values()) & {r[0] for r in db.execute(
        "SELECT DISTINCT v.language FROM arca.coverage c JOIN arca.scopes s ON s.id=c.sid "
        "JOIN arca.varieties v ON v.av=s.av WHERE c.layer='segmented'")} - {''}
    common = set(icons.values()) & crosswalk.keys()
    db.execute('CREATE TABLE shared_languages(language TEXT PRIMARY KEY)')
    db.executemany('INSERT INTO shared_languages VALUES(?)', [(x,) for x in sorted(shared_languages)])
    db.execute('CREATE TABLE common_icons(icon TEXT PRIMARY KEY)')
    db.executemany('INSERT INTO common_icons VALUES(?)', [(x,) for x in sorted(common)])
    for name, source, condition in [('sa', 'native_support', '1'), ('sr', 'ref_support', '1'),
                                    ('sd', 'ref_support', 's.direct=1')]:
        db.execute(f'CREATE TABLE {name} AS SELECT DISTINCT s.a,s.b,s.language FROM {source} s '
                   'JOIN shared_languages l ON l.language=s.language '
                   'JOIN common_icons a ON a.icon=s.a JOIN common_icons b ON b.icon=s.b WHERE ' + condition)
        db.execute(f'CREATE UNIQUE INDEX {name}_key ON {name}(a,b,language)')

    def sql_overlap(left, right, columns='a,b,language'):
        a = db.execute(f'SELECT COUNT(*) FROM (SELECT DISTINCT {columns} FROM {left})').fetchone()[0]
        b = db.execute(f'SELECT COUNT(*) FROM (SELECT DISTINCT {columns} FROM {right})').fetchone()[0]
        shared = db.execute(f'SELECT COUNT(*) FROM (SELECT {columns} FROM {left} INTERSECT '
                            f'SELECT {columns} FROM {right})').fetchone()[0]
        return dict(arca=a, reference=b, shared=shared, arca_only=a-shared, reference_only=b-shared)

    report['matched_clics4'] = dict(shared_current_glottolog_languages=len(shared_languages),
        note=('Language units use the same current Glottolog collapse; '
              'source questionnaires and readings are still different.'),
        pair_language_all=sql_overlap('sa', 'sr'),
        pair_language_direct_readings=sql_overlap('sa', 'sd'),
        edges_all=sql_overlap('sa', 'sr', 'a,b'),
        edges_direct_readings=sql_overlap('sa', 'sd', 'a,b'),
        direct_rule=('Both CLICS4 forms have empty ConceptInSource and distinct Local_ID; '
                     'expanded readings are excluded, not declared invalid.'))
    db.execute('CREATE INDEX forms_concepts ON forms(icon,lid,derived)')
    native_connection = sqlite3.connect(f'file:{native_db}?mode=ro', uri=True)
    native_connection.execute('PRAGMA cache_size=-8192')
    def native_available(a, b):
        return {r[2] for r in pair_status(native_connection,
                crosswalk[a]['concept_id'], crosswalk[b]['concept_id']) if r[2] in shared_languages}
    def reference_available(a, b):
        return {c4languages[r[0]] for r in db.execute(
            'SELECT DISTINCT f.lid FROM forms f JOIN forms g ON f.lid=g.lid '
            'WHERE f.icon=? AND g.icon=? AND f.derived=0 AND g.derived=0 AND f.local<>g.local', (a, b))}
    report['matched_clics4']['reference_direct_only_status_in_arca'] = discordance_statuses(
        db.execute('SELECT a,b,language FROM sd EXCEPT SELECT a,b,language FROM sa ORDER BY a,b,language'),
        native_available, ordered=True)
    report['matched_clics4']['arca_only_status_in_reference_direct'] = discordance_statuses(
        db.execute('SELECT a,b,language FROM sa EXCEPT SELECT a,b,language FROM sd ORDER BY a,b,language'),
        reference_available, ordered=True)
    native_connection.close()
    # Audit strongest missing pairs, largest family-count deltas and familiar patterns.
    # Pair coverage stays source-scoped; no dense coverage matrix is constructed.
    ref4 = {(r[0], r[1]): r[2] for r in db.execute(
        "SELECT a,b,families FROM edges WHERE version='clics4'") if r[0] in common and r[1] in common}
    import heapq
    chosen = set(heapq.nlargest(10, (k for k in ref4 if k not in arca_edges), key=lambda k: (ref4[k], k)))
    chosen.update(heapq.nlargest(10, (k for k in aa if k not in ref4), key=lambda k: (arca_edges[k][0], k)))
    chosen.update(heapq.nlargest(10, ref4, key=lambda k: (abs(ref4[k] - arca_edges.get(k, (0,))[0]), k)))
    chosen.update(pair(a, b) for a, b in [('906', '1803'), ('1313', '1370'), ('72', '1258'),
                                       ('1297', '1301'), ('1277', '1673'), ('763', '1204'),
                                       ('837', '1425'), ('634', '2259')])
    native_connection = sqlite3.connect(f'file:{native_db}?mode=ro', uri=True)
    native_connection.execute('PRAGMA cache_size=-8192')
    diagnostics = {}
    for a, b in sorted(chosen):
        if a not in crosswalk or b not in crosswalk:
            continue
        ac, bc = crosswalk[a]['concept_id'], crosswalk[b]['concept_id']
        native_comparable, native_positive = set(), set()
        for _, _, language, _, positive in pair_status(native_connection, ac, bc):
            if language in shared_languages:
                native_comparable.add(language)
                if positive:
                    native_positive.add(language)
        ref_positive = {r[0] for r in db.execute(
            'SELECT language FROM ref_support WHERE a=? AND b=? AND direct=1', (a, b))} & shared_languages
        ref_comparable = {c4languages[r[0]] for r in db.execute(
            'SELECT DISTINCT f.lid FROM forms f JOIN forms g ON f.lid=g.lid '
            'WHERE f.icon=? AND g.icon=? AND f.derived=0 AND g.derived=0 AND f.local<>g.local', (a, b))}
        ref_comparable &= shared_languages
        source_counts = dict(db.execute(
            "SELECT s.source,COUNT(DISTINCT s.av) FROM arca.witnesses w "
            "JOIN arca.scopes s ON s.id=w.sid WHERE w.a=? AND w.b=? "
            "AND w.layer='segmented' AND w.kind='observed' GROUP BY s.source ORDER BY COUNT(*) DESC",
            tuple(sorted((ac, bc)))))
        inferred = db.execute(
            "SELECT varieties FROM arca.edges WHERE layer='segmented' AND kind='inferred' AND a=? AND b=?",
            tuple(sorted((ac, bc)))).fetchone()
        diagnostics[a + ':' + b] = dict(concepticon_ids=[a, b], arca_ids=[ac, bc],
            labels=[crosswalk[a]['label'], crosswalk[b]['label']],
            arca_families=arca_edges.get((a, b), (0,))[0], reference_families=ref4.get((a, b), 0),
            arca_inferred_varieties=inferred[0] if inferred else 0,
            reference_current_language_units_all=db.execute(
                'SELECT COUNT(DISTINCT language) FROM ref_support WHERE a=? AND b=?', (a, b)).fetchone()[0],
            reference_current_language_units_direct=db.execute(
                'SELECT COUNT(DISTINCT language) FROM ref_support WHERE a=? AND b=? AND direct=1',
                (a, b)).fetchone()[0],
            shared_sample=dict(arca_comparable=len(native_comparable), reference_direct_comparable=len(ref_comparable),
                arca_positive_vs_reference_direct=status_counts(native_positive, ref_positive, ref_comparable),
                reference_direct_positive_vs_arca=status_counts(ref_positive, native_positive, native_comparable)),
            arca_supporting_sources_varieties=source_counts, reference_examples=[])
    native_connection.close()
    with zipped_csv(cache / 'clics4-colexifications.csv.zip', 'colexifications.csv') as rows:
        for row in rows:
            a, b = pair(icons[row['Source_Concept']], icons[row['Target_Concept']])
            diagnostic = diagnostics.get(a + ':' + b)
            if diagnostic is None:
                continue
            seen = set()
            for value in row['Forms'].split():
                fa, fb = form_pair(value)
                evidence = [db.execute('SELECT id,lid,derived,local,source,form,segments FROM forms WHERE id=?',
                                       (fid,)).fetchone() for fid in [fa, fb]]
                category = reference_category(evidence[0][2], evidence[0][3], evidence[1][2], evidence[1][3])
                if category in seen:
                    continue
                seen.add(category)
                diagnostic['reference_examples'].append(dict(category=category,
                    same_native_form=evidence[0][3] == evidence[1][3], forms=[dict(
                        zip(['id', 'variety_id', 'expanded', 'local_id', 'source', 'form', 'segments'], r))
                        for r in evidence]))
                if len(seen) == 3:
                    break
    arca_sources = {r[0] for r in db.execute(
        "SELECT DISTINCT s.source FROM arca.coverage c JOIN arca.scopes s ON s.id=c.sid "
        "WHERE c.layer='segmented'")}
    reference_sources = {r[0] for r in db.execute('SELECT DISTINCT source FROM forms')}
    report['source_namespace_overlap'] = dict(
        shared=sorted(arca_sources & reference_sources), reference_only=sorted(reference_sources - arca_sources),
        arca_only=sorted(arca_sources - reference_sources),
        note=('Exact namespace match only; versions and selected members may still differ. '
              'Shared sources are not independent confirmation.'))
    report['diagnostics'] = list(diagnostics.values())
    report['peak_rss_mib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    report['address_space_limit_mib'] = resource.getrlimit(resource.RLIMIT_AS)[0] / 1024 / 1024
    report['csv_sha256'] = sha(output.with_suffix('.csv'))
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    db.close()
    return report


def reference_category(derived_a, local_a, derived_b, local_b):
    if derived_a or derived_b:
        return 'expanded'
    return 'shared_native' if local_a == local_b else 'direct'


def compare(root, cache, scratch, output, fetch=False):
    """Commit an immutable complete bundle before switching its pointer.

    Flat CSV/JSON copies are compatibility exports. The bundle pointer is the
    authoritative publication and changes only after both files are complete.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.' + output.name + '-', dir=output.parent))
    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    lock = (scratch / '.comparison.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report = _compare(root, cache, scratch, stage / 'report', fetch)
        fingerprint = sha(stage / 'report.json')[:24]
        destination = output.parent / (output.name + '-bundles') / fingerprint
        destination.parent.mkdir(exist_ok=True)
        if not destination.exists():
            stage.rename(destination)
        else:
            for name in ['report.csv', 'report.json']:
                if sha(stage / name) != sha(destination / name):
                    raise ValueError('Conflicting comparison bundle')
        files = {name: dict(url=str((destination / name).relative_to(output.parent)),
                           sha256=sha(destination / name), bytes=(destination / name).stat().st_size)
                 for name in ['report.csv', 'report.json']}
        for suffix in ['csv', 'json']:
            temporary = output.with_suffix('.' + suffix + '.publishing')
            shutil.copyfile(destination / ('report.' + suffix), temporary)
            os.replace(temporary, output.with_suffix('.' + suffix))
        pointer = output.with_suffix('.bundle.json')
        temporary = pointer.with_suffix('.publishing')
        temporary.write_text(json.dumps(dict(files=files), indent=2) + '\n')
        os.replace(temporary, pointer)
        return report
    finally:
        lock.close()
        shutil.rmtree(stage, ignore_errors=True)
