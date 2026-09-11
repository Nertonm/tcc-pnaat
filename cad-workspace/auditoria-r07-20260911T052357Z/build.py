import FreeCAD as App, Part, Mesh, Import
from FreeCAD import Vector as V
from pathlib import Path
import json, zipfile, xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent
out={"scope":"topology-only coupon, not approved assembly", "freecad":App.Version()}
def stats(s):
 b=s.BoundBox
 return dict(valid=s.isValid(),closed=s.isClosed(),solids=len(s.Solids),shells=len(s.Shells),volume=s.Volume,bbox=[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax])
def meshstats(m):
 return dict(facets=m.CountFacets,points=m.CountPoints,solid=m.isSolid(),components=m.countComponents())
def cut_holes(s):
 s=s.cut(Part.makeCylinder(3.175,12,V(-30.5,64,10),V(0,1,0)))
 s=s.cut(Part.makeCylinder(3.175,12,V(-73,42,10),V(1,0,0)))
 for x in (-56,-5): s=s.cut(Part.makeCylinder(1.7,12,V(x,66,10),V(0,1,0)))
 return s.removeSplitter()
h=Part.makeBox(66,5,20,V(-66,67,0)); v=Part.makeBox(5,35,20,V(-71,32,0))
old=cut_holes(h.fuse(v))
hnew=Part.makeBox(71,5,20,V(-71,67,0))
new=cut_holes(hnew.fuse(v))
out['old_cant']=stats(old);out['candidate_cant']=stats(new)
out['old_join']={'area':h.common(v).Area,'volume':h.common(v).Volume,'edges':len(h.common(v).Edges)}
out['candidate_join']={'area':hnew.common(v).Area,'volume':hnew.common(v).Volume}
out['mutation_test']={'old_fails_one_solid':len(old.Solids)!=1,'candidate_passes_one_solid':len(new.Solids)==1 and new.isValid()}
out['holes_candidate']=[]
for f in new.Faces:
 c=f.Surface
 if isinstance(c,Part.Cylinder): out['holes_candidate'].append({'radius':c.Radius,'axis':list(c.Axis),'center':list(c.Center)})
for name in ['G-clamp_Tripod.stl','r07-01-g-clamp.stl','r07-02-cantoneira.stl','m6-bracket.stl']:
 m=Mesh.Mesh(str(P/'inputs'/name));out[name]=meshstats(m)
 # No boolean or inside tests on unvalidated mesh conversions.
 s=Part.Shape();s.makeShapeFromMesh(m.Topology,0.001)
 out[name]['brep_shell']=stats(s)
 if m.isSolid() and len(s.Shells)==1:
  solid=Part.makeSolid(s.Shells[0]);out[name]['converted_solid']=stats(solid)
z=zipfile.ZipFile(P/'inputs/redux-selftap.3mf')
models=[n for n in z.namelist() if n.endswith('.model')]
assert len(models)==1
r=ET.fromstring(z.read(models[0]));ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
assert r.attrib.get('unit','millimeter')=='millimeter'
objects={x.attrib['id']:x for x in r.findall('m:resources/m:object',ns)}
items=r.findall('m:build/m:item',ns)
out['3mf_structure']={'models':models,'objects':[o.attrib for o in objects.values()],'build':[i.attrib for i in items], 'unit':r.attrib.get('unit')}
# Fail closed rather than silently ignore assembly or placement semantics.
assert len(items)==1 and len(objects)==1
assert 'transform' not in items[0].attrib
obj=objects[items[0].attrib['objectid']]
assert obj.find('m:components',ns) is None
vs=[V(float(e.attrib['x']),float(e.attrib['y']),float(e.attrib['z'])) for e in obj.findall('m:mesh/m:vertices/m:vertex',ns)]
tris=[tuple(int(e.attrib[k]) for k in ('v1','v2','v3')) for e in obj.findall('m:mesh/m:triangles/m:triangle',ns)]
assert all(0<=i<len(vs) for t in tris for i in t)
m=Mesh.Mesh([[vs[i] for i in t] for t in tris]);out['redux_mesh']=meshstats(m)
s=Part.Shape();s.makeShapeFromMesh(m.Topology,0.001);out['redux_shell']=stats(s)
# Record actual sections for datum inspection, not minimum-collision scans.
sections={}
for zheight in (0.5,2,4,6,7):
 sec=s.section(Part.makePlane(200,200,V(-100,-100,zheight)))
 sections[str(zheight)]=[[list(e.Vertexes[0].Point),list(e.Vertexes[-1].Point)] for e in sec.Edges]
(P/'redux-sections.json').write_text(json.dumps(sections,indent=2))
rail=Part.read(str(P/'inputs/rail.step'));out['rail_original']=stats(rail)
rot=App.Rotation(V(1,1,1),120);cliprot=App.Rotation(V(1,0,0),-90)
rail_long=rot.multVec(V(1,0,0));rail_normal=rot.multVec(V(0,1,0));clip_normal=cliprot.multVec(V(0,0,1))
out['r07_datums']={'rail_length_axis':list(rail_long),'rail_section_normal':list(rail_normal),'clip_mounting_normal':list(clip_normal),'normal_dot':rail_normal.dot(clip_normal),'clip_normal_dot_rail_length':clip_normal.dot(rail_long),'interpretation':'normal mismatch; section normal uses STEP thickness Y and clip thickness Z'}
adapter=Part.read(str(P/'inputs/angle-100.step'));out['angle_adapter']=stats(adapter)
out['angle_adapter']['solid_details']=[stats(x) for x in adapter.Solids]
doc=App.newDocument('PNAAT_Coupon_NotAssembly')
f=doc.addObject('Part::Feature','TopologyCoupon');f.Label='CANDIDATO topologico - NAO montagem aprovada';f.Shape=new
doc.recompute();doc.saveAs(str(P/'cantoneira-topology-only.FCStd'))
Import.export([f],str(P/'cantoneira-topology-only.step'));new.exportStl(str(P/'cantoneira-topology-only.stl'))
(P/'checks-build.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
