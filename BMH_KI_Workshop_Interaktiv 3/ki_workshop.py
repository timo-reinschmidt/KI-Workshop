#!/usr/bin/env python3
"""Interaktiver BMH-KI-Workshop: lokale Live-Umfrage ohne Cloud und ohne pip."""
from __future__ import annotations
import csv, io, json, os, secrets, socket, sys, threading, webbrowser, os
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

BASE = Path(__file__).resolve().parent
QUESTIONS = json.loads((BASE / 'fragen.json').read_text(encoding='utf-8'))
PARTS = {1:'KI oder Mensch? · Ratespiel',2:'Warm-up: Wie stehen wir zu KI?',3:'Einsatzmöglichkeiten bei BMH',4:'Interaktive Übung: Grün, Gelb oder Rot?'}
assert len({q['id'] for q in QUESTIONS})==len(QUESTIONS)
assert all(q['type'] in ('wordcloud','choice','multi','scenario','detect') and q['part'] in PARTS for q in QUESTIONS)
PORT = int(os.environ.get("PORT",sys.argv[1] if len(sys.argv)>1 else 8765))
CLOUD = os.environ.get("RENDER","").lower() == "true" or bool(os.environ.get("RENDER_EXTERNAL_HOSTNAME"))
KEY = os.environ.get("ADMIN_KEY") or secrets.token_urlsafe(28)
SESSION = secrets.token_urlsafe(12)
LOCK = threading.RLock()
STATE = {'index':0,'open':True,'reveal':False,'generation':0,'votes':{q['id']:{} for q in QUESTIONS},'players':{},'scored':[]}

def find_ip():
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
            s.connect(('1.1.1.1',80)); return s.getsockname()[0]
    except OSError:
        try: return socket.gethostbyname(socket.gethostname())
        except OSError: return '127.0.0.1'
JOIN_URL = ('https://' + os.environ['RENDER_EXTERNAL_HOSTNAME'] + '/') if os.environ.get('RENDER_EXTERNAL_HOSTNAME') else os.environ.get('PUBLIC_URL', 'http://{}:{}/'.format(find_ip(),PORT))

def public_question(q, reveal=False):
    return {k:v for k,v in q.items() if k not in ('solution','reason','safer') or reveal}

def stats(q):
    votes=list(STATE['votes'][q['id']].values())
    if q['type']=='wordcloud':
        lower=Counter(str(v).casefold() for v in votes)
        display={str(v).casefold():v for v in votes}
        return {'total':len(votes),'words':[{'label':display[k],'count':n} for k,n in lower.most_common(80)]}
    if q['type']=='multi':
        count=Counter(v for row in votes for v in row)
        return {'total':len(votes),'rows':[{'label':o,'count':count[o]} for o in q['options']]}
    opts=['Grün','Gelb','Rot'] if q['type']=='scenario' else ['KI-generiert','Mensch'] if q['type']=='detect' else q['options']
    count=Counter(votes)
    result={'total':len(votes),'rows':[{'label':o,'count':count[o]} for o in opts]}
    if q['type'] in ('scenario','detect'): result['correct']=count[q['solution']]
    return result

def snapshot(admin=False):
    with LOCK:
        q=QUESTIONS[STATE['index']]
        seen=set(k for votes in STATE['votes'].values() for k in votes)
        reveal=STATE['reveal'] or admin
        questions=[public_question(x, reveal=admin or (reveal and x['id']==q['id'])) for x in QUESTIONS]
        ranking=[]
        for voter,player in STATE['players'].items():
            score=sum(100 for x in QUESTIONS if x['type'] in ('scenario','detect') and STATE['reveal'] or False) if False else 0
            for x in QUESTIONS:
                if x['type'] in ('scenario','detect') and x['id'] in STATE['scored'] and STATE['votes'][x['id']].get(voter)==x['solution']:score+=100
            ranking.append({'name':player,'points':score,'voter':voter})
        ranking.sort(key=lambda x:(-x['points'],x['name'].casefold()))
        data={'ranking':[{'name':x['name'],'points':x['points']} for x in ranking],'registered':len(ranking),'session':SESSION,'generation':STATE['generation'],'index':STATE['index'],'is_open':STATE['open'],'revealed':STATE['reveal'],
              'questions':questions,'parts':PARTS,'results':{x['id']:stats(x) for x in QUESTIONS},'participants':len(seen),'join_url':JOIN_URL}
        return data

def write_json(data): return json.dumps(data,ensure_ascii=False,separators=(',',':')).encode('utf-8')

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # Keine IPs speichern
    def respond(self, status=200, raw=b'', mime='application/json; charset=utf-8', headers=None):
        if isinstance(raw,(dict,list)): raw=write_json(raw)
        elif isinstance(raw,str): raw=raw.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        if headers:
            for k,v in headers.items(): self.send_header(k,v)
        self.end_headers()
        try: self.wfile.write(raw)
        except (BrokenPipeError,ConnectionResetError): pass
    def error(self,status,message): self.respond(status,{'error':message})
    def admin(self): return secrets.compare_digest(self.headers.get('X-Admin-Key',''),KEY)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/state': return self.respond(raw=snapshot(self.admin()))
        if path=='/api/admin/export':
            if not secrets.compare_digest(parse_qs(urlsplit(self.path).query).get('key',[''])[0],KEY): return self.error(403,'Zugriff verweigert')
            with LOCK:
                buff=io.StringIO(); w=csv.writer(buff,delimiter=';')
                w.writerow(['Teil','Frage','Antwort','Anzahl','Antwortende','Anteil in %','Lösung (bei Übung)'])
                for q in QUESTIONS:
                    r=stats(q)
                    items=r.get('rows',r.get('words',[]))
                    for a in items:
                        w.writerow([PARTS[q['part']],q['title'],a['label'],a['count'],r['total'],round(a['count']/r['total']*100,1) if r['total'] else 0,q.get('solution','')])
            raw=('\ufeff'+buff.getvalue()).encode('utf-8')
            return self.respond(raw=raw,mime='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="BMH_KI_Workshop_Ergebnisse.csv"'})
        if path=='/api/qr.svg':
            try:
                sys.path.insert(0,str(BASE/'vendor'))
                import qrcode
                from qrcode.image.svg import SvgPathImage
                qr=qrcode.make(JOIN_URL,image_factory=SvgPathImage,box_size=9,border=2)
                b=io.BytesIO();qr.save(b)
                return self.respond(raw=b.getvalue(),mime='image/svg+xml')
            except Exception as e: return self.error(500,'QR-Code konnte nicht erstellt werden: '+str(e))
        files={'/':'participant.html','/moderation':'presenter.html','/assets/style.css':'style.css','/assets/participant.js':'participant.js','/assets/presenter.js':'presenter.js'}
        if path.startswith('/assets/quiz_') and path.endswith('.jpg'):
            f=BASE/path.lstrip('/')
            if f.is_file():return self.respond(raw=f.read_bytes(),mime='image/jpeg')
        if path in files:
            f=BASE/'assets'/files[path]
            mime={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[f.suffix]
            return self.respond(raw=f.read_bytes(),mime=mime)
        return self.error(404,'Nicht gefunden')
    def do_POST(self):
        path=urlsplit(self.path).path
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>6000: return self.error(400,'Ungültige Eingabegrösse')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): return self.error(400,'Ungültige Daten')
        except (ValueError,UnicodeDecodeError):return self.error(400,'Ungültige JSON-Daten')
        if path=='/api/join':
            voter=data.get('voter');name=data.get('name','')
            if not isinstance(voter,str) or not 12<=len(voter)<=90 or not isinstance(name,str) or not 2<=len(name.strip())<=22 or any(ord(c)<32 or c in '<>' for c in name):return self.error(400,'Spitzname: 2 bis 22 Zeichen, ohne Sonderzeichen < >')
            with LOCK:
                if name.strip().casefold() in [v.casefold() for k,v in STATE['players'].items() if k!=voter]:return self.error(409,'Dieser Spitzname ist bereits vergeben')
                STATE['players'][voter]=name.strip()
            return self.respond(raw={'ok':True})
        if path=='/api/vote':
            voter=data.get('voter')
            if not isinstance(voter,str) or not 12<=len(voter)<=90 or not voter.isascii() or not all(c.isalnum() or c in '_-' for c in voter): return self.error(400,'Ungültige Teilnahmekennung')
            with LOCK:
                if voter not in STATE['players']:return self.error(403,'Bitte zuerst Spitznamen wählen')
                if not STATE['open']:return self.error(409,'Abstimmung geschlossen')
                q=QUESTIONS[STATE['index']]
                if data.get('question_id')!=q['id']:return self.error(409,'Die Frage hat gewechselt')
                v=data.get('answer'); t=q['type']
                if t=='wordcloud':
                    if not isinstance(v,str):return self.error(400,'Bitte ein Wort eingeben')
                    v=' '.join(v.strip().split())
                    if not 1<=len(v)<=q.get('limit',40) or any(ord(c)<32 for c in v) or '<' in v or '>' in v:return self.error(400,'Bitte eine kurze, unkritische Antwort eingeben')
                elif t=='multi':
                    if not isinstance(v,list) or not 1<=len(v)<=q['max_select'] or len(set(v))!=len(v) or any(x not in q['options'] for x in v):return self.error(400,'Bitte zulässige Antworten wählen')
                elif t=='detect':
                    if v not in ('KI-generiert','Mensch'):return self.error(400,'Bitte eine Antwort wählen')
                elif t=='scenario':
                    if v not in ('Grün','Gelb','Rot'):return self.error(400,'Bitte Grün, Gelb oder Rot wählen')
                elif not isinstance(v,str) or v not in q['options']:return self.error(400,'Bitte eine Antwort wählen')
                STATE['votes'][q['id']][voter]=v
            return self.respond(raw={'ok':True})
        if path=='/api/admin/action':
            if not self.admin():return self.error(403,'Kein Moderator-Zugriff')
            with LOCK:
                a=data.get('action')
                if a=='set_active':
                    i=data.get('index')
                    if type(i)!=int or not 0<=i<len(QUESTIONS):return self.error(400,'Ungültige Frage')
                    STATE['index']=i;STATE['open']=True;STATE['reveal']=False
                elif a=='set_open':STATE['open']=data.get('open') is True
                elif a=='set_reveal':
                    STATE['reveal']=data.get('reveal') is True
                    if STATE['reveal']:
                        STATE['open']=False
                        q=QUESTIONS[STATE['index']]
                        if q['type'] in ('scenario','detect') and q['id'] not in STATE['scored']:STATE['scored'].append(q['id'])
                elif a=='reset':
                    STATE.update(index=0,open=True,reveal=False,generation=STATE['generation']+1,votes={q['id']:{} for q in QUESTIONS},players={},scored=[])
                else:return self.error(400,'Unbekannte Aktion')
            return self.respond(raw={'ok':True})
        return self.error(404,'Unbekannte Anfrage')

def main():
    try: server=ThreadingHTTPServer(('0.0.0.0',PORT),Handler)
    except OSError as e: raise SystemExit('Start fehlgeschlagen, Port {} belegt: {}'.format(PORT,e))
    admin=(JOIN_URL.rstrip('/') if CLOUD else 'http://127.0.0.1:{}'.format(PORT))+'/moderation?key='+KEY
    print('\n'+'='*68+'\n  BMH · INTERAKTIVER KI-WORKSHOP\n'+'='*68)
    print('  MODERATION / BEAMER: '+admin)
    print('  SMARTPHONES:         '+JOIN_URL)
    print('  Cloud: öffentlich erreichbar' if CLOUD else '  Voraussetzung: Geräte im gleichen WLAN und Netzwerkzugriff erlaubt.')
    print('  Datenschutz: Lokal, flüchtig; CSV vor dem Beenden exportieren.')
    print('  Beenden: Ctrl+C / Strg+C\n'+'='*68+'\n')
    try:
        if not CLOUD: webbrowser.open(admin)
        server.serve_forever()
    except KeyboardInterrupt: print('\nWorkshop beendet.')
    finally: server.server_close()
if __name__=='__main__':main()
