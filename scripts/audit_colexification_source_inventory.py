"""Audit ten pinned source members, distinguishing prompts from lexical absence.

Bibliographic overlap is not proof of copied observations. Dataset-wide prompt
presence is not proof that a particular consultant was asked a question.
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from arcaverborum.colexification import sha

CASES = {"ids": ["277", "290", "306", "309"], "wold": ["Hup", "Wichi", "Mapudungun"], "tryoncad": ["LEW", "RUK", "KWA"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Refuse to overwrite source audit")
    a.output.mkdir(parents=True)
    intake_languages = list(csv.DictReader((a.root / "intake/lexibank/languages.csv").open()))
    inputs, inventories, cases = {}, [], []
    for source, members in CASES.items():
        base = a.root / "raw/lexibank" / source
        paths = [base / "cldf" / name for name in ["languages.csv", "parameters.csv", "forms.csv", "sources.bib"]]
        paths.append(base / "README.md")
        inputs.update({str(path.relative_to(a.root)): sha(path) for path in paths})
        languages = {r["ID"]: r for r in csv.DictReader(paths[0].open())}
        prompts = {r["ID"]: r for r in csv.DictReader(paths[1].open())}
        forms = defaultdict(list)
        for row in csv.DictReader(paths[2].open()):
            if row["Language_ID"] in members:
                forms[row["Language_ID"]].append(row)
        bib = paths[3].read_text()
        headers = list(re.finditer(r"(?m)^@\w+\{([^\s,}]+)", bib))
        entries = {
            m.group(1): bib[m.start() : headers[i + 1].start() if i + 1 < len(headers) else len(bib)].strip()
            for i, m in enumerate(headers)
        }
        for member in members:
            language = languages[member]
            rows = forms[member]
            counts = Counter(r["Parameter_ID"] for r in rows)
            refs = Counter(
                ref.strip().split("[", 1)[0] for r in rows for ref in r.get("Source", "").split(";") if ref.strip()
            )
            for pid, prompt in prompts.items():
                inventories.append(
                    dict(
                        source=source,
                        member=member,
                        parameter_id=pid,
                        name=prompt["Name"],
                        concepticon_id=prompt.get("Concepticon_ID", ""),
                        records=counts[pid],
                        status="record_present" if counts[pid] else "parameter_without_member_record",
                        elicitation_status="unknown",
                        lexical_absence="not_asserted",
                    )
                )
            cross = [
                dict(member=r["ID"], dataset=r["Dataset"], name=r["Name"])
                for r in intake_languages
                if r["Glottocode"] == language["Glottocode"] and r["Dataset"] != source
            ]
            case = dict(
                source=source,
                member=member,
                language=language,
                records=len(rows),
                parameter_inventory=len(prompts),
                parameters_with_records=len(counts),
                parameters_without_member_record=len(prompts) - len(counts),
                missing_row_source=sum(not r.get("Source") for r in rows),
                citations=dict(refs),
                bibliography={key: entries.get(key, "UNRESOLVED NATIVE REFERENCE") for key in refs},
                other_resource_members=cross,
                fieldwork_independence="unknown_without_record_level_lineage",
                questionnaire_absence_is_lexical_absence=False,
            )
            if source == "wold":
                contributions = base / "cldf/contributions.csv"
                inputs[str(contributions.relative_to(a.root))] = sha(contributions)
                contribution = next(r for r in csv.DictReader(contributions.open()) if r["Language_ID"] == member)
                case["contribution"] = contribution
                desc = base / f"cldf/descriptions/vocabulary_{contribution['ID']}.md"
                inputs[str(desc.relative_to(a.root))] = sha(desc)
                case["source_description"] = dict(path=str(desc.relative_to(a.root)), sha256=sha(desc))
            cases.append(case)
    with (a.output / "questionnaire_inventory.csv").open("w") as h:
        writer = csv.DictWriter(h, fieldnames=list(inventories[0]))
        writer.writeheader()
        writer.writerows(inventories)
    (a.output / "member_evidence.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n")
    report = dict(
        cases=len(cases),
        south_american_cases=sum(c["language"].get("Macroarea") == "South America" for c in cases),
        inputs=inputs,
        outputs={p.name: sha(p) for p in a.output.glob("*")},
        inventory_rows=len(inventories),
        explicit_not_elicited_assertions=0,
        lexical_absence_assertions=0,
        verified_independent_fieldwork_replicates=0,
        caveat="Native prompt presence/missing records do not establish elicitation or lexical absence.",
    )
    (a.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"inputs", "outputs"}}, indent=2))


if __name__ == "__main__":
    main()
