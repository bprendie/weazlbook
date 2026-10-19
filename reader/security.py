"""Authoritative local simulator lock; never deletes source documents."""
import hashlib
import hmac
import secrets
import json
import os
import re
from pathlib import Path

ITERATIONS = 100_000  # Provisional embedded work factor; benchmark on the board.

def verifier(code):
    salt=secrets.token_bytes(16)
    return {'version':2,'iterations':ITERATIONS,'length':len(code),'salt':salt.hex(),
            'hash':hashlib.pbkdf2_hmac('sha256',code.encode('ascii'),salt,ITERATIONS).hex()}

def valid_record(record):
    if not isinstance(record,dict) or record.get('version')!=2 or record.get('iterations')!=ITERATIONS:
        raise ValueError('Invalid device code verifier')
    if type(record.get('length')) is not int or not 4<=record['length']<=16:
        raise ValueError('Invalid device code length')
    for key,size in (('salt',32),('hash',64)):
        if not isinstance(record.get(key),str) or not re.fullmatch('[0-9a-f]{'+str(size)+'}',record[key]):
            raise ValueError('Invalid device code verifier')

def matches(record,code):
    if not record or len(code)!=record['length']:return False
    digest=hashlib.pbkdf2_hmac('sha256',code.encode('ascii'),bytes.fromhex(record['salt']),record['iterations'])
    return hmac.compare_digest(digest,bytes.fromhex(record['hash']))

class Security:
    def __init__(self, root):
        self.path=Path(root)/'device.json';self.attempt=''
        self.data={'unlock':'','duress':'','locked':False,'purged':False}
        if self.path.exists():
            # Fail closed on corruption, not an automatic reset.
            self.data=json.loads(self.path.read_text())
            migrated=False
            for key in ('unlock','duress'):
                record=self.data.get(key)
                if record == '':continue
                if isinstance(record,str):
                    if not re.fullmatch('[UDLR]{4,16}',record):raise ValueError('Invalid legacy device code')
                    self.data[key]=verifier(record);migrated=True
                else:valid_record(record)
            if type(self.data.get('locked')) is not bool or type(self.data.get('purged')) is not bool:
                raise ValueError('Invalid device security state')
            if self.data['locked'] and not self.data['unlock']:raise ValueError('Locked device has no verifier')
            if self.data['duress'] and (not self.data['unlock'] or self.data['duress']['length']!=self.data['unlock']['length']):raise ValueError('Invalid code lengths')
            if migrated:self.save()
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
        if other and (other['length']!=len(code) or matches(other,code)):raise ValueError('Codes must be different and the same length')
        previous=self.data[kind];self.data[kind]=verifier(code)
        try:self.save()
        except Exception:self.data[kind]=previous;raise
    def arrow(self,value):
        if value not in ('U','D','L','R'):raise ValueError('Invalid arrow')
        if not self.data['locked']:return ''
        self.attempt=(self.attempt+value)[-16:]
        results={}
        for key in ('duress','unlock'):
            record=self.data[key]
            results[key]=bool(record) and matches(record,self.attempt[-record['length']:])
        for key in ('duress','unlock'):
            if results[key]:self.attempt='';return key
        return ''
    def public(self):
        return {'locked':self.data['locked'],'unlock_set':bool(self.data['unlock']),'duress_set':bool(self.data['duress']),'purged':self.data['purged'],'code_length':self.data['unlock']['length'] if self.data['unlock'] else 0}
