"""Browser checks; --live additionally exercises both real Claude API flows."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
OUT=APP/'teaching-material/student-guide-preview'
OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument('--live',action='store_true')
args=parser.parse_args()
port=34102
base=f'http://127.0.0.1:{port}'
log=(OUT/'server.log').open('w',encoding='utf-8')
server=subprocess.Popen(['node','--env-file-if-exists=.env','node_modules/tsx/dist/cli.mjs','src/server.ts'],cwd=APP,
    env={**os.environ,'PORT':str(port)},stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
report={}
try:
    for _ in range(100):
        if server.poll() is not None:
            raise RuntimeError('Preview server exited; inspect the ignored local server log')
        try:
            with opener.open(base+'/api/config',timeout=1) as response:
                config=json.load(response)
            break
        except OSError:
            time.sleep(.2)
    else:
        raise RuntimeError('Preview server readiness timeout')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        for kind in ['manual','managed']:
            response=page.goto(base+f'/architecture-{kind}.svg',wait_until='networkidle')
            assert response.ok and 'image/svg+xml' in response.headers['content-type']
            bad=page.locator('svg text').evaluate_all('nodes=>nodes.filter(n=>{const b=n.getBBox();const s=n.ownerSVGElement.viewBox.baseVal;return b.x<0||b.x+b.width>s.width||b.y+b.height>s.height}).map(n=>n.textContent)')
            assert not bad,bad
            page.locator('svg').screenshot(path=str(APP/f'public/architecture-{kind}.png'))
        page.goto(base,wait_until='networkidle')
        page.wait_for_function('document.querySelector("#model").textContent!=="…"')
        assert page.locator('#run-both').is_enabled()
        assert min(page.locator('#prompt, #run-both, #run-manual, #run-managed, [data-sample]').evaluate_all('nodes=>nodes.map(n=>parseFloat(getComputedStyle(n).fontSize))'))>=18
        page.screenshot(path=str(OUT/'C02-Comparison-Lab.png'),full_page=True)
        prompt='Remember this prompt while I read the guide.'
        page.locator('#prompt').fill(prompt)
        page.locator('.student-nav a[href="/guide.html#learning"]').click()
        page.wait_for_url(base+'/guide.html#learning')
        assert page.locator('#learning .learning-card').count()==6
        assert page.locator('#run-guide .run-steps>li').count()==6
        page.locator('#learning').screenshot(path=str(OUT/'C02-What-You-Will-Learn.png'))
        page.locator('#run-guide').screenshot(path=str(OUT/'C02-How-To-Run.png'))
        page.locator('#themeToggle').click()
        page.locator('.student-nav[aria-label="Lesson sections"] a[href="/architecture.html"]').click()
        page.wait_for_url(base+'/architecture.html')
        assert page.locator('html').get_attribute('data-theme')=='dark'
        assert page.locator('#prerequisites .run-steps>li').count()==4
        assert page.locator('#walkthrough .run-steps>li').count()==9
        for step in page.locator('#walkthrough .run-steps>li').all():
            assert step.locator('pre code').count()>0
        minimum=min(page.locator('.code-example code').evaluate_all('nodes=>nodes.map(n=>parseFloat(getComputedStyle(n).fontSize))'))
        assert minimum>=19
        page.locator('#prerequisites').screenshot(path=str(OUT/'C02-Prerequisites-Dark.png'))
        page.locator('#themeToggle').click()
        page.evaluate('scrollTo(0,0)')
        page.screenshot(path=str(OUT/'C02-Architecture-Page.png'))
        page.locator('#walkthrough .run-steps>li').nth(4).screenshot(path=str(OUT/'C02-Code-Walkthrough.png'))
        for kind in ['manual','managed']:
            assert page.locator(f'img[src="/architecture-{kind}.svg"]').evaluate('e=>e.complete&&e.naturalWidth===1320')
            response=page.request.get(base+f'/architecture-{kind}.png')
            assert response.ok and response.headers['content-type']=='image/png'
        for width in [390,768,1024]:
            page.set_viewport_size({'width':width,'height':844})
            for path in ['/guide.html#run-guide','/architecture.html','/#comparison-lab']:
                page.goto(base+path,wait_until='networkidle')
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),f'Overflow: {width}px {path}'
            if width==390:
                page.goto(base+'/architecture.html',wait_until='networkidle')
                page.screenshot(path=str(OUT/'C02-Architecture-Mobile.png'))
                assert page.locator('.diagram-scroll').first.evaluate('e=>e.scrollWidth>e.clientWidth')
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(base,wait_until='networkidle')
        assert page.locator('#prompt').input_value()==prompt

        # Authored browser frames exercise rendering without pretending the
        # fixture is a model response or a real inventory operation.
        requested=[]
        stock=[{'sku':'SKU-100','name':'Astronaut mug','initial':12,'available':10},
               {'sku':'SKU-200','name':'Rocket hoodie','initial':3,'available':2},
               {'sku':'SKU-300','name':'Moon lamp','initial':0,'available':0}]
        def fixture(route):
            from urllib.parse import parse_qs,urlparse
            flow=parse_qs(urlparse(route.request.url).query)['flow'][0]
            requested.append(flow)
            frames=[{'type':'start','flow':flow,'prompt':'Authored browser fixture','model':'Fixture'},
                    {'type':'tool','trigger':'fixture','input':{'sku':'SKU-100','quantity':2},'result':json.dumps({'ok':True,'reservationId':'FIXTURE','remaining':10})},
                    {'type':'assistant','text':'<img src=x onerror="window.c02Injected=true">'},
                    {'type':'done','stats':[{'label':'fixture evidence','value':'authored'}],'stock':stock,'ms':25}]
            route.fulfill(status=200,content_type='text/event-stream',body=''.join('data: '+json.dumps(frame)+'\n\n' for frame in frames))
        page.route('**/api/run?*',fixture)
        page.locator('#run-both').click()
        page.wait_for_function('!document.querySelector("#run-both").disabled',timeout=20000)
        assert requested==['manual','managed']
        assert page.evaluate('window.c02Injected') is None
        for flow in ['manual','managed']:
            assert 'Done' in page.locator(f'#col-{flow} .status').inner_text()
            assert page.locator(f'#col-{flow} .stock tbody tr td:last-child').all_inner_texts()==['10','2','0']
        page.unroute('**/api/run?*')
        page.locator('#clear').click()
        report.update(desktop='passed',mobileWidths=[390,768,1024],navigation='passed',theme='passed across pages',
            promptPreservation='passed without automatic replay',codeFontMinimumPx=minimum,
            umlExports='SVG and PNG verified',fixture='authored browser SSE; ordering, rendering, and HTML escaping passed')
        if args.live:
            if not config.get('managedReady'):
                raise RuntimeError('Real managed flow needs configured resources')
            page.locator('[data-sample]').first.click()
            print('Starting actual C02 manual and managed runs, sequentially.',flush=True)
            page.locator('#run-both').click()
            page.wait_for_function('!document.querySelector("#run-both").disabled',timeout=240000)
            for flow in ['manual','managed']:
                status=page.locator(f'#col-{flow} .status').inner_text()
                if 'Done' not in status:
                    raise RuntimeError(flow+' live flow failed: '+page.locator(f'#col-{flow} .timeline').inner_text()[-800:])
                values=page.locator(f'#col-{flow} .stock tbody tr td:last-child').all_inner_texts()
                assert values==['10','2','0'],(flow,values)
            report['live']={'source':'actual Claude API operations; not fixture','manual':'passed','managed':'passed',
                            'remainingStock':[10,2,0],'managedSession':page.locator('#col-managed .session').inner_text().strip()}
            (OUT/'live-verification.json').write_text(json.dumps(report['live'],indent=2),encoding='utf-8')
            page.locator('.flows').screenshot(path=str(OUT/'C02-Actual-Live-Comparison.png'))
            print('Both actual flows passed; remaining stock 10 mugs, 2 hoodies, 0 lamps.',flush=True)
            page.set_viewport_size({'width':390,'height':844})
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),'Live result overflow'
        assert not errors,errors
        report['browserErrors']=errors
        browser.close()
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('C02 student pages and comparison checks passed.',flush=True)
finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
    log.close()
