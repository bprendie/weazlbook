import json
import shutil
from pathlib import Path
from zipfile import ZipFile
import pytest
from reader.documents import load, Unsupported
from reader.layout import paginate, locate, render
from reader.session import Session
from reader.state import Store
from tools.fixtures import generate, OUT

@pytest.fixture(scope='session',autouse=True)
def corpus(): generate()

def test_epub_spine_fonts_emphasis_and_links():
    b=load(OUT/'local.epub')
    assert b.title=='The Local Library'
    assert b.blocks[0].text=='Chapter one'
    assert any(x.text=='Chapter two' for x in b.blocks)
    assert '*Local*' in b.blocks[1].text and '**repairable**' in b.blocks[1].text
    assert ('Two','OPS/two.xhtml#start') in b.toc
    assert b.warnings

def test_pdf_source_pages_and_omission():
    for name in ('simple','flate'):
        b=load(OUT/f'{name}.pdf'); assert len(b.toc)==3
        assert 'Page 1, line 1' in b.blocks[0].text
    mixed=load(OUT/'mixed.pdf')
    assert len(mixed.toc)==2 and any('page 2' in w for w in mixed.warnings)

@pytest.mark.parametrize('name',['protected.epub','encrypted.pdf','scanned.pdf','broken.pdf','broken.epub'])
def test_explicit_rejection(name):
    with pytest.raises((Unsupported,ValueError)): load(OUT/name)

def test_independent_resume_marks_reflow_and_rename(tmp_path):
    store=Store(tmp_path/'state'); a=Session(load(OUT/'local.epub'),store)
    a.turn(5); a.bookmark('First'); a.turn(3); a.bookmark('Second')
    anchor=a.page.anchor; a.resize(28)
    assert store.book(a.book.identity)['resume']==anchor
    b=Session(load(OUT/'second.epub'),store); b.turn(2)
    shutil.copy(OUT/'local.epub',tmp_path/'renamed.epub')
    restored=Session(load(tmp_path/'renamed.epub'),Store(tmp_path/'state'),28)
    assert restored.position==locate(restored.pages,anchor)
    assert len(store.book(a.book.identity)['bookmarks'])==2
    assert b.book.identity != a.book.identity
    for size in (20,24,28):
        pages=paginate(a.book,size); im=render(a.book,pages[0],0,len(pages),size)
        assert im.size==(480,800) and im.mode=='1'

def test_torn_slot_preserves_last_commit(tmp_path):
    s=Store(tmp_path); key='a'*64
    s.book(key)['bookmarks'].append({'name':'survivor','anchor':{'source':'chapter','block':0,'offset':0}})
    s.save(); previous=json.loads(json.dumps(s.data)); s.book(key)['resume']={'source':'chapter','block':2,'offset':4}; s.save()
    newest=tmp_path/f'state-{s.sequence%2}.json'; raw=newest.read_bytes()
    for cut in (0,1,20,len(raw)//2,len(raw)-1):
        newest.write_bytes(raw[:cut]); recovered=Store(tmp_path)
        assert recovered.data==previous and recovered.recovered
    newest.write_bytes(raw)
    assert Store(tmp_path).data==s.data

def test_export_import_merge_and_invalid_atomic(tmp_path):
    a=Store(tmp_path/'a'); a.book('a'*64); a.save(); a.export(tmp_path/'state.json')
    b=Store(tmp_path/'b'); b.book('b'*64); b.save(); b.merge(tmp_path/'state.json')
    assert len(b.data['books'])==2
    (tmp_path/'bad.json').write_text('{"version":9}')
    with pytest.raises(ValueError): b.merge(tmp_path/'bad.json')
    assert len(Store(tmp_path/'b').data['books'])==2

def test_zip_traversal_and_xml_entity(tmp_path):
    for root in ('../escape.opf','/escape.opf'):
        p=tmp_path/'bad.epub'
        with ZipFile(p,'w') as z: z.writestr('META-INF/container.xml',f'<container><rootfile full-path="{root}"/></container>')
        with pytest.raises(Unsupported): load(p)
    with ZipFile(p,'w') as z:
        z.writestr('META-INF/container.xml','<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><container>&x;</container>')
    with pytest.raises(Exception): load(p)


def test_markdown_formatting_and_resume(tmp_path):
    b=load(Path('fixtures/formatting.md'))
    assert b.title=='A pocket library' and len(b.toc)==2
    assert any(x.kind=='pre' and '    read(book)' in x.text for x in b.blocks)
    assert any(x.kind=='quote' for x in b.blocks)
    assert {s for block in b.blocks for a,z,s in block.spans}>={'bold','em','code','link'}
    assert '**bold words**' not in '\n'.join(x.text for x in b.blocks)
    for size in (20,24,28):
        pages=paginate(b,size)
        assert all(len(p.styles)==len(p.lines) for p in pages)
        assert render(b,pages[0],0,len(pages),size).mode=='1'
    session=Session(b,Store(tmp_path/'state'));session.turn(1);session.bookmark('Notes')
    restored=Session(b,Store(tmp_path/'state'))
    assert restored.page.anchor==session.page.anchor
    restored.resize(28)
    assert restored.store.book(b.identity)['bookmarks'][0]['name']=='Notes'


def test_markdown_limits_and_literal_html(tmp_path):
    p=tmp_path/'notes.MD';p.write_bytes(b'\xff')
    with pytest.raises(Unsupported):load(p)
    p.write_bytes(b'\0')
    with pytest.raises(Unsupported):load(p)
    p.write_text('x'*(2*1024*1024+1))
    with pytest.raises(Unsupported):load(p)
    p.write_text('# Header\n\n<script>alert(1)</script>\n\n~~~\n**literal**\n~~~~\n')
    b=load(p)
    assert any(x.text=='<script>alert(1)</script>' for x in b.blocks)
    assert any(x.kind=='pre' and x.text=='**literal**' for x in b.blocks)
