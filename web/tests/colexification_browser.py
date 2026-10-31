"""Bounded concept neighborhoods, evidence integrity, source distinctions and missingness."""
import json
import math
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
    assert panel.locator('svg circle').count() <= 31
    assert panel.locator('svg .colex-neighbor-edge').count() > 0
    assert panel.locator('line[data-a]').count() <= 465
    lines = panel.locator('line[data-a]')
    family_widths = lines.evaluate_all(
        "els=>els.map(e=>[Number(e.dataset.strength),Number(e.getAttribute('stroke-width'))])")
    for count, width in family_widths:
        assert abs(width - (1 + .8 * math.log2(1 + count))) < 1e-10
    assert 'same scale across concepts' in panel.locator('.colex-strength-legend').inner_text()
    edge = lines.first
    edge.focus()
    page.keyboard.press('Enter')
    assert 'known families' in panel.locator('#colex-graph-selection').inner_text()
    panel.locator('#colex-weight').select_option('varieties')
    ready()
    assert 'accepted varieties' in panel.locator('.colex-strength-legend').inner_text()
    assert lines.evaluate_all("els=>els.some(e=>Number(e.dataset.strength)>1)")
    page.reload(wait_until='networkidle')
    ready()
    assert panel.locator('#colex-weight').input_value() == 'varieties'
    panel.locator('#colex-weight').select_option('languages')
    ready()
    assert 'known language units' in panel.locator('.colex-strength-legend').inner_text()
    panel.locator('#colex-weight').select_option('families')
    ready()
    viewport = panel.locator('.colex-viewport')
    panel.locator('#colex-zoom-in').click()
    assert 'scale(1.25)' in viewport.get_attribute('transform')
    panel.locator('#colex-reset').click()
    assert 'scale(1)' in viewport.get_attribute('transform')
    focus = panel.locator('svg [data-node="0"]')
    before = focus.get_attribute('transform')
    point = focus.locator('circle').bounding_box()
    page.mouse.move(point['x'] + point['width'] / 2, point['y'] + point['height'] / 2)
    page.mouse.down()
    page.mouse.move(point['x'] + 45, point['y'] + 35, steps=5)
    page.mouse.up()
    assert focus.get_attribute('transform') != before
    assert page.locator('#colex-counts').count() == 1  # dragging does not navigate
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
