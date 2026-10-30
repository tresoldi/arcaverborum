"""U source dictionaries, retained literal senses, historical witnesses and scoped readings."""
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

    rows = export('kri-kipea')
    assert len(rows) == 16 and all(not r['Segments'] and r['source_gloss'] for r in rows)
    assert any('Mŷcribæ' in r['Form'] and 'ibŷ' in r['Form'] for r in rows)
    legacy = export('unc-kariri-xoco')
    assert len(legacy) == 6 and all('Legacy Wiktionary kzw sample mixes' in r['Comment'] for r in legacy)
    for aid, member, count in [('atl-sereer', '85', 11183), ('atl-ewe', '2476', 13949),
                               ('atl-taabwa', '1972', 2204), ('atl-yasa', '1980', 1440)]:
        selected = [r for r in export(aid) if r['transcription_source'] == 'reflexremaining']
        assert len(selected) == count
        assert all(r['source_language_id'] == 'reflexremaining_' + member for r in selected)
        assert all(not r['concept_id'] and not r['Segments'] and r['source_gloss'] for r in selected)
        assert all(r['mapping_review'] == 'retain_source_sense_unmapped' for r in selected)
        assert all('by-nc-sa' in r['License'] for r in selected)
    selected = [r for r in export('urj-pite-saami') if r['transcription_source'] == 'piteoriginal']
    assert len(selected) == 5547 and all(not r['Segments'] and not r['concept_id'] for r in selected)
    for row in selected:
        original = json.JSONDecoder().raw_decode(row['Comment'])[0]['original']['entry']
        assert 'morphCats' not in original and 'variantOfRefNo' not in original
        assert original['ENG'] == row['source_gloss']
    cayuga = export('iro-cayuga')
    assert sum(r['transcription_source'] == 'cayugaverbs' for r in cayuga) == 1503
    assert sum(r['transcription_source'] == 'cayugaparticles' for r in cayuga) == 373
    for aid, source, added in [('atl-chakali', 'chakalioriginal', 1888),
                                ('atl-central-dagaare', 'dagaareoriginal', 3645),
                                ('afa-beja', 'bejaoriginal', 1015)]:
        selected = [r for r in export(aid) if r['transcription_source'] == source and not r['concept_id']]
        assert len(selected) == added and all(r['Segments_Source'] == 'profile' for r in selected)
        assert all(r['source_gloss'] and r['Segments'] for r in selected)
    selected = [r for r in export('sit-lepcha') if r['transcription_source'] == 'wiktionaryfr202610']
    assert len(selected) == 1224 and sum(r['Segments_Source'] == 'profile' for r in selected) == 565
    assert all(not r['concept_id'] and r['source_gloss'] for r in selected)
    assert sum('Reviewed unmapped affix:' in r['Comment'] for r in selected) == 30
    selected = [r for r in export('pny-woiwurrung') if r['transcription_source'] == 'currupperyarra']
    assert len(selected) == 104 and all(not r['Segments'] for r in selected)
    by_gloss = {r['source_gloss']: r['Form'] for r in selected}
    assert by_gloss['Emu'] == 'baraimal' and by_gloss['Black duck'] == 'tolom'
    assert 'Fish' not in by_gloss and by_gloss['Water'] == 'baarn'
    selected = [r for r in export('tup-tupinamba') if r['transcription_source'] == 'historiatupioriginal']
    assert len(selected) == 262 and all(not r['Segments'] and r['source_gloss'] for r in selected)
    assert any(r['Form'] == 'Ig' and r['source_gloss'] == 'aqua' for r in selected)
    assert not errors, errors
    browser.close()
print('PASS: U source dictionaries, native senses, scoped readings and historical exports')
