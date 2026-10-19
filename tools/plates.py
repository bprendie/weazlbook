"""Export authentic Anycubic Slicer Next projects using its installed profiles.
No G-code is generated. Provisional PolyLite ABS flow limit awaits calibration.
"""
import json
import os
import subprocess
from pathlib import Path
import trimesh
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/opt/AnycubicSlicerNext')
PROFILE=BASE/'resources/profiles/Anycubic'
OUT=ROOT/'artifacts/plates';OUT.mkdir(parents=True,exist_ok=True)
PROF=ROOT/'cad/print_profiles';PROF.mkdir(exist_ok=True)
def resolve(kind,name):
    d=json.loads((PROFILE/kind/(name+'.json')).read_text())
    parent=d.get('inherits');result=resolve(kind,parent) if parent else {}
    result.update(d);result['inherits']='';return result

machine=resolve('machine','Anycubic Kobra S1 0.4 nozzle')
machine['single_extruder_multi_material']='0'
machine['printer_notes']='R05: Kobra S1 0.4 confirmed by user. Separate-color plates. No ACE assumed.'
process=resolve('process','0.20mm Standard @Anycubic Kobra S1 0.4 nozzle')
process.update({'name':'WeazlBook R05 ABS prototype 0.20','print_settings_id':'WeazlBook R05 ABS prototype 0.20','layer_height':'0.2','initial_layer_print_height':'0.2','wall_loops':'4','top_shell_layers':'5','bottom_shell_layers':'5','sparse_infill_density':'25%','sparse_infill_pattern':'gyroid','outer_wall_speed':'70','inner_wall_speed':'150','sparse_infill_speed':'200','internal_solid_infill_speed':'150','top_surface_speed':'60','gap_infill_speed':'60','initial_layer_speed':'30','initial_layer_infill_speed':'40','normal_acceleration':'5000','outer_wall_acceleration':'2000','enable_support':'1','support_type':'normal(auto)','support_threshold_angle':'35','support_on_build_plate_only':'0','support_top_z_distance':'0.2','brim_type':'outer_only','brim_width':'8','enable_prime_tower':'0'})
filament=resolve('filament','Generic ABS @Anycubic Kobra S1 0.4 nozzle')
filament.update({'name':'WeazlBook Polymaker PolyLite ABS PROVISIONAL','filament_settings_id':['WeazlBook Polymaker PolyLite ABS PROVISIONAL'],'filament_vendor':['Polymaker'],'filament_type':['ABS'],'nozzle_temperature':['260'],'nozzle_temperature_initial_layer':['260'],'hot_plate_temp':['100'],'hot_plate_temp_initial_layer':['100'],'textured_plate_temp':['100'],'textured_plate_temp_initial_layer':['100'],'filament_max_volumetric_speed':['12'],'fan_min_speed':['0'],'fan_max_speed':['0'],'overhang_fan_speed':['20'],'additional_cooling_fan_speed':['0'],'filament_notes':['User specified Polymaker ABS, exact product pending. PolyLite assumption; flow 12 mm3/s provisional. Calibrate before speed increase. No XY shrink compensation until measured.']})
for name,d in [('machine',machine),('process',process),('filament',filament)]:
    (PROF/(name+'.json')).write_text(json.dumps(d,indent=2))
tpu=resolve('filament','Generic TPU @Anycubic Kobra S1 0.4 nozzle')
tpu.update({'name':'WeazlBook TPU 95A PROVISIONAL','filament_settings_id':['WeazlBook TPU 95A PROVISIONAL'],'filament_type':['TPU'],'filament_max_volumetric_speed':['2'],'filament_notes':['95A confirmed by user; product unspecified. Use external spool. Separate removable key faces, not rigid guides/stops. Calibrate fit.']})
tpu_process=dict(process)
tpu_process.update({'name':'WeazlBook TPU 95A key faces','print_settings_id':'WeazlBook TPU 95A key faces','outer_wall_speed':'20','inner_wall_speed':'25','sparse_infill_speed':'25','internal_solid_infill_speed':'25','top_surface_speed':'20','gap_infill_speed':'20','initial_layer_speed':'15','initial_layer_infill_speed':'15','normal_acceleration':'1000','outer_wall_acceleration':'800','sparse_infill_density':'100%','sparse_infill_pattern':'rectilinear','wall_loops':'3','enable_support':'0','brim_width':'3','brim_type':'outer_only'})
for name,d in [('tpu_filament',tpu),('tpu_process',tpu_process)]:
    (PROF/(name+'.json')).write_text(json.dumps(d,indent=2))

def orient(path,name):
    m=trimesh.load(path,force='mesh')
    if name in ('service_cover','ph_usb_cover'):
        # Outer rear plane to bed: rotate wedge slope flat, then turn over.
        m.apply_transform(trimesh.transformations.rotation_matrix(-np.arctan(1/13),[1,0,0]))
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
    elif name.startswith('nav_retainer') or name=='driver_carrier_adjustable':
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
    m.apply_translation(-m.bounds[0]);return m

def main():
    checks=json.loads((ROOT/'evidence/cad-checks.json').read_text())
    if checks['interferences'] or checks['component_interferences']:
        raise RuntimeError('CAD overlaps must be resolved before plate export')
    groups={'01_coupons':[p for p in (ROOT/'artifacts/cad/coupons').glob('*.stl') if 'tpu' not in p.stem]}
    for color in ('acid_green','black','cyan','magenta','tpu_black'):
        groups[color]=[ROOT/'artifacts/cad/stl'/f'{n}.stl' for n,p in checks['parts'].items() if p['color']==color]
    groups['tpu_black'].append(ROOT/'artifacts/cad/coupons/key_tpu_face.stl')
    # Cover is a separate black plate, making support/orientation review clear.
    cover=ROOT/'artifacts/cad/stl/service_cover.stl'
    groups['black'].remove(cover);groups['black_cover']=[cover]
    env=dict(os.environ);env['LD_LIBRARY_PATH']=str(BASE/'lib')+':'+str(BASE/'usr/lib')
    manifest={}
    for group,paths in groups.items():
        temp=OUT/'oriented'/group;temp.mkdir(parents=True,exist_ok=True)
        files=[]
        for path in paths:
            m=orient(path,path.stem);target=temp/path.name;m.export(target);files.append(str(target))
        project=OUT/(group+'.3mf')
        process_path=PROF/('tpu_process.json' if group=='tpu_black' else 'process.json')
        filament_path=PROF/('tpu_filament.json' if group=='tpu_black' else 'filament.json')
        command=[str(BASE/'usr/bin/AnycubicSlicerNext'),'--datadir',str(OUT/'slicer_data'),'--load-settings',str(PROF/'machine.json')+';'+str(process_path),'--load-filaments',str(filament_path),'--arrange','1','--orient','0','--ensure-on-bed','--export-3mf',str(project),*files]
        run=subprocess.run(command,env=env,capture_output=True,text=True,timeout=180)
        (ROOT/'evidence'/f'slicer-{group}.log').write_text(run.stdout+run.stderr)
        if run.returncode: raise RuntimeError(f'Slicer failed {group}: {run.returncode}; see evidence log')
        inspect=subprocess.run([str(BASE/'usr/bin/AnycubicSlicerNext'),'--datadir',str(OUT/'slicer_data'),'--info',str(project)],env=env,capture_output=True,text=True,timeout=60)
        (ROOT/'evidence'/f'slicer-{group}-reopen.log').write_text(inspect.stdout+inspect.stderr)
        if inspect.returncode:raise RuntimeError('Cannot reopen exported project')
        manifest[group]={'file':str(project.relative_to(ROOT)),'parts':[p.stem for p in paths],'export_exit':run.returncode,'reopen_exit':inspect.returncode,'printed':False,'sliced':False,'profile':'Generic TPU 95A, 2 mm3/s provisional' if group=='tpu_black' else 'Polymaker PolyLite ABS assumption, 12 mm3/s provisional'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
