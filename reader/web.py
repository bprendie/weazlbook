"""Local browser simulator. Run python -m reader.web --book /path/book.epub."""
import argparse
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .__main__ import bounded_load
from .state import Store
from .session import Session
from .layout import render, FONT
from .documents import identity
from .security import Security
from PIL import Image

WEB=Path(__file__).with_name('web_assets')

class Simulator:
    def __init__(self, paths, state):
        self.original_paths=[Path(p).expanduser().resolve() for p in paths]
        self.paths=list(self.original_paths)
        self.about_path=Path(__file__).resolve().parents[1]/'about.md'
        self.store=Store(state); self.loaded={}; self.current=None; self.active=0
        self.lock=threading.RLock(); self.revision=0
        self.security=Security(self.store.root)
        self.identities=[identity(p) for p in self.paths]
        if self.security.data['purged']: self.paths=[];self.identities=[]
        else: self.open(0)

    def open(self, which):
        if not 0<=which<len(self.paths): raise ValueError('Unknown book')
        if self.current: self.current.save()
        if which not in self.loaded: self.loaded[which]=bounded_load(self.paths[which])
        self.active=which; self.current=Session(self.loaded[which],self.store)
        self.revision+=1

    def reset_demo(self):
        self.security.data={'unlock':'','duress':'','locked':False,'purged':False};self.security.attempt='';self.security.save()
        self.store.data={'version':1,'books':{}};self.store.save();self.store.save()
        self.paths=list(self.original_paths);self.identities=[identity(p) for p in self.paths];self.loaded={};self.current=None;self.open(0)

    def purge_demo(self):
        # Commit the tombstone first; restart cannot re-import the source books.
        self.security.data={'unlock':'','duress':'','locked':False,'purged':True};self.security.save()
        self.current=None;self.loaded={};self.paths=[];self.identities=[]
        self.store.data={'version':1,'books':{}};self.store.save();self.store.save();self.revision+=1

    def info(self):
        security=self.security.public()
        if security['locked'] or not self.current:
            return {'security':security,'title':'Device locked' if security['locked'] else 'Clean device','book_id':'','page':0,'pages':0,'size':24,'source':'','revision':self.revision,'progress':0,'read':False,'bookmarks':[],'toc':[],'warnings':['Simulator reset only: source files are preserved.'] if security['purged'] else [],'active_book':-1,'library':[]}
        s=self.current; b=s.book
        return {'security':security,'title':b.title,'book_id':b.identity,'page':s.position+1,'pages':len(s.pages),
                'size':s.size,'source':s.page.anchor['source'],'revision':self.revision,
                'progress':s.progress,'read':self.store.book(b.identity).get('read',False),
                'bookmarks':self.store.book(b.identity)['bookmarks'],
                'toc':[{'label':name,'target':target} for name,target in b.toc],
                'warnings':b.warnings,'active_book':self.active,
                'library':[{'id':i,'title':self.loaded[i].title if i in self.loaded else p.stem,'progress':s.progress if i==self.active else self.store.book(self.identities[i]).get('progress',0),'read':self.store.book(self.identities[i]).get('read',False)} for i,p in enumerate(self.paths)]}

    def action(self, body):
        name=body.get('action'); s=self.current
        if name=='reset_simulator':self.reset_demo();return self.info()
        if name=='arrow':
            match=self.security.arrow(body.get('arrow'))
            if match=='duress':self.purge_demo()
            elif match=='unlock':self.security.data['locked']=False;self.security.save()
            return self.info()
        if self.security.data['locked']:raise PermissionError('Device locked; USB and book access denied')
        if name=='set_code':self.security.configure(body.get('kind'),body.get('code'));return self.info()
        if name=='lock':
            if not self.security.data['unlock']:raise ValueError('Set your unlock code first')
            self.security.data['locked']=True;self.security.attempt='';self.security.save();return self.info()
        if name=='about':
            if self.security.data['purged']:raise ValueError('Owner information was wiped')
            if self.current:self.current.save()
            self.current=Session(bounded_load(self.about_path),self.store);self.active=-1;self.revision+=1;return self.info()
        if not s:raise ValueError('No books. Use Reset simulator to restore the demo.')
        if name=='next': s.turn(1)
        elif name=='previous': s.turn(-1)
        elif name=='read_status':
            if not isinstance(body.get('read'),bool): raise ValueError('Expected read status')
            self.store.book(s.book.identity)['read']=body['read'];self.store.save()
        elif name=='font': s.resize(int(body['size']))
        elif name=='mark': s.bookmark(str(body.get('name',''))[:120])
        elif name=='jump_mark':
            marks=self.store.book(s.book.identity)['bookmarks']; i=int(body['index'])
            if not 0<=i<len(marks): raise ValueError('Unknown bookmark')
            s.jump(marks[i]['anchor'])
        elif name=='delete_mark':
            marks=self.store.book(s.book.identity)['bookmarks']; i=int(body['index'])
            if not 0<=i<len(marks): raise ValueError('Unknown bookmark')
            del marks[i]; self.store.save()
        elif name=='contents': s.source(str(body['target']))
        elif name=='open': self.open(int(body['book']))
        elif name=='goto':
            p=int(body['page'])
            if not 1<=p<=len(s.pages): raise ValueError('Page is out of range')
            s.position=p-1; s.save()
        elif name=='import_state':
            # Validate and merge in memory using the same rules as file import.
            from .state import validate
            incoming=validate(body['state'])
            import copy
            merged=copy.deepcopy(self.store.data)
            for key,value in incoming['books'].items():
                if key not in merged['books']: merged['books'][key]=copy.deepcopy(value)
                else:
                    dest=merged['books'][key]
                    for mark in value.get('bookmarks',[]):
                        if mark not in dest['bookmarks']: dest['bookmarks'].append(mark)
            validate(merged);self.store.data=merged;self.store.save()
        else: raise ValueError('Unknown action')
        self.revision+=1; return self.info()


def handler(sim):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            if args and isinstance(args[0],str) and '/screen.png' in args[0]: return
            super().log_message(fmt,*args)

        def reply(self,status,data,kind='application/json; charset=utf-8'):
            if not isinstance(data,bytes): data=json.dumps(data,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers();self.wfile.write(data)

        def local(self):
            return self.headers.get('Host') in (f'localhost:{self.server.server_port}',f'127.0.0.1:{self.server.server_port}')

        def do_GET(self):
            if not self.local(): return self.reply(403,{'error':'Localhost only'})
            path=urlsplit(self.path).path
            with sim.lock:
                if path=='/api/state': return self.reply(200,sim.info())
                if path in ('/api/export','/screen.png') and sim.security.data['locked']:return self.reply(403,{'error':'Device locked'})
                if path=='/api/export':
                    return self.reply(200,sim.store.data)
                if path=='/screen.png':
                    s=sim.current; out=io.BytesIO();im=render(s.book,s.page,s.position,len(s.pages),s.size) if s else Image.new('1',(480,800),1);im.save(out,format='PNG')
                    return self.reply(200,out.getvalue(),'image/png')
            assets={'/lock.js':('lock.js','text/javascript; charset=utf-8'),'/screensaver.png':('screensaver.png','image/png'),'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
            if path=='/plex.ttf': return self.reply(200,FONT.read_bytes(),'font/ttf')
            if path in assets:
                file,kind=assets[path];return self.reply(200,(WEB/file).read_bytes(),kind)
            self.reply(404,{'error':'Not found'})

        def do_POST(self):
            if not self.local():return self.reply(403,{'error':'Localhost only'})
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://localhost:{self.server.server_port}',f'http://127.0.0.1:{self.server.server_port}'):
                return self.reply(403,{'error':'Cross-origin request denied'})
            if urlsplit(self.path).path!='/api/action':return self.reply(404,{'error':'Not found'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=2*1024*1024:raise ValueError('Request size limit exceeded')
                body=json.loads(self.rfile.read(length))
                if not isinstance(body,dict):raise ValueError('Expected an object')
                with sim.lock: result=sim.action(body)
                self.reply(200,result)
            except PermissionError as e:self.reply(403,{'error':str(e)})
            except (ValueError,KeyError,IndexError,TypeError) as e:self.reply(400,{'error':str(e)})
            except Exception as e:self.reply(500,{'error':str(e)})
    return Handler


def main():
    p=argparse.ArgumentParser();p.add_argument('--book',action='append',required=True)
    p.add_argument('--port',type=int,default=5000);p.add_argument('--state',default='.reader-state/web')
    a=p.parse_args(); sim=Simulator(a.book,a.state)
    server=ThreadingHTTPServer(('127.0.0.1',a.port),handler(sim))
    print(f'WeazlBook simulator: http://localhost:{a.port} — {sim.info()['title']}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        if sim.current:sim.current.save()
        server.server_close()

if __name__=='__main__':main()
