import FreeCAD as App, Part, json, math, os, builtins
from FreeCAD import Vector as V
W=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/'
O=W+'validacao-astra-20260911/'
A=builtins.astra
def moved(s,v):
 t=s.copy();t.translate(V(*v));return t
def measure(a,b):
 c=a.common(b)
 if not c.isNull() and not c.isValid(): raise RuntimeError('Invalid intersection')
 v=c.Volume
 if not math.isfinite(v) or v < -1e-7: raise RuntimeError('Invalid volume')
 if not c.Solids and abs(v)>1e-7: raise RuntimeError('Nonzero volume without solids')
 return dict(volume=v,solids=len(c.Solids),null=c.isNull(),distance=a.distToShape(b)[0])
def contact(a,b):
 total=0.
 for f in a.Faces:
  for g in b.Faces:
   if f.BoundBox.intersect(g.BoundBox):
    total+=f.common(g).Area
 return total
r={}
cube=Part.makeBox(10,10,10)
r['instrument']={'positive':measure(cube,moved(cube,(5,0,0))),'negative':measure(cube,moved(cube,(500,0,0))),
'contact_positive':contact(cube,moved(cube,(10,0,0))),'contact_negative':contact(cube,moved(cube,(500,0,0)))}
p=A['p']; b=A['b']
r['raw_pair']={'nominal':measure(p,b),'positive':measure(p,p),'negative':measure(p,moved(b,(500,0,0)))}
# Explicit assembly placement derived from delivered assembly; no geometry regeneration.
pa=p.copy();pa.translate(A['assembly'].Solids[0].BoundBox.Center-p.BoundBox.Center)
A['pa']=pa
r['placement']=list(pa.BoundBox.Center-p.BoundBox.Center)
r['assembled_pair']={'nominal':measure(pa,b),'positive':measure(moved(pa,(0,0,1)),b),'negative':measure(moved(pa,(0,0,-500)),b),'contact':contact(pa,b),'contact_positive':contact(cube,moved(cube,(10,0,0))),'contact_negative':contact(pa,moved(b,(0,0,500)))}
for side in ['A','B']:
 rail=A['rails']['Montante'+side]
 bb=b.copy()
 if side=='B': bb.mirror(V(-30.5,0,0),V(1,0,0));bb.translate(V(400,0,0))
 r['rail'+side]={'nominal':measure(bb,rail),'positive':measure(moved(bb,(0,3,0)),rail),'negative':measure(moved(bb,(0,500,0)),rail)}
 j=A['rails']['Juncao'+side]
 r['sleeve'+side]={'nominal':measure(j,rail),'positive':measure(j,moved(rail,(.002,0,0))),'negative':measure(j,moved(rail,(500,0,0)))}
r['rail_bbox']=[A['rails']['MontanteA'].BoundBox.XLength,A['rails']['MontanteA'].BoundBox.YLength,A['rails']['MontanteA'].BoundBox.ZLength]
json.dump(r,open(O+'interface.json','w'),indent=2)
print(json.dumps(r))
