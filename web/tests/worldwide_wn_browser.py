"""WN additions, minimal-language pilots and source-fidelity export checks."""

import csv
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(accept_downloads=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def export(aid):
        state = dict(view="variety", id=aid, collection="all", vocab="all")
        page.goto(sys.argv[1] + "#s=" + quote(json.dumps(state)), wait_until="networkidle")
        page.wait_for_function(
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')"
        )
        with page.expect_download() as download:
            page.locator("#exportcsv").click()
        with open(download.value.path()) as handle:
            return list(csv.DictReader(handle))

    for aid in ["yan-yaroame", "aav-birhor", "nor-gamkonora"]:
        rows = export(aid)
        assert len(rows) == 1 and rows[0]["concept_id"] == "phy-water"
        assert rows[0]["raw_ipa"] and rows[0]["preferred_source"] == "wiktionary"
        assert rows[0]["gled_dependence"] == "none"
    for aid, count in [
        ("mus-chickasaw", 51),
        ("may-yucatec-maya", 57),
        ("alg-unami", 17),
        ("ath-western-apache", 14),
        ("atl-ewe", 35),
        ("ine-scots", 58),
        ("afa-kabyle", 34),
        ("sit-dzongkha", 51),
        ("sit-atong-india", 32),
    ]:
        rows = export(aid)
        supplied = [r for r in rows if r["transcription_source"] == "wiktionary"]
        assert len(supplied) == count and all(r["raw_ipa"] for r in supplied)
        legacy = [r for r in rows if r["transcription_source"] == "gled"]
        assert legacy and all("ASJP-derived" in r["representation_basis"] for r in legacy)
        assert all(r["preferred_source"] == "wiktionary" for r in supplied if r["concept_id"])
        assert "Scores summarize feature presence" in page.locator("#app").inner_text()
    rows = export("ine-palula")
    original = [r for r in rows if r["transcription_source"] == "dictpalula"]
    assert len(original) == 43 and all(r["preferred_source"] == "dictpalula" for r in original)
    eye = next(r for r in original if r["concept_id"] == "bod-eye")
    assert {"quantity", "pitch_or_accent"} <= set(eye["phonological_marks"].split(";"))
    assert len([r for r in rows if r["transcription_source"] == "gled"]) == 108
    rows = export("tim-wersing")
    original = [r for r in rows if r["transcription_source"] == "dictwersing"]
    assert len(original) == 28 and all(r["Segments_Source"] == "profile" for r in original)
    assert all("Peitoko" in r["Comment"] and "Pronunciation" in r["Comment"] for r in original)
    rows = export("afa-coptic")
    written = [r for r in rows if r["transcription_source"] == "copticsahidic"]
    assert len(written) == 72 and all(not r["Segments"] for r in written)
    assert all(r["representation_basis"] == "written_or_unresolved" for r in written)
    rows = export("mia-media-lengua")
    assert next(r for r in rows if r["source_parameter_id"] == "dictmedialengua_SN000410")["concept_id"] == "mod-bottle"
    assert not next(r for r in rows if r["source_parameter_id"] == "dictmedialengua_SN003074")["concept_id"]
    assert not errors, errors
    browser.close()
print("PASS: WN pilots, retained GLED, scoped dictionary readings, written Coptic and source-fidelity annotations")
