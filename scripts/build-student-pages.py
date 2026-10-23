"""Build C02's student pages from its actual TypeScript and browser source."""
from pathlib import Path
from html import escape
from textwrap import dedent

APP=Path(__file__).resolve().parents[1]
PUBLIC=APP/'public'


def code(file,start=None,end=None):
    source=(APP/file).read_text(encoding='utf-8')
    if start is None:
        return source.strip()
    at=source.index(start)
    stop=source.index(end,at) if end else len(source)
    prefix=source[source.rfind('\n',0,at)+1:at]
    return dedent((prefix if not prefix.strip() else '')+source[at:stop]).strip()


def snippet(file,text,explanation):
    return f'<figure class="code-example"><figcaption>{escape(file)} · source excerpt</figcaption><pre><code class="language-typescript">{escape(text)}</code></pre><p class="code-explanation">{escape(explanation)}</p></figure>'


def pre(text):
    return '<pre><code>'+escape(text)+'</code></pre>'


def step(title,body):
    return '<li><div class="step-content"><h3>'+title+'</h3>'+body+'</div></li>'


NAV='''<nav class="student-nav" aria-label="Lesson sections">
<a href="/guide.html#learning">What you will learn</a>
<a href="/guide.html#run-guide">How to run the application</a>
<a href="/architecture.html">Architecture &amp; workflow</a>
<a href="/#comparison-lab" class="lab-link">Comparison lab ↗</a></nav>'''


def page(title,heading,subtitle,content):
    return f'''<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C02 · {escape(title)}</title><link rel="stylesheet" href="/style.css"></head><body><main>
<div class="course-bar"><div class="course-title">How <span>Claude Managed Agents</span> Works</div><span class="course-tag">CONCEPT 02 / 60</span></div>
<header><div><p class="eyebrow">LESSON C02 / {escape(title.upper())}</p><h1>{heading}</h1><p class="intro">{subtitle}</p></div><div class="header-controls"><div class="hero-art"><img src="/astronaut.png" alt=""><span>LESSON C02<br>AGENT SURFACES</span></div><button id="themeToggle" class="secondary theme-toggle" type="button" aria-pressed="false">Switch to dark mode</button></div></header>
{NAV}{content}{NAV.replace('aria-label="Lesson sections"','aria-label="Continue learning"')}
</main><script src="/navigation.js"></script></body></html>'''


goals=[
 ('Choose the agent surface','Compare the Messages API with Managed Agents using the same reservation task. Identify who drives iteration and who retains conversation history.'),
 ('Keep the effect on the host','Both paths call the same local reserveStock handler. The model requests an operation; the host validates inputs and changes the seeded inventory.'),
 ('Build a manual tool loop','Read tool_use blocks, execute each requested call, append assistant calls and correlated tool_result records, then request the next model response.'),
 ('Answer managed custom tools','Create a session, open observation before sending a prompt, handle agent.custom_tool_use, and correlate the result with custom_tool_use_id.'),
 ('Understand setup and session state','Create or reuse an agent and environment. Distinguish a reusable configuration, a new session, the browser SSE stream, and provider events.'),
 ('Verify success and partial failure','Inspect reservation IDs, error results, final stock, and reported stop reasons. A model summary or a Done badge is not proof that every item was reserved.')]
cards=''.join(f'<article class="learning-card"><span class="concept-number">{i:02}</span><h3>{title}</h3><p>{body}</p></article>' for i,(title,body) in enumerate(goals,1))
run_steps=[
 step('Open the C02 application folder','<p>Use Node.js 24 or newer with npm. From the <strong>presentations</strong> folder:</p>'+pre('cd .\\lesson-c02\\lesson-c02-app\nnpm install')+'<p>If your terminal is already in the folder containing this app’s package.json, run only npm install.</p>'),
 step('Create .env without overwriting it','<p>Preserve existing configuration. Otherwise copy the template, then open .env in your editor:</p>'+pre('if (!(Test-Path .env)) { Copy-Item .env.example .env }')+pre('ANTHROPIC_API_KEY=your_api_key\nCLAUDE_MODEL=claude-opus-5-5\nPORT=3000')+'<p>The API key stays on the server. CLAUDE_MODEL selects the model; use one available to your workspace. C01 and C02 both default to port 3000, so stop the other app or choose a different PORT.</p>'),
 step('Prepare the managed resources once','<p>The manual flow needs only API access. For the managed flow, your workspace also needs Managed Agents access. If you do not have suitable resources:</p>'+pre('npm run managed:setup')+'<p>This creates an environment and an agent with the reserveStock custom tool, then writes .managed-ids.json. Save and reuse those resources. To select compatible existing resources, use MANAGED_AGENT_ID and MANAGED_ENVIRONMENT_ID in .env instead. The agent must expose the custom tool expected by this app.</p>'),
 step('Start the app and open the browser',pre('npm start')+'<p>Wait for the ready address, then open <code>http://127.0.0.1:3000</code>. <code>npm run dev</code> starts the same server. Keep the terminal open and restart after editing .env.</p>'),
 step('Run the same request through both surfaces','<p>Choose <strong>Happy path</strong> and click <strong>Run both</strong>. The app runs manual first, then managed, resetting the seed inventory for each flow. Follow the host tool calls in both columns. You can also run either column separately. Each run uses the real Claude API and may incur charges.</p><blockquote>Reserve 2 astronaut mugs (SKU-100) and 1 rocket hoodie (SKU-200), then summarize.</blockquote>'),
 step('Inspect evidence and compare failures','<p>The happy path should leave 10 mugs, 2 hoodies, and 0 lamps. Read tool results and the final stock table. Try <strong>Out of stock</strong> and <strong>Partial failure</strong>: a failed reservation should not subtract stock, but an earlier successful reservation is not rolled back.</p><p>Use one run at a time; inventory is shared process memory, not a durable warehouse. Visiting a guide does not cancel remote work. This sample has no interrupt control; do not retry an uncertain run blindly. Ctrl+C stops the local server.</p>')]
guide=f'''<section id="learning" class="student-section" aria-labelledby="learning-title"><div class="student-heading"><p class="eyebrow">YOUR LEARNING GOALS</p><h2 id="learning-title">What you will learn</h2><p>One warehouse task, two agent surfaces. Explain what changes and what remains the host’s responsibility.</p></div><div class="learning-grid">{cards}</div><p class="learning-outcome"><strong>By the end:</strong> you can trace the manual and managed tool-result protocols and justify the result using host evidence.</p></section>
<div class="guide-pager"><a href="#run-guide">Next: how to run the application →</a></div>
<section id="run-guide" class="student-section run-guide" aria-labelledby="run-title"><div class="student-heading"><p class="eyebrow">FROM SETUP TO YOUR FIRST COMPARISON</p><h2 id="run-title">How to run this application</h2><p>Follow these PowerShell steps. Keep resource setup separate from repeated application runs.</p></div><ol class="run-steps">{''.join(run_steps)}</ol><a class="guide-start" href="/#comparison-lab">Open the comparison lab ↗</a></section>'''
(PUBLIC/'guide.html').write_text(page('Student guide','Understand both loops.<br><span>Compare the evidence.</span>','Learn the concepts, configure the app, and follow both tool protocols using the same local handler.',guide),encoding='utf-8')

setup_steps=[
 step('Configure dependencies and the API key','<p>From the C02 app directory:</p>'+pre('npm install\nif (!(Test-Path .env)) { Copy-Item .env.example .env }')+'<p>Set ANTHROPIC_API_KEY in .env. The npm commands load .env into the host process. For a manual-only run, resource creation is not required.</p>'),
 step('Create the environment, then the custom-tool agent','<p>Run <code>npm run managed:setup</code> only when new resources are needed. C02 creates the cloud environment first, then registers an agent with the host-side reserveStock custom tool.</p>'+snippet('src/managed-setup.ts',code('src/managed-setup.ts','const environment =','const ids ='),'This is the actual setup order. Only a custom tool is registered: the reservation effect remains on the host rather than running in the cloud workspace.')),
 step('Save or override the resource IDs',snippet('src/managed-setup.ts',code('src/managed-setup.ts','const ids ='),'The setup script writes the returned agent and environment IDs to the local ID file. This file is excluded from Git.')+snippet('src/shared.ts',code('src/shared.ts','export function loadManagedIds()'),'Optional MANAGED_AGENT_ID and MANAGED_ENVIRONMENT_ID values take precedence over the saved file. These C02 variable names differ from C01.')+'<p>Reuse both IDs with a compatible custom-tool agent. Repeating setup creates another environment and agent; a session is created later during a managed run.</p>'),
 step('Start the comparison application',pre('npm start')+'<p>Open <code>http://127.0.0.1:3000</code>, or the configured PORT. The environment record describes a reusable configuration; creating it alone does not prove a command ran inside a cloud container.</p>')]

walk=[
 step('Choose a flow and open browser SSE',snippet('public/lab.js',code('public/lab.js','  function run(flow) {','  async function guarded('),'The browser opens a new run through /api/run. On a stream drop it closes EventSource rather than letting a reconnect start another reservation run.')+snippet('src/server.ts',code('src/server.ts','      const emit: Emit =','      } catch (err)'),'The local host runs the selected implementation and forwards structured progress records as SSE. The two flows share a result format, not the same provider protocol.')),
 step('Manual: own the messages array and model calls',snippet('src/flows/manual.ts',code('src/flows/manual.ts','  const messages:','    if (res.stop_reason === "tool_use")'),'The host initializes messages[] and drives a loop of at most ten model calls. Each call includes its locally retained history and the strict tool declaration.')),
 step('Manual: execute each requested tool',snippet('src/flows/manual.ts',code('src/flows/manual.ts','      const calls =','      // 3 · Keep the history:'),'The model can request multiple calls. The host runs reserveStock and pairs each result with the original tool_use_id. The schema is not a replacement for host validation.')),
 step('Manual: append results and continue',snippet('src/flows/manual.ts',code('src/flows/manual.ts','      messages.push','    if (res.stop_reason === "refusal")'),'The assistant call and the user tool-result message both enter history. continue triggers another model call. Non-tool stop reasons and the loop limit still need interpretation; a returned text response is not proof that every reservation succeeded.')),
 step('Managed: create, observe, then send',snippet('src/flows/managed.ts',code('src/flows/managed.ts','  const session =','  let stopReason ='),'The managed path creates a new session using reusable resources. It opens the provider stream before sending user.message. This provider stream is separate from the browser-to-host SSE connection.')),
 step('Managed: answer the custom-tool request',snippet('src/flows/managed.ts',code('src/flows/managed.ts','      case "agent.custom_tool_use":','      case "session.status_idle":'),'The same host handler executes the effect. The result is a user.custom_tool_result whose custom_tool_use_id is the requested event ID. The session manages the next model turn; no manual messages[] array is maintained here.')),
 step('Both paths: validate before changing inventory',snippet('src/inventory.ts',code('src/inventory.ts','export function reserveStock('),'The host rejects invalid quantities, unknown products, and insufficient stock. Only a successful call subtracts units and allocates a reservation ID. This in-memory sample has no durable idempotency ledger or transaction rollback across several calls.')),
 step('Managed: interpret idle and retained history',snippet('src/flows/managed.ts',code('src/flows/managed.ts','      case "session.status_idle":','      case "session.error":'),'requires_action keeps the stream consumer running while tool work is answered. Another idle reason or termination ends this sample runner; that is not a blanket assertion of business success.')+snippet('src/flows/managed.ts',code('src/flows/managed.ts','  const history ='),'The provider retains session history. The displayed counter is history.data.length from the first listed page, not an automatically paginated total. A retained session is not archived by this code.')),
 step('Render the returned evidence',snippet('public/lab.js',code('public/lab.js','      case "tool": {','      case "assistant":'),'The UI uses host-returned reservation results to show success or failure. Those values are escaped before being inserted into the timeline.')+snippet('public/lab.js',code('public/lab.js','      case "done": {','      case "error":'),'The Done badge means the runner reported done. Compare the stock table and tool error records before concluding that the whole request succeeded. Run both executes the two flows sequentially in one browser.'))]

def diagram(kind,title,description):
    return f'''<section class="student-section" aria-labelledby="{kind}-title"><div class="student-heading"><p class="eyebrow">UML / {kind.upper()} PATH</p><h2 id="{kind}-title">{title}</h2><p>{description}</p></div><figure class="uml-figure"><div class="diagram-scroll" tabindex="0" role="region" aria-label="Scrollable {kind} sequence diagram"><img class="uml-image" src="/architecture-{kind}.svg" alt="UML sequence for the C02 {kind} tool path; the numbered code walkthrough below is its text equivalent."></div><figcaption>Read calls from top to bottom. Dashed arrows return data; open arrows deliver events. The inventory handler is local host code even though it has its own lane. On mobile, scroll sideways to keep labels readable.</figcaption></figure><div class="student-nav diagram-links" aria-label="{kind} diagram files"><a href="/architecture-{kind}.svg" target="_blank" rel="noopener">Open full size ↗</a><a href="/architecture-{kind}.svg" download>Download SVG</a><a href="/architecture-{kind}.png" download>Download PNG</a></div></section>'''

architecture='<section id="prerequisites" class="student-section" aria-labelledby="prerequisites-title"><div class="student-heading"><p class="eyebrow">STEP 0 / PREPARE THE MANAGED PATH</p><h2 id="prerequisites-title">Create or reuse the agent and environment</h2><p>Resource setup is separate from the comparison run. Complete it once, then reuse the IDs.</p></div><ol class="run-steps">'+''.join(setup_steps)+'</ol><div class="student-nav"><a href="#manual-title">Manual sequence ↓</a><a href="#managed-title">Managed sequence ↓</a><a href="#walkthrough">Code walkthrough ↓</a></div></section>'
architecture+=diagram('manual','The host drives the tool loop','The host calls Messages, interprets tool_use, runs reserveStock, and appends results to its own messages array.')
architecture+=diagram('managed','The session drives the next turn','The host opens the session stream, answers custom-tool requests locally, and observes agent and lifecycle events.')
architecture+='<section id="walkthrough" class="student-section" aria-labelledby="walkthrough-title"><div class="student-heading"><p class="eyebrow">CONNECT THE DIAGRAMS TO THE SOURCE</p><h2 id="walkthrough-title">Walk through the application step by step</h2><p>These are excerpts from the actual implementation. Read the source files for the complete surrounding handlers.</p></div><ol class="run-steps">'+''.join(walk)+'</ol><p class="learning-outcome"><strong>Explain it back:</strong> which code changes stock, which layer owns history, and why can an ordinary completed run still contain a failed reservation?</p></section>'
(PUBLIC/'architecture.html').write_text(page('Architecture & workflow','One host-side effect.<br><span>Two different loops.</span>','Use the setup walkthrough, UML sequence diagrams, and actual code snippets to follow both agent surfaces.',architecture),encoding='utf-8')
print('Built C02 guide and architecture: 6 learning goals, 6 run steps, 4 prerequisites, 9 code steps.')
