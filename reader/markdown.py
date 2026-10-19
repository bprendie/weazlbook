"""Offline, bounded Markdown subset; no HTML execution or resource fetching."""
import re
from .model import Book, Block, Unsupported

LIMIT = 2 * 1024 * 1024
INLINE = re.compile(r'(!?\[([^\]\n]*)\]\(([^)\n]*)\)|\*\*([^*\n]+)\*\*|__([^_\n]+)__|\*([^*\n]+)\*|_([^_\n]+)_|`([^`\n]+)`)')

def inline(text):
    result, styles, pos = '', [], 0
    for m in INLINE.finditer(text):
        result += text[pos:m.start()]
        if m.group(2) is not None:
            value = '[Image: '+m.group(2)+']' if m.group(1).startswith('!') else m.group(2)+' ('+m.group(3)+')'
            style = 'link'
        else:
            value = next(x for x in m.groups()[3:] if x is not None)
            style = 'bold' if m.group(4) is not None or m.group(5) is not None else 'code' if m.group(8) is not None else 'em'
        start = len(result); result += value; styles.append((start,len(result),style)); pos = m.end()
    return result+text[pos:], styles

def load_markdown(path, identity):
    if path.stat().st_size > LIMIT: raise Unsupported('Markdown exceeds 2 MiB limit')
    try: text=path.read_text(encoding='utf-8-sig')
    except UnicodeError as e: raise Unsupported('Markdown must be UTF-8') from e
    if '\x00' in text: raise Unsupported('Markdown contains NUL bytes')
    blocks=[]; toc=[]; pending=[]; fence=None; code=[]; title=path.stem
    def add(raw,kind='p'):
        value,spans=(raw,[]) if kind=='pre' else inline(raw)
        if not value and kind!='pre': return
        ident='block-'+str(len(blocks)); blocks.append(Block(path.name,value,kind,ident,spans))
        if kind in ('h1','h2','h3','h4','h5','h6'): toc.append((value,path.name+'#'+ident))
    def flush():
        if pending: add(' '.join(pending)); pending.clear()
    lines=text.splitlines(); i=0
    while i<len(lines):
        line=lines[i]; stripped=line.strip(); i+=1
        if fence:
            if re.fullmatch(re.escape(fence[0])+'{'+str(len(fence))+',}\\s*',stripped):
                add('\n'.join(code),'pre'); code=[]; fence=None
            else: code.append(line.expandtabs(4))
            continue
        m=re.match(r'^(`{3,}|~{3,})(.*)$',stripped)
        if m: flush(); fence=m[1]; continue
        if not stripped: flush(); continue
        if i<len(lines) and re.fullmatch(r'\s*(={3,}|-{3,})\s*',lines[i]):
            flush(); add(stripped,'h1' if '=' in lines[i] else 'h2'); i+=1; continue
        m=re.match(r'^(#{1,6})\s+(.+?)(?:\s+#+)?$',stripped)
        if m: flush(); add(m[2],'h'+str(len(m[1]))); continue
        if re.fullmatch(r'(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,}',stripped): flush(); add('─'*20,'hr'); continue
        m=re.match(r'^(\s*)([-+*]|\d+[.)])\s+(.+)$',line)
        if m: flush(); prefix=' '*min(len(m[1]),8)+('•' if m[2] in '-+*' else m[2])+' '; add(prefix+m[3],'li'); continue
        if stripped.startswith('>'): flush(); add(stripped.lstrip('>').strip(),'quote'); continue
        if line.startswith('    ') or line.startswith('\t'): flush(); add(line.expandtabs(4)[4:],'pre'); continue
        pending.append(stripped)
    flush()
    if fence: add('\n'.join(code),'pre')
    if not blocks: raise Unsupported('Markdown has no readable text')
    title=next((b.text for b in blocks if b.kind=='h1'),title)
    return Book(identity(path),title,'md',blocks,toc,['Markdown subset: tables, nested inline markup and raw HTML remain literal; images use text labels. Links are offline text.'])
