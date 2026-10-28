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
    assert len(iquito) == 425 and len(profile_rows) == 69
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
    route.update(id="sit-bangru")
    page.goto(url + "#s=" + quote(json.dumps(route)), wait_until="networkidle")
    page.wait_for_function("document.querySelector('#app').textContent.includes('Lexical and transcription evidence')")
    with page.expect_download() as download:
        page.locator("#exportcsv").click()
    bangru = list(csv.DictReader(open(download.value.path())))
    assert len(bangru) == 99 and {r["transcription_source"] for r in bangru} == {"bodtbangru"}
    assert all(r["Segments_Source"] == "source" and not r["Cognacy"] for r in bangru)
    assert all('"speaker": "A"' in r["Comment"] and "pdf_sha256" in r["Comment"] for r in bangru)
    # Primary replacement preserves GLED evidence and isolates its new profile.
    for aid, total, derived, legacy in [("nub-xerente", 159, 120, 38), ("nub-xavante", 154, 107, 46),
                                        ("nub-ingain", 26, 26, 0), ("nub-panara", 70, 39, 31),
                                        ("nub-apinaye", 120, 79, 40)]:
        route.update(id=aid)
        page.goto(url + "#s=" + quote(json.dumps(route)), wait_until="networkidle")
        page.wait_for_function(
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')"
        )
        assert "gerardije2025" in page.locator("#app").inner_text()
        with page.expect_download() as download:
            page.locator("#exportcsv").click()
        lexical = list(csv.DictReader(open(download.value.path())))
        study = [r for r in lexical if r["transcription_source"] == "gerardije2025"]
        assert len(lexical) == total and len(study) == derived
        assert sum(r["transcription_source"] == "gled" for r in lexical) == legacy
        assert all(r["Segments_Source"] == "profile" and not r["Cognacy"] for r in study)
        assert all("original_row_sha256" in r["Comment"] for r in study)
        if aid == "nub-xerente":
            cross = next(r for r in study if r["source_form_id"] == "gerardije2025_658")
            assert cross["concept_id"] == "mot-traverse" and "atravessar" in cross["Comment"]
        assert not any(r["Segments_Source"] == "profile" for r in lexical
                       if r["transcription_source"] != "gerardije2025")
    for aid, total, counts in [("pan-mastanahua", 63, {"amazonianvoices": 37}),
                                ("tup-tupinamba", 320, {"tuled": 49, "lundgrenomagoa": 28})]:
        route.update(id=aid)
        page.goto(url + "#s=" + quote(json.dumps(route)), wait_until="networkidle")
        page.wait_for_function("document.querySelector('#app').textContent.includes('Supplemental lexical source')")
        with page.expect_download() as download:
            page.locator("#exportcsv").click()
        lexical = list(csv.DictReader(open(download.value.path())))
        assert len(lexical) == total
        for source_name, count in counts.items():
            selected = [r for r in lexical if r["transcription_source"] == source_name]
            assert len(selected) == count and all(r["Segments_Source"] == "source" for r in selected)
        if aid == "tup-tupinamba":
            tuled = {r["concept_id"] for r in lexical if r["transcription_source"] == "tuled"}
            lundgren = {r["concept_id"] for r in lexical if r["transcription_source"] == "lundgrenomagoa"}
            assert not tuled & lundgren
    assert not errors, errors
    print(
        "PASS: mixed-source provenance, separate IPA alternatives, stable pronunciation IDs, "
        "Core isolation, corrected dictionary attribution, source-scoped profile, "
        "South American supplements, original-source Bangru, Jê profile isolation, GLED replacements and Ingain"
    )
    browser.close()
