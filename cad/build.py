"""R05 editable CadQuery assembly. Exports prototype parts, not fit certification."""
import json
import math
from pathlib import Path
import cadquery as cq
import trimesh

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT/'cad/parameters.json').read_text())
OUT = ROOT/'artifacts/cad'; OUT.mkdir(parents=True, exist_ok=True)
for directory in ('step','stl','views','coupons'): (OUT/directory).mkdir(exist_ok=True)
SHELL=[(7,0),(73,0),(80,7),(80,141),(73,156),(7,156),(0,141),(0,7)]
FRONT=[(8.2,2.8),(71.8,2.8),(77.2,8.2),(77.2,140.4),(71.2,153.2),(8.8,153.2),(2.8,140.4),(2.8,8.2)]
INNER=[(8.4,2.4),(71.6,2.4),(77.6,8.4),(77.6,140.6),(71.5,153.6),(8.5,153.6),(2.4,140.6),(2.4,8.4)]
POSTS=[(6.2,9),(73.8,9),(4.4,68),(75.2,68),(15,150.4),(65,150.4)]

def rear(y): return P['top_depth']+(P['bottom_depth']-P['top_depth'])*y/P['height']
def box(x,y,z,w,h,d): return cq.Solid.makeBox(w,h,d,cq.Vector(x,y,z))
def cyl(x,y,z,r,h): return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def poly(points,z,h): return cq.Workplane('XY').polyline(points).close().extrude(h).translate((0,0,z)).val()
def loft(rings): return cq.Solid.makeLoft([cq.Wire.makePolygon([cq.Vector(*v) for v in ring],close=True) for ring in rings],ruled=True)
def join(shapes):
    s=shapes[0]
    for q in shapes[1:]: s=s.fuse(q)
    return s.clean()
def slot(x,y,z,length,width,depth):
    return cq.Workplane('XY').center(x,y).slot2D(length,width,angle=90).extrude(depth).translate((0,0,z)).val()

parts={}; colors={}; coupons={}
def add(name,shape,color='black'):
    parts[name]=shape.clean(); colors[name]=color; return shape

outer=loft([[(x,y,0) for x,y in FRONT],[(x,y,3) for x,y in SHELL],[(x,y,rear(y)-P['cover_thickness']-P['cover_gap']) for x,y in SHELL]])
cavity=loft([[(x,y,P['wall']) for x,y in INNER],[(x,y,rear(y)+2) for x,y in INNER]])
frame=outer.cut(cavity)
frame=frame.cut(box(11.58,8.7,2.1,56.84,97.22,4))
frame=frame.cut(box(13.7,10.9,-1,52.6,87,5))
bezel_blank=box(8,5,0,64,103.8,1.5)
frame=frame.cut(box(7.8,4.8,-1,64.4,104.2,2.5))
frame=frame.cut(cyl(40,129.5,-1,7,5))
for x in (24,56): frame=frame.cut(box(x-5.2,145.3,-2,10.4,6.4,6))
usb=box(-3,135.5,12.8,14,15.5,10.5); frame=frame.cut(usb)
for x,y in POSTS:
    top=rear(y)-P['cover_thickness']-P['cover_gap']
    post=cyl(x,y,1.5,P['post_radius'],top-1.5)
    post=post.cut(cyl(x,y,top-7,P['pilot_diameter']/2,8))
    frame=frame.fuse(post)
# Real mainboard underlap; pilot holes are for edge clamps, not fictitious PCB holes.
supports=[(10,121,16,2,18,121.5),(72,121,3.3,2,73.5,121.5),(36,146.4,9,2.5,40.5,148)]
for x,y,w,h,cx,cy in supports:
    frame=frame.fuse(box(x,y,2.2,w,h,11.8))
    frame=frame.cut(cyl(cx,cy,8,0.75,6.1))
for n,(cx,cy,edge_y) in enumerate(((18,121.5,120.5),(73.5,121.5,120.5),(40.5,148,147.6))):
    lip_y=120.5 if n<2 else 145.8
    clamp=box(cx-1.3,lip_y,15.8,2.6,3.8,1.0)
    clamp=clamp.fuse(box(cx-1.3,edge_y,14,2.6,1.3,1.8))
    clamp=clamp.cut(cyl(cx,cy,13,.9,5))
    add(f'mainboard_clamp_{n}',clamp)
# Nav load columns run directly to front/chin, clear glass and flex Y<=116.
for x,y in [(26.5,118),(57.5,118),(26.5,140),(57.5,140)]:
    frame=frame.fuse(cyl(x,y,2.2,1.5,6))
    frame=frame.cut(cyl(x,y,4,0.75,5))
# Carrier supports at exterior edges of glass, extending rearward without glass contact.
for x,y in [(9.5,40),(9.5,100),(70.5,40),(73.8,100)]:
    frame=frame.fuse(cyl(x,y,1.3,1.5,3.3))
    frame=frame.cut(cyl(x,y,2,0.75,4))
# Color inserts have actual shallow pockets.
for x,y,h in [(3.6,29,20),(74.3,37,17)]:
    frame=frame.cut(box(x-.15,y-.15,-1,2.4,h+.3,1.7))
frame=frame.cut(box(9.8,121.8,14,65.7,25.8,1.8))
add('shell',frame,'acid_green')
cover=loft([[(x,y,rear(y)-P['cover_thickness']) for x,y in SHELL],[(x,y,rear(y)) for x,y in FRONT]]).cut(usb)
for x,y in POSTS:
    cover=cover.cut(cyl(x,y,0,P['screw_clearance']/2,40))
    cover=cover.cut(cyl(x,y,rear(y)-1.0,2.05,4))
# Engraved inside, aligned with the sloped inner plane. Text cut is shallow.
text=cq.Workplane('XY').text('NEVER TAX THE GIG',3.0,.4,combine=True,fontPath=str(ROOT/'baseline/research/fonts/IBMPlexMono-Regular.ttf')).val()
text=text.rotate((0,0,0),(1,0,0),math.degrees(math.atan(1/13))).translate((40,31,rear(31)-P['cover_thickness']-.05))
cover=cover.cut(text)
add('service_cover',cover)
bezel=bezel_blank.cut(box(13.9,11,-1,52.2,86.8,4))
# Bezel screw pattern avoids glass footprint; M1.6 pilot pockets in shell.
for x,y in [(9.5,7),(70.5,7),(9.5,107),(70.5,107)]:
    bezel=bezel.cut(cyl(x,y,-1,.9,4))
    parts['shell']=parts['shell'].cut(cyl(x,y,1.5,.65,2))
add('bezel',bezel)
# Rigid front-side nav carrier. Hole centers belong to carrier, NOT nav PCB.
nav=box(25,116.5,8.2,33.8,26.5,1.2).cut(box(30,119.5,7,25,20,4))
for x,y in [(26.5,118),(57.5,118),(26.5,140),(57.5,140)]: nav=nav.cut(cyl(x,y,7,.9,4))
add('nav_carrier',nav)
# Edge retainer strips above PCB; provisional component-free edge strips need bench check.
for n,y in enumerate((118,140)):
    rail=box(25,y-1,12.7,7,2,1.0).fuse(box(25,y-1,9.4,2.5,2,3.3))
    rail=rail.cut(cyl(26.5,y,8,.9,7))
    add(f'nav_retainer_{n}',rail)
# Thin display support strips only in reserved rear backing allowance.
for n,y in enumerate((39,99)):
    strip=box(8, y,4.6,64,2,0.5)
    for x in (9.5,70.5): strip=strip.cut(cyl(x,y+1,4,.9,2))
    # Right lower mount relocated to avoid cell bay; lower strip ends before battery.
    if n: strip=box(8,y,4.6,30,2,.5).cut(cyl(9.5,y+1,4,.9,2))
    add(f'display_bridge_{n}',strip)
# Adjustable driver carrier sits behind driver envelope, slotted +/-3 mm in Y.
driver=box(6.4,50,13.7,24,49,1.0)
driver=driver.cut(box(8,54,13,20,41,3))
for x in (8,28.5):
    for y in (52,97): driver=driver.cut(slot(x,y,13,7,1.8,3))
# Side cheeks retain board laterally, without inventing PCB mounting holes.
for x in (5.8,29.4): driver=driver.fuse(box(x,53.7,5.3,1.2,41.6,8.5))
for y in (53,95.3): driver=driver.fuse(box(5.8,y,5.3,24.8,.7,8.5))
driver=driver.cut(box(7.5,47.8,7.6,21.2,6.4,2.8))
add('driver_carrier_adjustable',driver)
# Cover-side mounting bosses terminate on carrier rear face. The screws pass
# through Y slots from the open front of this removable driver/cover subassembly.
for x in (8,28.5):
    for y in (52,97):
        boss=cyl(x,y,14.7,1.5,rear(y)-P['cover_thickness']-14.7+.2)
        boss=boss.cut(cyl(x,y,14.6,.65,3.2))
        parts['service_cover']=parts['service_cover'].fuse(boss)
# Reduce rim by 0.5 mm to improve rear clearance; preserve floor, cell bay and notch.
tray=box(39.3,74.3,8.6,33.4,39.4,P['battery_tray_rim_z']-8.6).cut(box(40,75,9.5,32,38,9))
tray=tray.cut(box(53.5,112.8,14.9,5.5,1.4,3))
# Two tie slots outside pouch floor; strap is replaceable fabric, not squeezing cell.
for y in (82,103):
    tray=tray.cut(box(39, y,10.2,1.5,6,1.0))
    tray=tray.cut(box(71.5,y,10.2,1.5,6,1.0))
for y in (80,106):
    tray=tray.fuse(box(72.5,y-2,8.6,3.8,4,.9)).cut(cyl(74.5,y,8,.9,3))
    post=cyl(74.5,y,2.2,1.65,6.4).cut(cyl(74.5,y,5,.65,4))
    parts['shell']=parts['shell'].fuse(post)
add('battery_tray',tray)
for x,label in ((24,'back'),(56,'mark')):
    # Removable 95A TPU shoe over a rigid ABS head/neck; ABS defines hard travel.
    key=box(x-4,146.5,-.5,8,4,.6).fuse(box(x-3.7,146.8,.1,7.4,3.4,2.3))
    key=key.fuse(box(x-5.7,144.2,2.4,11.4,8.6,.8))
    key=key.fuse(cyl(x,148.5,3.2,1.25,.2))
    add(label+'_key',key)
    face=box(x-5,145.5,-1.5,10,6,2.1)
    clearance=P['key_face_clearance']
    face=face.cut(box(x-4-clearance,146.5-clearance,-.6,8+2*clearance,4+2*clearance,.8))
    face=face.cut(box(x-3.7-clearance,146.8-clearance,.2,7.4+2*clearance,3.4+2*clearance,.6))
    add(label+'_tpu_face',face,'tpu_black')
    carrier=box(x-6,143,7.9,12,10,1.2).cut(box(x-2.8,146.2,7,5.6,4.6,4))
    for dx in (-3.25,3.25):
        for dy in (-2.25,2.25): carrier=carrier.cut(cyl(x+dx,148.5+dy,7,.65,4))
    # Stop ledges under retaining flange; preload is set by shims/coupon.
    for dx in (-5.8,4.8): carrier=carrier.fuse(box(x+dx,144.2,3.6,1,8.6,4.4))
    # Feet seat on front and take load through frame; captive under removable
    # shell-side guide rails. A press-fit alone is not accepted as retention.
    # Outside flange width in X is only 0.3 mm per side: do not pretend this
    # supports a printable snap. Retention remains a measured chin-rail gate.
    add(label+'_carrier',carrier)
adapter=cyl(40,129.5,-1.6,3,4.7)
s=P['nav_stem_square']+P['nav_adapter_clearance']
adapter=adapter.cut(box(40-s/2,129.5-s/2,.1,s,s,4))
adapter=adapter.fuse(box(38.8,128.3,-3.2,2.4,2.4,1.6))
add('cap_adapter_provisional',adapter)
add('cyan_insert',box(3.6,29,0,2.1,20,.5),'cyan')
add('magenta_insert',box(74.3,37,0,2.1,17,.5),'magenta')

# Explicit part seats: subtract mating carrier/bezel volumes from frame, with a
# small clearance at printed side faces. Nominal planar bearing faces remain.
parts['shell']=parts['shell'].cut(box(7.8,4.8,-.1,64.4,104.2,1.6))
parts['shell']=parts['shell'].cut(nav)
parts['shell']=parts['shell'].cut(driver)
cover=parts['service_cover']

# Component envelopes and provisional keepouts are exported ONLY in reference STEP.
env={
 'glass':box(11.88,9,2.2,56.24,96.62,1.02),
 'display_backing':box(11.58,8.7,3.22,56.84,97.22,1.28),
 'driver':box(7.13,54,5.5,22,41,8),
 'driver_header':box(7.7,48,7.8,20.8,6,2.4),
 'cell':box(41,76,9.7,30,36,6),
 'nav_pcb':box(28,117,9.4,31,25,1.6),
 'nav_rear':box(28,117,11,31,25,1.5),
 'nav_mechanism':box(32.5,122,3.4,15,15,6),
 'nav_header':box(59,117,8.5,12,25,4),
 'mainboard_pcb':box(10,122,14,65.3,25.4,1.6),
 'module':box(49.8,125.7,15.6,25.5,18.2,3.25),
 'usb':box(9.5,137.8,15.6,8.3,9.1,3.8),
 'battery_socket':box(9.1,128.7,15.6,6.9,8.4,5.5),
 'battery_plug':box(3.2,129.2,15.8,6,7.4,5),
 'ph_check':box(2.4,124,14.9,7,12.7,6.2),
 'fpc_turn':box(11.5,105,4.55,40.5,11,3.45),
}
# Coupons: dimensions form their labels; full labeling in adjacent manifest.
for i,d in enumerate((1.5,1.6,1.7,1.8,1.9)):
    q=box(0,0,0,10,10,7).cut(cyl(5,5,1,d/2,7)); coupons[f'pilot_{d:.1f}mm']=q
for c in (.05,.1,.15,.2,.25):
    s=P['nav_stem_square']+c
    coupons[f'nav_square_{s:.2f}mm']=box(0,0,0,8,8,5).cut(box(4-s/2,4-s/2,1,s,s,5))
coupons['key_guide']=box(0,0,0,16,12,2.4).cut(box(2.8,2.8,-1,10.4,6.4,5))
coupons['key_slider']=parts['back_key'].translate((-18,-143,1.5))
coupons['key_tpu_face']=parts['back_tpu_face'].translate((-18,-143,1.5))
# Local simultaneous connector wall/roof section: real shell geometry, 100% scale.
coupons['ph_usb_wall']=parts['shell'].intersect(box(-1,123,0,20,30,28))
coupons['ph_usb_cover']=cover.intersect(box(-1,123,0,20,30,28))
coupons['fpc_radius_2_assumption']=box(0,0,0,16,10,3).fuse(cq.Solid.makeCylinder(2,16,cq.Vector(0,5,3),cq.Vector(1,0,0)))

def export():
    report={'revision':P['revision'],'status':'UNPRINTED PROTOTYPE — collisions and retention gates must be closed','parts':{},'interferences':[],'component_interferences':[]}
    assy=cq.Assembly(name='WeazlBook_R05_prototype'); ref=cq.Assembly(name='R05_reference_envelopes_NOT_PRINTABLE')
    palette={'acid_green':(.55,.91,.025),'black':(.08,.08,.08),'tpu_black':(.13,.13,.13),'cyan':(0,.7,.8),'magenta':(.8,0,.4)}
    for name,s in parts.items():
        assert s.isValid(),name
        cq.exporters.export(s,str(OUT/'step'/f'{name}.step'))
        cq.exporters.export(s,str(OUT/'stl'/f'{name}.stl'),tolerance=.04,angularTolerance=.15)
        mesh=trimesh.load(OUT/'stl'/f'{name}.stl',force='mesh')
        bb=s.BoundingBox()
        report['parts'][name]={'valid':s.isValid(),'solids':len(s.Solids()),'watertight':bool(mesh.is_watertight),'volume_mm3':s.Volume(),'bounds_mm':[[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]],'color':colors[name]}
        assy.add(s,name=name,color=cq.Color(*palette[colors[name]]))
    for name,s in env.items(): ref.add(s,name=name,color=cq.Color(.9,.5,.1,.4))
    assy.save(str(OUT/'assembly.step')); ref.save(str(OUT/'reference_envelopes.step'))
    keys=list(parts)
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            vol=parts[a].intersect(parts[b]).Volume()
            if vol>.001: report['interferences'].append({'a':a,'b':b,'volume_mm3':round(vol,4)})
        for b,shape in env.items():
            vol=parts[a].intersect(shape).Volume()
            if vol>.001: report['component_interferences'].append({'part':a,'envelope':b,'volume_mm3':round(vol,4)})
    for name,s in coupons.items():
        assert s.isValid(),name
        cq.exporters.export(s,str(OUT/'coupons'/f'{name}.stl'),tolerance=.04)
    compound=cq.Compound.makeCompound(list(parts.values()))
    for name,vec in [('front',(0,0,-1)),('side',(1,0,0)),('isometric',(1,-1,-1))]:
        cq.exporters.export(compound,str(OUT/'views'/f'{name}.svg'),exportType='SVG',opt={'projectionDir':vec,'showHidden':False,'width':800,'height':1000})
    exploded=cq.Compound.makeCompound([s.translate((0,0,i*5)) for i,s in enumerate(parts.values())])
    cq.exporters.export(exploded,str(OUT/'views/exploded.svg'),exportType='SVG',opt={'projectionDir':(1,-1,1),'showHidden':False,'width':1000,'height':1000})
    (ROOT/'evidence/cad-checks.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'parts':len(parts),'part_collisions':report['interferences'],'envelope_collisions':report['component_interferences']}))

if __name__=='__main__': export()
