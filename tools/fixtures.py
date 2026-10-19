"""Original CC0 fixture prose; deliberately includes malformed/unsupported files."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from reportlab.pdfgen.canvas import Canvas
from reportlab import rl_config
from pypdf import PdfReader, PdfWriter

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'fixtures'; OUT.mkdir(exist_ok=True)
PROSE='He kept the books on a machine he could open with a screwdriver. Outside, every sign wanted his name. The little screen asked for nothing.'

def make_epub(path, title='The Local Library', protected=False):
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        z.writestr('mimetype','application/epub+zip',compress_type=0)
        z.writestr('META-INF/container.xml','<container><rootfiles><rootfile full-path="OPS/package.opf"/></rootfiles></container>')
        z.writestr('OPS/package.opf',f'''<package xmlns:dc="http://purl.org/dc/elements/1.1/" version="3.0"><metadata><dc:title>{title}</dc:title></metadata><manifest><item id="one" href="one.xhtml" media-type="application/xhtml+xml"/><item id="two" href="two.xhtml" media-type="application/xhtml+xml"/><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/></manifest><spine><itemref idref="one"/><itemref idref="two"/></spine></package>''')
        for chapter in ('one','two'):
            z.writestr(f'OPS/{chapter}.xhtml','<html xmlns="http://www.w3.org/1999/xhtml"><body><h1 id="start">Chapter '+chapter+'</h1>'+''.join(f'<p id="p{i}">{i}: {PROSE} <em>Local</em>, <strong>repairable</strong>. Café — naïve.</p>' for i in range(40))+'<p><a href="two.xhtml#start">Next chapter</a></p></body></html>')
        z.writestr('OPS/nav.xhtml','<html><body><nav><a href="one.xhtml#start">One</a><a href="two.xhtml#start">Two</a></nav></body></html>')
        algo='urn:actual-encryption' if protected else 'http://www.idpf.org/2008/embedding'
        z.writestr('META-INF/encryption.xml',f'<encryption><EncryptionMethod Algorithm="{algo}"/></encryption>')

def generate():
    rl_config.useA85 = 0
    make_epub(OUT/'local.epub'); make_epub(OUT/'second.epub','Second Independent Book')
    make_epub(OUT/'protected.epub',protected=True)
    for name,compress in [('simple',False),('flate',True),('mixed',True),('scanned',True)]:
        c=Canvas(str(OUT/f'{name}.pdf'),pageCompression=compress); c.setTitle(name.title()+' PDF')
        for page in range(3):
            if name=='scanned' or (name=='mixed' and page==1):
                c.rect(50,50,400,600,fill=1)
            else:
                t=c.beginText(50,750); t.setFont('Helvetica',12)
                for line in range(30): t.textLine(f'Page {page+1}, line {line+1}: A local reader keeps each book and bookmark.')
                c.drawText(t)
            c.showPage()
        c.save()
    w=PdfWriter(); w.append(str(OUT/'simple.pdf')); w.encrypt('secret'); w.write(OUT/'encrypted.pdf')
    (OUT/'broken.pdf').write_bytes(b'%PDF-1.7\nnot a cross reference table')
    (OUT/'broken.epub').write_bytes(b'PK\x03\x04broken')

if __name__=='__main__': generate()
