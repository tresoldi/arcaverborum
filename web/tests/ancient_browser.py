"""Optional historical-scope and written-only export checks against a served build."""

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
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')", timeout=120000
        )
        with page.expect_download() as download:
            page.locator("#exportcsv").click()
        with open(download.value.path()) as f:
            return list(csv.DictReader(f))

    etruscan = export("etr-etruscan")
    written = [r for r in etruscan if r["transcription_source"] == "kaikkietruscan"]
    assert len(etruscan) == 94 and len(written) == 24
    assert all(not r["Segments"] and r["Segments_Source"] == "unclean" for r in written)
    assert all("orthographic_transcription_only" in r["Comment"] for r in written)
    assert "by-sa/4.0" in page.locator("#app").inner_text().lower()
    elamite = export("ela-elamite")
    assert len(elamite) == 790
    old = [r for r in elamite if r["transcription_source"] == "idssegmented"]
    assert len(old) == 787 and all("automatic_transcription_conversion" in r["Comment"] for r in old)
    script = [r for r in elamite if r["transcription_source"] == "wiktionary"]
    assert len(script) == 3 and all(not r["Segments"] for r in script)
    greek = export("ine-ionic-attic-ancient-greek")
    scoped = [r for r in greek if r["transcription_source"] == "wiktionary"]
    assert len(scoped) == 24 and all("5ᵗʰ BCE Attic" in r["Comment"] and r["raw_ipa"] for r in scoped)
    maya = export("may-epigraphic-mayan")
    assert len(maya) == 2
    hul = next(r for r in maya if r["transcription_source"] == "twkmmayan")
    assert hul["Form"] == "hul" and not hul["Segments"] and "1559st:24st" in hul["Comment"]
    assert "by/4.0" in page.locator("#app").inner_text().lower()
    assert not errors, errors
    print("PASS: Etruscan/Elamite lexical and reading-basis exports, Attic scope, Mayan scholarly transcription")
    browser.close()
