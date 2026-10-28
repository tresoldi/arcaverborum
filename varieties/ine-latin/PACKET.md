# Curation Packet — Latin (`ine-latin`)

> Reviewed **gold exemplar** for the curation machinery. Other CORE varieties
> begin as `build.py packet` scaffolds with sections marked _To be filled_.

- **Family / macroarea:** Indo-European / Eurasia · **Glottocode:** lati1261
- **Accepted source:** IECOR (transcription + cognates) · **Tier:** silver · **Pinned:** yes
- **Review status:** reviewed (2026-08-22)

## 1. Current accepted construction

Latin is built directly from **IECOR**, the curated canonical Indo-European
source, using its expert IPA transcriptions and expert cognate judgements
unchanged. No Arca corrections (`custom/*`) are applied. See `recipe.yaml`.

## 2. Coverage & quality (from the current CORE build)

| Metric | Value |
|---|---|
| Forms | 172 |
| Distinct concepts | 170 |
| `concept_id` mapped | 172 / 172 (100%) |
| **Basic-vocab core coverage** | **128 / 161** |
| Segments source-clean | 172 / 172 (100%) |
| Forms with expert Cognacy | 172 / 172 (100%) |

Latin is already at the quality ceiling for its source: fully mapped, fully
clean, fully cognated. The only coverage gap is the 33 basic-vocab core concepts
IECOR does not list for Latin.

## 3. Candidate sources

| Source | Coverage | Verdict | Reason |
|---|---|---|---|
| IECOR | full (170 concepts) | **used** | curated, expert IPA + expert cognacy, family-consistent |
| Wiktionary | partial | not used | fallback/research entry point only; would break IE consistency |

## 4. Transcription

172/172 forms validate as source-clean BIPA under merkmal `descriptive`. No
orthographic profile or transcription override is needed.

## 5. Concepts

Full `concept_id` coverage. Against the frozen 161-concept basic-vocabulary
core, Latin covers 128; the missing 33 are concepts outside IECOR's elicitation
list, not mapping failures.

## 6. Cognates

100% expert cognacy from IECOR. No computed cognates needed; if added later they
must pass the evaluation gate (workflow spec) and be recorded as
`cognates.method: computed` with method metadata.

## 7. Recommended recipe & follow-up

Keep IECOR as-is (see `recipe.yaml`). Optional future improvement: fill the 33
missing core concepts from a Latin-specific scholarly source as an Arca-derived
layer — only if the gain justifies departing from the single-source construction.

## 8. Gains / losses vs alternatives

- **Gains:** expert IPA + expert cognates; identical base to all other IE lects.
- **Known losses:** 33/161 core concepts absent; no Latin-specific enrichment.

## Accepted ancient evidence review — 2026-10-28

[Batch evidence and decisions](../../docs/ANCIENT_EXPANSION_2026-10-28.md).
Before: 172 forms, 128 supported core slots.
After: 187 forms, 142 supported core slots.
Statuses: {'source': 187}. Source rows: {'iecor': 172, 'wiktionary': 15}.

The existing primary selection and its profile/cognacy scope are retained.
Additions are individually guarded in [custom/supplements.csv](custom/supplements.csv).
[Historical reading rules](custom/historical_evidence.csv) distinguish original
segment origin from historical phonetic certainty. Source-specific reading
conventions are not interchangeable across periods or datasets. Written-only
admissions have blank segments and contribute no supported phonetic coverage.
Original forms, source glosses, reading alternatives and cognacy namespaces
remain visible; no primary expert judgments are copied onto supplements.

See the batch's authored admit/hold CSVs and pinned lexical source specifications
for exact semantics, version, terms and reproduction commands. No GLED swap or
new-language claim is made for this existing construction. Remaining uncertainties
are routed through [the held-work register](../../docs/planning/HELD.md).
