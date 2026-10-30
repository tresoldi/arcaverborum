# Concept links to WordNet

The primary target is **Open English WordNet 2025, standard edition**. Princeton
WordNet **3.0** compatibility is carried through the Collaborative Interlingual
Index (CILI), never by treating numeric offsets in different editions as equal.
The user selected typed approximate links and an explicit review queue.

This is a sidecar to the frozen concept catalog. It does not change concept IDs,
labels, definitions, lexical assignments, source glosses, cognacy or readings.
It covers all 3,789 active catalog concepts and accounts separately for 39 merged
entries. The 39 active and two merged concepts without accepted lexical records
are now visible in the web catalog too. A cross-linguistic meaning slot need not have a single
English WordNet equivalent; function words, classifiers and disjunctive meanings
must not be forced into an unrelated synset.

## Meaning of each status and relation

* `accepted`: either a guarded explicit sense review, or a unique normalized full
  definition identity supported by a matching lexical label and compatible POS.
* `source_association`: an inherited Concepticon association, independently checked
  for target identity but **not certified as an exact semantic equivalence**.
* `candidate`: a ranked search suggestion requiring sense review. Scores are search
  diagnostics, not confidence estimates or evidence of equivalence.

Accepted relations are `exact`, `broader`, `narrower`, and `related`. Direction is
**Arca concept → WordNet target**: `broader` means the **target** is broader than the
Arca meaning; `narrower` means the target is narrower. `related` records overlap
without asserting inclusion. `association` is reserved for inherited links and
unreviewed candidates. Do not use every row of `links.csv` as an equivalence map:
filter `status=accepted` and `relation=exact` for that purpose.

For example, generic **moon** is linked exactly to any planetary natural satellite,
while the inherited Earth-specific Moon association remains separately visible.
**Water** is linked to the chemical substance, rather than only the beverage.
**Child** has two narrower links: a young human, and offspring of any age. Cardinal
number concepts use noun senses rather than merely matching numeral adjectives.
Wife/husband definitions retain narrower links where the target imposes a spouse-sex
restriction absent from Arca's definition.

## Initial coverage, 2026-10-30

| Measure | Count |
| --- | ---: |
| Accepted exact links | 141 |
| Accepted broader / narrower / related links | 28 / 14 / 10 |
| Active concepts with any accepted link | 190 |
| Remaining inherited associations | 1,236 |
| Additional concepts with only inherited associations | 1,202 |
| Concepts with review candidates but no link | 2,365 |
| Active concepts currently unlinked | 32 |
| Search candidates, across linked and unlinked concepts | 10,791 |
| Merged entries, with no inherited or automatic links | 39 |

These are distinct quantities: 1,392 active concepts have an accepted link or an
inherited association, but only 190 have accepted sense judgments. The review
queue is deliberately much broader than accepted equivalence coverage. There are
158 explicit review decisions spanning 155 basic-vocabulary concepts, with
explicit holds for the other six; 35 further links meet the guarded definition/label/POS identity rule. Review remains necessary
for most of the catalog. All 161 core concepts have explicit sense decisions or
holds. Six pronoun/deictic cases have explicit holds to suppress homographic acronym, letter, numeral and locative-adverb suggestions.

## Resources and a corrected version ambiguity

All 1,372 rows of Concepticon v2.6.0's WordNet crosswalk were checked against
actual Princeton 3.0 **full glosses**, including examples; every row agrees.
Its metadata points to a 3.1 URI convention, which would be unsafe to trust as the
resource version. Adjective-satellite `a` aliases are resolved to native `s` only
when the actual dictionary gloss verifies the target. The original reference is
retained in each inherited link's `source_reference`. The verified crosswalk
covers 1,366 active Arca concepts before reviewed associations are superseded.

CILI maps verified PWN 3.0 senses to OEWN by ILI identity. If no standard OEWN
2025 target exists, the explicit PWN 3.0 target remains a fallback. This matters
for named entities moved outside the standard edition. No fabricated OEWN ID is
assigned, and external browsing may advance to a newer inventory: the frozen
ID, definition, version and ILI in the export remain authoritative here.

The [source manifest](../src/arcaverborum/data/wordnet/sources.json) records URLs,
SHA-256 hashes, versions, licenses, attribution and the complete Princeton license.
OEWN and Concepticon are CC BY 4.0; CILI is CC BY 4.0 or later; Princeton carries
its own permissive license. The Concepticon release's pinned `.zenodo.json`
establishes its license. WordNet definitions are attributed to their original
resource, not presented as Arca-authored definitions.

## Files and reproduction

Tracked files live under `src/arcaverborum/data/wordnet/`:

* `sources.json`: resource pins, attribution and licenses.
* `review.csv`: explicit reviewed relation, rationale, concept and target hashes.
* `holds.json`: guarded unresolved cases and reopening reasons.
* `bundle.json`: validated runtime sidecar containing links, candidates and selected
  frozen synsets. It is generated; do not hand-edit it.
* `links.csv`, `candidates.csv`, `coverage.csv`, `summary.json`: generated exports.

Rebuild from pinned resources without changing lexical data:

```sh
.venv/bin/python scripts/build_wordnet.py --fetch
.venv/bin/pytest -q tests/test_wordnet.py tests/test_research_web.py
.venv/bin/python scripts/build_research_web.py
```

Downloaded originals stay in ignored `raw/wordnet/`. Every resource is verified
before parsing. Candidate ranking is deterministic, with at most three suggestions
per concept. Reproduction requires no new runtime dependencies.

The loader requires a rebuild whenever review decisions, holds or source metadata change. It binds every concept to its frozen identity/definition/POS/status hash
and every target to its complete frozen target hash. Stale reviews, unknown
concepts, unresolved bridge glosses, duplicates and candidates masquerading as
accepted links fail validation. Merged entries remain accounted for without
silently equating their old meanings to replacements.

Every concept page shows its mapping status and counts of exact, approximate,
inherited and candidate links, without requiring a family download. Reviewed
sense links and inherited associations have separate sections; candidate details
remain collapsed, and held/merged/unlinked states are explicit. Concept search accepts synset/ILI identifiers. Seven downloadable
sidecars have manifest hashes; selection manifests retain this WordNet provenance.
Existing lexical CSV columns and all family records remain unchanged.

## Continuing review

Start with inherited associations and frequently attested concepts; inspect both
frozen definitions, POS, target lemmas and historical scope. Use multiple narrower
links for genuine disjunctions. Add a rationale and fresh concept/target hashes to
`review.csv`, rebuild, inspect the semantic diff, and run the tests above. For
rejected homographs or meanings not lexicalized in the pinned inventory, add a
specific guarded hold. Do not raise accepted coverage by relaxing the ranking
threshold, rewriting frozen concept definitions, or silently promoting inherited
Concepticon associations. OEWN upgrades require new resource pins and a reviewed
ILI/version crosswalk, including splits, merges and retired senses.

## Verification and publication

[Local verification](wordnet_verification_2026-10-30.json): 519 tests, full lint,
JavaScript syntax and 15 browser suites pass. WordNet/general browser checks were
repeated after the final core reviews. All five generated mapping files reproduce
byte-for-byte; all 401 lexical shards, aggregate hashes and earlier catalog fields
remain unchanged.

[Publication proof](wordnet_publication_2026-10-30.json): data commit `f217e5b1` is
pushed; CI and Pages succeed. All 414 checked canonical artifacts on
https://arcaverborum.org/ match, including the seven WordNet downloads. Live WordNet
and general research browser suites pass.
