import FreeCAD as App, Part, json
from FreeCAD import Vector as V
from pathlib import Path
W=Path('"${TCC_HOME:-$HOME/tcc-pnaat/github}/cad-workspace"'); O=W/'lote-impressao-20260911'
r={}
for name in ['case-pi5-base','case-pi5-tampa','clamp']:
 s=Part.read(str(O/('orientada-'+name+'.step'))); bb=s.BoundBox
 data={}
 for ax in range(3):
  for frac in [.2,.5,.8]:
   xyz=list(bb.Center); xyz[ax]=[bb.XMin,bb.YMin,bb.ZMin][ax]+frac*[bb.XLength,bb.YLength,bb.ZLength][ax]
   normal=[0,0,0];normal[ax]=1
   sec=s.section(Part.makePlane(1000,1000,V(*xyz)-V(*[0 if i==ax else 500 for i in range(3)]),V(*normal)))
   # use slice which has unambiguous plane origin
   wires=s.slice(V(*normal),xyz[ax])
   data[str((ax,frac))]=[[list(v.Point) for v in e.Vertexes] for wire in wires for e in wire.Edges]
 r[name]=data
json.dump(r,open(str(O/'astra2-secoes.json'),'w'))
print('sections saved',flush=True)
