"""Concept tables query SQLite across families with filtering, sorting and bounded loading."""
import json
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

base = sys.argv[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    manifest = page.request.get(base + 'data/manifest.json').json()
    index = page.request.get(base + manifest['concept_rows']['url']).json()
    family_urls = {spec['url'].split('/')[-1] for spec in manifest['shards'].values()}
    downloaded_families = []
    page.on('request', lambda request: downloaded_families.append(request.url)
            if request.url.split('?')[0].split('/')[-1] in family_urls else None)
    def ready():
        page.wait_for_function("document.querySelector('#conceptentries .exports') || "
                               "document.querySelector('#conceptentries .empty')")
    def count(sql, params=None):
        return page.evaluate("async q=>Number((await query(q.sql,q.params))[0].n)",
                             dict(sql=sql, params=params or []))
    def concept(cid):
        state = dict(view='concept', cid=cid, collection='all', vocab='all', family='', columns=[], page=0)
        page.goto(base + '#s=' + quote(json.dumps(state)), wait_until='networkidle')
        ready()
    concept('bod-hand')
    assert 'Choose a family' not in page.locator('#app').inner_text()
    assert '0 families loaded' in page.locator('#loaded').inner_text()
    expected = index['concepts']['bod-hand']['rows']
    assert count('SELECT COUNT(*) AS n FROM forms WHERE concept_id=?', ['bod-hand']) == expected
    assert page.locator('#conceptentries tbody tr').count() == 50
    assert not downloaded_families
    page.locator('#conceptentries [data-sort="Form"]').click()
    ready()
    forms = page.locator('#conceptentries tbody tr td:nth-child(2)').all_text_contents()
    assert forms == page.evaluate("xs=>[...xs].sort((a,b)=>a.localeCompare(b))", forms)
    page.locator('#family').select_option('Uralic')
    ready()
    variety_links = page.locator('#conceptentries tbody td:nth-child(5) a').evaluate_all(
        "els=>els.map(a=>decodeURIComponent(a.href))")
    assert variety_links and all('urj-' in href for href in variety_links)
    assert not downloaded_families
    with page.expect_download() as downloaded:
        page.locator('#exportmanifest').click()
    exported = json.load(open(downloaded.value.path()))
    assert exported['concept_entries']['cid'] == 'bod-hand'
    assert exported['concept_entries']['index']['sha256'] == manifest['concept_rows']['sha256']
    assert exported['records'] == page.evaluate("async()=>(await scopedRows(' AND concept_id=?',['bod-hand'])).length")
    page.locator('.filter-panel summary').click()
    page.locator('#statusfilter').select_option('source')
    ready()
    assert page.locator('#conceptentries tbody tr').count() > 0
    assert all(text == 'Source-supplied' for text in
               page.locator('#conceptentries tbody td:nth-child(4)').all_text_contents())
    page.locator('.filter-panel summary').click()
    page.locator('#statusfilter').select_option('')
    ready()
    # A form already in concept memory opens without downloading its whole family.
    page.locator('#conceptentries tbody td:nth-child(2) a').first.click()
    page.wait_for_function("document.querySelector('#app').textContent.includes('Provenance')")
    assert not downloaded_families
    # Switching concepts evicts the preceding concept-only rows.
    page.evaluate("()=>navigate({view:'concept',cid:'phy-water',family:'',page:0})")
    ready()
    assert count('SELECT COUNT(*) AS n FROM forms WHERE concept_id=?', ['bod-hand']) == 0
    water_count = count('SELECT COUNT(*) AS n FROM forms WHERE concept_id=?', ['phy-water'])
    assert water_count == index['concepts']['phy-water']['rows']
    assert not downloaded_families
    # Family loading promotes overlapping rows without duplicate forms/memberships.
    families = page.evaluate("()=>[...languages.values()].filter(l=>l.concept_ids.includes('phy-water') && "
                             "l.concept_ids.includes('bod-hand')).map(l=>l.Family||'Unclassified')")
    family = min(families, key=lambda name: manifest['shards'][name]['forms'])
    water_in_family = count('SELECT COUNT(*) AS n FROM forms f JOIN languages l ON l.av_id=f.av_id '
                            'WHERE f.concept_id=? AND l.Family=?', ['phy-water', family])
    assert water_in_family > 0
    page.evaluate("family=>ensure([family])", family)
    assert count('SELECT COUNT(*)-COUNT(DISTINCT ID) AS n FROM forms') == 0
    page.evaluate("()=>navigate({view:'concept',cid:'bod-hand',family:'',page:0})")
    ready()
    assert count('SELECT COUNT(*) AS n FROM forms f JOIN languages l ON l.av_id=f.av_id '
                 'WHERE f.concept_id=? AND l.Family=?', ['phy-water', family]) == water_in_family
    assert count('SELECT COUNT(*)-COUNT(DISTINCT ID) AS n FROM forms') == 0
    assert count('SELECT COUNT(*) AS n FROM (SELECT form_id,set_id,concept_id,source FROM memberships '
                 'GROUP BY form_id,set_id,concept_id,source HAVING COUNT(*)>1)') == 0
    page.set_viewport_size(dict(width=390, height=844))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    # A bad chunk rolls the SQL load back, retaining the preceding valid concept.
    page.evaluate("()=>navigate({view:'concept',cid:'phy-water',family:'',page:0})")
    ready()
    def corrupt(route):
        response = route.fetch()
        body = response.body()
        route.fulfill(response=response, body=b'x' + body[1:])
    page.route('**/bod-hand-000.json.gz', corrupt)
    page.evaluate("()=>navigate({view:'concept',cid:'bod-hand',family:'',page:0})")
    page.wait_for_selector('#app [role="alert"]')
    assert 'checksum mismatch' in page.locator('#app').inner_text()
    assert count('SELECT COUNT(*) AS n FROM forms WHERE concept_id=?', ['phy-water']) == water_count
    page.unroute('**/bod-hand-000.json.gz')
    assert not errors, errors
    browser.close()
print('PASS: automatic cross-family concept SQL tables, filters, sorting, exports, row eviction and family overlap')
