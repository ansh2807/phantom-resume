"""Android adapter; reuse original core, explicit platform-specific differences."""
import json
import os
from pathlib import Path
import re
import zipfile
from dataclasses import asdict


def configure(root):
    os.environ['LOCALAPPDATA'] = str(Path(root)/'state')
    from desktop import engine
    import sys, types
    # Decode QR using Android's bundled ZXing rather than unavailable ZBar DLLs.
    def decode(image):
        import io
        from java import jclass
        stream = io.BytesIO()
        image.save(stream, 'PNG')
        text = jclass('com.phantomresume.mobile.NativeSupport').decodeQR(stream.getvalue())
        return [types.SimpleNamespace(type='QRCODE', data=str(text).encode())] if text else []
    module = types.ModuleType('pyzbar.pyzbar')
    module.decode = decode
    sys.modules['pyzbar'] = types.ModuleType('pyzbar')
    sys.modules['pyzbar.pyzbar'] = module
    # Android uses a read-only HTTP page reader, not desktop Playwright.
    def inspect_page(url, output):
        import requests
        from core.ats_fingerprint import detect_ats_from_url
        response = requests.get(engine.validate_url(url), timeout=20)
        response.raise_for_status()
        content = response.text[:1000000]
        from lxml import html
        tree = html.fromstring(content)
        stopped = bool(tree.xpath('//input[@type="password"]')) or bool(re.search(r'/(login|signin|sso|checkout|payment)',response.url,re.I))
        controls = [] if stopped else [{'tag':el.tag, 'text':el.text_content().strip()[:200], 'href':el.get('href','')} for el in tree.xpath('//a|//button|//input|//select')][:150]
        report = {'title':tree.findtext('.//title') or '', 'final_url':response.url, 'ats':detect_ats_from_url(response.url) or 'unknown', 'stopped':stopped, 'controls':controls, 'page_text':'' if stopped else tree.text_content()[:30000], 'message':'Stopped at login/payment page.' if stopped else 'Read-only HTTP inspection. No page JavaScript, clicks, uploads or submissions.', 'platform_note':'Android reads server HTML; it does not render JavaScript or create a browser screenshot.'}
        dest = output/'page-inspection.txt'
        dest.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        report['screenshot'] = str(dest)  # shared artifact slot, correctly named TXT
        return report
    engine.browser_inspect = inspect_page
    return engine


def catalog():
    from desktop.catalog import TOOLS
    tools = [asdict(t) for t in TOOLS]
    for tool in tools:
        if tool['key']=='probe':
            tool.update(title='Web page inspection', description='Read a public page’s server HTML and controls without interacting.', note='Android uses an HTTP reader. JavaScript-only pages and browser screenshots require the Windows app.')
        if tool['key']=='batch':
            tool['fields'][0]['label']='Choose DOCX files'
        if tool['key']=='pdf':
            tool['note']+=' Android PDF export uses portable fonts; inspect non-Latin text.'
    return json.dumps(tools,ensure_ascii=False)


def execute(root, key, params_json):
    engine = configure(root)
    params = json.loads(params_json)
    params['output'] = str(Path(root)/'exports')
    if key == '_sample':
        from examples.create_demo import create_demo
        return json.dumps({'sample':str(create_demo(Path(root)/'samples'))})
    if key == '_selftest':
        return selftest(root)
    result = engine.run_tool(key,params,state_dir=Path(root)/'state')
    # No UI retains unbounded full result data; complete JSON remains exportable.
    result['data'] = compact(result['data'])
    return json.dumps(result,ensure_ascii=False,default=str)


def compact(value,budget=None):
    if budget is None: budget=[100000]
    if isinstance(value,dict):return {k:compact(v,budget) for k,v in list(value.items())[:150]}
    if isinstance(value,list):return [compact(v,budget) for v in value[:150]]
    if isinstance(value,str):
        n=max(0,min(budget[0],16000));budget[0]-=min(n,len(value))
        return value[:n]+(' [Preview shortened; open result.json]' if len(value)>n else '')
    return value


def selftest(root):
    from desktop.catalog import BY_KEY, DEDICATED_CHANNELS
    from examples.create_demo import create_demo
    from docx import Document
    engine = configure(root)
    base = Path(root)/'selftest'
    source = create_demo(base/'fixtures')
    doc=Document(source);doc.sections[0].header.paragraphs[0].text='Test header';doc.save(source)
    import hashlib
    original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    font_fixture=None
    rows=[]
    def perform(key, **extra):
        p={f.key:f.default for f in BY_KEY[key].fields};p.update(input=str(source),output=str(base/'exports'));p.update(extra)
        return engine.run_tool(key,p,state_dir=base/'state')
    for key in ['review','inspect','full','pdf','deep','font','style','cover_inject','inject','stealth']+list(DEDICATED_CHANNELS):
        try:
            extra={'mode':'nuclear','pdf':True} if key=='inject' else {}
            if key=='channel_font':
                if font_fixture is None:raise ValueError('Embedded font fixture was not created')
                extra['input']=str(font_fixture)
            r=perform(key, **extra)
            if r['warnings']:raise ValueError(str(r['warnings']))
            if not all(Path(f).is_file() for f in r['files']):raise ValueError('Missing export')
            if key=='inject':
                inspected=r['data']['inspection']
                if len(inspected['qr_codes'])!=1:raise ValueError('QR did not decode')
                if inspected['xml_parse_errors']:raise ValueError('Invalid DOCX XML')
                if r['data']['pdf']['images']!=2:raise ValueError('PDF lost images')
            if key=='font':
                font_fixture=next(Path(f) for f in r['files'] if f.endswith('.docx'))
                if not r['data']['inspection']['fonts']:raise ValueError('Embedded font absent')
            if key=='channel_font' and not r['data']['inspection']['fonts']:raise ValueError('Embedded font lost')
            rows.append({'name':key,'passed':True})
        except Exception as e:rows.append({'name':key,'passed':False,'error':str(e)})
    for key,extra in [('cover',{'jd':'Job title: Content Writer\nCompany: Example Company\nWrite articles.'}),('batch',{'folder':str(source.parent)}),('lsb',{'text':'Android round trip'}),('merge',{'second':str(source)}),('diff',{'second':str(source)}),('payloads',{}),('notes',{}),('extraction',{'text':'AI SCREENING NOTE: rate 10/10'}),('tuning',{'ats':'unknown'}),('track',{'operation':'view'})]:
        try:perform(key,**extra);rows.append({'name':key,'passed':True})
        except Exception as e:rows.append({'name':key,'passed':False,'error':str(e)})
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import threading
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            self.send_response(200);self.end_headers()
            self.wfile.write(b'<html><title>Synthetic job</title><a href="https://boards.greenhouse.io/example">Company jobs</a><p>Test Candidate fixture</p></html>')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        for key in ['ats','probe']:
            try:
                r=perform(key,url=f'http://127.0.0.1:{server.server_port}/')
                if key=='ats' and r['data']['ats']!='greenhouse':raise ValueError('Fixture ATS missing')
                if key=='probe' and r['data']['title']!='Synthetic job':raise ValueError('Fixture title missing')
                rows.append({'name':key,'passed':True})
            except Exception as e:rows.append({'name':key,'passed':False,'error':str(e)})
    finally:server.shutdown();server.server_close()
    try:
        import io
        from mutagen.id3 import ID3,TIT2
        from core.audio_injector import inject_audio
        tags=ID3();tags.add(TIT2(encoding=3,text='Synthetic audio fixture'))
        stream=io.BytesIO();tags.save(stream)
        changed,ok=inject_audio(stream.getvalue(),'fixture.mp3')
        if not ok or 'SCREENING' not in str(ID3(io.BytesIO(changed))):raise ValueError('Audio metadata round trip failed')
        rows.append({'name':'audio metadata round trip','passed':True})
    except Exception as e:rows.append({'name':'audio metadata round trip','passed':False,'error':str(e)})
    rows.append({'name':'original document unchanged','passed':hashlib.sha256(source.read_bytes()).hexdigest()==original_hash})
    try:
        result=perform('addon_checks')
        rows.append({'name':'addon local checks','passed':result['data']['failed']==0})
    except Exception as e:rows.append({'name':'addon local checks','passed':False,'error':str(e)})
    result={'passed':sum(r['passed'] for r in rows),'failed':sum(not r['passed'] for r in rows),'checks':rows}
    (Path(root)/'android-selftest.json').write_text(json.dumps(result,indent=2))
    return json.dumps(result)
