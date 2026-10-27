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
    route = dict(view="variety", id="ine-brazilian-portuguese", collection="all", vocab="all")
    page.goto(url + "#s=" + quote(json.dumps(route)), wait_until="networkidle")
    page.wait_for_function(
        "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')", timeout=120000
    )
    assert "Supplemental lexical source" in page.locator("#app").inner_text()
    assert "149" in page.locator("#app").inner_text()
    with page.expect_download() as download:
        page.locator("#exportcsv").click()
    rows = list(csv.DictReader(open(download.value.path())))
    assert len(rows) == 204 and sum(r["pronunciation_tags"] == '["Brazil"]' for r in rows) == 34
    scoped = [r for r in rows if r["pronunciation_tags"] == '["Brazil"]']
    assert len({r["source_pronunciation_id"] for r in scoped}) == 34
    assert all(r["raw_ipa"] and r["transcription_source"] == "wiktionary" for r in scoped)
    # The same variety has distinct Core-source metrics and exports.
    page.locator("#collection").select_option("core")
    page.wait_for_timeout(500)
    page.wait_for_function("!document.querySelector('#app').textContent.includes('Supplemental lexical source')")
    with page.expect_download() as download:
        page.locator("#exportcsv").click()
    core = list(csv.DictReader(open(download.value.path())))
    assert len(core) == 170 and {r["transcription_source"] for r in core} == {"iecor"}
    assert not any(r["pronunciation_tags"] for r in core)
    # Separate supplied readings have persistent IDs and readable evidence.
    route.update(collection="all", view="form", id=scoped[0]["ID"])
    page.goto(url + "#s=" + quote(json.dumps(route)), wait_until="networkidle")
    page.wait_for_function("document.querySelector('#app').textContent.includes('Provenance')", timeout=120000)
    assert "Brazil" in page.locator("#app").inner_text() and "raw ipa" in page.locator("#app").inner_text()
    route.update(view="variety", id="mia-media-lengua")
    page.goto(url + "#s=" + quote(json.dumps(route)), wait_until="networkidle")
    page.wait_for_function(
        "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')", timeout=120000
    )
    text = page.locator("#app").inner_text()
    assert "Stewart" in text and "dictmedialengua" in text and "3,216" in text
    assert "Kalamang" not in text
    # A dictionary profile applies to its source only, with derived status exported.
    route.update(view="variety", id="zap-iquito", collection="all")
    page.goto(url + "#s=" + quote(json.dumps(route)), wait_until="networkidle")
    page.wait_for_function("document.querySelector('#app').textContent.includes('Supplemental lexical source')")
    with page.expect_download() as download:
        page.locator("#exportcsv").click()
    iquito = list(csv.DictReader(open(download.value.path())))
    profile_rows = [r for r in iquito if r["transcription_source"] == "dictiquito"]
    assert len(iquito) == 382 and len(profile_rows) == 26
    assert all(r["Segments_Source"] == "profile" for r in profile_rows)
    assert all("Source-scoped orthographic profile" in r["Comment"] for r in profile_rows)
    assert not any(r["Segments_Source"] == "profile" for r in iquito if r["transcription_source"] == "huntergatherer")
    route.update(id="gub-sikuani")
    page.goto(url + "#s=" + quote(json.dumps(route)), wait_until="networkidle")
    page.wait_for_function("document.querySelector('#app').textContent.includes('Supplemental lexical source')")
    with page.expect_download() as download:
        page.locator("#exportcsv").click()
    sikuani = list(csv.DictReader(open(download.value.path())))
    supplements = [r for r in sikuani if r["transcription_source"] == "hubercolumbian"]
    assert len(supplements) == 104
    assert not any(r["Form"] == "al fin de la cita" for r in supplements)
    assert all(r["Segments_Source"] == "source" for r in supplements)
    assert not errors, errors
    print(
        "PASS: mixed-source provenance, separate IPA alternatives, stable pronunciation IDs, "
        "Core isolation, corrected dictionary attribution, source-scoped profile and South American supplements"
    )
    browser.close()
