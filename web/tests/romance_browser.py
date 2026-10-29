"""Optional end-to-end checks for named Romance samples and RVID/profile exports."""

import csv
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

url = sys.argv[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def export(aid):
        state = dict(view="variety", id=aid, collection="all", vocab="all")
        page.goto(url + "#s=" + quote(json.dumps(state)), wait_until="networkidle")
        page.wait_for_function(
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')",
            timeout=120000,
        )
        with page.expect_download() as download:
            page.locator("#exportcsv").click()
        with open(download.value.path()) as f:
            return list(csv.DictReader(f))

    cremona = export("ine-rvid-cremona")
    assert len(cremona) == 11
    assert "Lombard" in page.locator("#app").inner_text()
    assert "gpl-3.0" in page.locator("#app").inner_text().lower()
    assert all(r["transcription_source"] == "rvidinfinitives" for r in cremona)
    assert all('"morphology_cell": "INF"' in r["Comment"] and '"raw_ipa"' in r["Comment"] for r in cremona)
    assert not any(r["Cognacy"] for r in cremona)
    gallurese = export("ine-gallurese-sardinian")
    assert len(gallurese) == 254
    assert sum(r["Segments_Source"] == "profile" for r in gallurese) == 16
    assert sum(r["Segments_Source"] == "source" for r in gallurese) == 3
    literal = next(r for r in gallurese if r["source_form_id"] == "wikt_2836027")
    figurative = next(r for r in gallurese if r["source_form_id"] == "wikt_2836821")
    assert literal["concept_id"] == "ani-dog" and not figurative["concept_id"]
    sample = export("ine-saenko-lanzo-torinese")
    assert len(sample) == 113
    assert {r["source_language_id"] for r in sample} == {"saenkoromance_lanzotorinesepiemontese"}
    assert "Piemontese" in page.locator("#app").inner_text()
    corsican = export("ine-corsican")
    assert len(corsican) == 116
    assert {r["transcription_source"] for r in corsican} == {"gled", "wiktionary"}
    assert len([r for r in corsican if r["transcription_source"] == "wiktionary"]) == 77
    assert not errors, errors
    print(
        "PASS: RVID licence/morphology, Gallurese profile/sense scope, "
        "named sample isolation, retained GLED exports"
    )
    browser.close()
