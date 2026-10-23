"""Create editable UML infographics for the actual two C02 protocols."""
from pathlib import Path
from html import escape

PUBLIC=Path(__file__).resolve().parents[1]/'public'


def build(kind,title,provider,subtitle,messages,conclusion):
    height=560+len(messages)*62
    p=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="{height}" viewBox="0 0 1320 {height}" role="img" aria-labelledby="title description">
<title id="title">C02 — {escape(title)}</title><desc id="description">{escape(subtitle)} Five participant lanes show the student, browser, Node host, remote provider, and local inventory handler. The architecture page includes the code and text equivalent.</desc>
<defs><marker id="call" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="10" markerHeight="10" orient="auto"><path d="M0 0 L12 6 L0 12 Z" fill="#193269"/></marker><marker id="open" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="10" markerHeight="10" orient="auto"><path d="M1 1 L11 6 L1 11" fill="none" stroke="#193269" stroke-width="2"/></marker></defs>
<rect x="1" y="1" width="1318" height="{height-2}" rx="26" fill="#fff" stroke="#d7e7f5" stroke-width="2"/>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#090d3b}}</style>''']
    def text(x,y,value,size=26,color='#193269',bold=False):
        p.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" style="fill:{color}">{escape(value)}</text>')
    def box(x,y,w,h,fill):
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="#d7e7f5" stroke-width="2"/>')
    text(34,48,'LESSON C02 / '+kind.upper()+' TOOL WORKFLOW',26,'#0872d4',True)
    text(34,102,title,42,'#090d3b',True)
    text(34,145,subtitle,26)
    roles=[(140,'Student','Browser user','#edf7ff'),(400,'Browser UI','public/lab.js','#edf7ff'),
           (660,'Node.js host','TypeScript + SDK','#f3edff'),(920,provider,'Remote API','#eaf8f1'),
           (1180,'Inventory','Local host code','#f3edff')]
    bottom=350+(len(messages)-1)*62
    for x,name,detail,fill in roles:
        box(x-113,191,226,94,fill)
        text(x-100,231,name,27,'#090d3b',True)
        text(x-100,269,detail,26)
        p.append(f'<line x1="{x}" y1="285" x2="{x}" y2="{bottom+28}" stroke="#97aac1" stroke-width="2" stroke-dasharray="7 7"/>')
    for i,(a,b,label,mode) in enumerate(messages,1):
        y=350+(i-1)*62
        if a==b:
            p.append(f'<path d="M{a} {y-18} h42 v24 h-42" fill="none" stroke="#193269" stroke-width="2.5" marker-end="url(#call)"/>')
            text(a+54,y-1,f'{i}. '+label)
        else:
            dash=' stroke-dasharray="9 7"' if mode=='return' else ''
            marker='call' if mode=='call' else 'open'
            p.append(f'<line x1="{a}" y1="{y}" x2="{b}" y2="{y}" stroke="#193269" stroke-width="2.5"{dash} marker-end="url(#{marker})"/>')
            text(min(a,b)+10,y-12,f'{i}. '+label)
    box(27,bottom+62,1266,72,'#eaf8f1')
    text(45,bottom+107,conclusion,27,'#056b4b',True)
    text(43,bottom+179,'Solid arrow: request    ·    Dashed arrow: returned data    ·    Open arrow: event',26)
    text(43,bottom+218,'The local host executes reserveStock in both flows. No cloud inventory tool is used.',26)
    p.append('</svg>')
    (PUBLIC/f'architecture-{kind}.svg').write_text('\n'.join(p),encoding='utf-8')


build('manual','Your host drives the tool round trip.','Messages API',
      'One illustrated tool round trip; the host may repeat it or handle several requested calls.',[
 (140,400,'Run manual','call'),(400,660,'GET /api/run','call'),
 (660,920,'messages.create','call'),(920,660,'tool_use + ID','return'),
 (660,1180,'reserveStock(input)','call'),(1180,660,'Checked result','return'),
 (660,660,'Append history','call'),(660,920,'messages.create','call'),
 (920,660,'Final response','return'),(660,400,'SSE steps + stock','event'),
 (400,140,'Reply + evidence','return')],
 'Host owns messages[] → correlate tool_result → call the model again; max 10 calls.')

build('managed','The session drives the next model turn.','Managed Agents',
      'The host observes custom-tool requests and returns results tied to the requested event.',[
 (140,400,'Run managed','call'),(400,660,'GET /api/run','call'),
 (660,920,'Create session','call'),(920,660,'Session ID','return'),
 (660,920,'Open stream','call'),(660,920,'user.message','call'),
 (920,660,'Custom tool use','event'),(660,1180,'reserveStock(input)','call'),
 (1180,660,'Checked result','return'),(660,920,'Custom result','call'),
 (920,660,'Agent message','event'),(920,660,'Idle + stop reason','event'),
 (660,920,'events.list','call'),(920,660,'History first page','return'),
 (660,400,'SSE steps + stock','event'),(400,140,'Reply + evidence','return')],
 'Stream before send → return user.custom_tool_result → provider retains session history.')
print('Built both C02 UML sequence infographics.')
