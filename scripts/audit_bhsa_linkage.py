"""Audit pinned BHSA lemma/occurrence/verse linkage without changing intake.

Run: uv run --no-project --with text-fabric --with requests python
scripts/audit_bhsa_linkage.py [--fetch]
"""

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

import requests
from tf.fabric import Fabric

root = Path(__file__).resolve().parents[1]
path = root / "raw/curation/gw/bhsa2021"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--fetch", action="store_true")
args = parser.parse_args()
manifest = json.loads((root / "docs/worldwide_gw08_bhsa_linkage_sources_2026-10-29.json").read_text())
path.mkdir(parents=True, exist_ok=True)
for feature in manifest["features"]:
    target = path / (feature["feature"] + ".tf")
    if args.fetch:
        response = requests.get(feature["url"], timeout=60)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest() != feature["sha256"]:
            raise ValueError("Pinned BHSA acquisition differs: " + feature["feature"])
        target.write_bytes(response.content)
    if hashlib.sha256(target.read_bytes()).hexdigest() != feature["sha256"]:
        raise ValueError("Pinned BHSA bytes differ: " + feature["feature"])
TF = Fabric(locations=str(path), silent="deep")
api = TF.load("lex_utf8 g_word_utf8 gloss language book chapter verse lex g_lex_utf8", silent="deep")
assert api is not None
F, T = api.F, api.T
words = F.otype.s("word")
counts = collections.Counter(F.language.v(n) for n in words)
selected = []
for language, limit in [("Hebrew", 10), ("Aramaic", 5)]:
    found = 0
    for node in words:
        if F.language.v(node) != language:
            continue
        section = T.sectionFromNode(node)
        assert len(section) == 3 and all(s is not None for s in section)
        selected.append(
            dict(
                word_node=node,
                language=language,
                source_lexeme_id=F.lex.v(node),
                consonantal_lexeme=F.lex_utf8.v(node),
                pointed_lexeme=F.g_lex_utf8.v(node),
                occurrence=F.g_word_utf8.v(node),
                source_gloss=F.gloss.v(node),
                book=section[0],
                chapter=section[1],
                verse=section[2],
                status="linkage_witness_only",
                reading_basis="Later Masoretic pointed writing, not inferred ancient surface IPA",
                license="CC BY-NC4.0",
            )
        )
        found += 1
        if found == limit:
            break
    assert found == limit
with (root / "docs/worldwide_gw08_bhsa_linkage_witnesses_2026-10-29.csv").open("w") as f:
    w = csv.DictWriter(f, fieldnames=list(selected[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(selected)
out = dict(
    word_nodes=len(words),
    language_counts=dict(counts),
    linked_witnesses=len(selected),
    hebrew_witnesses=10,
    aramaic_witnesses=5,
    decision=(
        "Node/lexeme/verse and language linkage now demonstrated with official Text-Fabric loader. "
        "Lexical admission remains bounded: proclitic word nodes are not automatically independent headwords; "
        "exact frozen sense and historical stage need separate review. No intake or lexical outputs changed."
    ),
    examples=[{k: r[k] for k in ["word_node", "language", "book", "chapter", "verse"]} for r in selected],
)
(root / "docs/worldwide_gw08_bhsa_linkage_2026-10-29.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n"
)
print(json.dumps({k: v for k, v in out.items() if k != "examples"}, indent=2))
