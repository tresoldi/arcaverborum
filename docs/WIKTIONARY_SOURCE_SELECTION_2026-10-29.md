# Reviewed Wiktionary source preference — 2026-10-29

This batch applies the user's preference for trustworthy, richer Wiktionary
readings over the historical GLED-before-Wiktionary ordering. It changes four
explicit recipes: Yurok, Ternate, Corsican and Lombard. No global source-name
ranking or runtime fallback is inverted. Missing guarded primary evidence fails
closed under the existing build rules.

## Evidence and decisions

The source is the existing frozen Kaikki/Wiktionary snapshot, SHA256
`a6a32d41e35990b79a886d9082ebb3459a16fbaed6d2995aaedf6ef46d3ee643`.
New admissions use supplied IPA matched to the exact language, NFC headword and
POS, with the existing conservative unqualified-pronunciation rules. Full original
IPA, URL and source evidence remain attached; no spelling is promoted to IPA.
Lombard's earlier reviewed Milanese-tagged readings retain their exact scope and
all eligible alternatives. No generic Lombard pronunciation system is inferred.

[Authored sense review](wiktionary_source_selection_review_2026-10-29.csv) covers
128 Yurok/Ternate candidate records, including earlier admissions. Anatomy versus
measurement, edible fruit versus plant, pronoun number, and material versus plant
are distinguished. Existing shared sense corrections and specialist-review holds
are retained. Corsican and Lombard use their earlier reviewed admissions unchanged.

The bounded Wiktionary primary is an evidence preference, not a claim that it
covers the entire language better than every GLED row. Every earlier GLED record
remains in a guarded supplemental ledger, retaining its source-specific cognacy
and residual coverage. GLED overlap is not independent confirmation, and its
ASJP-derived representations remain limited. No variety-level score or expert cognacy judgment is changed. The existing per-form
formula recalculates some retained GLED scores because a guarded ledger makes the
concept mapping explicit; this is an annotation effect, not evidence of improved
GLED phonology. The metrics count these changes separately.

A concrete distinction is Lombard dog: earlier GLED readings are `k ɐ` and
`k ɐ ŋ`; the explicitly Milanese Wiktionary reading is `k ãː`, raw `/ˈkãː/`.
These are source/locality-specific alternatives, not three independent votes.
The supplied nasalization and quantity are preserved rather than treating a
normalized ASJP sequence as an equivalent reconstruction.

| Construction | Wiktionary records | Wiktionary concepts / core | Retained GLED records | Supported concepts still only in GLED / core |
| --- | ---: | ---: | ---: | ---: |
| Yurok | 54 | 46 / 36 | 62 | 24 / 22 |
| Ternate | 66 | 66 / 32 | 41 | 23 / 22 |
| Corsican | 16 | 15 / 15 | 39 | 38 / 36 |
| Lombard | 42 | 39 / 16 | 81 | 35 / 33 |

These are bounded supplied-reading preferences with retained legacy coverage,
not complete dictionary replacements. All120 admitted Yurok/Ternate entries were
also rechecked against strict cached pronunciation decisions and raw IPA comments.

## Rethinking the existing choices

The historical replacement screen measures mapped/supported **core** potential
from raw intake. Its zero lossless positive supplied-reading swaps is not a
quality veto: it omits finite profiles, qualified pronunciation recovery,
non-core depth and retained GLED supplements. Current selection is explicit
configuration; old `fallback p2` notes were historical selections, not an active
universal preference engine.

Use `scripts/audit_reviewed_source_choices.py --output PATH` to inventory existing
guarded alternatives across **all accepted primaries**, including profile/scoped
admissions. [Post-batch inventory](reviewed_source_choices_2026-10-29.csv) is a
review queue, not source certification: profile groups can include written-only
policies and counts are authored ledger rows, not independent attestations.
The [pre-batch ordinary-IPA screen](wiktionary_source_ipa_screen_2026-10-29.csv) finds161 candidate members, with unreviewed senses and no quality certification. Use it alongside the raw replacement/opportunity screens and exact generated
readings; do not rank by token validity or count alone.

The next easy review group is Chickasaw, Yucatec Maya, Unami and Western Apache:
trusted earlier Wiktionary slices already exist, while the frozen snapshot offers
additional supplied IPA. Extend exact sense/POS review before promoting a very
small slice. Scots and Kabyle have substantial supplied-IPA potential but no
existing admitted Wiktionary ledger. Tewa/Taos need exact community scope;
Coptic needs dialect and historical-stage separation. No automatic pooling.

Zeeuws, Higaonon and Plautdietsch have large spelling dictionaries but insufficient
ordinary supplied IPA. They are profile-research candidates, not quick promotions:
obtain source-specific orthographic authority and check omitted contrasts before
admitting pronunciation. Other non-GLED choices also belong in the inventory;
a trusted source label alone does not exempt them from comparison.

## Reproduction and verification

Rebuild the four affected constructions, aggregate and website with the normal
onboarding commands. The guarded primary/supplement ledgers are the executable
recipe. [Metrics and preservation proof](wiktionary_source_selection_summary_2026-10-29.json)
record measured gains, all earlier evidence preservation and actual source-role
changes. No new language or intake namespace is claimed.

Verified result:97 supplied-IPA records,59 supported concept slots/16 core; four
primary changes and no new languages. All2,071,680 earlier records/readings/cognacy
and original source comments survive.223 per-form GLED scores recalculate solely
through the existing explicit-mapping bonus;81 comments change only the derived
supplement/primary role label. All401 website artifact hashes and3 aggregate
input hashes pass.456 tests/lint and source-preference/Romance/mixed-source browser
checks pass. Post-batch inventory contains140 guarded source alternatives.

Data commit:`9e758d89b36b93420bd255e89ee0417d5c8d92f0`. [CI](https://github.com/tresoldi/arcaverborum/actions/runs/40890661775) and [Pages](https://github.com/tresoldi/arcaverborum/actions/runs/40890662366) succeed. [Canonical publication proof](wiktionary_source_selection_publication_2026-10-29.json): manifest/catalog/recordings/bibliography plus all three affected family shards match committed bytes/hashes (7 artifacts). Source-preference browser/export checks pass on https://arcaverborum.org/.

Aggregate-position-derived export IDs shift when earlier rows are inserted;391
family shard bytes change as a result. Original source-form IDs and pronunciation
IDs remain preserved. The preservation audit excludes only derived aggregate IDs,
review-role annotations and the explicitly checked223 score recalculations; it
checks original evidence/readings/cognacy and all earlier concept coverage.
