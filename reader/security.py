"""Authoritative local simulator lock; never deletes source documents."""
import json
import os
import re
from pathlib import Path

class Security:
    def __init__(self, root):
        self.path=Path(root)/'device.json';self.attempt=''
        self.data={'unlock':'','duress':'','locked':False,'purged':False}
        if self.path.exists():
            # Fail closed on corruption, not an automatic reset.
            self.data=json.loads(self.path.read_text())
            for key in ('unlock','duress'):
                if self.data.get(key) and not re.fullmatch('[UDLR]{4,16}',self.data[key]):raise ValueError('Invalid device code state')
    def save(self):
        tmp=self.path.with_suffix('.tmp')
        with open(tmp,'w') as f:
            os.chmod(tmp,0o600);json.dump(self.data,f);f.flush();os.fsync(f.fileno())
        os.replace(tmp,self.path)
        fd=os.open(self.path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    def configure(self,kind,code):
        if self.data['locked']:raise PermissionError('Device locked')
        if kind not in ('unlock','duress') or not isinstance(code,str) or not re.fullmatch('[UDLR]{4,16}',code):raise ValueError('Use 4–16 arrows')
        other=self.data['duress' if kind=='unlock' else 'unlock']
        if kind=='duress' and not other:raise ValueError('Set an unlock code first')
        if other and (len(other)!=len(code) or other==code):raise ValueError('Codes must be different and the same length')
        self.data[kind]=code;self.save()
    def arrow(self,value):
        if value not in ('U','D','L','R'):raise ValueError('Invalid arrow')
        if not self.data['locked']:return ''
        self.attempt=(self.attempt+value)[-16:]
        for key in ('duress','unlock'):
            code=self.data[key]
            if code and self.attempt.endswith(code):self.attempt='';return key
        return ''
    def public(self):
        return {'locked':self.data['locked'],'unlock_set':bool(self.data['unlock']),'duress_set':bool(self.data['duress']),'purged':self.data['purged'],'code_length':len(self.data['unlock'])}
