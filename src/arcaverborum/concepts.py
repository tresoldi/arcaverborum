"""concept_id assignment: semantic-field-prefixed, human-readable concept IDs.

Scheme (decided 2026-05): ``<field_code>-<label_slug>[-<qualifier_slug>|-<n>]``

* ``field_code`` — a stable 3-char code for the concept's Concepticon
  SEMANTICFIELD (e.g. ``bod`` = The body, ``act`` = Basic actions and
  technology). Codes live in a committed, curatable registry
  (``data/semantic_field_codes.csv``); the 24 IDS fields are fully
  seeded below. ``und`` = no/unknown field. Only the *coarse, stable*
  semantic dimension goes in the key — part of speech and the
  Concepticon mapping stay as columns.
* ``label_slug`` — the lowercased, ASCII-folded clean gloss, with any
  trailing Concepticon parenthetical disambiguator stripped off (it is
  reattached as a ``-qualifier`` only when needed to break a collision).
* ``-<qualifier>`` / ``-<n>`` — appended only to break collisions inside
  one field: the disambiguator slug first (``mot-blow-of-wind`` vs
  ``mot-blow``), then a numeric suffix, in Concepticon-ID order so the
  lowest id keeps the bare slug.

This mirrors the variety ``av_id`` scheme (see ``arcaverborum.avid``):
our own frozen, human-readable primary key, mapping to the external
authority (Concepticon) as a column. IDs are **assigned once and
frozen** in ``data/concepts.csv``; later Concepticon drift is flagged,
never silently re-keyed.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from arcaverborum.idscheme import build_codes, code_for, load_codes, slugify_name, write_codes

DATA_DIR = Path(__file__).parent / "data"
FIELD_CODES_CSV = DATA_DIR / "semantic_field_codes.csv"
CONCEPTS_CSV = DATA_DIR / "concepts.csv"

# Code used when a concept has no resolved semantic field.
UNDETERMINED_CODE = "und"

# Conventional 3-char codes for the 24 Concepticon/IDS semantic fields,
# keyed by EXACT Concepticon SEMANTICFIELD name. All in use by the core
# set; curate freely in data/semantic_field_codes.csv. (Note: Possession
# is "pss", not "pos", to avoid clashing with the part-of-speech column.)
SEED_FIELD_CODES: dict[str, str] = {
    "Animals": "ani",
    "Basic actions and technology": "act",
    "The body": "bod",
    "Agriculture and vegetation": "agr",
    "The physical world": "phy",
    "Quantity": "qua",
    "Food and drink": "foo",
    "Kinship": "kin",
    "Emotions and values": "emo",
    "Modern world": "mod",
    "Spatial relations": "spa",
    "Motion": "mot",
    "Time": "tim",
    "Social and political relations": "soc",
    "Sense perception": "sns",
    "Clothing and grooming": "clo",
    "Cognition": "cog",
    "The house": "hou",
    "Speech and language": "lng",
    "Possession": "pss",
    "Warfare and hunting": "war",
    "Religion and belief": "rel",
    "Law": "law",
    "Miscellaneous function words": "fun",
}

# Concepticon ONTOLOGICAL_CATEGORY -> our part-of-speech tag (a column,
# never in the id). Blank/unknown -> "".
POS_FOR_CATEGORY: dict[str, str] = {
    "Person/Thing": "n",
    "Action/Process": "v",
    "Property": "adj",
    "Number": "num",
    "Classifier": "clf",
    "Other": "x",
}

CONCEPT_FIELDS = (
    "concept_id",
    "concepticon_id",
    "label",
    "pos",
    "semantic_field",
    "definition",
    "status",
    "replacement_id",
    "notes",
)


@dataclass(slots=True)
class Concept:
    concept_id: str
    concepticon_id: str = ""
    label: str = ""
    pos: str = ""
    semantic_field: str = ""
    definition: str = ""
    status: str = "active"
    replacement_id: str = ""
    notes: str = ""


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

# A single trailing parenthetical, e.g. "BLOW (OF WIND)" -> head + "OF WIND".
_TRAILING_PAREN = re.compile(r"^(.*?)\s*\(([^()]*)\)\s*$")


def normalize_gloss(gloss: str) -> tuple[str, str]:
    """Split a Concepticon gloss into (clean lowercase label, qualifier).

    A single trailing parenthetical becomes the qualifier (moved out of
    the label), unless stripping it would leave nothing. Everything is
    lowercased; the messy uppercase/parenthesised display form is gone.

        "BLOW (OF WIND)" -> ("blow", "of wind")
        "BELOW OR UNDER"  -> ("below or under", "")
        "(SOMEONE)"       -> ("(someone)", "")   # nothing left if stripped
    """
    g = gloss.strip()
    qualifier = ""
    m = _TRAILING_PAREN.match(g)
    if m and m.group(1).strip():
        g, qualifier = m.group(1).strip(), m.group(2).strip()
    return g.lower(), qualifier.lower()


def pos_for_category(category: str) -> str:
    return POS_FOR_CATEGORY.get((category or "").strip(), "")


# --------------------------------------------------------------------------
# Field codes (mirror of avid.build_family_codes / family_code_for)
# --------------------------------------------------------------------------

def build_field_codes(
    fields: list[str],
    seed: dict[str, str] | None = None,
) -> dict[str, str]:
    """Assign a unique 3-char code to each semantic-field name."""
    return build_codes(fields, SEED_FIELD_CODES if seed is None else seed)


def field_code_for(field: str, codes: dict[str, str]) -> str:
    return code_for(field, codes)


def load_field_codes(path: Path = FIELD_CODES_CSV) -> dict[str, str]:
    return load_codes(path, "field", "code")


def write_field_codes(codes: dict[str, str], path: Path = FIELD_CODES_CSV) -> None:
    write_codes(codes, path, "field", "code")


# --------------------------------------------------------------------------
# concept_id minting / assignment
# --------------------------------------------------------------------------

def _candidate_ids(preferred: str, with_qualifier: str = ""):
    """Yield concept_id candidates in priority order.

    Disambiguator slug first (when present), then the bare preferred id,
    then numeric ``-2``, ``-3`` … suffixes. Infinite generator; the
    caller stops at the first not-yet-taken candidate.
    """
    if with_qualifier and with_qualifier != preferred:
        yield with_qualifier
    yield preferred
    n = 2
    while True:
        yield f"{preferred}-{n}"
        n += 1


def mint_concept_id(
    gloss: str,
    semantic_field: str,
    field_codes: dict[str, str],
    taken: set[str],
    concepticon_id: str = "",
) -> str:
    """Mint one fresh, non-colliding concept_id for a single concept.

    Used when a Concepticon id appears that the frozen registry doesn't
    yet cover. ``taken`` is the set of concept_ids already in use; the
    result is not added to it (the caller decides).
    """
    code = field_code_for(semantic_field, field_codes)
    label, qualifier = normalize_gloss(gloss)
    base = slugify_name(label, fallback=concepticon_id)
    preferred = f"{code}-{base}"
    qual_id = f"{code}-{base}-{slugify_name(qualifier)}" if qualifier else ""
    for cand in _candidate_ids(preferred, qual_id):
        if cand not in taken:
            return cand
    raise RuntimeError("unreachable")  # _candidate_ids is infinite


def assign_concept_ids(
    concepts: list[dict[str, str]],
    field_codes: dict[str, str],
) -> dict[str, str]:
    """Map each concept's Concepticon id to a proposed concept_id.

    ``concepts`` items need ``concepticon_id``, ``gloss``,
    ``semantic_field``. Within a (field, base-slug) collision the bare
    slug goes to the lowest Concepticon id; others take their
    disambiguator slug, else a numeric suffix — so assignment is
    order-independent and stable. Returns ``{concepticon_id: concept_id}``.
    """
    # Stable order: numeric Concepticon id where possible, else string.
    def _sort_key(c: dict[str, str]):
        cid = str(c.get("concepticon_id", "")).strip()
        return (0, int(cid)) if cid.isdigit() else (1, cid)

    prepared = []
    for c in sorted(concepts, key=_sort_key):
        cid = str(c.get("concepticon_id", "")).strip()
        if not cid:
            continue
        code = field_code_for(str(c.get("semantic_field", "")), field_codes)
        label, qualifier = normalize_gloss(str(c.get("gloss", "")))
        base = slugify_name(label, fallback=cid)
        preferred = f"{code}-{base}"
        qual_id = f"{code}-{base}-{slugify_name(qualifier)}" if qualifier else ""
        prepared.append((cid, preferred, qual_id))

    # Unique preferreds claim the bare slug; only ambiguous ones fall back
    # to the qualifier/numeric forms.
    from collections import Counter
    pref_counts = Counter(p[1] for p in prepared)

    out: dict[str, str] = {}
    taken: set[str] = set()
    # Pass 1: singletons get their bare preferred id.
    for cid, preferred, _qual in prepared:
        if pref_counts[preferred] == 1:
            out[cid] = preferred
            taken.add(preferred)
    # Pass 2: collisions, in the stable order already established.
    for cid, preferred, qual in prepared:
        if cid in out:
            continue
        for cand in _candidate_ids(preferred, qual):
            if cand not in taken:
                out[cid] = cand
                taken.add(cand)
                break
    return out


# --------------------------------------------------------------------------
# Registry I/O
# --------------------------------------------------------------------------

def load_concepts(path: Path = CONCEPTS_CSV) -> list[Concept]:
    concepts: list[Concept] = []
    if not path.exists():
        return concepts
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = (row.get("concept_id") or "").strip()
            if not cid:
                continue
            concepts.append(Concept(
                concept_id=cid,
                concepticon_id=(row.get("concepticon_id") or "").strip(),
                label=(row.get("label") or "").strip(),
                pos=(row.get("pos") or "").strip(),
                semantic_field=(row.get("semantic_field") or "").strip(),
                definition=(row.get("definition") or "").strip(),
                status=(row.get("status") or "active").strip(),
                replacement_id=(row.get("replacement_id") or "").strip(),
                notes=(row.get("notes") or "").strip(),
            ))
    return concepts


def write_concepts(concepts: list[Concept], path: Path = CONCEPTS_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONCEPT_FIELDS)
        w.writeheader()
        for c in sorted(concepts, key=lambda x: x.concept_id):
            w.writerow({
                "concept_id": c.concept_id,
                "concepticon_id": c.concepticon_id,
                "label": c.label,
                "pos": c.pos,
                "semantic_field": c.semantic_field,
                "definition": c.definition,
                "status": c.status,
                "replacement_id": c.replacement_id,
                "notes": c.notes,
            })


def load_concept_index(path: Path = CONCEPTS_CSV) -> dict[str, tuple[str, str]]:
    """Build the build-time lookup ``{concepticon_id: (concept_id, label)}``.

    Keyed on the external Concepticon id, which is what the per-form
    parameter resolution already produces. Concepts with no Concepticon
    mapping are not reachable this way (by design — they are added by
    explicit concept_id, not via Concepticon).
    """
    index: dict[str, tuple[str, str]] = {}
    for c in load_concepts(path):
        if c.concepticon_id:
            index.setdefault(c.concepticon_id, (c.concept_id, c.label))
    return index


def load_concept_maps(
    path: Path = CONCEPTS_CSV,
) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """Load the two lookups the build needs in one pass over the registry:

    * ``cid_index``  — ``{concepticon_id: (concept_id, label)}``
    * ``label_by_id`` — ``{concept_id: label}`` (for explicit concept_id
      overrides in custom files)
    """
    cid_index: dict[str, tuple[str, str]] = {}
    label_by_id: dict[str, str] = {}
    for c in load_concepts(path):
        label_by_id[c.concept_id] = c.label
        if c.concepticon_id:
            cid_index.setdefault(c.concepticon_id, (c.concept_id, c.label))
    return cid_index, label_by_id
