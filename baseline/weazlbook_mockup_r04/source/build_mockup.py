"""WeazlBook R04: dimensioned approval blockout, not production CAD.

All coordinates in mm: X right, Y down, Z rearward from the shell front.
Published footprints are distinguished from provisional occupied envelopes.
Run with PYTHONPATH=/tmp/weazlbook-render-deps python3 source/build_mockup.py.
"""
from pathlib import Path
import math, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cadquery as cq
import moderngl

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'render'; OUT.mkdir(exist_ok=True)
FONT=ROOT.parent/'research/fonts/IBMPlexMono-Regular.ttf'
BOLD=ROOT.parent/'research/fonts/IBMPlexMono-SemiBold.ttf'
W,H=80.,156.
def rear(y): return 14+12*y/H
ACID=(.55,.91,.025); BLACK=(.043,.050,.051); DARK=(.065,.078,.079)
MAGENTA=(.77,.016,.27); CYAN=(.02,.65,.72); METAL=(.36,.40,.41)
BLUE=(.02,.24,.38); BATTERY=(.61,.64,.63); GOLD=(.63,.35,.035)
PANEL=(.78,.79,.72)
SHELL=[(7,0),(73,0),(80,7),(80,141),(73,156),(7,156),(0,141),(0,7)]
FRONT=[(8.2,2.8),(71.8,2.8),(77.2,8.2),(77.2,140.4),(71.2,153.2),(8.8,153.2),(2.8,140.4),(2.8,8.2)]
INNER=[(8.4,2.4),(71.6,2.4),(77.6,8.4),(77.6,140.6),(71.5,153.6),(8.5,153.6),(2.4,140.6),(2.4,8.4)]

def wire(points): return cq.Wire.makePolygon([cq.Vector(*p) for p in points],close=True)
def loft(rings): return cq.Solid.makeLoft([wire(r) for r in rings],ruled=True)
def flatpoly(points,z,h): return cq.Workplane('XY').polyline(points).close().extrude(h).translate((0,0,z)).val()
def rect(x,y,z,w,h,d): return cq.Solid.makeBox(w,h,d,cq.Vector(x,y,z))
def cyl(x,y,z,r,d): return cq.Solid.makeCylinder(r,d,cq.Vector(x,y,z))
def octagon(x,y,w,h,c=2): return [(x+c,y),(x+w-c,y),(x+w,y+c),(x+w,y+h-c),(x+w-c,y+h),(x+c,y+h),(x,y+h-c),(x,y+c)]

parts=[]
def add(name,shape,color,group='shell',texture=None,grain=0.0):
    parts.append(dict(name=name,shape=shape,color=color,group=group,texture=texture,grain=grain))
    return shape

# The outer and inner walls have the same real taper in every view.
outer=loft([[(x,y,0) for x,y in FRONT],[(x,y,3) for x,y in SHELL],[(x,y,rear(y)-2.6) for x,y in SHELL]])
cavity=loft([[(x,y,2.4) for x,y in INNER],[(x,y,rear(y)+3) for x,y in INNER]])
frame=outer.cut(cavity)
frame=frame.cut(rect(11.58,8.7,2.1,56.84,97.22,3))
# Front display aperture and controls.
frame=frame.cut(rect(13.7,10.9,-2,52.6,87.0,8))
frame=frame.cut(cyl(40,129.5,-2,5.4,8))
for x in (24,56): frame=frame.cut(rect(x-4,145,-2,8,6,8))
# Broad native USB opening. It is open to the edge, not a narrow cable tunnel.
usb_void=rect(-3,135.5,12.8,14,15.5,10.5)
frame=frame.cut(usb_void)
# Six service screw posts, outside component envelopes.
posts=[(6.2,9),(73.8,9),(4.4,68),(75.2,68),(15,150.4),(65,150.4)]
for x,y in posts:
    post=cyl(x,y,2.4,2.45,rear(y)-5.2).cut(cyl(x,y,-1,1.1,32))
    frame=frame.fuse(post)
    frame=frame.cut(cyl(x,y,-1,1.1,6))
add('Acid green shell',frame,ACID,grain=1)
cover=loft([[(x,y,rear(y)-2.25) for x,y in SHELL],[(x,y,rear(y)) for x,y in FRONT]])
cover=cover.cut(usb_void)
for x,y in posts: cover=cover.cut(cyl(x,y,0,1.25,35))
add('Removable rear cover',cover,BLACK,'cover',grain=1)

# Black front screen plate is a true ring around the actual active area.
bezel=flatpoly(octagon(8.0,5.0,64.,103.8,2.2),-.15,1.65)
bezel=bezel.cut(rect(13.9,11.0,-1,52.2,86.8,5))
add('Screen bezel',bezel,BLACK,grain=1)
for x,y in [(10.4,7.8),(69.6,7.8),(10.4,106.2),(69.6,106.2)]:
    head=cyl(x,y,-.6,1.55,.65).cut(cyl(x,y,-.8,.68,.4))
    add('Bezel fastener',head,METAL)
for x,y in posts:
    head=cyl(x,y,-.35,1.75,.45).cut(cyl(x,y,-.5,.7,.35))
    add('Service screw',head,(.16,.19,.20))
    add('Rear screw',cyl(x,y,rear(y)-.1,1.7,.2),METAL,'cover')

# Published glass dimensions. 1.02 includes published +0.10 tolerance.
add('Raw display glass',rect(11.88,9,2.2,56.24,96.62,1.02),PANEL,'inside')
add('Display back insulation allowance',rect(11.58,8.7,3.22,56.84,97.22,1.28),DARK,'inside')

def font(n,b=False): return ImageFont.truetype(str(BOLD if b else FONT),n)
screen=Image.new('RGB',(480,800),(220,222,207)); d=ImageDraw.Draw(screen)
d.text((25,29),'CHAPTER 12',font=font(21,b=True),fill=(21,25,24))
d.line((25,71,455,71),fill=(42,47,44),width=1)
lines=['He kept the books on a','machine he could open','with a screwdriver.','','Outside, every sign','wanted his name.','','He passed them under','the sodium lamps, one','dark window at a time.','','The little screen','asked for nothing.']
for i,line in enumerate(lines): d.text((25,110+39*i),line,font=font(23),fill=(23,27,25))
d.line((25,739,455,739),fill=(90,94,87),width=1)
d.text((25,757),'LOCAL',font=font(16),fill=(38,43,39)); d.text((355,757),'12 / 38',font=font(16),fill=(38,43,39))
screen.save(OUT/'screen_sample.png')

# Replaceable printed navigation surround. Cap dimensions are a reserved envelope.
navface=flatpoly(octagon(27.2,117.2,25.6,24.6,4),-.7,2.5).cut(cyl(40,129.5,-2,5.1,6))
add('Navigation faceplate',navface,BLACK,grain=1)
rim=flatpoly(octagon(32.8,122.3,14.4,14.4,3),-1.2,.8).cut(cyl(40,129.5,-2,5.1,4))
add('Magenta navigation surround',rim,MAGENTA,grain=1)
add('Printed cap adapter envelope',cyl(40,129.5,-1.7,3.0,5.0),DARK)
cap=cyl(40,129.5,-3.8,4.8,2.3)
add('Black rubber cap envelope',cap,BLACK)
for a in range(-3,4):
    for b in range(-3,4):
        if a*a+b*b<11: add('Cap texture',cyl(40+a*1.1,129.5+b*1.1,-3.95,.24,.2),DARK)
for x,y in [(29.8,120.5),(50.2,120.5),(29.8,139),(50.2,139)]:
    add('Nav faceplate screw',cyl(x,y,-.95,1.15,.5).cut(cyl(x,y,-1.1,.45,.3)),METAL)
for x,label in [(24,'BACK'),(56,'MARK')]:
    key=flatpoly(octagon(x-5,145.5,10,6,1.2),-1.5,3.6)
    add(label+' key',key,BLACK,grain=1)
    add(label+' switch envelope',rect(x-6,143,3.5,12,10,9),MAGENTA,'inside')
# Printed accent inserts: purely mechanical, not LEDs or switches.
add('Cyan index insert',flatpoly([(3.6,29),(5.7,26.9),(5.7,49.1),(3.6,51.2)],-.12,.7),CYAN)
add('Magenta index insert',flatpoly([(74.3,37.2),(76.4,35.1),(76.4,53.7),(74.3,55.8)],-.12,.7),MAGENTA)
for x in (14.5,62.5):
    add('Grip facet',flatpoly([(x,115),(x+3,118),(x+3,135),(x,138)],-.08,.5),ACID,grain=1)

# Internals: real planar dimensions, deliberately simplified hardware, no fake ICs.
add('DESPI-C02 occupied envelope',rect(7.13,54,5.5,22,41,8),BLUE,'inside')
add('DESPI PCB',rect(7.13,54,8.6,22,41,1.6),(.025,.17,.25),'inside')
add('DESPI FPC housing allowance',rect(8.5,88,6.0,19,6,2.6),(.78,.79,.74),'inside')
add('DESPI right angle header allowance',rect(7.7,48,7.8,20.8,9,2.4),DARK,'inside')
for x in np.linspace(9,26.8,8): add('Display header pin',rect(x,48,8.5,.5,6,.5),GOLD,'inside')

# Battery pocket is 32 x 38 x 7; cell envelope is 30 x 36 x 6.
batterytray=rect(39.3,74.3,8.6,33.4,39.4,8.3).cut(rect(40,75,9.5,32,38,9))
batterytray=batterytray.cut(rect(53.5,112.8,14.9,5.5,1.4,2.4))
add('Battery tray allowance',batterytray,BLACK,'inside',grain=1)
add('500mAh battery envelope',rect(41,76,9.7,30,36,6),BATTERY,'inside')
add('Battery taped end allowance',rect(41,107.2,9.65,30,4.8,6.1),GOLD,'inside')

# Nav PCB position includes the photographed stem offset (~12 mm from left).
add('31 x 25 nav PCB',rect(28,117,9.4,31,25,1.6),(.06,.25,.18),'inside')
add('Navigation mechanism allowance',rect(32.5,122,3.4,15,15,6),DARK,'inside')
add('Navigation rear allowance',rect(28,117,11,31,25,1.5),(.13,.36,.25),'inside')
add('Nav header plus wire allowance',rect(59,117,8.5,12,25,4),DARK,'inside')

# Mainboard horizontal, component face toward the removable rear.
add('LOLIN S3 PRO PCB',rect(10,122,14,65.3,25.4,1.6),DARK,'inside')
# Official module height, photo-derived X/Y placement and ports.
add('ESP32-S3 module region',rect(49.8,125.7,15.6,25.5,18.2,3.25),METAL,'inside')
add('Antenna region',rect(69,125.7,15.6,6.3,18.2,3.25),BLACK,'inside')
add('USB-C housing allowance',rect(9.5,137.8,15.6,8.3,9.1,3.8),METAL,'inside')
add('USB-C opening',rect(9.35,138.65,16.2,.2,7.4,2.5),BLACK,'inside')
add('Battery JST socket allowance',rect(9.1,128.7,15.6,6.9,8.4,5.5),(.79,.80,.74),'inside')
add('Battery mating plug allowance',rect(3.2,129.2,15.8,6,7.4,5),(.63,.66,.61),'inside')
add('microSD housing allowance',rect(28.3,125.4,15.6,6,11.8,2),METAL,'inside')

# Mainboard edge supports avoid the lower key wells and the USB pocket.
for x,y,w,h in [(10,121,16,2),(72,121,3.3,2),(36,146.4,9,2.5)]:
    add('Mainboard edge support allowance',rect(x,y,2.4,w,h,11.6),BLACK,'inside',grain=1)

def tube(points,r,color,name,group='inside'):
    for p,q in zip(points[:-1],points[1:]):
        a,b=np.asarray(p),np.asarray(q); v=b-a; length=np.linalg.norm(v)
        if length>1e-4: add(name,cq.Solid.makeCylinder(r,float(length),cq.Vector(*a),cq.Vector(*v)),color,group)

# Short harness corridors are shown, with service loops kept out of the cell bay.
for j,col in enumerate(((.55,.055,.055),BLACK)):
    tube([(55+j*1.3,112,16),(55+j*1.3,115.5,16),(6+j*1.3,115.5,17),(6+j*1.3,123,18)],.52,col,'Factory battery lead route to service allowance')
# No fabricated PH lead bend: this local access volume remains a measured-fit gate.
add('Battery plug and lead-turn check volume',rect(2.4,124,14.9,7,12.7,6.2),GOLD,'inside')
for j,col in enumerate((GOLD,BLACK,CYAN)):
    tube([(11+j,48,9),(11+j,44-j,9),(33+j*.8,44-j,9),(33+j*.8,112,13.2),(25+j,116,13.2),(21+j,120,16.3),(21+j,124,16.3)],.38,col,'Display harness corridor illustration; not pinout')

# FPC represents topology only; the amber pocket in the plan carries the fit status.
# Tail-tip route uses R2 and tip y93, both explicitly provisional.
start_y=105.62; tip_y=93.; r=2.; length=33.66
a=(length-(start_y-tip_y)-math.pi*r)/2
path=[(start_y,3.3),(start_y+a,3.3)]
for theta in np.linspace(-math.pi/2,math.pi/2,20):
    path.append((start_y+a+r*math.cos(theta),5.3+r*math.sin(theta)))
path.append((tip_y,7.3))
add('FPC fold pocket: reserved space, not flex geometry',rect(11.5,105.0,4.55,40.5,11.0,3.45),GOLD,'inside')

# Fact / assumption ledger used by the approval sheets.
ledger={
 'revision':'R04','status':'DIMENSIONED APPROVAL BLOCKOUT; NOT PRINT-READY',
 'units':'mm; X right Y down Z rearward from shell front',
 'shell':{'width':80,'height':156,'top_depth':14,'grip_depth':26,'wall_nominal':2.4,'rear_cover':2.2,'controls_protrude':3.95},
 'parts':[
  {'name':'GDEY0397T81P','published':[56.24,96.62,.92],'tolerance':[.2,.2,.1],'xy':[11.88,9],'z_glass':[2.2,3.22],'source':'https://www.good-display.com/product/613.html'},
  {'name':'DESPI-C02','published_pcb':[41,22],'reserved_full_depth':8,'xy':[7.13,54],'xyz_envelope':[7.13,54,5.5,22,41,8],'header_projection':6,'source':'https://www.good-display.com/product/516.html'},
  {'name':'LOLIN S3 PRO','published_pcb':[65.3,25.4],'xy':[10,122],'pcb_z':[14,15.6],'max_regional_z':21.1,'source':'https://www.wemos.cc/en/latest/s3/s3_pro.html'},
  {'name':'Adafruit 1578 500mAh','catalog':[29,36,4.75],'design_cell_envelope':[30,36,6],'bay':[40,75,9.5,32,38,7],'source':'https://www.adafruit.com/product/1578'},
  {'name':'EC Buying navigation','published_pcb':[31,25],'xy':[28,117],'rear_z_max':12.5,'stem_xy_estimated':[40,129.5],'header_and_wire_projection':12,'source':'https://www.amazon.com/dp/B0D8T4YQ3Y'},
  {'name':'Sprintek 109-00060 rubber cap','cap_geometry':'provisional Ø9.6 x2.3; keep Ø14 sweep zone; adapter required','source':'https://store.sprintek.com/category/flexpoint-pointing-stick'},
  {'name':'2 x Omron B3F-1000','published_body':[6,6,4.3],'occupied_bays':[[18,143,3.5,12,10,9],[50,143,3.5,12,10,9]],'source':'https://components.omron.com/us-en/datasheet_pdf/A070-E1.pdf'}],
 'remaining_measurements':['DESPI-C02 full assembly height and exact FPC insertion depth','Navigation stem, cap socket and installed rear depth <=12.5','S3 PCB thickness and connector heights; USB cable boot with battery plug simultaneously inserted','Actual protected cell and wire exit; current GDEY delivered panel suffix'],
 'fpc':{'published_tip_extension':33.66,'reserved_pocket':[11.5,91,3,40.5,25,5],'proposed_bend_radius':2,'proposed_tip_y':93,'computed_apex_y':round(start_y+a+r,3),'status':'Amber block shows fold clearance only, not a fabricated flex model. Provisional new fold; not manufacturer bend validation. Driver carrier must allow adjustment for actual ZIF insertion depth.'},
 'claims_not_made':['No production tolerances or screw lengths frozen','No measured battery runtime','No working firmware represented','No verified RF clearance or antenna performance'],
 'notes':['Major component footprints at source dimensions; connector bodies simplified to allowances','Amber blocks reserve FPC fold space and a PH plug/lead fit check; they are not fabricated hardware models','Colored strands indicate harness corridors, not wire count or a final pinout','Rear access for microSD; no invented external SD slot','Short 28AWG device harness; retain factory protected battery leads','Original concept outer target preserved at the 14/26 mm endpoints']}
(ROOT/'source/component_layout.json').write_text(json.dumps(ledger,indent=2))

# Headless OpenGL renderer. Every view uses the same solids and coordinate system.
os.environ.setdefault('MESA_SHADER_CACHE_DIR','/tmp/weazlbook-mesa-cache')
ctx=moderngl.create_standalone_context(backend='egl')
program=ctx.program(vertex_shader='''#version 330
uniform mat4 mvp; in vec3 position; in vec3 normal; in vec3 color; in float grain;
out vec3 p; out vec3 n; out vec3 c; out float g;
void main(){ p=position; n=normal; c=color; g=grain; gl_Position=mvp*vec4(position,1.0); }
''',fragment_shader='''#version 330
in vec3 p; in vec3 n; in vec3 c; in float g; out vec4 frag; uniform vec3 eye;
float h(vec3 a){return fract(sin(dot(a,vec3(12.9898,78.233,37.719)))*43758.5453);}
void main(){ vec3 nn=normalize(n); if(!gl_FrontFacing) nn=-nn;
vec3 l=normalize(vec3(-.5,.9,1.2)); vec3 l2=normalize(vec3(.7,-.2,-.8));
float light=.48+.42*max(dot(nn,l),0.)+.18*max(dot(nn,l2),0.);
float layers=1.0-g*(.035+.03*sin(p.z*31.416)+.035*h(floor(p*9.)));
vec3 v=normalize(eye-p); float spec=pow(max(dot(nn,normalize(l+v)),0.),35.)*.09;
vec3 base=c*light*layers+spec;
frag=vec4(pow(clamp(base,0.,1.),vec3(.87)),1.); }
''')
texprog=ctx.program(vertex_shader='''#version 330
uniform mat4 mvp; in vec3 position; in vec2 uv; out vec2 t;
void main(){t=uv; gl_Position=mvp*vec4(position,1.0);}
''',fragment_shader='''#version 330
uniform sampler2D tex; in vec2 t; out vec4 frag;
void main(){frag=texture(tex,t); if(frag.a<.1) discard;}
''')
def world(v): return np.asarray((v[0]-40,78-v[1],-v[2]),dtype='f4')
meshes=[]
for p in parts:
    vs,ts=p['shape'].tessellate(.10,.2)
    a=np.array([world(v.toTuple()) for v in vs]); rows=[]
    for tri in ts:
        pts=a[list(tri)]; n=np.cross(pts[1]-pts[0],pts[2]-pts[0]); n=n/(np.linalg.norm(n)+1e-12)
        for v in pts: rows.append([*v,*n,*p['color'],p['grain']])
    buf=ctx.buffer(np.asarray(rows,dtype='f4').tobytes())
    vao=ctx.vertex_array(program,[(buf,'3f 3f 3f 1f','position','normal','color','grain')])
    meshes.append((p,vao))

def lookat(eye,target=(0,0,-8),up=(0,1,0)):
    e=np.array(eye,float); f=np.array(target)-e; f/=np.linalg.norm(f); u=np.array(up,float)
    s=np.cross(f,u); s/=np.linalg.norm(s); u=np.cross(s,f)
    m=np.eye(4); m[:3,:3]=np.array([s,u,-f]); m[:3,3]=-m[:3,:3]@e; return m
def ortho(width,height):
    m=np.eye(4); m[0,0]=2/width; m[1,1]=2/height; m[2,2]=-2/1000; return m

def texquad(im,corners,mvp):
    im=im.convert('RGBA'); tex=ctx.texture(im.size,4,im.tobytes()); tex.filter=(moderngl.LINEAR,moderngl.LINEAR); tex.use()
    data=[]
    uv=[(0,0),(1,0),(1,1),(0,1)]
    for j in (0,1,2,0,2,3): data.append([*world(corners[j]),*uv[j]])
    buf=ctx.buffer(np.asarray(data,dtype='f4').tobytes()); vao=ctx.vertex_array(texprog,[(buf,'3f 2f','position','uv')])
    texprog['mvp'].write(mvp.T.astype('f4').tobytes()); texprog['tex']=0; vao.render(); vao.release(); buf.release(); tex.release()
def label_image(text,w=500,h=80,fg=(184,192,184),bg=(17,20,20),size=42):
    im=Image.new('RGBA',(w,h),bg+(255,)); dr=ImageDraw.Draw(im); dr.text((w/2,h/2),text,font=font(size),fill=fg,anchor='mm'); return im
def render(name,eye,size=(1400,1900),span=187,groups=('shell','cover','inside'),screen_on=True,inside_cover=False):
    fb=ctx.simple_framebuffer(size,components=4,samples=4); fb.use(); fb.clear(.068,.083,.087,1,depth=1)
    ctx.enable(moderngl.DEPTH_TEST); ctx.disable(moderngl.CULL_FACE)
    mvp=ortho(span*size[0]/size[1],span)@lookat(eye)
    program['mvp'].write(mvp.T.astype('f4').tobytes()); program['eye'].value=tuple(eye)
    for p,vao in meshes:
        if p['group'] in groups: vao.render()
    if screen_on:
        texquad(screen,[(14.08,11.2,2.18),(65.92,11.2,2.18),(65.92,97.6,2.18),(14.08,97.6,2.18)],mvp)
        for x,s in [(24,'BACK'),(56,'MARK')]: texquad(label_image(s,240,80,size=43),[(x-4.2,146.8,-1.53),(x+4.2,146.8,-1.53),(x+4.2,149.6,-1.53),(x-4.2,149.6,-1.53)],mvp)
        texquad(label_image('wb // 04',380,70,fg=(20,28,10),bg=(150,215,18),size=42),[(55,111.5,-.12),(70,111.5,-.12),(70,114.3,-.12),(55,114.3,-.12)],mvp)
    if 'inside' in groups:
        # Readable rear-facing labels on honest component envelope blocks.
        for s,x,y,z,w,h in [('DESPI-C02',8.2,69,13.52,20,3.7),('41 x 22',9.2,74,13.52,18,3.5),('500mAh',44,85,15.72,24,5),('LOLIN S3 PRO',16,139,15.63,30,4)]:
            texquad(label_image(s,500,90,size=44),[(x+w,y,z),(x,y,z),(x,y+h,z),(x+w,y+h,z)],mvp)
    if inside_cover:
        texquad(label_image('NEVER TAX THE GIG',900,100,fg=(99,113,108),bg=(16,19,19),size=49),[(16,72,rear(72)-2.29),(64,72,rear(72)-2.29),(64,77.34,rear(77.34)-2.29),(16,77.34,rear(77.34)-2.29)],mvp)
    target=ctx.simple_framebuffer(size,components=4); ctx.copy_framebuffer(target,fb)
    result=Image.frombytes('RGBA',size,target.read(components=4)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGB')
    result.save(OUT/(name+'.png')); fb.release(); target.release(); return result

render('assembled',(-170,150,330),size=(1600,2100),span=186)
render('front',(0,0,380),size=(1200,2100),span=175)
render('left_profile',(-380,0,0),size=(650,2100),span=175,screen_on=False)
render('rear_open',(145,95,-380),size=(1600,2100),span=184,groups=('shell','inside'),screen_on=False)
render('rear_orthographic',(0,0,-380),size=(1200,2100),span=175,groups=('shell','inside'),screen_on=False)
render('inside_cover',(-60,40,380),size=(1200,2100),span=175,groups=('cover',),screen_on=False,inside_cover=True)
print(json.dumps({'solids':len(parts),'output':str(OUT),'fpc_apex_mm':ledger['fpc']['computed_apex_y']}))
