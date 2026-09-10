"""REFERENCE_ONLY=true MEASURED=false FABRICATION_ALLOWED=false
Synthetic boxes only; not camera mounts, machine geometry or manufacturing data.
Run with workspace .venv/bin/python. Existing exports are never overwritten.
"""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import sys
import cadquery as cq
import trimesh

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'exports/concepts/grip-mdf-fdm-r01'
FLAGS = dict(REFERENCE_ONLY=True, MEASURED=False, FABRICATION_ALLOWED=False)
WARNING = 'REFERENCE_ONLY=true MEASURED=false FABRICATION_ALLOWED=false'

def write_json(path, obj):
    with path.open('x') as f:
        json.dump({**FLAGS, **obj}, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def bounds(s):
    b = s.BoundingBox()
    return [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]

def validate():
    data = json.loads((OUT / 'components.json').read_text())
    results = []
    solids = {}
    for c in data['components']:
        s = cq.importers.importStep(str(OUT / (c['name'] + '.step'))).val()
        m = trimesh.load_mesh(OUT / (c['name'] + '.stl'), process=True)
        assert s.isValid() and len(s.Solids()) == 1 and s.Volume() > 0
        assert all(math.isfinite(v) for v in bounds(s) + [s.Volume()])
        assert max(abs(a-b) for a,b in zip(bounds(s), c['bounds_mm'])) < 1e-5
        assert abs(s.Volume()-c['volume_mm3']) < 1e-4
        assert m.is_watertight and m.is_winding_consistent and m.volume > 0
        assert all(math.isfinite(float(v)) for v in m.vertices.flat)
        assert max(abs(float(a)-b) for a,b in zip(m.bounds.flatten(), c['bounds_mm'])) < 0.1
        assert abs(float(m.volume)-c['volume_mm3']) < max(0.01, c['volume_mm3']*1e-5)
        solids[c['name']] = s
        results.append(dict(name=c['name'], step_valid=True, stl_watertight=True, positive_finite=True))
    combined = cq.importers.importStep(str(OUT / 'REFERENCE_ONLY_NOT_FOR_FABRICATION.step')).val()
    remaining = list(combined.Solids())
    assert combined.isValid() and len(remaining) == len(results)
    for c in data['components']:
        index = next(i for i,s in enumerate(remaining) if max(abs(a-b) for a,b in zip(bounds(s),c['bounds_mm'])) < 1e-5 and abs(s.Volume()-c['volume_mm3']) < 1e-4)
        remaining.pop(index)
    for scene in ['A','B']:
        components = [c for c in data['components'] if c['scene'] == scene]
        assert sum(c['role']=='camera' for c in components) == 3
        assert sum(c['role']=='lighting' for c in components) == 3
        assert { 'base','adapter','portal','crossbar','camera','lighting','trigger','pi','cable','adjustment','exclusion','belt','mount' } <= {c['role'] for c in components}
        belt = solids[scene+'_belt']
        forbidden = [solids[c['name']] for c in components if c['role']=='exclusion']
        for c in components:
            if c['role'] not in ['belt','exclusion','adjustment']:
                assert solids[c['name']].distance(belt) > 0
                assert all(solids[c['name']].intersect(f).Volume() < 1e-6 for f in forbidden)
        pi = next(c for c in components if c['role']=='pi')
        base = next(c for c in components if c['name']==scene+'_base_right')
        assert abs(pi['bounds_mm'][2]-base['bounds_mm'][5]) < 1e-5
        assert all(base['bounds_mm'][k] <= pi['bounds_mm'][k] and pi['bounds_mm'][k+3] <= base['bounds_mm'][k+3] for k in [0,1])
        assert pi['bounds_mm'][5] < 0
    write_json(OUT/'validation.json', dict(status='PASS_REFERENCE_ONLY', components=results,
        assembly_step_readback=True, all_envelopes_present=True, no_belt_support=True,
        pi_supported_on_separate_base=True, exclusion_intersection_check=True,
        stl_processing='merge coincident vertices only via trimesh process=True; no hole repair',
        limitations='No strength, camera optics, real fit, complete cable routes or adjustment sweep validated. Boxes and contacts are conceptual.'))

def generate():
    if list(OUT.iterdir()):
        raise SystemExit('Preserving existing artifacts: export directory must be empty.')
    items = []
    assembly = cq.Assembly(name='REFERENCE_ONLY_NOT_FOR_FABRICATION')
    def box(scene, name, role, size, center, provenance='SPECULATIVE: display-only choice; no physical dimension'):
        offset = 0 if scene=='A' else 1200
        center = [center[0], center[1]+offset, center[2]]
        name = scene+'_'+name
        s = cq.Workplane('XY').box(*size).translate(center).val()
        step = OUT/(name+'.step')
        stl = OUT/(name+'.stl')
        cq.exporters.export(s, str(step))
        step.write_text(step.read_text().replace('HEADER;', 'HEADER;\n/* '+WARNING+' */', 1))
        cq.exporters.export(s, str(stl), tolerance=0.1, angularTolerance=0.1)
        raw = stl.read_bytes()
        stl.write_bytes(WARNING.encode().ljust(80, b' ')+raw[80:])
        color = {'belt':(0.1,0.1,0.1), 'exclusion':(1,0,0,0.15), 'adjustment':(0,1,0,0.2), 'portal':(0.65,0.45,0.2), 'crossbar':(0.65,0.45,0.2), 'camera':(0.1,0.3,0.8), 'lighting':(1,1,0.7), 'pi':(0,0.6,0.3)}.get(role,(0.5,0.5,0.5))
        assembly.add(s, name=name, color=cq.Color(*color))
        items.append(dict(name=name, scene=scene, role=role, size_mm=size, center_mm=center,
                          bounds_mm=bounds(s), volume_mm3=s.Volume(), evidence=provenance, **FLAGS))
    for scene,length,width in [('A',1470,300),('B',450,200)]:
        box(scene,'belt','belt',[length,width,10],[0,0,-5], 'REFERENCE: A Large catalog 1470x300; B YAML nominal 450x200. SPECULATIVE thickness 10 and origin.')
        box(scene,'belt_exclusion','exclusion',[length,width,10],[0,0,-5])
        box(scene,'product_sweep','exclusion',[length,80,240],[0,0,120])
        for end in [-1,1]:
            box(scene,'roller_exclusion_'+str(end),'exclusion',[60,width+40,80],[end*length/2,0,-40])
        box(scene,'motor_exclusion','exclusion',[100,100,100],[length/2, width/2+70,-70])
        for side,y in [('left',-280),('right',280)]:
            box(scene,'adapter_'+side,'adapter',[180,160,40],[0,y,-130])
            box(scene,'base_'+side,'base',[240,180,20],[0,y,-100])
            box(scene,'post_'+side,'portal',[80,20,520],[0,y,170])
            box(scene,'adjust_'+side,'adjustment',[100,70,180],[0,y,160])
            cy = -200 if y<0 else 200
            box(scene,'camera_'+side,'camera',[60,40,40],[0,cy,140])
            box(scene,'mount_'+side,'mount',[60,50,40],[0,(cy+y)/2,140])
            box(scene,'lighting_'+side,'lighting',[20,80,10],[80,cy,180])
            box(scene,'cable_'+side,'cable',[15,15,330],[45,y,90])
        box(scene,'crossbar','crossbar',[80,580,20],[0,0,440])
        box(scene,'top_mount','mount',[40,40,70],[0,0,395])
        box(scene,'camera_top','camera',[60,60,40],[0,0,340])
        box(scene,'lighting_top','lighting',[20,180,10],[80,0,320])
        box(scene,'trigger','trigger',[30,30,30],[-100,-200,140])
        box(scene,'top_adjust','adjustment',[100,100,100],[0,0,340])
        box(scene,'pi_box','pi',[100,65,45],[0,330,-67.5])
        box(scene,'cable_top','cable',[15,560,15],[45,0,470])
    target=OUT/'REFERENCE_ONLY_NOT_FOR_FABRICATION.step'
    assembly.export(str(target))
    target.write_text(target.read_text().replace('HEADER;', 'HEADER;\n/* '+WARNING+' */',1))
    write_json(OUT/'components.json', dict(units='mm', evidence_state='SPECULATIVE',
        coordinates='x transport, y transverse, z up; synthetic belt top z=0. B presentation offset y=1200.',
        warning=WARNING, components=items,
        notes=['A/B adapter boxes are alternatives, not approved contact surfaces.',
               'No holes, slots, threads or real clamps. Green boxes denote desired adjustment zones only.',
               'Cables are discontinuous occupancy corridors. Lighting and trigger attachment details omitted.',
               'MDF-like boxes are not selected board thicknesses. FDM mounts are placeholders.',
               'Assembly includes coincident belt/exclusion volumes intentionally; not a fused printable object.']))
    subprocess.run([sys.executable, str(Path(__file__).resolve()), '--validate'], check=True)
    files = [Path(__file__).resolve()] + sorted(p for p in OUT.iterdir() if p.is_file())
    write_json(OUT/'manifest.json', dict(hash_policy='Payloads only; excludes manifest and later reports/checksum index.',
        files=[dict(path=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]))

if __name__=='__main__':
    validate() if '--validate' in sys.argv else generate()
