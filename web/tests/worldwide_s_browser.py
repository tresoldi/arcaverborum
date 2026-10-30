"""S original dictionaries, written pilots, source layers and named-lect exports."""
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

    for aid, count in [('atl-gaa', 50), ('atl-gula-iro', 21), ('atl-ginyanga', 36)]:
        rows = export(aid)
        assert len(rows) == count
        assert all(not r['Segments'] and 'by-nc-sa' in r['Comment'] for r in rows)
        assert all(r['representation_basis'] == 'written_or_unresolved' for r in rows)
    for aid, source, count, retained in [
        ('atl-chakali', 'chakalioriginal', 51, 44),
        ('atl-central-dagaare', 'dagaareoriginal', 62, 33),
        ('afa-beja', 'bejaoriginal', 41, 116),
    ]:
        rows = export(aid)
        selected = [r for r in rows if r['transcription_source'] == source]
        assert len(selected) == count and all(r['Segments_Source'] == 'profile' for r in selected)
        assert sum(r['transcription_source'] == 'gled' for r in rows) == retained
        assert all('raw_block' in r['Comment'] for r in selected)
    rows = export('map-welaun')
    assert len(rows) == 47
    assert all('upstream_profile_conversion' in r['Comment'] for r in rows)
    assert all('Local_Orthography' in r['Comment'] and 'Form_according_to_Source' in r['Comment'] for r in rows)
    rows = export('ine-tuatschin')
    assert len(rows) == 38
    assert sum(r['Segments_Source'] == 'profile' for r in rows) == 36
    assert all(r['source_language_id'] == 'tuatschinoriginal_Dictionary' for r in rows)
    assert all('raw_block' in r['Comment'] and 'surs1244' == r['Glottocode'] for r in rows)
    rows = export('man-goo')
    assert len(rows) == 24 and sum(r['Segments_Source'] == 'profile' for r in rows) == 11
    assert any('̋' in r['Segments'] for r in rows)
    rows = export('pny-bulloo-river')
    selected = [r for r in rows if r['transcription_source'] == 'kullillioriginal']
    assert len(selected) == 22 and sum(r['Segments_Source'] == 'profile' for r in selected) == 20
    assert all('pdf_page' in r['Comment'] for r in selected)
    assert not errors, errors
    browser.close()
print('PASS: S original-source primaries, preserved GLED, source layers, scoped varieties and readings')
