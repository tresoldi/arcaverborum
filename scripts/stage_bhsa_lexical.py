"""Stage the finite reviewed BHSA consonantal lexeme pilot, never inferred IPA.

Run with the optional Text-Fabric environment after audit_bhsa_linkage.py --fetch:
uv run --no-project --with text-fabric python scripts/stage_bhsa_lexical.py
Then ingest bhsalexical outside active intake and append the new namespace once.
"""

import csv
import hashlib
import json
from pathlib import Path

from tf.fabric import Fabric

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def write(path, rows):
    with path.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stage():
    manifest = json.loads((ROOT / "docs/worldwide_gw08_bhsa_linkage_sources_2026-10-29.json").read_text())
    source = ROOT / "raw/curation/gw/bhsa2021"
    for item in manifest["features"]:
        if hashlib.sha256((source / (item["feature"] + ".tf")).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Pinned BHSA feature differs: " + item["feature"])
    api = Fabric(locations=str(source), silent="deep").load(
        "lex_utf8 g_word_utf8 gloss language book chapter verse lex g_lex_utf8", silent="deep"
    )
    if not api:
        raise ValueError("BHSA feature loading failed")
    features, text = api.F, api.T
    concepts = {r["concept_id"]: r for r in read(ROOT / "src/arcaverborum/data/concepts.csv")}
    forms, parameters, seen = [], [], set()
    for review in read(ROOT / "docs/worldwide_wf09_bhsa_review_2026-10-29.csv"):
        if review["decision"] != "admit":
            continue
        node = int(review["word_node"])
        if node in seen or features.otype.v(node) != "word":
            raise ValueError("BHSA review has duplicate or non-word node")
        seen.add(node)
        context = dict(
            word_node=node,
            language=features.language.v(node),
            source_lexeme_id=features.lex.v(node),
            consonantal_lexeme=features.lex_utf8.v(node),
            pointed_stem=features.g_lex_utf8.v(node),
            occurrence=features.g_word_utf8.v(node),
            source_gloss=features.gloss.v(node),
            verse=list(text.sectionFromNode(node)),
        )
        encoded = json.dumps(context, ensure_ascii=False, sort_keys=True)
        if (
            hashlib.sha256(encoded.encode()).hexdigest() != review["expected_context_sha256"]
            or review["Form"] != context["consonantal_lexeme"]
            or review["source_sense"] != context["source_gloss"]
            or review["source_language"] != context["language"]
            or not review["rationale"]
        ):
            raise ValueError("Reviewed BHSA lexeme/context changed")
        concept = concepts[review["concept_id"]]
        key = "word-" + str(node)
        parameters.append(
            dict(
                ID=key,
                Name=context["source_gloss"],
                Concepticon_ID=concept["concepticon_id"],
                Concepticon_Gloss=concept["label"],
            )
        )
        context.update(
            reading_basis="orthographic_transcription_only",
            mapping_review=review["rationale"],
            source_snapshot="BHSA2021@4db00e2157915495e1a4d3d57e41223df24775da",
            license="CC BY-NC4.0",
        )
        forms.append(
            dict(
                ID=key,
                Language_ID=context["language"],
                Parameter_ID=key,
                Value=context["consonantal_lexeme"],
                Form=context["consonantal_lexeme"],
                Segments="",
                Source="bhsa",
                Comment=json.dumps(context, ensure_ascii=False, sort_keys=True),
            )
        )
    languages = [
        dict(
            ID="Hebrew",
            Name="Biblical Hebrew (BHSA corpus)",
            Glottocode="anci1244",
            Glottolog_Name="Ancient Hebrew",
            Family="Afro-Asiatic",
            Macroarea="Eurasia",
        ),
        dict(
            ID="Aramaic",
            Name="Biblical Aramaic (BHSA corpus)",
            Glottocode="",
            Glottolog_Name="",
            Family="Afro-Asiatic",
            Macroarea="Eurasia",
        ),
    ]
    out = ROOT / "raw/lexibank/bhsalexical/cldf"
    out.mkdir(parents=True, exist_ok=True)
    term = "http://cldf.clld.org/v1.0/terms.rdf#"
    props = dict(
        ID="id",
        Name="name",
        Form="form",
        Value="value",
        Segments="segments",
        Language_ID="languageReference",
        Parameter_ID="parameterReference",
        Source="source",
        Comment="comment",
        Glottocode="glottocode",
        Concepticon_ID="concepticonReference",
    )
    metadata = {
        "@context": "http://www.w3.org/ns/csvw",
        "dc:conformsTo": term + "Wordlist",
        "dc:title": "BHSA2021 reviewed consonantal lexemes with original verse witnesses",
        "dc:bibliographicCitation": (
            "ETCBC. Biblia Hebraica Stuttgartensia Amstelodamensis (BHSA), 2021 data, "
            "commit 4db00e2157915495e1a4d3d57e41223df24775da. Finite reviewed lexeme derivative."
        ),
        "dc:license": "https://creativecommons.org/licenses/by-nc/4.0/",
        "dcat:accessURL": "https://github.com/ETCBC/bhsa",
        "prov:wasDerivedFrom": [{"dc:title": "Repository", "dc:created": "4db00e2157915495e1a4d3d57e41223df24775da"}],
        "dc:source": "sources.bib",
        "tables": [],
    }
    for filename, rows, kind in [
        ("forms.csv", forms, "FormTable"),
        ("parameters.csv", parameters, "ParameterTable"),
        ("languages.csv", languages, "LanguageTable"),
    ]:
        write(out / filename, rows)
        metadata["tables"].append(
            dict(
                url=filename,
                **{"dc:conformsTo": term + kind},
                tableSchema=dict(
                    columns=[
                        dict(name=k, datatype="string", **({"propertyUrl": term + props[k]} if k in props else {}))
                        for k in rows[0]
                    ]
                ),
            )
        )
    (out / "cldf-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    (out / "sources.bib").write_text(
        "@misc{bhsa, author={ETCBC}, title={BHSA 2021: reviewed consonantal lexeme derivative}, "
        "year={2021}, url={https://github.com/ETCBC/bhsa}, "
        "note={CC BY-NC 4.0; source commit 4db00e2157915495e1a4d3d57e41223df24775da}}\n"
    )
    print(len(forms), "reviewed written lexemes; no inferred pronunciation")


if __name__ == "__main__":
    stage()
