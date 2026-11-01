"""The BAG counterexample is corrected and reported/model evidence stays distinct."""
import gzip
import json
import sys
from urllib.parse import quote, urljoin

from playwright.sync_api import sync_playwright

url=sys.argv[1]
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    page=browser.new_page()
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    release=page.request.get(urljoin(url,'data/manifest.json')).json()
    network_url=urljoin(url,release['colexification']['url'])
    network=page.request.get(network_url).json()
    assert network['policy']['algorithm']=='arca-whole-form-colexification-v2'
    assert 0<network['stats']['backbone_edges']<next(
        r['edges'] for r in network['stats']['networks'] if r['layer']=='segmented' and r['kind']=='observed')
    node=page.request.get(urljoin(network_url,network['nodes']['act-bag']['url'])).json()
    for spec in node['layers']['segmented']['observed']['pages']:
        edges=page.request.get(urljoin(network_url,spec['url'])).json()['edges']
        assert all(edge['concept_id']!='rel-witch' for edge in edges)
        assert all('assessment' in edge for edge in edges)
    entry_url=urljoin(url,release['concept_rows']['url'])
    entries=page.request.get(entry_url).json()
    form_index=release['fields'].index('Form')
    for spec in entries['concepts']['act-bag']['pages']:
        rows=json.loads(gzip.decompress(page.request.get(urljoin(entry_url,spec['url'])).body()))
        assert not any(row[form_index] in {'antaruxa','lurpia'} for row in rows)
    state=dict(view='concept',cid='act-bag',collection='all',vocab='all')
    page.goto(url+'#s='+quote(json.dumps(state)),wait_until='networkidle')
    page.wait_for_selector('.colex-assessment',timeout=120000)
    assert page.locator('#colex-weight').input_value()=='robust'
    assert 'not a p-value' in page.locator('.colex-strength-legend').inner_text()
    assert 'Mapping and replication' in page.locator('#colex-neighbors').inner_text()
    assert not errors,errors
    browser.close()
print('PASS: BAG/WITCH regression, candidate/model distinction, bounded strength and concept entries')
