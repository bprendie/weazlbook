from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

FONT = Path(__file__).resolve().parents[1] / 'baseline/research/fonts/IBMPlexMono-Regular.ttf'
COVERAGE = set(TTFont(FONT).getBestCmap())


@dataclass
class Page:
    anchor: dict
    lines: list[str]
    styles: list = field(default_factory=list)


def anchor(book, i, offset):
    block = book.blocks[i]
    return {'source': block.source, 'block': i, 'id': block.id, 'offset': offset,
            'context': block.text[max(0, offset-24):offset+48]}


def paginate(book, size=24):
    if size not in (20, 24, 28): raise ValueError('Font size must be 20, 24 or 28')
    f = ImageFont.truetype(str(FONT), size)
    cols = int(432 // f.getlength('M')); rows = 680 // (size + 8)
    pages, lines, start, styles = [], [], None, []
    for i, block in enumerate(book.blocks):
        pos = 0
        while pos < len(block.text):
            if start is None: start = anchor(book, i, pos)
            line_start = pos
            end = min(len(block.text), pos + cols)
            newline = block.text.find('\n', pos, end)
            if newline >= 0: end = newline
            elif end < len(block.text):
                space = block.text.rfind(' ', pos+1, end)
                if space > pos: end = space
            if end == pos:
                line = ''; pos += 1
            else:
                line = block.text[pos:end]; pos = end
                if pos < len(block.text) and block.text[pos] in ' \n': pos += 1
            lines.append(line)
            styles.append((block.kind, [(max(0,a-line_start),min(len(line),b-line_start),style) for a,b,style in block.spans if a < line_start+len(line) and b > line_start]))
            if len(lines) == rows:
                pages.append(Page(start, lines, styles)); lines, start, styles = [], None, []
        if lines:
            lines.append('')
            styles.append(('p', []))
            if len(lines) >= rows:
                pages.append(Page(start, lines, styles)); lines, start, styles = [], None, []
    if lines: pages.append(Page(start, lines, styles))
    return pages


def locate(pages, mark):
    if not mark: return 0
    best = 0
    for i, p in enumerate(pages):
        a = p.anchor
        if (a['block'], a['offset']) <= (mark['block'], mark['offset']): best = i
    return best


def visible(s):
    return ''.join(c if ord(c) in COVERAGE else '□' for c in s)


def render(book, page, index, count, size=24):
    im = Image.new('1', (480, 800), 1); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(FONT), size); small = ImageFont.truetype(str(FONT), 16)
    d.text((24, 16), visible(book.title[:42]), font=small, fill=0)
    d.line((24, 44, 456, 44), fill=0)
    bold = ImageFont.truetype(str(FONT.with_name('IBMPlexMono-SemiBold.ttf')), size)
    cell = f.getlength('M')
    for i, line in enumerate(page.lines):
        y = 60+i*(size+8)
        kind, spans = page.styles[i] if i < len(page.styles) else ('p', [])
        if book.format != 'md': kind, spans = 'p', []
        if kind == 'quote': d.line((18,y,18,y+size+3),fill=0,width=2)
        if kind == 'pre': d.line((20,y,20,y+size+8),fill=0)
        if kind == 'hr': d.line((24,y+size//2,456,y+size//2),fill=0); continue
        for j,char in enumerate(line):
            style = next((s for a,b,s in spans if a<=j<b), '')
            x = 24+j*cell
            d.text((x,y),visible(char),font=bold if kind.startswith('h') or style=='bold' else f,fill=0)
            if style in ('em','link'): d.line((x,y+size+3,x+cell-1,y+size+3),fill=0)
            if style=='code': d.line((x,y+size+5,x+cell-1,y+size+5),fill=0)

    d.line((24, 750, 456, 750), fill=0)
    d.text((24, 762), f'{index+1}/{count}  {page.anchor["source"][-26:]}', font=small, fill=0)
    return im
