"""Bounded concept neighborhoods, evidence integrity, source distinctions and missingness."""
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))

    def concept(cid):
        state = dict(view='concept', cid=cid, collection='all', vocab='all')
        page.goto(sys.argv[1] + '#s=' + quote(json.dumps(state)), wait_until='networkidle')
        page.wait_for_selector('#colex-counts')
        page.wait_for_function("!document.querySelector('#colex-neighbors').textContent.includes('Loading')")
        return page.locator('#colexification')

    def ready():
        page.wait_for_selector('#colex-neighbors')
        page.wait_for_function("!document.querySelector('#colex-neighbors').textContent.includes('Loading')")

    panel = concept('bod-hand')
    assert '0 families loaded' in page.locator('#loaded').inner_text()
    assert panel.locator('svg circle').count() <= 13
    assert 0 < panel.locator('tbody tr').count() <= 40
    assert 'lexical filters do not change' in panel.inner_text()
    panel.locator('tbody details').first.locator('summary').click()
    assert 'Comparison basis:' in panel.locator('tbody details').first.inner_text()
    assert 'Source forms:' in panel.locator('tbody details').first.inner_text()
    panel.locator('#colex-kind').select_option('inferred')
    ready()
    assert 'one underspecified slot' in panel.inner_text()
    assert 'Not applicable' in panel.locator('tbody').inner_text()
    assert '"colexKind":"inferred"' in page.evaluate('decodeURIComponent(location.hash)')
    page.reload(wait_until='networkidle')
    ready()
    assert panel.locator('#colex-kind').input_value() == 'inferred'
    panel.locator('tbody details').first.locator('summary').click()
    assert 'not two independently recorded' in panel.locator('tbody details').first.inner_text()
    panel.locator('#colex-kind').select_option('observed')
    ready()
    panel.locator('#colex-strong').check()
    ready()
    for cell in panel.locator('tbody tr td:nth-child(2)').all():
        assert int(cell.inner_text()) >= 3
    panel.locator('#colex-layer').select_option('written')
    ready()
    assert 'Citation forms' in panel.inner_text()
    panel.locator('#colex-layer').select_option('reduced')
    ready()
    assert 'ASJP' in panel.inner_text()
    panel = concept('agr-alang-alang-grass')
    assert 'No usable segmented records' in panel.inner_text()
    assert panel.locator('svg').count() == 0
    panel = concept('act-pull-up')
    assert 'Merged concept; excluded' in panel.inner_text()
    panel = concept('bod-arm-or-hand')
    assert 'slot is underspecified' in panel.inner_text()
    page.set_viewport_size(dict(width=390, height=844))
    panel = concept('bod-hand')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')

    def corrupt(route):
        response = route.fetch()
        body = response.body()
        route.fulfill(response=response, body=b' ' + body[1:])

    page.route('**/phy-fire.json', corrupt)
    state = dict(view='concept', cid='phy-fire', collection='all', vocab='all')
    page.goto(sys.argv[1] + '#s=' + quote(json.dumps(state)), wait_until='networkidle')
    page.wait_for_selector('#colexification [role="alert"]')
    assert 'checksum mismatch' in page.locator('#colexification').inner_text()
    assert 'WordNet sense links' in page.locator('#app').inner_text()
    page.unroute('**/phy-fire.json')
    assert not errors, errors
    browser.close()
print('PASS: colexification scopes, bounded ego networks, evidence, missingness, mobile and integrity rejection')
