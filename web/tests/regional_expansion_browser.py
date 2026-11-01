"""Regional accepted evidence survives browser CSV export and source rendering."""
import csv
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

url = sys.argv[1]
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    for av, count in [('mon-china-buriat',17), ('map-busoa',641), ('map-kaimbulawa',341),
                      ('map-wotu',313), ('sit-wenzhou',556)]:
        page.goto(url + '#s=' + quote(json.dumps(dict(view='variety', id=av, collection='all', vocab='all'))),
                  wait_until='networkidle')
        page.wait_for_function(
            "document.querySelector('#app').textContent.includes('Lexical and transcription evidence')", timeout=120000)
        with page.expect_download() as download:
            page.locator('#exportcsv').click()
        with open(download.value.path()) as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == count, (av, len(rows))
        if av == 'mon-china-buriat':
            assert all(r['transcription_source']=='mongolicbv2026' and not r['Segments']
                       and r['Segments_Source'] not in {'source','profile'} for r in rows)
            assert all('by-nc/4.0' in r['License'] for r in rows)
            assert all('Shinekhen' in r['Comment'] for r in rows)
        elif av.startswith('map-'):
            assert any(r['transcription_source']=='gled' for r in rows)
            assert any(r['transcription_source']=='lexirumahoriginal'
                       and r['evidence_role']=='configured_primary_supported'
                       for r in rows), (av, sorted({r['evidence_role'] for r in rows}))
        else:
            native = next(r for r in rows if r['source_form_id']=='liusinitic_Wenzhou-138_head-1')
            assert native['Form']=='dɤu³⁴¹' and native['Segments_Source']=='source'
        print(av, len(rows))
    assert not errors, errors
    browser.close()
print('PASS: regional written evidence, source authority, GLED retention and native tones')
