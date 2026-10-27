"""Verify/materialize the licensed original Bangru slice, then ingest into staging only.

The source is a document deposit, not a Git repository. --fetch downloads its
frozen PDF and checks the deposit license. --audit-pdf additionally needs
PyMuPDF and verifies authored source-entry spans against the PDF itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.bangru_original import DATA, materialize, read

ROOT = Path(__file__).resolve().parents[1]


def audit_pdf(pdf, reviews):
    import pymupdf

    document = pymupdf.open(pdf)
    entries = []
    current = None
    for page_index in range(24):
        for block in document[page_index].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line["spans"]
                text = "".join(s["text"] for s in spans).strip()
                if not text or text.isdigit() or text == "List of Glosses":
                    continue
                first = spans[0]
                margin = any(abs(first["bbox"][0] - x) < 1 for x in (56.8, 311.9))
                new_entry = "Bold" in first["font"] and margin
                if new_entry:
                    gloss = ""
                    for span in spans:
                        if "Bold" not in span["font"]:
                            break
                        gloss += span["text"]
                    gloss = gloss.strip()
                    if gloss.startswith(("Root:", "Dammai:", "Namrei:", "Koro:", "Aka:", "COMPARE", "MINIMALPAIR")):
                        new_entry = False
                if new_entry:
                    current = dict(gloss=gloss, page=page_index + 1, entry=text)
                    entries.append(current)
                elif current:
                    current["entry"] += " " + text
    lookup = {(e["page"], e["gloss"]): hashlib.sha256(e["entry"].encode()).hexdigest() for e in entries}
    for row in reviews:
        if lookup.get((int(row["source_page"]), row["source_gloss"])) != row["entry_sha256"]:
            raise ValueError("Reviewed Bangru PDF span changed: " + row["ID"])
    print(len(reviews), "authored source-entry spans verified against the original PDF")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--audit-pdf", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "raw/curation/bangru-stage")
    args = parser.parse_args()
    active = (ROOT / "intake").resolve()
    output = args.output.resolve()
    if output == active or output.is_relative_to(active):
        raise ValueError("Bangru staging must be outside active intake")
    result = materialize(ROOT / "raw", download=args.fetch)
    print(result)
    if args.audit_pdf:
        spec = json.loads((DATA / "bangru_original_source.json").read_text())
        audit_pdf(ROOT / "raw/lexibank/bodtbangru" / spec["filename"], read(DATA / "bangru_original_forms.csv"))
    result = ingest_lexibank(ROOT / "raw", output, datasets=["bodtbangru"])
    if result["datasets_ingested"] != 1:
        raise ValueError("Bangru did not stage successfully")
    print(result)


if __name__ == "__main__":
    main()
