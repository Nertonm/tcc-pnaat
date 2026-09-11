import FreeCAD as A,Part,Mesh,json,time
from pathlib import Path
from FreeCAD import Vector as V
P=Path(__file__).resolve().parent
out={}
b=Part.read(str(P/'DIN Rail Bracket 4mm-component0.stl.brep'));r=Part.read(str(P/'inputs/dinr135-007.5.step'));r.rotate(V(),V(1,0,0),90);r.translate(V(7.5,0,0))
out['M6_rail']={'common':b.common(r).Volume,'distance':b.distToShape(r)[0], 'normal_dot':1, 'insertion_depth':5.5}
for name in ['screw_and_knurled_knobHD.stl','clamp_protector.stl']:
 t=time.time();m=Mesh.Mesh(str(P/'inputs'/name));s=Part.Shape();s.makeShapeFromMesh(m.Topology,.00001);s=Part.makeSolid(s.Shells[0]);s=s.removeSplitter();out[name]={'valid':s.isValid(),'volume':s.Volume,'faces':len(s.Faces),'seconds':time.time()-t};s.exportBrep(str(P/(name+'.brep')));(P/'mechanism-probe.json').write_text(json.dumps(out,indent=2));print(name,out[name],flush=True)
g=Part.read(str(P/'G-clamp_Tripod-component0.stl.brep'))
s=Part.read(str(P/'screw_and_knurled_knobHD.stl.brep'));s.rotate(V(),V(0,1,0),-90);s.translate(V(40,42,10));out['screw_frame_first']={'common':g.common(s).Volume,'distance':g.distToShape(s)[0]}
pad=Part.read(str(P/'clamp_protector.stl.brep'));pad.rotate(V(),V(0,1,0),90);pad.translate(V(40-67.308-6,42,10));out['screw_pad']={'common':s.common(pad).Volume,'distance':s.distToShape(pad)[0]}
(P/'mechanism-probe.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
