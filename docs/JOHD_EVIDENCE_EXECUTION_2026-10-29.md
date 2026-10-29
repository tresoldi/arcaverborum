# JOHD/HGN evidence execution — 2026-10-29

The user authorized all opportunities from the [JOHD555 assessment](SOURCE_ASSESSMENT_JOHD555_2026-10-29.md), sequentially with autonomous specifics. Four bounded tracks are complete: original Nadëb recovery; other-member triage/depth; explicitly reconstructed inventories; aggregate identity/semantic comparison. Accepted records, interpretations and source genealogy remain separate.

| Track | Result | Evidence / limits |
| --- | --- | --- |
| J01 |71 original supplied phonemic citations:48 Roçado/23 Rio Negro; original Roçado authority becomes primary and the preceding single record remains verbatim | [Review](johd_j01_hgn_review_2026-10-29.csv). Exact HGN122/121 members, feature IDs, table headers, complete native rows and metadata pinned to Lexibank717ad159. Empty orthography no longer hides selected phonemic-only entries. No alternative chosen, affix removed, stress imposed or cognacy invented. |
| J02 |101-member triage completed;20 supplied Yabarana citations added, with existing primary retained | [Ranking](johd_j02_hgn_ranking_2026-10-29.csv), [Yabarana review](johd_j02_yabarana_review_2026-10-29.csv). Native HGN80 explicitly distinguishes Yebarana and attributes Méndez Arocha1959. Bará identity remains uncertain in its own source; Sanapaná/Enlhet-to-Toba code assignment also held. Other raw counts are not promised gains. |
| J03 | Three20-concept written reconstruction inventories: Proto-Quechuan, Proto-Aymaran and Proto-Guaicuruan | [Exact original-row review](johd_j03_proto_review_2026-10-29.csv), [all15 inventories](johd_j03_reconstruction_inventory_2026-10-29.csv). Original repository stars, bound-stem hyphens, unknown vowels and complete forms survive. No supplied/reconstructed IPA or expert cognacy admitted. Collective original-edition attribution limitations remain explicit. Three analytical inventories, zero new extant languages. |
| J04 | All2,683 non-proto nonmatches triaged; seven code/alias cases reconciled; ten existing TuLeD records mapped to daughter-of-woman | [Screen](johd_j04_nonproto_screen_2026-10-29.csv), [counts](johd_j04_nonproto_summary_2026-10-29.json), [identity](johd_j04_identity_reconciliation_2026-10-29.csv), [30-case semantic sample](johd_j04_semantic_sample_2026-10-29.csv), [accepted mappings](johd_j04_mapping_review_2026-10-29.csv). Boundary/stress similarities and shared forms remain leads. Navel/bellybutton was already mapped, so no re-keying. Generic or ambiguous pronouns were not forced into inclusive/exclusive/person distinctions. |

## Original-source recovery and representation

The original cached HGN v2.0 builder selects nonempty Orthographic Form, leaving
phonemic-only rows outside its CLDF forms table. J01/J02 materialize only reviewed
original Phonemicized Form entries under additive `hgnphonemic` and
`hgnphonemicdepth` namespaces. The complete64,607-row older Hunter-Gatherer
namespace is untouched. Whole raw JSON resources, native member name, source
bibliography, row notes, semantic fields, morphology/alternative context and
feature IDs remain in the source evidence. Etymological inheritance labels do not
become cognacy judgments or independent confirmation.

Martins2005, *Reconstrução Fonológica do Protomaku Oriental*, LOT104, printed55–74
(PDF73–92), explains the shared phonology but distinct lexical entries of Roçado
and Rio Negro, including vowel quality, quantity, nasality and laryngealization.
It also discusses grammatical functions of length/phonation and fixed final stress;
HGN citations are retained as source-cited forms, not silently converted to neutral
roots. The original publisher PDF was downloaded and page55 visually inspected:
[LOT full text](https://www.lotpublications.nl/Documents/104_fulltext.pdf), SHA256
`ea9ef51923136ba21ece92722d05e096fa4fd469fd985e131625eb28b99477e0`.
Acute marks are not assumed to be phonemic tones; the bounded Nadëb slice excludes
unresolved accent, underbar, colon, alternative and editorial cases. Accepted
canonical segment normalization retains supplied quantity, nasalization and
laryngealization; original Unicode/spaces remain in Value/native JSON.

One earlier Nadëb entry, including its mystery-vowel note and unresolved reading,
is pinned through `preserved_forms.csv`. The new authority neither reinterprets
that spelling nor substitutes ASJP. Yabarana's existing MatterCariban construction
and all prior readings remain; HGN overlaps are not independent witnesses.

## Explicitly reconstructed inventories

The `johdproto` namespace uses original CSV rows from repository commit8d8b6358,
before its notebooks stripped reconstruction markers and boundaries. The published
Zenodo20330494 record declares CC BY4.0; JOHD compilation and collective original
authorities are attributed per row. These are source-reported written hypotheses,
not independently established edition-page agreements or fresh reconstructions.
No inferred chronology, canonical family-node Glottocode or geographic location
is assigned. `source_reported_reconstruction` evidence and blank segments are
required by the accepted ledger.

`construction_kinds.csv` explicitly marks the three analytical inventories in the
research catalog. The research export rejects conflicting identity/primary/member
scope, removed reconstruction markers or phonetic upgrades. The catalog presents
“analytical reconstruction”; stars and bound forms remain in lexical downloads.
Other reconstructed inventories are separately reviewed leads. Proto-Tucanoan's
existing family-code scope is not a new language. Proto-Zaparoan's original source
file is absent from the inspected repository tree; its final39-row derivative and
a notebook mention do not resolve that provenance gate.

## Aggregate comparison and semantic decisions

The2,683-row screen is compared with pre-batch namespaces, not with the newly
admitted HGN evidence: nine exact matches emerge after identity reconciliation;
1,432 possible boundary/stress differences,589 same-form/different-sense-or-mapping
leads and653 unresolved original-source cases remain. These categories do not
certify phonetic equivalence. The30-case manual semantic sample documents ten
navel/bellybutton cases and20 pronoun cases without admitting narrow derivative
interpretations. Original Mapudungun/HGN person-label inconsistencies remain a
reason to consult source-language grammar, not to overwrite a better source.

A bounded ten TuLeD-primary constructions have existing parameter97 explicitly
labelled DAUGHTER OF WOMAN but an empty Concepticon mapping. Per-form/parameter/
expected-spelling guards now map these records to frozen kin-daughter-of-woman3930.
No new lexical row, transcription, morphology or cognacy is authored by this
semantic correction; the JOHD mapping is a useful lead, not a new attestation.

## Verification and closure

Source reproduction: `scripts/verify_johd_evidence.py` verifies six complete
resource hashes and reproduces all three namespaces71/20/60, including native
rows, parameters, member identity, metadata and licenses. Stages were appended
once with preserving append guards; no existing source was subset-ingested.
New tests reject member/header/feature/evidence drift, omitted source context,
unreviewed alternatives, removed reconstruction markers and false catalog
identity. The Nadëb and Yabarana plus three inventories and ten semantic
constructions build successfully. Final counts, preservation and publication
proof are recorded at closure below.


Final result:151 new records,64 supported slots/45 core,124 mapped slots/103 core,
three explicitly analytical written inventories, zero new extant languages and
one primary authority change. Accepted7,346 constructions/2,072,746 forms. All
2,072,595 earlier readings, native cognacy and source comments remain; ten existing
records gain exact mappings. Ten derived per-form CI-bonus score recalculations,
zero variety-level score and role-comment changes. [Metrics](johd_execution_summary_2026-10-29.json).

[Verification](johd_execution_verification_2026-10-29.json):476 tests in both
HAVE_UTF8PROC flag states, full lint,15 affected builds, ten browser suites,401
artifact hashes/3 aggregate hashes and151 native source-row reproductions pass.
[Source-fidelity summary](johd_source_fidelity_2026-10-29.json); the generated CSV
remains under output/report. Publication verification follows the data commit.
