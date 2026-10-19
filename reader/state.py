"""Two-slot checked state. Desktop fsync tested; FAT durability needs bench tests."""
import copy
import hashlib
import json
import os
from pathlib import Path


def encoded(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def validate(data):
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('books'), dict):
        raise ValueError('Unsupported state schema')
    if len(data['books']) > 10000:
        raise ValueError('Too many book states')
    for key, record in data['books'].items():
        if len(key) != 64 or any(c not in '0123456789abcdef' for c in key):
            raise ValueError('Invalid content identity')
        if not isinstance(record, dict) or not isinstance(record.get('bookmarks', []), list):
            raise ValueError('Invalid book record')
        if 'read' in record and not isinstance(record['read'],bool): raise ValueError('Invalid read status')
        if 'progress' in record and (isinstance(record['progress'],bool) or not isinstance(record['progress'],(int,float)) or not 0<=record['progress']<=100): raise ValueError('Invalid progress')
        if len(record.get('bookmarks', [])) > 1000:
            raise ValueError('Too many bookmarks')
        for anchor in [record.get('resume')] + [x.get('anchor') for x in record.get('bookmarks', [])]:
            if anchor is None: continue
            if not isinstance(anchor, dict) or not isinstance(anchor.get('source'), str):
                raise ValueError('Invalid source anchor')
            if not isinstance(anchor.get('block'), int) or anchor['block'] < 0 or not isinstance(anchor.get('offset'), int) or anchor['offset'] < 0:
                raise ValueError('Invalid position')
    return data


class Store:
    def __init__(self, root):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.sequence = -1; self.data = {'version': 1, 'books': {}}
        self.recovered = False
        for i in range(2):
            p = self.root / f'state-{i}.json'
            try:
                if p.stat().st_size > 8 * 1024 * 1024: raise ValueError('State too large')
                r = json.loads(p.read_text())
                if hashlib.sha256(encoded(r['payload'])).hexdigest() != r['sha256']:
                    raise ValueError('State checksum mismatch')
                validate(r['payload'])
                if not isinstance(r['sequence'], int) or r['sequence'] < 0: raise ValueError('Bad sequence')
                if r['sequence'] > self.sequence:
                    self.sequence, self.data = r['sequence'], r['payload']
            except FileNotFoundError: pass
            except (ValueError, KeyError, TypeError): self.recovered = True

    def save(self):
        validate(self.data)
        seq = self.sequence + 1
        record = {'sequence': seq, 'payload': self.data, 'sha256': hashlib.sha256(encoded(self.data)).hexdigest()}
        # Overwrite only the inactive slot: interruption cannot destroy last good slot.
        with open(self.root / f'state-{seq % 2}.json', 'wb') as f:
            f.write(encoded(record)); f.flush(); os.fsync(f.fileno())
        fd = os.open(self.root, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
        self.sequence = seq

    def book(self, identity):
        return self.data['books'].setdefault(identity, {'bookmarks': []})

    def export(self, path):
        Path(path).write_bytes(encoded(self.data))

    def merge(self, path):
        p = Path(path)
        if p.stat().st_size > 8 * 1024 * 1024: raise ValueError('State import too large')
        incoming = validate(json.loads(p.read_text()))
        merged = copy.deepcopy(self.data)
        for key, value in incoming['books'].items():
            if key not in merged['books']:
                merged['books'][key] = copy.deepcopy(value); continue
            rec = merged['books'][key]
            for mark in value.get('bookmarks', []):
                if mark not in rec['bookmarks']: rec['bookmarks'].append(mark)
            # Existing local resume wins. An import does not rewind a known book.
            if 'resume' not in rec and 'resume' in value: rec['resume'] = value['resume']
        validate(merged); self.data = merged; self.save()
