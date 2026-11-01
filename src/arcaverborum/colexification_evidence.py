"""Sense eligibility and bounded-influence projections of reported identities.

These are auditable robustness measures, not probabilities or significance tests.
Raw observed witnesses and rare associations remain available independently.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path


def rows(path):
    with path.open(newline='') as handle:
        yield from csv.DictReader(handle)


def inputs(root):
    root = Path(root)
    candidates = [root / 'intake/wiktionary/parameters_raw.csv',
                  root / 'src/arcaverborum/data/wiktionary_sense_overrides.csv',
                  root / 'src/arcaverborum/data/colexification/resource_blocks.json', Path(__file__)]
    candidates.append(root / 'src/arcaverborum/data/colexification/concept_relations.csv')
    for name in ['core_review.csv', 'source_sense_review.csv', 'concept_map.csv', 'primary.csv', 'supplements.csv']:
        candidates.extend(sorted((root / 'varieties').glob('*/custom/' + name)))
    return [p for p in candidates if p.exists()]


class SemanticEligibility:
    """Reviewed equivalences fail closed on conflicts, holds and ambiguous IDs."""
    def __init__(self, root):
        root = Path(root)
        self.shared, self.local, self.records = {}, {}, {}
        self.holds, self.record_holds, self.ambiguous = set(), set(), set()
        registry = block_registry(root)
        self.dictionary_sources = {'wiktionary'} | {s for s, b in registry.items() if b == 'wiktionary'}
        source = root / 'intake/wiktionary/parameters_raw.csv'
        rule = root / 'src/arcaverborum/data/wiktionary_sense_overrides.csv'
        authored = list(rows(rule)) if rule.exists() else []
        local, records = defaultdict(set), defaultdict(set)
        names = {'core_review.csv', 'source_sense_review.csv', 'concept_map.csv', 'primary.csv', 'supplements.csv'}
        for path in sorted((root / 'varieties').glob('*/custom/*.csv')):
            if path.name not in names:
                continue
            av = path.parents[1].name
            for r in rows(path):
                pid = r.get('Parameter_ID', '')
                decision = r.get('decision') or r.get('action')
                if pid.startswith('wikt_'):
                    if decision == 'needs_review':
                        self.holds.add((av, pid))
                    if decision in {'map', 'retain'}:
                        target = r.get('target_concept_id') or r.get('concept_id')
                        if target:
                            local[av, pid].add(target)
                if r.get('source') in self.dictionary_sources and r.get('source_form_id'):
                    key = av, r['source_form_id']
                    if decision == 'needs_review':
                        self.record_holds.add(key)
                    if decision == 'admit' and r.get('concept_id'):
                        records[key].add(r['concept_id'])
        self.local = {key: next(iter(v)) if len(v) == 1 else '' for key, v in local.items()}
        self.records = {key: next(iter(v)) if len(v) == 1 else '' for key, v in records.items()}
        wanted = {r['Parameter_ID'] for r in authored} | {pid for _, pid in self.local}
        parameters = {}
        if source.exists():
            for r in rows(source):
                if r['ID'] not in wanted:
                    continue
                if r['ID'] in parameters and parameters[r['ID']]['Name'] != r['Name']:
                    self.ambiguous.add(r['ID'])
                parameters[r['ID']] = r
        for r in authored:
            pid = r['Parameter_ID']
            if pid in self.ambiguous:
                raise ValueError('Ambiguous source parameter ID needs native-record review: ' + pid)
            p = parameters.get(pid, {})
            if (p.get('Name'), p.get('Concepticon_ID')) != (
                    r['expected_source_name'], r['expected_source_concepticon_id']):
                raise ValueError('Semantic review source drift: ' + pid)
            target = r['concept_id'] if r['action'] == 'map' else ''
            if pid in self.shared and self.shared[pid] != target:
                raise ValueError('Conflicting shared semantic reviews: ' + pid)
            self.shared[pid] = target

    def status(self, row):
        if row['transcription_source'] not in self.dictionary_sources:
            return 'source_mapping'  # An upstream equivalence, not independent semantic certification.
        av, pid, cid = row['av_id'], row['source_parameter_id'], row['concept_id']
        native = av, row['source_form_id']
        if native in self.record_holds or (native in self.records and not self.records[native]):
            return 'unreviewed_dictionary_sense'
        if self.records.get(native) == cid:
            return 'reviewed_dictionary_sense'  # Exact reviewed record may resolve a parameter-level hold.
        key = av, pid
        if pid in self.ambiguous or key in self.holds or (key in self.local and not self.local[key]):
            return 'unreviewed_dictionary_sense'
        if pid in self.shared and self.shared[pid] != cid:
            return 'unreviewed_dictionary_sense'
        if self.local.get(key) == cid or self.shared.get(pid) == cid:
            return 'reviewed_dictionary_sense'
        return 'unreviewed_dictionary_sense'


def block_registry(root):
    path = Path(root) / 'src/arcaverborum/data/colexification/resource_blocks.json'
    result = {}
    if path.exists():
        for block, members in json.loads(path.read_text())['blocks'].items():
            for member in members:
                if member in result:
                    raise ValueError('Duplicate resource block member: ' + member)
                result[member] = block
    return result


def summarize(family_blocks, multiplicity=None):
    """Minimax support: cap each lineage, then remove the most influential block.

    Each identity with k senses contributes 1 / choose(k,2) per reported pair.
    For each family take a maximum, rather than adding sources/lects/synonyms.
    Removing any one known resource block gives a lower sensitivity bound.
    """
    if any(not math.isfinite(w) or not 0 < w <= 1 for b in family_blocks.values() for w in b.values()):
        raise ValueError('Projection masses must lie in (0,1]')
    if multiplicity is not None and any(type(n) is not int or n < 0 for n in multiplicity.values()):
        raise ValueError('Family multiplicities must be nonnegative integers')
    weights = {family: blocks for family,blocks in family_blocks.items()
               if family and (multiplicity is None or multiplicity.get(family,0)>0)}
    def factor(family):
        return 1 if multiplicity is None else multiplicity.get(family,0)
    total = sum(max(blocks.values()) * factor(family) for family,blocks in weights.items())
    blocks = sorted({block for values in weights.values() for block in values})
    survivor = total
    min_families = len(weights)
    for removed in blocks:
        survivor = min(survivor, sum(max((w for block,w in values.items() if block!=removed), default=0)
                                    * factor(family) for family,values in weights.items()))
        min_families = min(min_families, sum(any(b!=removed for b in values) for values in weights.values()))
    if not blocks:
        survivor = 0
    eligible = len(weights)>=2 and survivor>0
    return dict(eligible_families=len(weights),resource_blocks=len(blocks),
                adjusted_support=round(total,12),resource_survival_support=round(survivor,12),
                families_without_one_block_min=min_families,backbone_eligible=eligible,
                clustering_weight=round(survivor,12) if eligible else 0.0)


def assess(db, root):
    """Only witness-sized sparse tables; no concept-pair or language dense matrix."""
    blocks = block_registry(root)
    db.execute('CREATE TABLE concept_relations(a TEXT,b TEXT,relation TEXT,PRIMARY KEY(a,b))')
    path = Path(root) / 'src/arcaverborum/data/colexification/concept_relations.csv'
    if path.exists():
        concepts = {r['concept_id']: r for r in rows(Path(root) / 'src/arcaverborum/data/concepts.csv')}
        for r in rows(path):
            a, b = r['a'], r['b']
            if a >= b or r['relation'] not in {'contains', 'overlap', 'equivalent'} or not r['rationale'].strip():
                raise ValueError('Invalid reviewed concept relation')
            for cid, guard in [(a, r['a_sha256']), (b, r['b_sha256'])]:
                if cid not in concepts or concepts[cid]['status'] != 'active':
                    raise ValueError('Unknown or inactive concept relation: ' + cid)
                encoded = json.dumps(concepts[cid], ensure_ascii=False, sort_keys=True).encode()
                actual = hashlib.sha256(encoded).hexdigest()
                if actual != guard:
                    raise ValueError('Concept relation definition drift: ' + cid)
            db.execute('INSERT INTO concept_relations VALUES(?,?,?)', (a, b, r['relation']))
    db.execute('CREATE TABLE resource_blocks(source TEXT PRIMARY KEY, block TEXT)')
    db.executemany('INSERT INTO resource_blocks VALUES(?,?)',
                   [(source,blocks.get(source,source)) for source, in db.execute('SELECT DISTINCT source FROM scopes')])
    db.executescript('''
      CREATE TABLE projection_blocks AS
       SELECT w.layer,w.a,w.b,v.family,b.block,MAX(2.0/(g.concepts*(g.concepts-1))) AS mass
       FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
       JOIN resource_blocks b ON b.source=s.source
       JOIN groups g ON g.sid=w.sid AND g.layer=w.layer AND g.key=w.key
       JOIN readings ra ON ra.id=w.ra JOIN readings rb ON rb.id=w.rb
       WHERE w.kind='observed' AND v.family<>''
         AND ra.semantic<>'unreviewed_dictionary_sense' AND rb.semantic<>'unreviewed_dictionary_sense'
       GROUP BY w.layer,w.a,w.b,v.family,b.block;
      CREATE UNIQUE INDEX projection_pair ON projection_blocks(layer,a,b,family,block);
      CREATE TABLE assessments(layer TEXT,a TEXT,b TEXT,value TEXT,PRIMARY KEY(layer,a,b));
    ''')
    for layer,a,b in db.execute("SELECT layer,a,b FROM edges WHERE kind='observed' ORDER BY layer,a,b"):
        family_blocks = defaultdict(dict)
        for family,block,mass in db.execute('SELECT family,block,mass FROM projection_blocks '
                                            'WHERE layer=? AND a=? AND b=?',(layer,a,b)):
            family_blocks[family][block] = mass
        assessment = summarize(family_blocks)
        counts = db.execute('''SELECT SUM(ra.semantic='unreviewed_dictionary_sense'
          OR rb.semantic='unreviewed_dictionary_sense'),COUNT(*) FROM witnesses w
          JOIN readings ra ON ra.id=w.ra JOIN readings rb ON rb.id=w.rb
          WHERE w.layer=? AND w.kind='observed' AND w.a=? AND w.b=?''',(layer,a,b)).fetchone()
        assessment.update(unreviewed_semantic_witnesses=counts[0] or 0,reported_witnesses=counts[1],
                          status='replicated_backbone' if assessment['backbone_eligible'] else
                          'semantic_review_required' if counts[0] == counts[1] else 'limited_replication')
        relation = db.execute('SELECT relation FROM concept_relations WHERE a=? AND b=?', (a, b)).fetchone()
        if relation:
            assessment.update(catalog_relation=relation[0], status='catalog_overlap',
                              backbone_eligible=False, clustering_weight=0.0)
        db.execute('INSERT INTO assessments VALUES(?,?,?,?)',(layer,a,b,json.dumps(assessment,sort_keys=True)))
    db.commit()


def projection_edges(db,index,multiplicity=None,where='',params=()):
    """Recompute deletion/resampling bounds from gated witness groups, not raw counts."""
    query='''SELECT w.a,w.b,v.family,b.block,MAX(2.0/(g.concepts*(g.concepts-1)))
      FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
      JOIN resource_blocks b ON b.source=s.source
      JOIN groups g ON g.sid=w.sid AND g.layer=w.layer AND g.key=w.key
      JOIN readings ra ON ra.id=w.ra JOIN readings rb ON rb.id=w.rb
      WHERE w.layer='segmented' AND w.kind='observed' AND v.family<>''
        AND ra.semantic<>'unreviewed_dictionary_sense' AND rb.semantic<>'unreviewed_dictionary_sense' '''
    if where:
        query+=' AND ('+where+')'
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='concept_relations'").fetchone():
        query += ' AND NOT EXISTS (SELECT 1 FROM concept_relations cr WHERE cr.a=w.a AND cr.b=w.b)'
    query+=' GROUP BY w.a,w.b,v.family,b.block ORDER BY w.a,w.b,v.family,b.block'
    result=[]
    for (a,b),group in itertools.groupby(db.execute(query,params), key=lambda r:r[:2]):
        family_blocks=defaultdict(dict)
        for _,_,family,block,mass in group:
            family_blocks[family][block]=mass
        value=summarize(family_blocks,multiplicity)['clustering_weight']
        if value>0:
            result.append((index[a],index[b],value))
    return result
