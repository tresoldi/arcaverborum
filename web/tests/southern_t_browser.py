"""T historical written witnesses, finite reading recovery and regional supplements."""
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

    for aid, count, witness in [('cha-charrua', 10, 'Arias1842'),
                                 ('cha-chana', 16, 'Soriano1815'),
                                 ('cha-guenoa', 1, 'Guenoa1787')]:
        rows = export(aid)
        assert len(rows) == count
        assert all(not r['Segments'] and witness in r['source_language_id'] for r in rows)
        assert all('pdf_page' in r['Comment'] for r in rows)
        assert all(r['representation_basis'] == 'written_or_unresolved' for r in rows)
    rows = export('nub-xokleng')
    assert len(rows) == 368
    profiles = {r['Form']: r['Segments'] for r in rows if r['Segments_Source'] == 'profile'}
    assert profiles == {'jan': 'j a n', 'nũl': 'n ũ l', 'zéj': 'ð ɛ j', 'txá': 'tʃ ə'}
    rows = export('pny-woiwurrung-thagungwurrung')
    assert len(rows) == 87
    assert sum(r['transcription_source'] == 'gled' for r in rows) == 58
    original = [r for r in rows if r['transcription_source'] == 'lower_yarraoriginal']
    assert len(original) == 29 and all(not r['Segments'] for r in original)
    assert all('BunceLowerYarra' in r['source_language_id'] for r in original)
    assert not any(r['concept_id'] == 'foo-egg' for r in original)
    for aid, count in [('nub-kaingang', 328), ('pue-puelche', 319),
                       ('tup-mbya-guarani', 284), ('che-tehuelche', 868)]:
        assert len(export(aid)) == count
    assert not errors, errors
    browser.close()
print('PASS: T historical witnesses, reading scopes, preserved GLED and regional exports')
