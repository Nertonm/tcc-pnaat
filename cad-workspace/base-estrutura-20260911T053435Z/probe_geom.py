import FreeCAD as A,Part,Mesh,json
from pathlib import Path
from FreeCAD import Vector as V
P=Path(__file__).resolve().parent
out={}
def stats(s):
 b=s.BoundBox;return dict(valid=s.isValid(),solids=len(s.Solids),closed=s.isClosed(),volume=s.Volume,bbox=[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],faces=len(s.Faces))
for name in ['G-clamp_Tripod-component0.stl','DIN Rail Bracket 4mm-component0.stl']:
 m=Mesh.Mesh(str(P/'inputs'/name));s=Part.Shape();s.makeShapeFromMesh(m.Topology,.00001)
 s=Part.makeSolid(s.Shells[0]);s=s.removeSplitter();out[name]=stats(s);s.exportBrep(str(P/(name+'.brep')))
r=Part.read(str(P/'inputs/dinr135-007.5.step'));out['rail']=stats(r)
out['rail_end_faces']=[{'area':f.Area,'bbox':stats(f)['bbox']} for f in r.Faces if f.BoundBox.XLength<1e-5]
# rail local length X, section depth Y, width Z; bracket length X,widthY,normalZ
rr=r.copy();rr.rotate(V(),V(1,0,0),90);out['rotatedrail']=stats(rr)
(P/'inspection.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
