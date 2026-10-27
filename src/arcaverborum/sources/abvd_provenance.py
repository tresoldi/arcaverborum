"""Retain contribution and judgment notes omitted by the compact intake schema."""

from __future__ import annotations

import json


def preserve(forms, *, use_cognate_table=False):
    if "Contribution_ID" not in forms:
        return forms
    forms = forms.copy()
    if "Comment" not in forms:
        forms["Comment"] = ""
    for index, row in forms.iterrows():
        extras = {k: row.get(k, "") for k in ["Contribution_ID", "Cognacy_Comment", "Loan_Raw"] if row.get(k, "")}
        if use_cognate_table:
            if row.get("Cognacy", ""):
                extras["Cognacy_Raw"] = row["Cognacy"]
            extras["cognacy_scope"] = "Membership uses structured CognateTable IDs; raw labels are within-concept notes"
        contribution = row.get("Contribution_ID", "")
        if contribution:
            extras["contribution_urls"] = [
                "https://abvd.eva.mpg.de/austronesian/language.php?id=" + key.strip()
                for key in contribution.split(";")
                if key.strip().isdigit()
            ]
        if not row.get("Source", ""):
            forms.at[index, "Source"] = "Greenhilletal2008"
            extras["citation_scope"] = "Dataset-level citation only; no individual bibliographic reference supplied"
        if extras:
            annotation = "Upstream contribution evidence: " + json.dumps(extras, ensure_ascii=False, sort_keys=True)
            forms.at[index, "Comment"] = "; ".join(filter(None, [row.get("Comment", ""), annotation]))
    if use_cognate_table and "Cognacy" in forms:
        # ABVD raw labels such as "1,64" are scoped to a meaning. The
        # CognateTable already expands them into hand-1, hand-64, etc.
        # Unioning both would invent cross-meaning sets and composite IDs.
        forms["Cognacy"] = ""
    return forms
