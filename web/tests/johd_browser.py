"""Original HGN phonemic recovery and explicitly written reconstruction exports."""
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

    rows = export('nad-nadeb')
    assert len(rows) == 110
    original = [r for r in rows if r['transcription_source'] == 'hgnphonemic']
    assert len(original) == 109
    assert sum(r['source_language_id'] == 'hgnphonemic_122' for r in original) == 75
    assert sum(r['source_language_id'] == 'hgnphonemic_121' for r in original) == 34
    bone = [r for r in original if r['concept_id'] == 'bod-bone']
    assert {r['Segments'] for r in bone} == {'k ɨ̰ː ʔ', 'k ə̰ː h'}
    assert all('source_reported_phonemic_citation' in r['Comment'] for r in original)
    assert len([r for r in rows if r['transcription_source'] == 'huntergatherer']) == 1
    rows = export('car-yabarana')
    assert len([r for r in rows if r['transcription_source'] == 'hgnphonemicdepth']) == 20
    for av in ['qwe-proto-quechuan-johd', 'aym-proto-aymaran-johd', 'gua-proto-guaicuruan-johd']:
        rows = export(av)
        assert len(rows) == 20
        assert all(r['Form'].startswith('*') and not r['Segments'] and not r['raw_ipa'] for r in rows)
        assert all(not r['Glottocode'] and 'source_reported_reconstruction' in r['Comment'] for r in rows)
        assert 'analytical reconstruction' in page.locator('#app').inner_text()
        assert all(r['representation_basis'] == 'written_or_unresolved' for r in rows)
    rows = export('tup-akuntsu')
    daughter = next(r for r in rows if r['source_form_id'] == 'tuled_Akuntsu-97-1')
    assert daughter['concept_id'] == 'kin-daughter-of-woman' and daughter['Concepticon_ID'] == '3930'
    assert not errors, errors
    browser.close()
print('PASS: JOHD/HGN dialect scopes, original phonation, written reconstructions and exact daughter mapping')
