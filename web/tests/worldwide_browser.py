"""Optional worldwide evidence/export check against a served accepted build."""

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
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')",
            timeout=120000,
        )
        with page.expect_download() as download:
            page.locator("#exportcsv").click()
        with open(download.value.path()) as f:
            return list(csv.DictReader(f))

    rows = export("sit-zaiwa")
    sky = next(r for r in rows if r["source_form_id"] == "suntb_Atsi-1_sky-1")
    assert "²¹" in sky["Segments"] and "upstream_profile_conversion" in sky["Comment"]
    rows = export("ine-palula")
    assert len(rows) == 151 and sum(r["transcription_source"] == "gled" for r in rows) == 108
    profiles = [r for r in rows if r["transcription_source"] == "dictpalula"]
    assert len(profiles) == 43 and all(r["Segments_Source"] == "profile" for r in profiles)
    eye = next(r for r in profiles if r["concept_id"] == "bod-eye")
    assert "îː" in eye["Segments"] and "Phonetic" in eye["Comment"] and "by/4.0" in eye["License"]
    rows = export("yam-nen")
    assert len(rows) == 498
    original = [r for r in rows if r["transcription_source"] == "dictnen"]
    assert len(original) == 42 and all(r["Segments_Source"] == "profile" for r in original)
    assert all("epenthetic" in r["Comment"] for r in original)
    rows = export("map-teop")
    assert len(rows) == 325
    original = [r for r in rows if r["transcription_source"] == "dictteop"]
    assert len(original) == 58
    moon = next(r for r in original if r["concept_id"] == "phy-moon")
    assert "ɔː" in moon["Segments"] and "non-standardization" in moon["Comment"]
    rows = export("map-wanukaka")
    original = [r for r in rows if r["transcription_source"] == "dictwanukaka"]
    assert len(original) == 33 and all(not r["Segments"] for r in original)
    assert all("quantity" in r["Comment"] for r in original)
    rows = export("chi-bribri")
    original = [r for r in rows if r["source_pronunciation_id"].startswith("original-")]
    assert len(original) == 10 and all(r["raw_ipa"] for r in original)
    all_word = next(r for r in original if r["concept_id"] == "qua-all")
    assert "w̃" in all_word["Segments"] and "ã́" in all_word["Segments"]
    assert json.loads(all_word["pronunciation_tags"]) == ["A"]
    rows = export("ine-lombard")
    milanese = [r for r in rows if r["pronunciation_tags"] == '["Milanese"]']
    assert len(milanese) == 39 and all(r["raw_ipa"] for r in milanese)
    iron = [r for r in milanese if r["concept_id"] == "act-iron"]
    assert len(iron) == 2 and len({r["source_pronunciation_id"] for r in iron}) == 2
    for aid, count in [("ine-rvid-travo", 9), ("ine-rvid-lugo", 15), ("ine-rvid-ascrea", 35)]:
        rows = export(aid)
        assert len(rows) == count and all(not r["Glottocode"] for r in rows)
        assert all("gpl-3.0" in r["License"] and '"morphology_cell": "INF"' in r["Comment"] for r in rows)
    rows = export("ela-elamite")
    old = [r for r in rows if r["transcription_source"] == "idssegmented"]
    assert len(old) == 787 and all("Original IDS Elamite context" in r["Comment"] for r in old)
    uncertain = next(r for r in old if r["source_form_id"] == "idssegmented_elamite-3-180-1")
    assert "EW 111" in uncertain["Comment"] and "EW 499" in uncertain["Comment"]
    assert "ba-at (?)-ir" in uncertain["Comment"] and uncertain["Form"] == "ba-at_-ir"
    rows = export("etr-etruscan")
    viku = next(r for r in rows if r["source_form_id"] == "wikt_805165")
    assert not viku["concept_id"] and "CIE3234" in viku["Comment"]
    rows = export("pid-broome-pearling-lugger-pidgin")
    assert len(rows) == 11 and all(not r["Segments"] for r in rows)
    assert all(r["Glottocode"] == "broo1238" and r["source_language_id"] == "wikt_bpl" for r in rows)
    assert len([r for r in rows if r["Form"] == "-kaa"]) == 2
    rows = export("art-esperanto")
    pointer = next(r for r in rows if r["source_form_id"] == "wikt_222195")
    assert not pointer["concept_id"] and pointer["mapping_review"] == "shared unmap"
    rows = export("nak-sanzhi-dargwa")
    assert len(rows) == 20 and all(r["Glottocode"] == "sanz1248" for r in rows)
    assert all(r["source_language_id"] == "dictsanzhi_dar" and r["Segments_Source"] == "profile" for r in rows)
    rows = export("afa-biblical-aramaic-bhsa")
    assert len(rows) == 5 and all(not r["Segments"] and not r["Glottocode"] for r in rows)
    assert all("by-nc/4.0" in r["License"] and '"verse"' in r["Comment"] for r in rows)
    rows = export("web-kalamang")
    original = [r for r in rows if r["transcription_source"] == "dictkalamang"]
    assert len(original) == 30 and all(r["Segments_Source"] == "profile" for r in original)
    avocado = next(r for r in original if r["concept_id"] == "foo-avocado")
    assert "t̚" in avocado["Segments"] and "Pronunciation" in avocado["Comment"]
    for aid, count in [("nua-aro-mukweym-orok", 5), ("nua-kombio", 2), ("nua-mufian", 1)]:
        original = [r for r in export(aid) if r["transcription_source"] == "wiktionary"]
        assert len(original) == count and all(not r["Segments"] for r in original)
    rows = export("art-esperanto")
    for source_id in ["wikt_100686", "wikt_177077", "wikt_382169"]:
        corrected = next(r for r in rows if r["source_form_id"] == source_id)
        assert not corrected["concept_id"] and corrected["mapping_review"] == "shared unmap"
    assert not errors, errors
    browser.close()
print("PASS: worldwide profiles, original IPA recovery, locality scope, ancient context and semantic corrections")
