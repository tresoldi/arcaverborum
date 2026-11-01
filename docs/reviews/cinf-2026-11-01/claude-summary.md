# Claude first-pass review: colexification inference cases, 2026-11-01 (v2)

- **Reviewer:** Claude (`claude-opus-5-5`), model-assisted first pass.
- **Input:** `output/colexification-inference/review-2026-11-01-v2/blinded_worksheet.csv`, 146 cases.
- **Rubric:** `raw/curation/cinf-2026-11-01/review-rubric.md`.
- **Output:** `claude-first-pass.csv`, which uses the exact rubric columns and has one row per case.

**These judgments are model-assisted triage. They are not expert gold judgments.** They
record what the source exports show. They do not assess the languages themselves.

## Independence

This review did not read the following:

- `analyst_key.json` or `manifest.json`;
- predictions, other reviewers' outputs, or earlier case reviews;
- `claude-review-result.json` or `claude-review-stderr.txt`, which already sit in this directory;
- `docs/COLEXIFICATION_REVIEW_2026-10-31.md` or `docs/reviews/colexification/`.

The worksheet's own `decision`, `notes` and similar columns were empty, and none of them was used.

## Method

For each case, a scratch script outside the repository read the source member's original CLDF
export from `raw/lexibank/<source>/cldf/`. It collected:

- the `languages.csv` row;
- every `parameters.csv` row cited by a worksheet record or sharing either concept's Concepticon ID;
- **all** forms for those parameters (every synonym, with Value/Form/Segments/Comment/Source/Loan);
- every other form in the same member with an identical Value or Form, as homophony context.

Six cases had no parameter match by Concepticon ID: Xiamen, Faka'uvea, Iruhito, Ollari Gadba,
Tseltal and the three Wiktionary varieties. I searched their parameter names, the Wiktionary
intake (`intake/wiktionary/forms.csv`, `pronunciations.csv`), and Tseltal `entries.csv`/`senses.csv`
by keyword. I then judged every case by hand from that evidence.

Conventions applied:

- **Identity**
  - Complete Values were compared, not just normalized Segments.
  - Parenthesised material, apostrophes, accent/tone marks and comma-separated variants were all checked.
  - A match that holds only across two different sources under one member is `ambiguous_scope`.
  - Missing records on either side give `insufficient_evidence`; this is not read as lexical absence.
- **Sense**
  - `source_supported` means only that the source's own elicitation label (e.g. "tree", "Day",
    "man (vs. woman)") matches the concept. No case had native-language senses
    (`native_senses_*` were all empty), and that limitation is stated on each row.
  - Nested catalog pairs are `catalog_overlap`: hair ⊂ hair-or-fur, path ⊂ path-or-road, foot ⊂ foot-or-leg.
- **Reading fidelity**
  - Flags tone, accent, length or apostrophes dropped from Segments, and odd grapheme mappings.
  - Flags Value/Form mismatches and truncated synonym lists.
  - Uses `insufficient_evidence` when one side has no record to compare.
- **Interpretation**
  - `unresolved` unless the source gives explicit lexeme-level evidence.
  - Only one case met that bar: Tseltal *k'ab* 'mano, brazo'.

## Counts (146 cases)

| identity_evidence | n |
|---|---|
| sampled_nonmatch | 54 |
| insufficient_evidence | 52 |
| represented_identity | 37 |
| ambiguous_scope | 3 |

| sense_evidence | n |
|---|---|
| source_supported | 76 |
| insufficient_evidence | 45 |
| catalog_overlap | 23 |
| mapping_unverified | 2 |

| reading_fidelity | n |
|---|---|
| retained_consistent | 65 |
| insufficient_evidence | 49 |
| derivation_requires_review | 26 |
| suspected_truncation | 3 |
| inconsistent | 3 |

| interpretation | n |
|---|---|
| unresolved | 117 |
| catalog_overlap | 23 |
| underspecified_source | 5 |
| documented_polysemy | 1 |

Worksheet bases: 142 `normalized_segments`, 3 `supplied_ipa`, 1 `explicit_stress_citation`.

## Notable findings for the analysts

1. **Missing cases.** 16 cases have no worksheet record on either side, and 37 have a record on
   one side only. Many of these name a parameter that exists in the dataset but is unfilled for that
   language.
   - All three `supplied_ipa` cases (Silesian, Erromintxela, Xerénte) have no records and no
     intake pronunciation rows for the concepts.
2. **A source record missing from the worksheet.** Sateré-Mawé (`4f129fcf…`): the raw TuLeD
   export has THUNDER *hurure* (`tuled_Mawe-391-1`), but the worksheet's b side is empty.
3. **Synonyms dropped from the worksheet.**
   - Barasana (`acd82992…`): only the first item of each comma group was kept. Lost: father
     *hak-ɨ, kak-ɨ*; mother *kak-o*.
   - Lower Sorbian (`182a5506…`): *woko* is segmented `ɔ k ɔ`, missing the w-.
   - Iyora (`12646ef6…`): *My* is segmented `m j`, with no vowel.
4. **Identity produced by stripping parentheses or marks.**
   - Fuyug Mafulu: *i(ye)* vs *i(me)*.
   - Fore: *(a)'no* vs *(a)no*; the apostrophe is lost.
   - Embera Chamí: *bí* vs *bi*; an exact ɓi = ɓi match also exists.
   - Manange: *1pho* vs *1pʰo (2)*. The source's homonym indices separate belly from 'male'.
5. **Cross-source pseudo-identity.**
   - Saniyo-Hiyewe *yo*: Dye 1968 for dog vs MacDonald 1973 for path.
   - Southern Kiwai *gabo*: Wurm 1973 vs McElhanon & Voorhoeve 1970.
   - Dedua *hani-*/*hani*: same two-source pattern.
6. **Defective source exports.**
   - Xiandao head hair *u³¹*: the source compiler commented "I suspect something is wrong or missing here".
   - Lisu: body-hair and feather Values disagree with their Forms.
7. **Systematic loss in Koelle (Polyglotta Africana) Segments.** The under-dot vowels (ẹ, ọ) are
   rendered as rhotic `e˞`/`o˞`, and acute/macron tone or length marks are dropped. This affects Yála,
   Karekare and Īhéwe. Several Grollemund, LSI and Hunter-Gatherer rows also drop tone or accent.
8. **Heavy homophony in monosyllabic lists.**
   - Nuosu *tshi³³*: fall, ten, throw, squeeze.
   - Irarutu *ɛ*: tree, wood, 'you (pl.)'.
   - Anjam *ŋam*: tree, eye, fire.
   - Southern Qiandong *teu⁴⁴*: four meanings.
   - Pawaia *sia*: fire, red, eel, sun.

   In all of these, spelling identity alone is weak evidence.

## Limitations

- **Sources:** I consulted no source scans, printed dictionaries or publisher pages. All evidence
  is from the local Lexibank/CLDF exports and the Wiktionary intake. Page-level provenance,
  original orthographies and editorial context were not verified.
- **Senses and pronunciation:** no case had native-language sense glosses. Matching spelling was
  never treated as matching pronunciation. Many sources leave tone, length or glottalisation
  unmarked in tonal or glottal-contrast languages (e.g. Mazera, Tangkhul, Tause, 19th-century
  Tolmie and Koelle lists).
- **Absence:** a sampled nonmatch or a missing parameter does not establish lexical absence. Pooled
  multi-source rows (Hunter-Gatherer) do not show which source attests which sense.
- **Matching:** parameter matching by Concepticon ID can miss a source's combined concepts. I
  searched by name for the cases with no match, but other near-miss parameters may exist.

## Familiarity disclosure

My only knowledge of these languages comes from general training data. I am not an expert in any
of them and have no fieldwork. My familiarity is:

- **Moderate**, from widely documented languages: Japanese, Standard Arabic, Tagalog, Nepali,
  Kannada, Tatar, Tongan, Tahitian, Rapa Nui, Lower Sorbian, Tetun, Igbo.
- **Moderate**, from the Lexibank datasets and conventions: IDS, NorthEuraLex, TNG, LSI, Koelle's
  *Polyglotta Africana*.
- **Little or none:** most Papuan, Amazonian, Chadic, Yi and Tibeto-Burman varieties here.

Background knowledge appears only as flagged caveats in `limitations`, never as evidence. Examples:
Koelle's under-dot convention, prothetic w- in Lower Sorbian *woko*, and Tetun *loron*.
