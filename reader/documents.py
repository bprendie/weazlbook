"""Bounded desktop import. PDF decoding is an optional desktop capability.

This module is NOT the ESP32 parser. XML never resolves entities or fetches URLs.
The CLI runs import in a separate resource-limited process.
"""
import hashlib
import posixpath
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from defusedxml import ElementTree as ET
from .model import Book, Block, Unsupported

MAX_FILE = 64 * 1024 * 1024
MAX_MEMBER = 2 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
MAX_BLOCKS = 50000


def local(tag):
    return tag.rsplit('}', 1)[-1]


def link(base, href):
    u = urlsplit(href)
    if u.scheme or u.netloc:
        raise Unsupported('External resource is not part of the offline book')
    p = posixpath.normpath(posixpath.join(posixpath.dirname(base), unquote(u.path)))
    if p.startswith('../') or p.startswith('/') or '\\' in p:
        raise Unsupported('Archive path escapes book')
    return p


def identity(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while data := f.read(65536):
            h.update(data)
    return h.hexdigest()


def load(path):
    path = Path(path)
    if path.stat().st_size > MAX_FILE:
        raise Unsupported('Book exceeds 64 MiB import limit')
    try:
        if path.suffix.lower() == '.epub':
            return epub(path)
        if path.suffix.lower() == '.pdf':
            return pdf(path)
        if path.suffix.lower() in ('.md', '.markdown'):
            from .markdown import load_markdown
            return load_markdown(path, identity)
        raise Unsupported('Supported source extensions: .epub, .pdf, .md and .markdown')
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise Unsupported(f'Malformed document: {exc}') from exc


def epub(path):
    blocks, toc, warnings = [], [], []
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        if len(infos) > 4096 or len({i.filename for i in infos}) != len(infos):
            raise Unsupported('Too many archive members or duplicate names')
        if sum(i.file_size for i in infos) > MAX_TOTAL:
            raise Unsupported('Archive exceeds 32 MiB expanded limit')
        for i in infos:
            if i.flag_bits & 1:
                raise Unsupported('Encrypted ZIP member')
            if i.file_size > MAX_MEMBER:
                raise Unsupported(f'Archive member exceeds 2 MiB: {i.filename}')
        def read(name):
            data = z.read(name)
            if len(data) > MAX_MEMBER:
                raise Unsupported('Expanded member limit exceeded')
            return data
        def xml(name):
            root = ET.fromstring(read(name))
            stack = [(root, 0)]
            count = 0
            while stack:
                n, depth = stack.pop(); count += 1
                if depth > 64 or count > 50000:
                    raise Unsupported('XML nesting/node limit exceeded')
                stack.extend((c, depth + 1) for c in n)
            return root
        if 'META-INF/encryption.xml' in z.namelist():
            for n in xml('META-INF/encryption.xml').iter():
                if local(n.tag) == 'EncryptionMethod' and n.get('Algorithm') not in (
                    'http://www.idpf.org/2008/embedding',
                    'http://ns.adobe.com/pdf/enc#RC'):
                    raise Unsupported('Protected EPUB content is unsupported')
            warnings.append('Embedded obfuscated fonts ignored; using IBM Plex Mono')
        container = xml('META-INF/container.xml')
        roots = [n.get('full-path') for n in container.iter() if local(n.tag) == 'rootfile']
        if not roots:
            raise Unsupported('EPUB container has no package')
        package = link('', roots[0]); opf = xml(package)
        title = next((n.text for n in opf.iter() if local(n.tag) == 'title' and n.text), path.stem)
        if any(local(n.tag) == 'meta' and n.get('property') == 'rendition:layout'
               and (n.text or '').strip() == 'pre-paginated' for n in opf.iter()):
            raise Unsupported('Fixed-layout EPUB is not supported')
        items = {n.get('id'): n for n in opf.iter() if local(n.tag) == 'item'}
        spine = [n.get('idref') for n in opf.iter() if local(n.tag) == 'itemref']
        if not spine or len(spine) > 2048:
            raise Unsupported('Missing or oversized EPUB spine')
        for key in spine:
            item = items[key]
            if item.get('media-type') != 'application/xhtml+xml':
                raise Unsupported('Non-XHTML spine item is unsupported')
            src = link(package, item.get('href', '')); root = xml(src)
            def walk(n):
                tag = local(n.tag)
                if tag in ('script', 'style', 'head'):
                    return
                if tag in ('img', 'svg', 'math'):
                    blocks.append(Block(src, '[Illustration: ' + n.get('alt', tag) + ']', 'notice'))
                    warnings.append(f'{src}: {tag} represented by a text notice')
                    return
                if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'pre', 'dt', 'dd', 'tr'):
                    def inline(el):
                        t = el.text or ''
                        for c in el:
                            ct = local(c.tag)
                            val = inline(c) if ct not in ('script', 'style') else ''
                            if ct in ('em', 'i'): val = '*' + val + '*'
                            if ct in ('strong', 'b'): val = '**' + val + '**'
                            if ct == 'br': val = '\n'
                            if ct == 'img': val = '[Illustration: ' + c.get('alt', 'image') + ']'
                            if ct == 'a' and c.get('href'):
                                target = c.get('href')
                                if not urlsplit(target).scheme:
                                    toc.append((val or target, src + target if target.startswith('#') else link(src, target) + ('#' + urlsplit(target).fragment if urlsplit(target).fragment else '')))
                            t += val + (c.tail or '')
                        return t
                    text = inline(n)
                    text = text.strip() if tag == 'pre' else re.sub(r'\s+', ' ', text).strip()
                    if text:
                        blocks.append(Block(src, text, tag, n.get('id', '')))
                        if tag.startswith('h'):
                            toc.append((text, src + ('#' + n.get('id') if n.get('id') else '')))
                    return
                if n.text and n.text.strip() and tag in ('body', 'div', 'section'):
                    blocks.append(Block(src, re.sub(r'\s+', ' ', n.text).strip()))
                for c in n:
                    walk(c)
            walk(root)
            if len(blocks) > MAX_BLOCKS:
                raise Unsupported('Too many text blocks')
        for item in items.values():
            if 'nav' in item.get('properties', '').split():
                src = link(package, item.get('href', ''))
                for n in xml(src).iter():
                    if local(n.tag) == 'a' and n.get('href'):
                        href = n.get('href'); frag = urlsplit(href).fragment
                        toc.append((''.join(n.itertext()).strip(), link(src, href) + ('#' + frag if frag else '')))
        if not blocks:
            raise Unsupported('EPUB has no readable text')
        return Book(identity(path), title, 'epub', blocks, list(dict.fromkeys(toc)), list(dict.fromkeys(warnings)))


def pdf(path):
    from pypdf import PdfReader
    try:
        r = PdfReader(path, strict=True)
        if r.is_encrypted:
            raise Unsupported('Encrypted PDF is unsupported')
        if len(r.pages) > 2000:
            raise Unsupported('PDF exceeds 2000 source pages')
        blocks, warnings, toc = [], [], []
        labels = r.page_labels
        for i, page in enumerate(r.pages):
            src = f'page:{i + 1}'
            text = page.extract_text(extraction_mode='plain') or ''
            if not text.strip():
                warnings.append(f'Source page {i+1} ({labels[i]}): no usable text; omitted, no OCR')
                continue
            if len(text) > MAX_MEMBER:
                raise Unsupported(f'Source page {i+1} exceeds text limit')
            # Conservative source line preservation, no invented column order.
            for p in re.split(r'\n\s*\n', text):
                if p.strip(): blocks.append(Block(src, p.strip()))
            toc.append((f'Page {labels[i]}', src))
            if len(blocks) > MAX_BLOCKS:
                raise Unsupported('Too many text blocks')
        if not blocks:
            raise Unsupported('Image-only PDF or no useful text; OCR is not supported')
        warnings.append('Desktop PDF reflow: reading order follows content stream; inspect complex columns and tables')
        return Book(identity(path), str((r.metadata or {}).get('/Title') or path.stem), 'pdf', blocks, toc, warnings)
    except Unsupported:
        raise
    except Exception as exc:
        raise Unsupported(f'Unsupported or malformed PDF: {exc}') from exc
