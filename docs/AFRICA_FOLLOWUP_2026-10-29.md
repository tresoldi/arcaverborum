# African follow-up AX01–AX06 — 2026-10-29

The user authorized all six tracks with autonomous specifics. Completed in order
**AX02 → AX04 → AX03 → AX06 → AX05 → AX01**, with bounded admissions and explicit
holds. The baseline is data commit `a1f8e941692d5e1f6ec893e37edf916d5b40058e`;
[realized metrics and preservation audit](africa_followup_summary_2026-10-29.json)
are authoritative. Publication evidence is recorded in STATUS.

## Realized results

7,332 constructions, 2,070,480 forms, 468,581 supported core slots and 542,492
mapped core slots. Added **363 lexical records**: 30 upstream supplied conversions,
204 finite profile readings and 129 written-only entries. Supported coverage gains
**256 distinct variety–concept slots**, 80 core and 176 outside core. Recovered
readings for **80 existing written records**; this is separate from new records.
Profile forms rise by 284 including those recoveries. Gimnime is one new language,
with 20 written-only entries and zero supported phonetic slots. No new named
variety is claimed. Momi corrects an existing construction's identity.

Fwe and Sidaama dictionary primaries replace GLED, retaining all 96 earlier GLED
rows and their source-specific cognacy. GLED primary selections fall 1,575→1,573.
Bantu scope remains 485 constructions: 150,574 forms, 35,101 supported core slots,
95 GLED primaries and 23 zero-supported-core cases. Written evidence and valid
segment tokens alone do not certify pronunciation.

## Sequential execution

| Track | Outcome | Decision evidence |
| --- | --- | --- |
| AX02 dictionary depth | Ruruuli +74 written; Fwe +91; Gyeli +103. Broader vocabulary beyond core, original classes/prefixes/senses retained. | `africa_ax02_*_review_2026-10-29.csv`; current Fwe/Gyeli pointers superseded by AX04 reviews |
| AX04 reading quality | Source-specific units resolved; 21 formerly held Fwe/Gyeli readings (5 baseline, 16 new AX02); 7 additional Gyeli cluster corrections. All 45 Sidaama entries now have source-reported phonemic witnesses. Fwe/Sidaama primaries promoted without loss. | `africa_ax04_*_2026-10-29.*` |
| AX03 source notation | All 30 existing Kam entries receive finite source-authorized readings; Konyagi's 20 entries remain written-only. | `africa_ax03_*_2026-10-29.*` |
| AX06 diversity and identity | Gimnime +20 written; Momi +33 written, 3 marked Gimnime candidates held. Correct existing Momi identity, preserving stable URL and 37 prior GLED rows. | `africa_ax06_*_2026-10-29.*` |
| AX05 explicit tones | Re-reviewed all 52 previous holds: 12 admissions (Bambara 5, Soninke 6, Koyra Chiini 1), 40 remain held. | `africa_ax05_*_2026-10-29.*` |
| AX01 original alignment | Shashi 30 supplied conversions admitted within existing Ikizu scope; 32 held. Temi/Sonjo receives zero admissions: bad meaning/form pairs exist in original CSV and ODS. | `africa_ax01_*_2026-10-29.*` |

## Linguistic decisions

Fwe prenasalized phonemes remain units (including validated ⁿk, ŋɡ, ⁿʃ and ᵐv).
Gyeli's author distinguishes voiced prenasalized units from voiceless NC clusters;
these systems are not conflated. Native notation remains in source evidence.
Fwe n-síkì and Gyeli mbvû remain written-only pending exact boundary/unit authority.
Ruruuli tone is not supplied by its spelling; new entries remain written-only.

Sidaama's pinned original dictionary separates `lx_SidIPA` (explicit phonemic
notation) from official spelling. All homographs must agree before acceptance.
`scripts/verify_sidaama_phonemic.py` verifies the original hashes and 45 witnesses.
No unmarked stress, tone or glottals are invented. Earlier staging-only wording
is explicitly superseded in current reading metadata; original JSON is retained.

Kam matches the original Lesage2019 spreadsheet and Lesage2020 grammar §2.6.
Preserve source H/M/L tones and the author's incomplete M-tone rechecking caveat;
do not infer contextual allophones. This corroborates the original source, not
an independent elicitation. Konyagi requires the exact Santos notation authority,
not related later papers. West African superscript nasality and source vowel
quantity are recoverable; undertilde phonation is not equated with nasalization.
Missing tone, ambiguous compounds and duplicate year entries remain held.

Shashi optional prefixes are admitted only with exact original PREFIX/STEM/Form
agreement. Native optional/bound notation remains visible. Questionable bh/ny/ng
conversions, alternatives and narrow senses remain held. Supplied conversions
retain `upstream_profile_conversion` disclosure. Temi/Sonjo's maEga→father and
melOngO etandato→burn mismatches predate CLDF; no guessed relabeling was made.

### Semantics and identity

Corrected 14 mappings: **10 earlier accepted records**, plus 4 new candidates.
Gyeli fishing/barking/fly distinguish POS and homonyms; Sidaama skin v is unmapped,
bark v is barking, open adj is state, sleep nominal is the activity, and ganʃo is
the illness common cold. Hdi barking follows original Concepticon 1206 and French
aboyer. Kam rain v maps to raining. New Fwe barking/draw-milk and Gyeli dust v/
cry nominal are corrected or unmapped rather than forced into convenient labels.
The dated reviews and `africa_final_semantic_audit_2026-10-29.csv` retain decisions.
Compiler guards reject unsupported POS and original comparison-meaning conflicts;
explicit unmaps carry original-form/parameter guards.

Existing `atl-mom-jango` actually selects `gled_MOMI`. Primary survey evidence
separates Momi/Yadim (Vere Kaadam) from Jango; canonical metadata is now
**Momi (Vere Kaadam), vere1252**, with the existing identifier/permalink retained.
All 37 original rows and cognacy remain. The old source route momj1237 is explicit,
and required source member `gled_MOMI` fails closed if absent. RefLex's country CM
conflicts with primary Yadim/Nigeria evidence and stays raw, not canonical geography.
Original Momi dictionary URLs returned 404; the acquired primary survey and failed
URLs are recorded honestly in the identity-source manifest. Momi is not a new language.

## Source pins and reproducibility

The [immutable lexical registry](../src/arcaverborum/data/african_lexical_sources.json)
contains original dictionary/RefLex pins and current cumulative review pointers.
LangSci Fwe351 commit9134466812515305638fb6afa32e757cbb665338;
Gyeli298 fbcdc58811049568454fa80990e36af940e56ad1;
Ruruuli326 5c8dd12975c308c32638756216544703cafbbd8d (CC BY 4.0).
Sidaama commit51897791fcb5fad622e7956de657d9a84576056e; AX04 hash manifest
covers the original SFM and recipe. AX03 hashes the original Kam spreadsheet and
grammar. AX05 hashes original West African profiles/recipes. AX01 hashes original
TLS CSV, ODS, profile and recipe at9d55b7c6f4e7f71045cd9fddf21da23542fd663c.
AX06 uses the already frozen April2026 RefLex archive (CC BY-NC-SA 4.0), original
sources2897/3294 and actual Dieu/Perrois/Tourneux2016 and Blench/Edwards1988 citations.
`reflexdiversity` is a distinct attribution namespace, not an independent genealogy.

All **662 original-source intake rows** reproduce from immutable resource bytes.
Namespaces now: ruruulioriginal92, fweoriginal120, gyelioriginal169,
reflexoriginal50, westafricanoriginal88, hdioriginal45, sidaamaoriginal45,
reflexdiversity53. Guarded full-stage expansions were applied exactly once;
never replay old expected counts or namespace appends. Materialized CLDF metadata
now reports actual table extents; metadata-only repairs preserve lexical bytes,
citations, terms, versions and bibliography. Intake totals7,192,595 rows.

## Verification and future work

447 tests and full lint pass. All 7,332 accepted constructions update successfully;
changed semantic/identity builds pass. All **2,070,117 earlier lexical records**
and original comments/JSON evidence are preserved with exactly the reviewed 80
reading recoveries, 10 semantic corrections and 37 Momi identity changes. Derived
IDs/captions and 97 mechanical quality scores may change; these scores are not
linguistic certification. 401 web hashes and three aggregate-input hashes match.
Research, African, ancient and mixed-source local browser/export checks pass.
The African check explicitly verifies common-cold/barking/rain POS, unmaps,
source tones, profile scope, retained GLED rows and written-only NC-SA evidence.

Fresh African member and GLED screens are linked from NEXT, with method/counts
in `africa_followup_opportunities_2026-10-29.json`. Raw alternatives overlap and
include held cases. Remaining work requires new source authority or a newly
reviewed slice, not replaying prior holds as gains. See [NEXT](NEXT.md) and
[held register](planning/HELD.md). Earlier reports remain historical evidence.
