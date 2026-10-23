"""Screenshot a sanitized copy of .env; raw values never enter the browser."""
from pathlib import Path
from html import escape
import re
from playwright.sync_api import sync_playwright

APP=Path(__file__).resolve().parents[1]
target=APP/'docs/images/env-redacted.png'
target.parent.mkdir(parents=True,exist_ok=True)
settings=[]
original_values=[]
for line in (APP/'.env').read_text(encoding='utf-8-sig').splitlines():
    match=re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$',line)
    if not match:
        continue
    key,value=match.groups()
    if len(value.strip())>8:
        original_values.append(value.strip().strip('\"\''))
    safe=value.strip() if key=='PORT' and re.fullmatch(r'\d{1,5}',value.strip()) and 1<=int(value.strip())<=65535 else '[REDACTED]'
    settings.append((key,safe))
if not settings:
    raise SystemExit('No environment assignments found.')
rows=''.join(f'<div class="row"><span class="number">{i}</span><code><span class="key">{escape(key)}</span>=<span class="value">{escape(value)}</span></code></div>' for i,(key,value) in enumerate(settings,1))
html='''<!doctype html><meta charset="utf-8"><style>*{box-sizing:border-box}body{margin:0;padding:30px;background:#edf7ff;font-family:Arial,sans-serif;color:#090d3b}main{border:1px solid #cddff0;border-radius:20px;background:#fff;overflow:hidden}header{padding:22px 28px;border-bottom:1px solid #d7e7f5;font-size:25px;font-weight:bold}header span{float:right;font-size:20px;color:#075cae}section{background:#112342;padding:28px 20px;color:#e2edff}.row{display:flex;gap:22px;line-height:2}.number{color:#9cadc7;width:36px;text-align:right;font:22px/2 Consolas,monospace}.row code{font:24px/2 Consolas,monospace}.key{color:#a8d4ff}.value{color:#a5e6bd}footer{padding:20px 28px;font-size:21px;line-height:1.6;color:#193269}strong{color:#075cae}</style><main><header>.env <span>C02 · local configuration</span></header><section>'''+rows+'''</section><footer><strong>Sanitized snapshot of the current local .env</strong><br>All values except PORT are redacted, including API keys and resource IDs.<br>Use your own values locally. The real .env remains excluded from Git.</footer></main>'''
if any(value and value in html for value in original_values):
    raise SystemExit('Sanitization check failed; no screenshot generated.')
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1280,'height':800},device_scale_factor=1)
    page.set_content(html)
    page.locator('main').screenshot(path=str(target))
    browser.close()
print('Saved docs/images/env-redacted.png with non-PORT values redacted before rendering.')
