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

    for aid, count in [("atl-wamey", 20), ("atl-gimnime", 20)]:
        rows = export(aid)
        assert len(rows) == count
        assert all(not r["Segments"] and r["Segments_Source"] == "unclean" for r in rows)
        assert all("by-nc-sa/4.0" in r["License"] and "attribution" in r["Comment"] for r in rows)
    rows = export("atl-gyele")
    assert len(rows) == 228
    assert sum(r["transcription_source"] == "gled" for r in rows) == 36
    original = [r for r in rows if r["transcription_source"] == "gyelioriginal"]
    assert sum(r["Segments_Source"] == "profile" for r in original) == 191
    assert sum(not r["Segments"] for r in original) == 1
    assert all(
        "native_sha256" in r["Comment"] and r["mapping_review"] != "source mapping; no local review recorded"
        for r in original
    )
    rows = export("afa-hdi")
    assert len(rows) == 77 and sum(r["transcription_source"] == "gled" for r in rows) == 32
    assert sum(r["Segments_Source"] == "profile" for r in rows) == 45
    barking = next(r for r in rows if r["source_form_id"] == "hdioriginal_senses-SN000306")
    assert barking["concept_id"] == "ani-barking"
    rows = export("man-bambara")
    added = [r for r in rows if r["transcription_source"] == "westafricanoriginal"]
    assert len(added) == 17 and all(r["Segments_Source"] == "profile" for r in added)
    assert all(any(t in r["Segments"] for t in "áàéèíìóòúùɛ́ɔ́") for r in added)
    child = next(r for r in added if r["source_form_id"].endswith("Bambara-46_child-1"))
    assert "ẽ́" in child["Segments"] and "déⁿ" in child["Value"]
    rows = export("atl-kam")
    assert len(rows) == 30 and all(r["Segments_Source"] == "profile" for r in rows)
    assert all("M-tone" in r["Comment"] and "by-nc-sa/4.0" in r["License"] for r in rows)
    assert next(r for r in rows if r["Form"] == "kpár")["concept_id"] == "phy-rain-raining"
    rows = export("atl-fwe")
    assert len(rows) == 189 and sum(r["transcription_source"] == "gled" for r in rows) == 47
    assert sum(r["Segments_Source"] == "profile" for r in rows) == 141
    rows = export("afa-sidamo")
    assert len(rows) == 94 and sum(r["transcription_source"] == "gled" for r in rows) == 49
    original = [r for r in rows if r["transcription_source"] == "sidaamaoriginal"]
    assert len(original) == 45 and all(r["Segments_Source"] == "profile" for r in original)
    assert all("lx_SidIPA" in r["Comment"] and "source_reported_phonemic_citation" in r["Comment"] for r in original)
    skin = next(r for r in original if r["Form"] == "duli")
    assert not skin["concept_id"] and skin["mapping_review"] == "unmap"
    cold = next(r for r in original if r["Form"] == "ganʃo")
    assert cold["concept_id"] == "bod-common-cold"
    rows = export("atl-mom-jango")
    assert len(rows) == 70 and all(r["Glottocode"] == "vere1252" for r in rows)
    legacy = [r for r in rows if r["transcription_source"] == "gled"]
    assert len(legacy) == 37 and all(r["source_language_id"] == "gled_MOMI" for r in legacy)
    assert "Momi (Vere Kaadam)" in page.locator("#app").inner_text()
    rows = export("atl-ikizu")
    shashi = [r for r in rows if r["source_language_id"] == "tls_ShashiSiz"]
    assert len(shashi) == 30 and all("upstream_profile_conversion" in r["Comment"] for r in shashi)
    assert any("(okw)" in r["Value"] or "(oku)" in r["Value"] for r in shashi)
    assert not errors, errors
    print("PASS: African dictionaries, reading/semantic recovery, stable Momi identity, Gimnime and Shashi scopes")
    browser.close()
