"""Community exploration remains bounded, versioned and distinct from local evidence."""
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    url = sys.argv[1] + '#s=' + quote(json.dumps(dict(view='concept', cid='bod-hand', collection='all', vocab='all')))
    page.goto(url, wait_until='networkidle')
    page.wait_for_selector('#colex-view')
    page.select_option('#colex-view', 'community')
    page.wait_for_function(
        "document.querySelector('.colex-graph figcaption')?.textContent.includes('community members')")
    assert page.locator('.colex-network [data-node]').count() <= 31
    assert page.locator('.colex-network line[data-a]').count() <= 465
    assert '0 families loaded' in page.locator('#loaded').inner_text()
    assert 'source namespaces' in page.locator('#colexification').inner_text().lower() or \
        'resource namespaces' in page.locator('#colexification').inner_text().lower()
    page.locator('#colex-community summary').click()
    assert 'not confidence' in page.locator('#colex-community').inner_text()
    assert page.locator('#colex-community a[download]').count() == 2
    page.reload(wait_until='networkidle')
    page.wait_for_selector('#colex-view')
    assert page.locator('#colex-view').input_value() == 'community'
    page.select_option('#colex-layer', 'written')
    page.wait_for_function(
        "document.querySelector('#colex-layer')?.value==='written' && "
        "!document.querySelector('#colex-neighbors')?.textContent.includes('Loading')")
    assert page.locator('#colex-view').count() == 0
    page.select_option('#colex-layer', 'segmented')
    page.wait_for_selector('#colex-view')
    page.set_viewport_size(dict(width=390, height=844))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+2')
    assert not errors, errors

    # Corruption in a community sidecar is rejected before it can be displayed.
    def corrupt(route):
        response = route.fetch()
        route.fulfill(response=response, body=response.text() + ' ')
    page.route('**/data/colexification-communities/**/bod-hand.json', corrupt)
    page.goto(url, wait_until='networkidle')
    page.reload(wait_until='networkidle')
    page.wait_for_selector('#colexification [role="alert"]')
    assert 'declared limit' in page.locator('#colexification').inner_text() or \
        'checksum' in page.locator('#colexification').inner_text().lower()
    browser.close()
print('Community browser checks passed')
