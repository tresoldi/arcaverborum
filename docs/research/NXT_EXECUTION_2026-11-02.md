# NXT-01–04 and NXT-06 execution

User authorized these five tracks with autonomous decisions. **NXT-05 is deferred**:
no cognator/regulae diagnostic, new control expansion or new confidence model is
included. Regeneration/verification of existing published analyses follows the
lexical changes and is not a new methodological experiment.

Baseline: published2,119,822 lexical records in7,366 accepted constructions;
1,123 concepts with accepted WordNet links. Starting commit `df3760f01`.

## NXT-01 — Catalog/source lineage

[Seven definition decisions](nxt_concept_lineage_2026-11-02.json) resolve BECAUSE OF,
BEAD, four husband-side kinship paths and A LITTLE. Pinned Concepticon contains
the same inherited errors; online Concepticon checks did not independently fix
them. Native NorthEuraLex `wegen::PRP`/`ein wenig::ADV`, IDS/WOLD bead parameters,
and Beida's original Chinese prompts determine the corrected scopes. All stable
IDs, display labels and lexical assignments remain.573 exposed assignments were
not573 proven incorrect translations and are not automatically moved or deleted.

Four kinship WordNet targets are broader than the age/spouse-specific meanings.
The bead target has crossing shape/purpose restrictions and is related, not an
asserted containment or a pearl equivalence. Causal BECAUSE OF remains an inventory
hold rather than a decomposition link; A LITTLE remains related to its adjective
quantity target after removing the contradictory count restriction.

## NXT-02 — Audited semantic extension

Accepted typed alignment increases1,123→1,350 active concepts. **235 new links**
cover227 additional concepts: five source-lineage links under NXT-01 and230
NXT-02 definition reviews. Current link counts:768 exact,258 broader,243 narrower,
99 related. [Full-catalog accounting](nxt-wordnet-2026-11-02/summary.json):2,393
pending,22 held,24 inventory gaps; all3,789 active concepts remain accounted for.

[Prior-batch diagnostic](nxt_wordnet_prior_audit_2026-11-02.json) reviews34 decisions,
three per relation/POS stratum where available, using deterministic stratum seeds.
All34 remain defensible with their existing qualifications. This is same-model
re-review, neither independent specialist gold nor a corpus error-rate estimate.

[Six draft scope corrections](nxt_wordnet_scope_corrections_2026-11-02.json) revise
BEAD, ARM, TIE, MEDICINE, SWALLOW and ANIMAL before publication. Crossing species,
region, object or use restrictions do not establish one-direction containment.
ANIMAL's inherited definition wrongly attributes noncellulose cell walls to
animals; the proposed exact link is withdrawn and held pending scientific wording
and original elicitation scope, including whether humans are excluded. See
[OpenStax's biological distinction](https://openstax.org/books/biology/pages/27-1-features-of-the-animal-kingdom).
No lexical animal record is deleted or remapped.

Compound hyphens/spaces now normalize for candidate retrieval, recovering e.g.
twenty-one/twenty one. Retrieval never approves a sense.26 additional cardinal
identities are explicitly reviewed by arithmetic definition, choosing number
entities rather than cards, ordinals, banknotes or numeral adjectives. A footpath
sense is recovered outside the old truncated candidate list. No acceptance quota
or calibrated confidence is imposed; missing function-word senses remain explicit.

## NXT-03 — Five exact source constructions

[Admissions/exclusions](nxt_language_admissions_2026-11-02.csv),
[identity/cohort review](nxt_language_review_2026-11-02.json).

| Construction | Accepted citations | Reading status | Scope |
| --- | ---: | --- | --- |
| Reyesano |9| Written only | Exact `rey` / `reye1240`; Spanish etymology of waka survives in native evidence |
| Kallawaya |7| Written only | `caw` / `call1235`; specialist Speech Register, not a new independent living-language claim |
| Toba-Enenlhet / Toba Mascoy |5| Written only | Exact `tmf` / `toba1268`, distinct from other Toba labels |
| Habun, Cribas |213| Upstream profile conversion | Exact `hbu` / `habu1241`; Dawson2014 Manatuto survey |
| Anyin Morofo / Agni morofoué |189| Written only | Exact `mtb` / `anyi1244`; one-sense noun/pronoun cohort |

This adds four language-level identities plus one named register construction,
not five independent languages. Every primary selects exact native source IDs
through hashed guards. Full native entry JSON, French senses/POS, spelling,
source URLs, variants and etymology survive. Kallawaya's botanical citations stay
unmapped where no exact catalog concept exists. A language-name entry, three
ambiguous Habun entry notes, three African typo/POS cases and six multi-sense
African entries are held;565 African rows lie outside this noun/pronoun cohort.
Three African nouns have native sound notation, retained but not promoted to
verified IPA. No generic spelling profile is inferred.

[Habun authority](nxt_habun_profile_authority_2026-11-02.json) pins the original
`p/manatuto` and `p/general` resources. Original source spelling, normalized Form
and upstream Segments are distinct; conversion is not new author-supplied IPA.
The same generic sibling elicitation behind brother/sister prompts is excluded,
preventing an unsupported brother–sister colexification. Automatic cognacy is not
imported as expert evidence. No GLED primary is promoted or discarded.

## NXT-04 — Continuous original historical collation

Complete printed section I, Mamiani1699 pp1–6/PDF21–26, is reviewed as a continuous
unit, not selected OCR hits. [Page/image anchors and exclusions](nxt_kipea_section_review_2026-11-02.json),
[combined historical review](nxt_kipea_review_2026-11-02.csv).18 new written
citations increase Kipeá20→38; six new citations receive reviewed mappings and
12 retain literal senses unmapped. The opening alphabet, Portuguese pronunciation
examples, unglossed particles, an ethnonym and unresolved glyphs/compounds are not
invented lexical admissions. Repeated Hietçã on two pages is admitted once.

Padre is not silently mapped to genealogical father; `cagado` retains its literal
historical gloss without forced modern interpretation. Missionary Deos records
that source register, not a reconstructed precontact theology. Existing `Buyê`
survives with one source-visible comment explicitly qualifying its unresolved
final accent. All other older record fields remain unchanged. New transcriptions
carry `model_assisted_visual_review` and `printed_facsimile` in native evidence;
legacy native hashes remain intact. No IPA/profile or independent expert reading
is claimed. Nantes1709 Dzubukuá is not pooled with this Kipeá witness.

## NXT-06 — Reviewed release and precise attribution

[UraLex binding](nxt_uralex_terms_binding_2026-11-02.json) joins all9,968 accepted
values/forms to the exact current native snapshot, and all10,106 materialized
native forms to the clean tracked TSVs. The README and `.zenodo.json` explicitly
declare CC BY4.0 at commit `6b3667f770e709ebe4aa3426f8fffb9a0a818323`. A guarded
aggregate metadata overlay binds that declaration, authors/citation and version
to the exact accepted witness; changed metadata, review document or readings
fail closed. Intake declarations are not silently rewritten.

Kogan's native metadata has null license; Williamson's declaration is absent;
the legacy English Wiktionary archive still lacks verified dump-date/license
metadata. Full-collection bulk publication remains held on these three cases.
This does not assert that every other source has undergone a fresh rights audit.

The separately named **Reviewed sources** export admits only UraLex,
LexiRumah-original, pinned French Wiktionary and independently authored Kipeá
transcriptions under their exact reviewed terms. It filters actual accepted rows,
not whole construction names, and excludes unreviewed cross-source cognacy and
all other namespaces. Each row carries its source license. Original attributions,
modifications, conceptual/WordNet terms and Princeton notice remain packaged.
No raw source scan or recording file is included. The complete explorer and the
historical Core download are different collections. Packaging, remote-byte and
public download receipts are recorded at final closure below.

## Verification and publication

[Accepted rebuild](nxt_accepted_rebuild_2026-11-02.json): all7,371 accepted
constructions rebuilt successfully. The broad --all command also encountered
three pre-existing nonaccepted configs; none had accepted output or lost data.
The enrolled empty prototype remains outside the public accepted count.

[Preservation](nxt_preservation_2026-11-02.json) independently streams every older
record:2,119,822 retained, one explicit uncertainty comment, all other fields
unchanged.441 records added; total2,120,263.7,369 lexical constructions plus two
recording-only;755 recordings preserved. Supported slots increase37 core/38 total;
mapped slots increase63 core/84 total. No independently supplied new IPA or
expert gold is claimed. Both installed merkmal normalization flag paths pass618
tests; these are not two separately compiled libraries. Lint and source-scoped
release exclusion/determinism tests pass.

[Inactive-cache recovery](nxt_private_cache_recovery_2026-11-02.json) records
round-trip-verified compression of two private historical analytical indexes to
make space for the full intake rebuild. Current analytical inputs are retained;
full build/resource and canonical publication receipts follow after regeneration.

### Regenerated analytical and browser checks

Current core `df2109b3879099b439719641`, graphs `f022f7b0eb8e8fb500b79ac2`,
communities `34129820be138f5b72a85e07`, concept rows `f8aa9076f7d973cb6e634420`.
[Projection](nxt_projection_2026-11-02.json) preserves all259,495 positive witness
identities. [Community verifier](nxt_communities_verification_2026-11-02.json)
checks3,828 node files/117,662 memberships and independently reproduces the selected
partition:239 communities/1,610 assigned concepts,81 standard runs. This refresh
is not deferred NXT-05 work. The analytical commands retain256MiB address-space
limits; the separate intake and lexical web builders have higher memory use.
All eight local explorer suites pass. [Retirement receipt](nxt_asset_retirement_2026-11-02.json)
verifies24,713 inactive-generation members before retiring only unreferenced web
assets; current generations and every accepted construction remain available.

### Release closure

Data revision `2ca6d8de2b4bc3503d3d6e1ba607e746baf009fb` is committed/pushed.
CI passes Python3.12/3.13. The separately named
[Reviewed sources public release](https://github.com/tresoldi/arcaverborum/releases/tag/reviewed-sources-2026-11-02)
contains13,230 rows/47 constructions,5,482,196 bytes/23 verified members.
SHA256 `92b0d6e54c11e6f0c3cde6b04b8d3e2d6ea73291e3b385a37730cb90a0c96a35`.
Both builds match exactly; all five remote assets match local hashes/sizes and
anonymous archive bytes reproduce the checksum. A browser downloads the real
archive, verifies its hash, checks the four-source table and mobile width.
[Public receipts](../releases/reviewed-sources-2026-11-02/upload.json).

The complete updated collection remains a private RC4 draft:96,822,710 bytes,
8,699 members, SHA256 `e92c1fc3c042a7c10f1a0190a3d0fa6f7edc2ab44b33d15cdda455e8b2d7525a`.
Two builds match; five remote asset hashes/sizes match. Three missing declarations
and other unreviewed/restrictive terms prevent treating the full archive as public.
[Private-candidate receipt](../releases/all-accepted-2026-11-02-rc4/upload.json).
RC3 remains historical and is superseded. Neither archive asserts a new DOI.

Six affected construction counts and seven definitions pass an additional browser
check. Both existing review workspaces pass source rendering, guarded model-assisted
export validation and mobile width; expert gold remains zero. Final canonical
explorer-byte verification is recorded after download-page deployment.
