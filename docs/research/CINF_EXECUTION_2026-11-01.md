# Colexification validation and fidelity execution

Authorized CINF-01–05 in sequence on 2026-11-01. This is a running execution
record; queued tasks are not completed findings. See [the paper record](COLEXIFICATION_RESEARCH.md)
and [active queue](../NEXT.md).

## CINF-01 — bounded first-pass review complete; expert gate retained

The frozen 146-case worksheet is reviewed independently against an explicit
rubric. Both Codex and Claude completed all 146 cases. The comparison
script validates case coverage, allowed decisions and cited native IDs, retaining
all disagreements. Neither model supplies an independent expert gold standard.
No confidence calibration or annotation error rate is inferred from agreement.
The Codex reviewer disclosed general prior familiarity with the BAG–WITCH and
Hunter–Gatherer issues and incidental exposure to an older agent status summary;
it had not previously reviewed these case IDs. Blinding is therefore partial,
not an assurance that the reviewer had no methodological context.

All native-sense arrays in this worksheet are empty. A separately hashed
`review-2026-11-01-native-labels` supplement now recovers all 172 targeted
questionnaire labels from intake; the blinded worksheet is unchanged. Catalog definitions and
source parameter IDs do not independently certify source meaning. This limits
semantic validation even when comparison-basis identity is checkable.

Critical initial assessment: suspected truncations require source adjudication.
Dedua `hani-` versus `hani` may reflect a bound-form citation convention rather
than damaged lexical content; a hyphen is not sufficient grounds for rejection.
Fuyug `i(ye)`/`i(me)` and Fore `(a)'no`/`(a)no` require source-specific optionality
and apostrophe interpretation. Lower Sorbian spelling/segments differences are
not automatically pronunciation errors. Lisu's conflicting tone strings warrant
source review, not silent conversion. These flags do not authorize corrections.

Two axes must remain separate: represented full-form equality/nonidentity in
retained evidence, and eligibility under semantic/reading/source gates. A reviewer
can observe two different retained forms where the analytical pipeline correctly
returns unknown. Their labels must not be scored as binary gold against pipeline
outcomes or used to override the gates.

The [versioned review package](../reviews/cinf-2026-11-01/summary.json)
records agreement on identity in139/146, meaning36/146, reading61/146 and
interpretation128/146;122 cases differ on at least one axis. These are not
accuracy estimates. Claude inspected additional raw CLDF exports and applied
`source_supported` to questionnaire-label agreement, while Codex generally used
`mapping_unverified` without native meaning evidence. This explains much of the
semantic disagreement and is not resolved by majority vote.41 supplementary
citations are outside the frozen packet and are explicitly flagged for source
verification by the comparator, rather than certified by ID appearance.

Root checks independently confirm the cited publication split in Saniyo-Hiyewe,
Dedua and Southern Kiwai. In Saniyo-Hiyewe only cross-publication combinations
match (`you`/`yo` versus `yo`/`yomay`); this is a real aggregation concern,
not evidence of an incorrect source word. The other two also cross publications,
with bound-form/catalog scope complications. None establishes polysemy.
Tseltal `k'ab` with Spanish `mano, brazo` establishes a documented broad gloss;
it does not by itself establish two senses rather than one general meaning.
The reviewer's `documented_polysemy` classification is retained in its report
but not accepted as gold. Expert adjudications remain zero. No error-rate or
posterior recalibration is licensed by these model-assisted judgments.

## CINF-02 — guarded repairs built; aggregate verification pending

Read-only preparation found a retained `Phonemic` CLDF column and native
`Phonemicized Form` values that the spelling-derived tokenization did not use.
Upstream FormSpec also treats apostrophes as paired brackets and strips accents
and nasalization. Native columns provide a recovery lead, not automatic verified
IPA. Wa’ikhana's two columns often repeat the same spelling, including apostrophes;
that duplication does not establish their phonetic interpretation.

Primary database pages checked: [Piaroa](https://huntergatherer.la.utexas.edu/languages/language/130),
[Wa’ikhana](https://huntergatherer.la.utexas.edu/languages/language/137),
[Yukuna](https://huntergatherer.la.utexas.edu/languages/language/65).
The retained upstream conversion explicitly stores the native phonemic column:
[Lexibank converter](https://github.com/lexibank/huntergatherer/blob/master/lexibank_huntergatherer.py).
Original bibliography, row-level attribution and unresolved notation remain
separate from database-supplied phonemicization.

[Repair manifest](hg_fidelity_repairs_2026-11-01.json),
[record verification](hg_fidelity_verification_2026-11-01.json),
[38 retained holds](hg_fidelity_holds_2026-11-01.csv).
326 exact, hash-guarded repairs: Piaroa108, Wa’ikhana123, Yucuna95.
109 use single, supported database-supplied phonemic strings (21 Piaroa/88
Yucuna);217 are explicitly orthographic-only. Wa’ikhana's apostrophe convention
is not inferred from two identical source columns. Piaroa's non-IPA capital
`Ɂ`, private-use characters and unreviewed apostrophes are not guessed into
pronunciations. Native phonemic strings are retained in comments for those
written-only cases. Historical phonological analysis remains source-specific.

All964 records across these constructions remain in their original order.
Only326 guarded records changed: Form/Segments, explicit source reading and
pronunciation ID where supplied, explanatory comments, and mechanical quality
scores. Original Value, concept assignments, native IDs, source citations,
cognacy and every other output column remain unchanged. Previous parser Form
and Segments are recorded in each correction comment and retained in intake.
Lower phonetic support for217 formerly token-valid prefixes is an intended
correction of false confidence, not evidence that spelling constitutes IPA.
Aggregate and graph deltas are measured later; no new languages are claimed.

## CINF-03 — bounded audit complete; original-witness gaps retained

[Member evidence](source-inventory-2026-11-01/member_evidence.json),
[genealogy edges](source-inventory-2026-11-01/genealogy_edges.json), and
[14,612 native prompt/member cells](source-inventory-2026-11-01/questionnaire_inventory.csv)
cover ten IDS/WOLD/Tryon members, seven in South America. Blank member records
are recorded as `parameter_without_member_record`, with elicitation unknown.
There are zero inferred lexical absences or asserted not-elicited cells.

The [WOLD project](https://wold.clld.org/) explicitly derives its meaning list
from IDS: questionnaire dependence is documented, lexical copying is not thereby
proved. Mapudungun WOLD cites IDS in its source description, a real bibliographic
connection requiring record-level follow-up. Hup's description attributes its
lexical data to Epps's2000–2004 fieldwork. Wichí WOLD identifies Vidal/Nercesian,
but its retained bibliography entry is empty; author identity does not establish
independence from Braunstein's IDS contribution. Guaraní, Wichí and Mapudungun
IDS lack row citations throughout these retained member samples. Cashibo's744
rows each cite the same three Shell references; these are not2,232 independent
witnesses. Shell1959/1965 titles remain unidentified in native metadata.

The [publisher's Tryon preview](https://api.pageplace.de/preview/DT0400.9783110884012_A19589064/preview-9783110884012_A19589064.pdf)
identifies Paul Jen-kuei Li's Rukai wordlist as Budai (printed p.297).
The source-specific configuration note now records this, without relabelling
all Rukai or its separate cognate source. Lewo/Kwamera's compilation is identified;
original lexical collection and any reuse from Tryon1976 remain unresolved.
Do not treat matching Glottocodes or contributor names as independent fieldwork.

The three source-scope cases from CINF-01 show why bibliography belongs in
observation-scope sensitivity. The current dataset/member grouping is broader
than a publication. Cross-publication-only equality remains a representation
candidate, not verified within-publication polysemy. No new independent
replicate is claimed and no blanket production block merger is justified.


## CINF-04 — broader streamed protocol frozen; execution pending

76 pairs are selected before broader context extraction:40 sampled common,
18 sampled rare/South-American-anchored pairs and18 prior purposive controls.
The first frame has309,275 unordered pairs among787 concepts represented in
at least50 known families; the second has185,732 pairs anchoring236 concepts
with2–20 families worldwide and at least two South American families to a common
concept. Legacy controls are excluded from both sampled frames. Exact frame
counts, marginal counts, hashes and inclusion probabilities are frozen in
[protocol v2](../../src/arcaverborum/data/colexification/validation_protocol_v2.json).
These are marginal-coverage frames, not a random sample of all world concepts
or of directly observed comparable pairs. The panels are fitted and scored
separately; purposive controls cannot inflate a population calibration claim.

A SQLite context/prediction store replaces the global in-memory context list.
The ridge fitter can reiterate training queries rather than retaining examples;
a reference test recovers the earlier fit and scores to1e-12 on a small fixture.
Workers have a256MiB address-space cap and512MiB SQLite store budget.
Publication sensitivity uses common singleton native citations; pooled/absent
references stay unknown. IDS/WOLD combined-questionnaire-block sensitivity
is diagnostic, not a new claim that their lexical observations were copied.
Hypothetical held-out label flips at0/.05/.10 are sensitivity diagnostics,
not measured annotation-error estimates or refitted error-corrected models.

An independent external timing run reproduced the exact frame/protocol hash at
approximately33MiB RSS under the cap. An initial launcher-reported ru_maxrss
of709MiB was inconsistent with that cap; it is not used as a process-memory
measurement. The execution CLI records Linux VmHWM as well as the hard limit.


## CINF-05 — analytical publication (queued)

Source genealogy, broader streamed protocol and analytical publication follow
the bounded review and source-fidelity work. Experimental probabilities remain
research diagnostics, not public graph strength or calibrated polysemy confidence.

## Rebuild prerequisite: canonical parent identity

A full rebuild exposed one pre-existing stale accepted output: Sursilvan's115
records remained in the aggregate, but `load_avid_registry` let the Tuatschin
custom-dialect row sharing `surs1244` overwrite the canonical Sursilvan mapping.
Canonical Glottolog rows now take priority independently of CSV row order;
contradictory canonical mappings fail closed. Both Sursilvan and Tuatschin rebuilt
successfully (115/38 records). This repairs catalog visibility, not a language
addition or independent lexical evidence. Only `surs1244` has duplicate registry
rows in the current registry; the scope of this repair was checked explicitly.
The full rebuild's other three failures are catalog-absent historical/sign
configurations with no generated lexical output; none is counted as accepted
new data. Aggregate row and unaffected-record checks follow the final rebuild.
