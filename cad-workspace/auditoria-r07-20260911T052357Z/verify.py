import FreeCAD as App, Part, Mesh
from pathlib import Path
from FreeCAD import Vector as V
import json,hashlib
p=Path(__file__).resolve().parent
expected=json.loads((p/'checks-build.json').read_text())['candidate_cant']
def measure(s):
 b=s.BoundBox
 return {'valid':s.isValid(),'solids':len(s.Solids),'volume':s.Volume,'bbox':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]}
s=Part.read(str(p/'cantoneira-topology-only.step'))
d=App.openDocument(str(p/'cantoneira-topology-only.FCStd'))
f=[o for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
assert len(f)==1
out={'step':measure(s),'fcstd':measure(f[0].Shape)}
m=Mesh.Mesh(str(p/'cantoneira-topology-only.stl'))
out['stl']={'solid':m.isSolid(),'components':m.countComponents(),'volume':m.Volume,'facets':m.CountFacets}
assert m.isSolid() and m.countComponents()==1
for key in ('step','fcstd'):
 a=out[key];a['volume_delta']=abs(a['volume']-expected['volume']);a['bbox_max_delta']=max(abs(x-y) for x,y in zip(a['bbox'],expected['bbox']))
 assert a['valid'] and a['solids']==1 and a['volume_delta']<1e-5 and a['bbox_max_delta']<1e-5
out['stl']['relative_volume_error']=abs(m.Volume-expected['volume'])/expected['volume']
assert out['stl']['relative_volume_error']<0.001
# Solids.common discards lower-dimensional contact: compare boundary faces.
def face_at_y(sh,y):
 return [f for f in sh.Faces if abs(f.BoundBox.YMin-y)<1e-7 and abs(f.BoundBox.YMax-y)<1e-7]
v=Part.makeBox(5,35,20,V(-71,32,0));h=Part.makeBox(66,5,20,V(-66,67,0));hn=Part.makeBox(71,5,20,V(-71,67,0))
out['join_face_area_mm2']={'old':sum(a.common(b).Area for a in face_at_y(h,67) for b in face_at_y(v,67)), 'candidate':sum(a.common(b).Area for a in face_at_y(hn,67) for b in face_at_y(v,67))}
assert abs(out['join_face_area_mm2']['candidate']-100)<1e-7
assert out['join_face_area_mm2']['old']==0
out['holes']=[]
for x,y,z,axis in [(-56,67,10,V(0,1,0)),(-30.5,67,10,V(0,1,0)),(-5,67,10,V(0,1,0)),(-71,42,10,V(1,0,0))]:
 test=Part.makeCylinder(0.5,5,V(x,y,z),axis);vol=s.common(test).Volume
 out['holes'].append({'start':[x,y,z],'axis':list(axis),'probe_radius':0.5,'probe_length':5,'blocked_volume':vol});assert abs(vol)<1e-7
baseline=json.loads((p/'baseline.json').read_text())
out['source_preservation']={path:hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha for path,sha in baseline['inputs'].items()}
assert all(out['source_preservation'].values())
out['result']='PASS_TOPOLOGY_ONLY; ASSEMBLY_BLOCKED'
(p/'checks-verify.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
