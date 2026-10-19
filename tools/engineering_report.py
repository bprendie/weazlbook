"""Dimensioned review sheets from actual R05 geometry, plus 3MF placement audit."""
import json,math,sys
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
import cadquery as cq
import cairosvg
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/cad'; VIEWS=OUT/'views'
pdfmetrics.registerFont(TTFont('Plex',str(ROOT/'baseline/research/fonts/IBMPlexMono-Regular.ttf')))

def report():
    checks=json.loads((ROOT/'evidence/cad-checks.json').read_text())
    # Cut real assembly solids by X slab; section has its actual geometry.
    assembly=cq.importers.importStep(str(OUT/'assembly.step')).val()
    section=assembly.intersect(cq.Solid.makeBox(.2,160,40,cq.Vector(39.9,-2,-5)))
    cq.exporters.export(section,str(VIEWS/'section-x40.svg'),exportType='SVG',opt={'projectionDir':(1,0,0),'showHidden':False,'width':800,'height':1000})
    for name in ('front','side','isometric','exploded','section-x40'):
        cairosvg.svg2png(url=str(VIEWS/(name+'.svg')),write_to=str(VIEWS/(name+'.png')))
    c=Canvas(str(OUT/'R05-engineering-review.pdf'),pagesize=(842,595))
    def title(sub):
        c.setFont('Plex',20);c.drawString(28,560,'WEAZLBOOK / R05')
        c.setFont('Plex',10);c.drawString(28,538,sub)
        c.setFont('Plex',8);c.drawString(28,20,'UNPRINTED PROTOTYPE / dimensions in mm / measured fit and retention gates remain open')
    def pic(name,x,y,w,h):c.drawImage(str(VIEWS/(name+'.png')),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
    title('ACTUAL CAD PROJECTIONS / approved external envelope retained')
    pic('front',20,70,255,440);pic('side',285,70,160,440);pic('isometric',475,130,330,360)
    c.setFont('Plex',11);c.drawString(80,54,'80 wide × 156 tall');c.drawString(290,54,'14 → 26 deep')
    c.setFont('Plex',9);c.drawString(485,100,'Front plane Z0; rear Z14+Y/13')
    c.drawString(485,83,'R04 front bevel / six service posts retained')
    c.showPage();title('SECTION X40 / EXPLODED GEOMETRY / service screw and load-path review')
    pic('section-x40',25,80,265,430);pic('exploded',320,80,470,430)
    c.setFont('Plex',9);c.drawString(30,52,'Section slab thickness0.2; exploded Z offsets are illustrative')
    c.showPage();title('DIMENSION AND CLEARANCE LEDGER / values computed from R05 sources')
    rows=[('Shell outline','80 × 156; outer octagon preserved'),('Rear envelope','14 at Y0;26 at Y156'),('Glass pocket','56.84 × 97.22; starts Z2.1'),('Glass allowance','56.24 × 96.62 × 1.02'),('Battery tray rim','Z16.4; nominal plane gap1.115 at Y74.3'),('Nav rear to PCB','Z12.5 → Z14 =1.5'),('FPC loop assumption','R2;33.66 length;tipY93;apexY114.998'),('FPC apex to nav','Y117-114.998 =2.002; bend NOT approved'),('Battery plug turn','X3.2-2.4 =0.8; real lead turn unresolved'),('Mainboard clamps','0.2 nominal shim gap above PCB'),('Service pilots','diameter1.7;depth7;M2x8 candidate'),('Key guide / stop','0.2 per side;0.4 travel;carrier retention OPEN'),('Part collision volumes',str(len(checks['interferences']))+' intersections >0.001 mm3'),('Component block collisions',str(len(checks['component_interferences']))+' intersections >0.001 mm3')]
    y=500
    for label,value in rows:c.setFont('Plex',9);c.drawString(30,y,label);c.drawString(265,y,value);y-=27
    c.showPage();title('LOAD PATHS / ASSEMBLY ACCESS / PHYSICAL GATES')
    text=[
    'Thumb → nav PCB bearing edges → front carrier → columns → chin/frame.',
    'Glass and battery are excluded from the thumb load path.',
    'Display → measured compliant gasket/insulation → bezel/front ledge + bridges.',
    'Battery → tray floor and loose fabric strap → two shell-side tray lugs.',
    'Mainboard → three R04 underlap supports; removable edge clamps retain it.',
    'Rear cover → six M2 service posts. Check engagement and blind-hole floor.',
    'Driver carrier attaches to cover: opening/FPC access must be demonstrated.',
    'Driver Y slots allow ±3 adjustment; seated tail tip is not connector mouth.',
    'Key carrier retention and VBUS sensor mounting remain OPEN CAD gates.',
    'USB cable and PH plug must be inserted simultaneously for fit verification.',
    'No physical battery life, RF, USB-copy or drop-test result is asserted.',
    ]
    y=495
    for line in text:c.setFont('Plex',10);c.drawString(30,y,line);y-=36
    c.save()

def plate_audit():
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    prod='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
    def transform(text):
        if not text:return np.eye(4)
        a=np.array(list(map(float,text.split()))).reshape(4,3);m=np.eye(4);m[:3,:3]=a[:3,:].T;m[:3,3]=a[3];return m
    results=[]
    for path in sorted((ROOT/'artifacts/plates').glob('*.3mf')):
        with ZipFile(path) as z:
            root=ET.fromstring(z.read('3D/3dmodel.model'));objects={o.get('id'):o for o in root.findall('m:resources/m:object',ns)}
            entries=[]; footprints=[]
            for item in root.findall('m:build/m:item',ns):
                obj=objects[item.get('objectid')];comp=obj.find('m:components/m:component',ns)
                subpath=comp.get(prod+'path').lstrip('/');sub=ET.fromstring(z.read(subpath))
                mesh=sub.find('.//m:mesh',ns);v=np.array([[float(n.get(k)) for k in ('x','y','z')] for n in mesh.findall('m:vertices/m:vertex',ns)])
                matrix=transform(item.get('transform'))@transform(comp.get('transform'))
                v=(np.c_[v,np.ones(len(v))]@matrix.T)[:,:3];lo=v.min(0);hi=v.max(0)
                triangles=[[int(t.get(k)) for k in ('v1','v2','v3')] for t in mesh.findall('m:triangles/m:triangle',ns)]
                shapes=[Polygon(v[t,:2]) for t in triangles]
                footprints.append(unary_union([p for p in shapes if p.area>1e-8]))
                entries.append({'name':Path(subpath).name,'min':lo.tolist(),'max':hi.tolist(),'within_bed':bool(lo[0]>=-0.01 and lo[1]>=-0.01 and lo[2]>=-.01 and hi[0]<=250.01 and hi[1]<=250.01 and hi[2]<=250.01)})
            # AABB checks conservatively flag nesting, rather than calling it proven collision.
            overlaps=[]
            for i,a in enumerate(entries):
                for b in entries[i+1:]:
                    d=np.minimum(a['max'][:2],b['max'][:2])-np.maximum(a['min'][:2],b['min'][:2])
                    if np.all(d>.01):overlaps.append([a['name'],b['name']])
            true_overlap=[]
            for i,a in enumerate(footprints):
                for j,b in enumerate(footprints[i+1:],i+1):
                    area=a.intersection(b).area
                    if area>.001:true_overlap.append({'a':entries[i]['name'],'b':entries[j]['name'],'area_mm2':area})
            results.append({'project':path.name,'entries':entries,'xy_aabb_overlaps':overlaps,'actual_projected_overlaps':true_overlap,'within_bed':all(e['within_bed'] for e in entries)})
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            fig,ax=plt.subplots(figsize=(8,8));ax.set_aspect('equal');ax.set_xlim(0,250);ax.set_ylim(0,250);ax.set_title(path.name+' / exported slicer placement')
            for i,shape in enumerate(footprints):
                for poly in ([shape] if shape.geom_type=='Polygon' else shape.geoms):
                    ax.fill(*poly.exterior.xy,color='#94b852',alpha=.65)
                    for interior in poly.interiors:ax.fill(*interior.xy,color='white')
                ax.text(shape.centroid.x,shape.centroid.y,str(i+1),fontsize=7,ha='center')
            ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.grid(alpha=.2);fig.savefig(ROOT/'artifacts/plates'/f'{path.stem}-placement.png',dpi=120);plt.close(fig)
    (ROOT/'evidence/plate-placement.json').write_text(json.dumps(results,indent=2))
    print([(r['project'],r['within_bed'],len(r['actual_projected_overlaps'])) for r in results])
if __name__=='__main__':report();plate_audit()
