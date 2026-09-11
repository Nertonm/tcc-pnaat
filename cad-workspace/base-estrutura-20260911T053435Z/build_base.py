import FreeCAD as A,Part,Import,json
from pathlib import Path
from FreeCAD import Vector as V
P=Path(__file__).resolve().parent
D=A.newDocument('PNAAT_Base_DatumCandidate');items={}
def add(n,s):
 f=D.addObject('Part::Feature',n);f.Shape=s;items[n]=f;return s
def box(x,y,z,p):return Part.makeBox(x,y,z,V(*p))
def move(s,ang=90,t=(-30.5,80.0009994506836,10)):
 s=s.copy();s.rotate(V(),V(0,0,1),ang);s.translate(V(*t));return s
def stats(s):
 b=s.BoundBox;return {'valid':s.isValid(),'solids':len(s.Solids),'volume':s.Volume,'bbox':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]}
g=add('ClampFunctionalSource',Part.read(str(P/'G-clamp_Tripod-component0.stl.brep')))
b=Part.read(str(P/'DIN Rail Bracket 4mm-component0.stl.brep'))
# Retention bridge behind the source socket; open a nut access pocket, not the flange seats.
b=b.fuse(box(35,16,3.1,(-13,-8,-5))).cut(box(11,10,5,(11,-5,1.001)))
b=b.cut(Part.makeCylinder(2.2,12,V(15.6,0,-6),V(0,0,1))).removeSplitter();b=move(b)
yseat=g.BoundBox.YMax; zmax=g.BoundBox.ZMax
saddle=box(43,6,36,(-52,yseat,-8))
for z in (-8,zmax+.15):saddle=saddle.fuse(box(43,yseat-59,8-.15,(-52,59,z)))
saddle=saddle.fuse(b).removeSplitter()
cap=box(43,3,36,(-52,54,-8))
for x,z in [(-48,-5),(-13,25)]:
 tool=Part.makeCylinder(2.2,30,V(x,50,z),V(0,1,0));saddle=saddle.cut(tool);cap=cap.cut(tool)
add('SocketSaddleAdapted',saddle.removeSplitter());add('SpineCap',cap.removeSplitter())
for i,(x,z) in enumerate([(-48,-5),(-13,25)]):
 # Unthreaded mating envelopes only; explicit M4 candidate size, not vendor fastener CAD.
 sh=Part.makeCylinder(2,25,V(x,54,z),V(0,1,0)).fuse(Part.makeCylinder(3.5,3,V(x,51,z),V(0,1,0)))
 add('SaddleBoltEnvelope'+str(i),sh)
 nut=Part.makeCylinder(3.5,3,V(x,yseat+6,z),V(0,1,0)).cut(Part.makeCylinder(2,3,V(x,yseat+6,z),V(0,1,0)))
 add('SaddleNutEnvelope'+str(i),nut)
r=Part.read(str(P/'inputs/dinr135-007.5.step'));r.rotate(V(),V(1,0,0),90);r.translate(V(7.5,0,0));r=move(r);add('Rail75Actual',r)
pin=Part.makeCylinder(2,10,V(15.6,0,-5),V(0,0,1)).fuse(Part.makeCylinder(3.5,3,V(15.6,0,-8),V(0,0,1)))
add('RailRetentionBoltEnvelope',move(pin))
nut=Part.makeCylinder(3.5,3,V(15.6,0,1.001),V(0,0,1)).cut(Part.makeCylinder(2,3,V(15.6,0,1.001),V(0,0,1)))
add('RailRetentionNutEnvelope',move(nut))
# Write before expensive all-pair checks so evidence survives failures.
D.recompute();D.saveAs(str(P/'base-candidate.FCStd'));Import.export(list(items.values()),str(P/'base-candidate.step'))
out={'parts':{n:stats(f.Shape) for n,f in items.items()},'pairs':{},'source_socket_insertion_mm':5.5,'datum_normal_dot':1.0,'mounting_tripod_holes_used':0,'not_validated':['load','threaded fasteners','print tolerances','actual conveyor']}
for i,(n,a) in enumerate(items.items()):
 for m,b in list(items.items())[i+1:]:
  if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):continue
  out['pairs'][n+'__'+m]=a.Shape.common(b.Shape).Volume
  (P/'base-checks.json').write_text(json.dumps(out,indent=2))
# retention mutation: no free extraction in socket direction beyond1.1mm axial clearance
mut=r.copy();mut.translate(V(0,2,0));out['negative_extraction_pin_overlap']=mut.common(items['RailRetentionBoltEnvelope'].Shape).Volume
out['base_parts_pass']=all(v['valid'] and v['solids']==1 for v in out['parts'].values())
out['base_collision_pass']=all(abs(v)<1e-6 for v in out['pairs'].values())
(P/'base-checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
