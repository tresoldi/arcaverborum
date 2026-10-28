# Romance expansion R01–R06 — 2026-10-28

Authorized six-track batch, executed in order. [Initial investigation](ROMANCE_INVESTIGATION_2026-10-28.md)
is the prospective baseline; [measured results](romance_expansion_summary_2026-10-28.json)
are authoritative for this batch.

## Results and interpretation

| Measure | Before | After |
| --- | ---: | ---: |
| Accepted constructions | 7,315 | 7,329 |
| Lexical rows | 2,067,575 | 2,069,214 |
| Supplied-source rows | 1,744,382 | 1,746,021 |
| Profile readings | 13,869 | 13,885 |
| Supported core slots | 466,443 | 467,872 |
| Mapped core slots | 540,270 | 541,637 |
| GLED primaries | 1,577 | 1,577 |

There are **176 newly admitted lexical evidence rows**, plus1,463 existing Saenko
rows exposed again in13 named constructions. Parents remain accepted. Sixteen
Gallurese profile readings enrich existing rows rather than adding lexical rows.
The1,429 supported-slot increase comprises138 in existing constructions,4 in the
new Cremona sample and1,287 in the13 isolated Saenko samples. This is **14 named
varieties and zero distinct-new-language claims**. Repeated source rows and shared
GLD ancestry must not be treated as independent observations in downstream studies.

## R01 — supplied pronunciations

[Review](romance_r01_review_2026-10-28.csv), compiled with
`scripts/compile_supplements.py`; guarded per-form evidence hashes and source
concept/member checks remain in each variety's supplements ledger.

71 forms admitted: Corsican16, Lombard3, Sicilian8, Ligurian9, Venetian2,
Romagnol2 and Italian31. They supply68 new supported core slots. Core coverage:
Corsican36→51, Lombard38→41, Sicilian99→107, Ligurian99→106,
Venetian99→101, Romagnol98→100, Italian128→159. Italian uses29 selected
Wiktionary readings plus Northeuralex's direct thou/way entries, avoiding overlap.
Homonyms, figurative senses, duplicates and one malformed Sicilian stress/length
reading remain held. No whole-source GLED replacement: loss screens favored
additive evidence. Source readings are supplied evidence, not independently
certified pronunciations or transferred cognacy.

## R02 — bounded spelling recovery

[Review](romance_r02_review_2026-10-28.csv), compiler
[`gallurese_profile.py`](../scripts/gallurese_profile.py), exact anchored profile
and form-specific concept corrections under `ine-gallurese-sardinian/custom`.
Ten unambiguous spellings yield16 profile readings and2 new supported core slots:
Gallurese0→2. The [Gallurese convention](https://unionegallura.it/wp-content/uploads/2023/10/3564_6cunveniuoltugraficu.pdf),
section6, supports this neutral broad segment subset. No stress, contextual
lenition or surface vowel length inferred. Mid vowels, rhotics, glides, palatal
ambiguities and undocumented spelling systems are excluded. The source's three
supplied readings remain unchanged.

Five incompatible/underspecified senses are explicitly unmapped while their
lexical rows remain. An exact-profile build also changes225 previously resegmented
spellings to explicitly unresolved output, rather than presenting unsupported
letter segmentation as pronunciation. Original Form/Value and all254 lexical rows
remain. Thus241 records change some transcription/mapping fields; this is not241
new readings. Four of the five semantic corrections change a previously assigned
concept; one was already unresolved.

Lombard/Venetian spelling mixtures do not establish one orthography or local
pronunciation. Istriot mixes locality conventions without an established conversion
authority. These were screened and held rather than assigned generic profiles.
The small Gallurese pilot is complete; larger profiles require new evidence.

## R03 — source locality and Sardinian identity

[43-member audit](romance_r03_identity_audit_2026-10-28.csv). All Saenko members
already mapped to accepted constructions; none was a missing-language discovery.
Thirteen pooled samples now have explicit named constructions with parent links:
Lanzo Torinese, Barbania, Carmagnola, Vercellese; Ferrarese, Carpigiano, Reggiano;
Venice, Primiero, Bellunese; Palermitan, Catanian and Southeastern Sicilian.

Each selects exactly one original member through `source_language_id` and a
reviewed `source_glottocode`. Canonical Glottocode/ISO and coordinates remain blank;
no town code or speaker location is guessed. These are source-defined samples,
including regional rather than strictly municipal labels. Earlier parent rows
remain. The frozen registries, configs, packets and recipes agree on the hierarchy.

Saenko2015/v1.0-1-ga463ddc is CC BY4.0 and GLD/Starling-derived. It is not an
independent replacement for GLED simply because its dataset name differs. Its
Logudorese member remains linked to Barbaricino: no lexical evidence was copied
to the broader parent or Nuorese on that basis. Genoese and Messinese already had
separate constructions and were not duplicated here.

## R04 — RVID acquisition

[47 infinitive decisions](romance_r04_review_2026-10-28.csv):33 admit/14 hold.
Source repository pinned at `eb1efef3ef02fbbf06f96f77637736d9cd27db8a`, with
all table, README and licence hashes in [source specification](../src/arcaverborum/data/rvid_source.json).
Materializer [`rvid.py`](../src/arcaverborum/sources/rvid.py) and
[`stage_rvid.py`](../scripts/stage_rvid.py) reproduce a four-sample derivative
outside active intake. The new `rvidinfinitives` namespace was staged completely
and appended; earlier intake bytes were retained by the append mechanism.

Admissions: Sassarese7, Nuorese12, Logudorese3, Cremona11. Existing core support:
Nuorese0→4, Logudorese0→1; Sassarese38 remains38 while gaining lexical depth.
Cremona is a new named sample under Lombard, with4 core concepts and11 infinitives,
using the source's regional45.13/10.03 point. Its canonical dialect code is blank;
RVID's Closest_Glottocode is retained as metadata, not promoted to identity.

Modern lexical Meaning, INF cell, source bibliography, dating, raw IPA, original
form/lexeme/etymon IDs and comments remain visible. Etymon IDs are metadata rather
than fabricated expert cognacy. Missing `?`, copular/existential ambiguity,
verbal/adjectival tame, unspecified hold/worth and Cremona's questionable bare
have alternatives were held. Full paradigms were not emitted as lexical lemmas.

The [source publication](https://aclanthology.org/2020.lrec-1.370/) describes a
cleaned broad-IPA resource; this does not make its readings infallible fieldwork.
The derivative remains GPLv3, with public [notice](../web/data/RVID_NOTICE.txt)
and [licence](../web/data/RVID_GPL-3.0.txt), corresponding source and reproducible
transformation links. The code's MIT licence does not relicense these data.

## R05 — Alpine feasibility and acquisition outcomes

[Endpoint evidence and reopening gates](romance_r05_acquisition_2026-10-28.json).
Zero lexical admissions; no audio or type labels converted into guessed IPA.

* **VerbaAlpina:** live API/docs return emergency maintenance HTML, despite HTTP200.
  The [LMU archival sample record](https://discover.ub.uni-muenchen.de/catalog/98411a8e-8312-3d3e-a437-1412bb0eab84)
  advertises a CC BY-SA4.0 CSV and SHA512. Its linked download host fails DNS here;
  both live and archival paths were attempted. Recover verified token payloads,
  then review source, locality, notation and modern concept. Metadata alone is no gain.
* **digitALD:** the [current site](https://www.ald.gwi.uni-muenchen.de/) explicitly
  displays CC BY-SA4.0. This narrows the earlier unspecified-rights hold for site
  material. The [speaking-atlas documentation](https://www.ald.gwi.uni-muenchen.de/en/sprechender-informationen/)
  establishes Böhmer–Ascoli–AIS notation and a transcription/audio date mismatch.
  Its21 speaking points must not be conflated with217 atlas points. Selected-table
  scope, structured extraction and a reviewed notation conversion remain necessary.
* **VinKo:** the [primary project page](https://alpilink.it/en/vinko/) identifies
  v1.2 and CC BY-NC-SA4.0. This supersedes treating a secondary ND listing as the
  project's stated licence. Deposit access/actual lexical transcription remain
  unverified; audio/sentence totals are not transcribed lemma coverage.

No permission-seeking contacts were sent. Sound Comparisons' separate derivative
restriction remains held; this was not reinterpreted from another project's terms.

## R06 — wider Romance

[Review](romance_r06_review_2026-10-28.csv):79 candidates,72 admit/7 hold.
Occitan gains67 forms/59 supported core slots (0→59); Romansh5/4 (0→4).
Observed Wiktionary readings remain source varieties within broad constructions,
not a synthesized pan-dialect standard. Narrow Romansh varieties remain separate.
Figurative star, complementizer that, animal paw, smoke/dust cloud and non-plant
roots are excluded. Original source tags/comments remain.

Extremaduran390 rows (11 supplied), Picard248 (2 supplied), Fala82 (51 supplied)
and Arpitan54 (54 supplied, GLED) were separately screened. Their current core
baselines4/0/17/31 persist. Primary-source/profile recovery is outside alternative
ranking, but the screened remaining spellings did not establish source-system
and pronunciation authority. Broader profiles are held, not silently completed.
Previously completed Galician, Aragonese and Asturian pilots were not repeated.

## Verification and reproducibility

430 tests pass, including six new RVID morphology/lexical drift checks; full lint
passes. Profile and supplementary compilers validate against current intake.
Affected constructions rebuild without failures; aggregate and web artifacts are
regenerated. [Preservation audit](romance_preservation_2026-10-28.json) checks2,463
prior affected records, with only documented Gallurese transcription/mapping
changes. All earlier Form/Value/source IDs retained. All401 catalog/shard/recording
hashes and aggregate/catalog totals verified. Public RVID licence is included.

[Updated global ranking](romance_expansion_opportunities_2026-10-28.csv) and
[method summary](romance_expansion_opportunities_2026-10-28.json) are discovery
snapshots, not additional admissions. New blank-code named samples are excluded
from automatic cross-source identity matching. See STATUS for publication checks
and NEXT/HELD for the remaining evidence-driven queue.
