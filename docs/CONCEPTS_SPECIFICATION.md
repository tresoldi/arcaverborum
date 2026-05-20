# Concept Catalog Specification

Arca Verborum keeps its **own concept catalog** — a frozen, human-readable
id space for comparanda — and maps to Concepticon only as a column. This
mirrors the variety `av_id` scheme (our own key; Glottocode demoted to a
column) and exists for the same reasons: stable keys we control, and clean
labels free of Concepticon's verb/noun ambiguity, parentheses, disjunctive
glosses, and odd default synonyms.

## The key: `concept_id`

```
<field_code>-<label_slug>[-<qualifier_slug> | -<n>]
```

* `field_code` — a 3-char code for the concept's Concepticon
  **SEMANTICFIELD** (`bod` = The body, `act` = Basic actions and
  technology, `phy` = The physical world, …). The coarse, stable semantic
  dimension is the only thing in the key, so the id survives label
  re-curation. Codes live in the committed, curatable
  `data/semantic_field_codes.csv` (24 IDS fields, fully seeded; `und` =
  none). Possession is `pss`, not `pos`, to avoid clashing with the
  part-of-speech column.
* `label_slug` — the lowercased, ASCII-folded clean gloss. A trailing
  Concepticon parenthetical is stripped (it becomes the qualifier).
* `-<qualifier_slug>` / `-<n>` — added **only** to break a collision
  inside one field: the disambiguator slug first
  (`mot-blow` vs `act-blow-with-mouth`), then a numeric suffix, in
  Concepticon-id order so the lowest id keeps the bare slug.

Everything is lowercase. Examples: `phy-water`, `bod-hair`, `act-eat`,
`kin-mother`, `spa-below-or-under`, `lng-tongue` vs `bod-tongue`.

The full inventory: **3,823 concepts, 24 fields, zero collisions, zero
numeric suffixes** (every within-field homograph was separable by its
qualifier). 869 ids carry a qualifier slug.

## The registry: `data/concepts.csv` (frozen)

One row per concept, assigned once and frozen — like `data/varieties.csv`.

| Column | Meaning |
|---|---|
| `concept_id` | our primary key (above) |
| `concepticon_id` | external mapping to Concepticon (may be empty for future hand-added concepts) |
| `label` | clean lowercase display gloss (the de-messed form) |
| `pos` | from Concepticon ONTOLOGICAL_CATEGORY: `n`/`v`/`adj`/`num`/`clf`/`x` — a queryable column, never in the id, so verb/noun is never lost |
| `semantic_field` | full Concepticon field name (source of the prefix) |
| `definition` | Concepticon DEFINITION (clean prose; replaces parentheses as the disambiguator) |
| `status` | `active` / `merged` (Concepticon gave it a replacement) |
| `replacement_id` | Concepticon REPLACEMENT_ID, when merged |
| `notes` | curation notes |

Scope is **core comparanda only**: the Concepticon-mapped concepts the
sources actually use. Wiktionary's unmapped senses get `concept_id = ""`
and remain a separate, uncurated layer until they earn a Concepticon
mapping or hand curation.

## Curation

* `data/concepts.csv` is hand-editable; it is the source of truth.
* `data/concept_overrides.csv` (`concepticon_id, concept_id, label, pos,
  semantic_field, definition, notes`) is the pre-bootstrap fix layer —
  force a clean label, a different field/prefix, a corrected pos, or an
  explicit/merged `concept_id`, then re-bootstrap. (Analogous to
  `variety_overrides.csv`.)
* Re-curating a label/field/id rebuilds the forms that resolve through it:
  `concepts.csv` and `semantic_field_codes.csv` are part of the build
  *recipe* (`tracking._RECIPE_FILES`).

## Resolution in the build

Per form: `Parameter_ID → concepticon_id` (the existing parameter index)
`→ (concept_id, label)` (the registry, via
`concepts.load_concept_maps`). Unmapped Concepticon ids resolve to an
empty `concept_id`. A variety's `custom/concept_map.csv` may pin a
`concept_id` directly (overrides the Concepticon route);
`custom/forms.csv` accepts a `concept_id` or a `Concepticon_ID`.

The forms output carries `concept_id`, `concept_label`, and
`Concepticon_ID` (the external mapping). `Concepticon_Gloss` is **retired**
from the forms output — the clean label lives in the registry and is
echoed as `concept_label`.

## Drift (`build.py concepts`)

The registry is frozen; Concepticon moves. `build.py concepts` audits the
gap without re-keying anything, reporting:

* **new in-use** — Concepticon ids now in intake but not yet in the
  registry (mint with `build.py concepts --mint`);
* **now merged** — concepts Concepticon has since superseded;
* **field drift** — concepts whose Concepticon field changed (the prefix
  *would* move if re-derived — flagged, not changed);
* **dropped** — concepts gone from the Concepticon master.

`--mint` appends freshly minted ids for new in-use concepts (collision-safe
against the existing registry), extending the frozen catalog.

## Bootstrap / planning

* `scripts/plan_concepts.py` — dry run; writes the proposed registry +
  report to `output/concept_migration/`, touching nothing under `data/`.
* `scripts/bootstrap_concepts.py` — writes the real
  `data/concepts.csv` + `data/semantic_field_codes.csv` from the in-use
  Concepticon ids in intake + the Concepticon master + overrides.

Code: `arcaverborum.concepts` (slug/field-code/mint/assign + registry I/O),
`arcaverborum.concept_audit` (drift), `arcaverborum.concepticon`
(master loader). Tests: `tests/test_concepts.py`,
`tests/test_concept_audit.py`.
