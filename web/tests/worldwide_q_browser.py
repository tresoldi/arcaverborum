"""Q recovery, locality, preservation and written-first source exports."""
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

    for aid, count in [('ine-afrikaans', 75), ('ine-sranan-tongo', 42), ('map-brunei', 38)]:
        supplied = [r for r in export(aid) if r['transcription_source'] == 'wiktionary']
        assert len(supplied) == count and all(r['raw_ipa'] for r in supplied)
    for aid in ['atl-gimme', 'atl-basa-benue']:
        rows = export(aid)
        assert len(rows) == 24 and all(not r['Segments'] for r in rows)
        assert all(r['transcription_source'] == 'reflexqdict' for r in rows)
        assert all(r['Segments_Source'] == 'unclean' for r in rows)
    rows = export('ine-northern-frisian')
    mooring = [r for r in rows if r['transcription_source'] == 'wiktionary']
    assert len(mooring) == 33
    assert all(json.loads(r['pronunciation_tags']) == ['Mooring'] for r in mooring)
    assert len([r for r in rows if r['transcription_source'] == 'gled']) == 43
    for aid, oldsource, retained, newsource, count, unmapped in [
        ('atl-ruuli', 'wiktionary', 6, 'ruruulioriginal', 116, 4),
        ('sit-chintang', 'lsi', 85, 'dictchintang', 26, 2),
    ]:
        rows = export(aid)
        old = [r for r in rows if r['transcription_source'] == oldsource]
        new = [r for r in rows if r['transcription_source'] == newsource]
        assert len(old) == retained and sum(not r['concept_id'] for r in old) == unmapped
        assert len(new) == count
        assert all(r['preferred_source'] == newsource for r in new if r['Segments_Source'] == 'profile')
        if aid == 'atl-ruuli':
            assert all(not r['Segments'] for r in new)
            assert all(not r['raw_ipa'] for r in old)
    rows = export('afa-kabyle')
    letter = next(r for r in rows if r['Form'] == 'asekkil')
    assert not letter['concept_id'] and letter['raw_ipa'] == '/asəkːil/'
    rows = export('afa-coptic')
    written = [r for r in rows if r['transcription_source'] == 'copticsahidic']
    assert len(written) == 72 and all(not r['Segments'] for r in written)
    assert not errors, errors
    browser.close()
print('PASS: Q reading recovery, written pilots, Mooring scope, native preservation and sense correction')
