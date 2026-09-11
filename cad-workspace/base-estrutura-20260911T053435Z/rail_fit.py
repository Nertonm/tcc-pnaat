import FreeCAD as A,Part,json
from FreeCAD import Vector as V
from pathlib import Path
P=Path(__file__).resolve().parent
r=Part.read(str(P/'inputs/dinr135-007.5.step'));b=Part.read(str(P/'DIN Rail Bracket 4mm-component0.stl.brep'))
r.rotate(V(),V(1,0,0),90);r.translate(V(7.5,0,0))
o={'m6_overlap':b.common(r).Volume,'m6_gap':b.distToShape(r)[0],'rail_faces':[{'type':str(type(f.Surface)),'area':f.Area,'center':list(f.CenterOfMass),'bbox':[f.BoundBox.XMin,f.BoundBox.YMin,f.BoundBox.ZMin,f.BoundBox.XMax,f.BoundBox.YMax,f.BoundBox.ZMax]} for f in r.Faces]}
(P/'rail-fit.json').write_text(json.dumps(o,indent=2));print(json.dumps(o,indent=2))
