"""Optional original African evidence/export regression against a served build."""

import csv
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def export(aid):
        state = dict(view="variety", id=aid, collection="all", vocab="all")
        page.goto(sys.argv[1] + "#s=" + quote(json.dumps(state)), wait_until="networkidle")
        page.wait_for_function(
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')", timeout=120000
        )
        with page.expect_download() as download:
            page.locator("#exportcsv").click()
        with open(download.value.path()) as f:
            return list(csv.DictReader(f))

    for aid, count in [("atl-wamey", 20), ("atl-kam", 30)]:
        rows = export(aid)
        assert len(rows) == count
        assert all(not r["Segments"] and r["Segments_Source"] == "unclean" for r in rows)
        assert all("by-nc-sa/4.0" in r["License"] and "attribution" in r["Comment"] for r in rows)
    rows = export("atl-gyele")
    assert len(rows) == 102
    assert sum(r["transcription_source"] == "gled" for r in rows) == 36
    original = [r for r in rows if r["transcription_source"] == "gyelioriginal"]
    assert sum(r["Segments_Source"] == "profile" for r in original) == 64
    assert sum(not r["Segments"] for r in original) == 2
    assert all(
        "native_sha256" in r["Comment"] and r["mapping_review"] != "source mapping; no local review recorded"
        for r in original
    )
    rows = export("afa-hdi")
    assert len(rows) == 77 and sum(r["transcription_source"] == "gled" for r in rows) == 32
    assert sum(r["Segments_Source"] == "profile" for r in rows) == 45
    rows = export("man-bambara")
    added = [r for r in rows if r["transcription_source"] == "westafricanoriginal"]
    assert len(added) == 12 and all(r["Segments_Source"] == "profile" for r in added)
    assert all(any(t in r["Segments"] for t in "áàéèíìóòúùɛ́ɔ́") for r in added)
    assert not errors, errors
    print("PASS: Konyagi/Kam written-only terms, Gyeli/Hdi primaries and GLED preservation, original tone exports")
    browser.close()
