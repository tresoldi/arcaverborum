"""Check reviewed Wiktionary primary slices and retained GLED in browser exports."""

import csv
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

url = sys.argv[1]
expected = {"alg-yurok": 54, "nor-ternate": 66, "ine-corsican": 16, "ine-lombard": 42}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(accept_downloads=True)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    for aid, count in expected.items():
        page.goto(
            url + "#s=" + quote(json.dumps(dict(view="variety", id=aid, collection="all", vocab="all"))),
            wait_until="networkidle",
        )
        page.wait_for_function(
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')", timeout=120000
        )
        with page.expect_download() as dl:
            page.locator("#exportcsv").click()
        with open(dl.value.path()) as f:
            rs = list(csv.DictReader(f))
        ws = [r for r in rs if r["transcription_source"] == "wiktionary"]
        assert len(ws) == count, (aid, len(ws))
        assert all(r["raw_ipa"] and r["Segments_Source"] == "source" for r in ws)
        assert any(r["transcription_source"] == "gled" for r in rs)
        if aid == "ine-lombard":
            assert sum(r["pronunciation_tags"] == '["Milanese"]' for r in ws) == 39
        print(aid, len(rs), "rows;", len(ws), "Wiktionary supplied readings")
    assert not errors, errors
    b.close()
print("PASS: reviewed source preference, retained GLED, supplied IPA and Milanese scope in live exports")
