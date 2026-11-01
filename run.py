from __future__ import annotations
import json, logging, secrets, threading, os
import psycopg
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import main

BASE=Path(__file__).resolve().parent
DATABASE_URL=os.getenv('DATABASE_URL','').strip(); LOG=BASE/'bot.log'; KEY_FILE=BASE/'web_admin.key'; PORT=int(os.getenv('PORT', '8080'))
if not DATABASE_URL: raise RuntimeError('DATABASE_URL environment variable is required')
if KEY_FILE.exists(): KEY=KEY_FILE.read_text().strip()
else:
    KEY=secrets.token_urlsafe(36); KEY_FILE.write_text(KEY); KEY_FILE.chmod(0o600)
root=logging.getLogger(); root.setLevel(logging.INFO)
try:
    fh=logging.FileHandler(LOG,encoding='utf-8'); fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')); root.addHandler(fh)
except Exception: pass
HTML='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tanmay Control</title><style>body{font-family:system-ui;background:#080d18;color:#eee;margin:0;padding:18px}.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}.c{background:#121b2d;border:1px solid #263653;border-radius:16px;padding:16px}.n{font-size:28px;font-weight:800}.row{display:flex;gap:8px;flex-wrap:wrap}button{border:0;border-radius:10px;padding:11px 15px;background:#2d78ff;color:#fff;font-weight:700}.danger{background:#d64b4b}pre{background:#050912;padding:12px;border-radius:12px;max-height:450px;overflow:auto;white-space:pre-wrap}</style><h1>꧁TanmayᎧᎮ᭄꧂ • Control Center</h1><p>One website for bot + website control, groups/channels and automatic logs.</p><div class=g><div class=c>Bot<div id=b class=n>—</div></div><div class=c>Users<div id=u class=n>—</div></div><div class=c>Admins<div id=a class=n>—</div></div><div class=c>Groups/Channels<div id=cx class=n>—</div></div><div class=c>Load<div id=l class=n>—</div></div><div class=c>Maintenance<div id=m class=n>—</div></div></div><div class=c style="margin-top:12px"><h2>Admin Switch</h2><div class=row><button onclick="sw(1)">ON</button><button class=danger onclick="sw(0)">OFF</button><button onclick="tl()">Test log</button></div></div><div class=c style="margin-top:12px"><h2>Groups / Channels</h2><div id=list>Loading…</div></div><div class=c style="margin-top:12px"><h2>All Logs</h2><pre id=logs>Loading…</pre></div><script>const k=new URLSearchParams(location.search).get('key')||'';const H={'X-Admin-Key':k,'Content-Type':'application/json'};async function j(x,o){let r=await fetch(x,o);return r.json()}async function go(){try{let s=await j('/api/status',{headers:H});b.textContent=s.bot;u.textContent=s.users;a.textContent=s.admins;cx.textContent=s.force_chats;l.textContent=s.load??'N/A';m.textContent=s.maintenance?'ON':'OFF';let q=await j('/api/chats',{headers:H});list.innerHTML=q.chats.map(x=>`<div class=c><b>${x.title||'Untitled'}</b><br>${x.chat_type||''} · ${x.username||x.chat_id||''}</div>`).join('')||'No groups/channels';let z=await j('/api/logs',{headers:H});logs.textContent=z.lines.join('\\n')}catch(e){logs.textContent='ERROR '+e}}async function sw(v){await j('/api/maintenance',{method:'POST',headers:H,body:JSON.stringify({enabled:!!v})});go()}async function tl(){await j('/api/log-test',{method:'POST',headers:H,body:'{}'});go()}go();setInterval(go,5000)</script>'''

def send(h,code,obj,ctype='application/json'):
    raw=obj if isinstance(obj,bytes) else obj.encode(); h.send_response(code); h.send_header('Content-Type',ctype); h.send_header('Content-Length',str(len(raw))); h.end_headers(); h.wfile.write(raw)
class H(BaseHTTPRequestHandler):
    def auth(self): return self.headers.get('X-Admin-Key')==KEY or parse_qs(urlparse(self.path).query).get('key',[''])[0]==KEY
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/health': return send(self,200,b'{"ok":true}')
        if not self.auth(): return send(self,401,b'Unauthorized','text/plain')
        if p=='/': return send(self,200,HTML,'text/html; charset=utf-8')
        if p=='/api/status':
            try: load=__import__('os').getloadavg()[0]
            except Exception: load=None
            try:
                with psycopg.connect(DATABASE_URL) as d:
                    n=lambda t:d.execute('select count(*) from '+t).fetchone()[0]
                    maint=(d.execute("select value from settings where key='maintenance'").fetchone() or ['0'])[0]=='1'
                    obj={'ok':True,'bot':'running','users':n('users'),'admins':n('admins'),'force_chats':n('force_channels'),'maintenance':maint,'load':load}
            except Exception as e: obj={'ok':True,'bot':'starting','error':str(e),'users':0,'admins':0,'force_chats':0,'maintenance':False,'load':load}
            return send(self,200,json.dumps(obj))
        if p=='/api/logs':
            try: lines=LOG.read_text(encoding='utf-8',errors='replace').splitlines()[-400:]
            except Exception as e: lines=['LOG ERROR: '+str(e)]
            return send(self,200,json.dumps({'ok':True,'lines':lines}))
        if p=='/api/chats':
            try:
                with psycopg.connect(DATABASE_URL) as d: rows=d.execute('select id,username,title,chat_id,chat_type,invite_link,added_date from force_channels order by id desc').fetchall()
                chats=[dict(id=r[0],username=r[1],title=r[2],chat_id=r[3],chat_type=r[4],invite_link=r[5],added_date=r[6]) for r in rows]
            except Exception: chats=[]
            return send(self,200,json.dumps({'ok':True,'chats':chats}))
        return send(self,404,b'Not found','text/plain')
    def do_POST(self):
        if not self.auth(): return send(self,401,b'Unauthorized','text/plain')
        p=urlparse(self.path).path; n=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(min(n,8192))
        try: data=json.loads(raw or b'{}')
        except Exception: data={}
        if p=='/api/maintenance':
            v='1' if data.get('enabled') else '0'
            with psycopg.connect(DATABASE_URL) as d: d.execute("insert into settings(key,value) values('maintenance',%s) on conflict(key) do update set value=excluded.value",(v,)); d.commit()
            logging.info('WEB ADMIN: maintenance=%s',v); return send(self,200,json.dumps({'ok':True,'maintenance':v=='1'}))
        if p=='/api/log-test': logging.info('WEB ADMIN: log test'); return send(self,200,b'{"ok":true}')
        return send(self,404,b'Not found','text/plain')
    def log_message(self,fmt,*args): logging.info('WEB | '+fmt,*args)

if __name__=='__main__':
    threading.Thread(target=lambda:ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever(),daemon=True).start()
    logging.info('CONTROL WEBSITE: port %s',PORT); logging.info('CONTROL WEBSITE KEY FILE: %s',KEY_FILE)
    app=main.build_application(); logging.info('Starting TANMAY FILE STORE BOT + CONTROL WEBSITE'); app.run_polling(allowed_updates=['message','callback_query'],drop_pending_updates=True)
