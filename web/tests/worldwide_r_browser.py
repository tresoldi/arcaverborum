"""R written pilots, complete upstream attribution and exact profile exports."""
import csv
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))

    def export(aid):
        state = dict(view='variety', id=aid, collection='all', vocab='all')
        page.goto(sys.argv[1] + '#s=' + quote(json.dumps(state)), wait_until='networkidle')
        page.wait_for_function(
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')")
        with page.expect_download() as download:
            page.locator('#exportcsv').click()
        with open(download.value.path()) as handle:
            return list(csv.DictReader(handle))

    for aid, count in [('man-goo', 24), ('afa-buu', 27), ('atl-ndoola', 29)]:
        rows = export(aid)
        assert len(rows) == count
        assert all(r['transcription_source'] == 'reflexrpilots' and not r['Segments'] for r in rows)
        assert all(r['representation_basis'] == 'written_or_unresolved' for r in rows)
        assert all('by-nc-sa' in r['Comment'] for r in rows)
    for aid, source, count in [
        ('dog-ampari-dogon', 'heathdogon', 20), ('wea-seget', 'berrywestpapuan', 17),
        ('wea-kalabra', 'berrywestpapuan', 18), ('afa-maltese', 'spagnolmaltese', 39),
    ]:
        rows = export(aid)
        selected = [r for r in rows if r['transcription_source'] == source]
        assert len(selected) == count
        assert all('native_form' in r['Comment'] and 'upstream_profile_conversion' in r['Comment'] for r in selected)
        assert any(r['transcription_source'] != source for r in rows)
    zapotec = export('oto-isthmus-zapotec')
    selected = [r for r in zapotec if r['source_form_id'] == 'dictdiidxaza_S0534']
    assert len(selected) == 1 and selected[0]['Segments_Source'] == 'profile'
    assert selected[0]['Segments'] == 'm ù n í'
    assert not errors, errors
    browser.close()
print('PASS: R written language pilots, archive terms, full upstream evidence and exact Zapotec tone')
