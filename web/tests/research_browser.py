"""Optional end-to-end check: uv run --with playwright python web/tests/research_browser.py URL."""
import gzip
import json
import sys
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8799/'
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    metadata = page.request.get(urljoin(url, 'data/manifest.json')).json()
    catalog_response = page.request.get(urljoin(url, metadata['catalog']['url'])).body()
    catalog_data = json.loads(gzip.decompress(catalog_response))
    core_count = sum(bool(row['core_collection']) for row in catalog_data['languages'])
    page.goto(url, wait_until='networkidle')
    page.wait_for_function("n => document.querySelector('#counts').textContent.includes(n)",
                           arg=f'{metadata["counts"]["forms"]:,}', timeout=60000)
    page.wait_for_selector('[data-select]')
    assert page.locator('#collection').input_value() == 'all'
    page.locator('#collection').select_option('core')
    page.wait_for_function("n => document.querySelector('#app').textContent.includes(n)", arg=f'{core_count:,} matches')
    page.reload()
    page.wait_for_function("n => document.querySelector('#app').textContent.includes(n)",
                           arg=f'{core_count:,} matches', timeout=60000)
    page.locator('#collection').select_option('all')
    page.locator('#varietysearch').fill('Vach')
    page.wait_for_timeout(600)
    page.locator('[data-select="urj-vach-vasjugan"]').check()
    page.wait_for_timeout(200)
    page.locator('#nav a').filter(has_text='Compare').click()
    page.wait_for_selector('#comparisonconcepts')
    page.locator('#comparisonconcepts').select_option(['kin-i', 'phy-water'])
    page.wait_for_selector('#buildmatrix')
    page.locator('#buildmatrix').click()
    page.wait_for_selector('#matrix table', timeout=120000)
    assert page.locator('#matrix tbody tr').count() == 2
    with page.expect_download() as download:
        page.locator('#exportmanifest').click()
    exported = json.loads(open(download.value.path()).read())
    assert exported['records'] >= 2
    assert exported['filters']['selected'] == ['urj-vach-vasjugan']
    assert len(exported['source_files']['forms.csv']) == 64
    with page.expect_download() as download:
        page.locator('#exportcsv').click()
    csv_text = open(download.value.path()).read()
    assert 'source_form_id' in csv_text and 'mapping_review' in csv_text and 'License' in csv_text
    page.locator('#matrix .matrixform a').first.click()
    page.wait_for_function("document.querySelector('#app').textContent.includes('Provenance')")
    assert 'view' in page.url and 'form' in page.url
    assert page.locator('#app').inner_text().count('source') > 0
    # Coverage additions shift aggregate row numbers; old links must still
    # resolve an unambiguous variety/source-form identity.
    legacy = page.evaluate("JSON.parse(decodeURIComponent(location.hash.slice(3)))")
    legacy['id'] = legacy['id'].rsplit(':', 1)[0] + ':999999999'
    page.evaluate("s => history.replaceState(null,'','#s='+encodeURIComponent(JSON.stringify(s)))", legacy)
    page.reload()
    page.wait_for_function("document.querySelector('#app').textContent.includes('Provenance')", timeout=120000)
    page.get_by_role('link', name='← Vach-Vasjugan', exact=True).click()
    page.wait_for_selector('#varietymap path.leaflet-interactive')
    geography = page.locator('#varietymap path.leaflet-interactive').first
    assert geography.get_attribute('fill-opacity') == '1'
    assert float(geography.get_attribute('stroke-width')) >= 1
    assert 'Linguistic identity' in page.locator('#app').inner_text()
    assert 'Source version' in page.locator('#app').inner_text()
    page.locator('#segmentinventory summary').click()
    assert 'not a verified phoneme inventory' in page.locator('#segmentinventory').inner_text()
    page.go_back()
    page.wait_for_function("document.querySelector('#app').textContent.includes('Provenance')")
    page.go_back()
    page.wait_for_selector('#comparisonconcepts')
    page.locator('#family').select_option('Uralic')
    page.locator('#nav a').filter(has_text='Search').click()
    page.locator('#formsearch').fill('a')
    page.locator('#formsearch').press('Tab')
    page.wait_for_timeout(200)
    page.locator('#runsearch').click()
    page.wait_for_selector('#searchresults table', timeout=60000)
    assert 'matches' in page.locator('#searchresults').inner_text()
    page.locator('#nav a').filter(has_text='SQL').click()
    page.locator('#sqlquery').fill('PRAGMA query_only=OFF')
    page.locator('#runsql').click()
    page.wait_for_function("document.querySelector('#activity').textContent.includes('schema-inspection')")
    page.locator('#sqlquery').fill('SELECT COUNT(*) AS n FROM forms')
    page.locator('#runsql').click()
    page.wait_for_selector('#sqlresults table')
    page.locator('#nav a').filter(has_text='Map').click()
    page.wait_for_selector('.leaflet-container')
    page.wait_for_selector('[data-legend]')
    page.locator('[data-legend]').last.click()
    page.locator('#nav a').filter(has_text='Varieties').click()
    page.set_viewport_size({'width': 390, 'height': 844})
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    page.locator('#app a').first.focus()
    assert page.evaluate("document.activeElement.tagName") == 'A'
    page.emulate_media(color_scheme='dark', reduced_motion='reduce')
    page.screenshot(path='/tmp/arca-research-mobile.png')
    assert not errors, errors
    print('PASS: collection scopes, URL restoration, comparison, provenance, CSV/manifest export, '
          'variety metadata/inventory, legacy form links, search, read-only SQL, map contrast, mobile, keyboard links')
    browser.close()
