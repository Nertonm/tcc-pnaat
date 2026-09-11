import os
import FreeCAD as App, Part, json, builtins, MeshPart,math
from FreeCAD import Vector as V
A=builtins.astra
O=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/validacao-astra-20260911/'
def mv(s,v):
 t=s.copy();t.translate(V(*v));return t
def iv(a,b):
 c=a.common(b);v=c.Volume
 if (not c.isNull() and not c.isValid()) or not math.isfinite(v) or (not c.Solids and abs(v)>1e-7):raise RuntimeError('boolean fail')
 return v
r={'controls':{'positive':iv(Part.makeBox(10,10,10),Part.makeBox(10,10,10)),'negative':iv(Part.makeBox(10,10,10),Part.makeBox(10,10,10,V(500,0,0))) }}
p=A['pa'].copy();p.mirror(V(-30.5,0,0),V(1,0,0));p.translate(V(400,0,0))
b=A['b'].copy();b.mirror(V(-30.5,0,0),V(1,0,0));b.translate(V(400,0,0))
r['sideB']={'nominal':iv(p,b),'positive':iv(mv(p,(0,0,1)),b),'negative':iv(mv(p,(0,0,-500)),b),'contact':sum(f.common(g).Area for f in p.Faces for g in b.Faces if f.BoundBox.intersect(g.BoundBox))}
r['piece_rail']={'nominal':iv(A['pa'],A['rails']['MontanteA']),'positive_self':iv(A['pa'],A['pa']),'negative':iv(mv(A['pa'],(500,0,0)),A['rails']['MontanteA'])}
# Retain the mirrored geometry, then rotate its outward platform onto the bed.
q=p.copy();q.Placement=App.Placement(V(),App.Rotation(V(-1,0,0),V(0,0,1))).multiply(q.Placement)
bb=q.BoundBox;q.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
q.exportStep(O+'orientada-pecaB.step')
mesh=MeshPart.meshFromShape(Shape=q,LinearDeflection=.05,AngularDeflection=.15,Relative=False);mesh.write(O+'orientada-pecaB.stl')
r['pieceB_export']={'before':p.Volume,'after':q.Volume,'closed':mesh.isSolid(),'solids':len(q.Solids)}
# Native clamp STL component audit against the BREP; no automatic repair.
import Mesh
m=Mesh.Mesh(os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/references/vendor/g-clamp-tripod/G-clamp_Tripod.stl')
r['clamp_source_mesh']={'closed':m.isSolid(),'components':len(m.getSeparateComponents()),'facets':m.CountFacets}
# Ray controls in the same round as a repetition of the local recess rays.
cube=Part.makeBox(10,10,10)
r['ray_controls']={'positive':cube.common(Part.makeLine(V(5,5,-1),V(5,5,11))).Length,'negative':cube.common(Part.makeLine(V(500,5,-1),V(500,5,11))).Length}
r['recess_ray']= [[e.BoundBox.ZMin,e.BoundBox.ZMax] for e in A['p'].common(Part.makeLine(V(-30.5,72.5,-1),V(-30.5,72.5,25))).Edges]
json.dump(r,open(O+'additional.json','w'),indent=2)
print('additional done')
