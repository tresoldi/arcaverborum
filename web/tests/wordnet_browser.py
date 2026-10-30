"""Sense links work without downloading a lexical family; exports retain types."""
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

    def concept(cid):
        state = dict(view='concept', cid=cid, collection='all', vocab='all')
        page.goto(sys.argv[1] + '#s=' + quote(json.dumps(state)), wait_until='networkidle')
        page.wait_for_selector('section[aria-label="WordNet sense links"]')
        return page.locator('section[aria-label="WordNet sense links"]')

    panel = concept('phy-water')
    assert 'oewn-14869913-n' in panel.inner_text()
    assert 'exact match' in panel.inner_text()
    assert '0 families loaded' in page.locator('#loaded').inner_text()
    with page.expect_download() as download:
        panel.get_by_text('Links CSV', exact=True).click()
    with open(download.value.path()) as handle:
        rows = list(csv.DictReader(handle))
    assert any(r['concept_id'] == 'phy-water' and r['relation'] == 'exact' for r in rows)
    assert any(r['status'] == 'source_association' for r in rows)
    assert not any(r['status'] == 'candidate' for r in rows)
    panel = concept('kin-child')
    assert panel.get_by_text('narrower match', exact=True).count() == 2
    panel = concept('cog-know-something')
    assert panel.get_by_text('narrower match', exact=True).count() == 2
    panel = concept('agr-grass')
    assert panel.get_by_text('related match', exact=True).count() == 1
    panel = concept('phy-moon')
    assert 'oewn-09381123-n' in panel.inner_text()
    assert 'Inherited association' in panel.inner_text()
    panel = concept('cog-who')
    assert 'No reviewed matching pronoun' in panel.inner_text()
    assert panel.locator('details').count() == 0
    panel = concept('act-pull-up')
    assert 'Merged catalog entry' in page.locator('#app').inner_text()
    assert 'No accepted mapping' in panel.inner_text()
    panel = concept('agr-alang-alang-grass')
    assert 'WordNet sense links' in panel.inner_text()
    state = dict(view='concepts', collection='all', vocab='all', term='oewn-14869913-n')
    page.goto(sys.argv[1] + '#s=' + quote(json.dumps(state)), wait_until='networkidle')
    page.wait_for_selector('#conceptsearch')
    assert 'water' in page.locator('#app').inner_text().lower()
    assert not errors, errors
    browser.close()
print('PASS: WordNet senses, typed relations, separate candidates, downloads and identifier search')
