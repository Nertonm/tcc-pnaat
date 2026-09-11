import os
import FreeCAD as App, Part, MeshPart, json, builtins, math, traceback
from FreeCAD import Vector as V
A=builtins.astra
O=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/validacao-astra-20260911/'
def move(s,v):
 t=s.copy();t.translate(V(*v));return t
def vol(s):
 v=s.Volume
 if not s.isNull() and not s.isValid():raise RuntimeError('invalid shape')
 if not math.isfinite(v) or (not s.Solids and abs(v)>1e-7):raise RuntimeError('ambiguous volume')
 return v
def export(s,name,up):
 t=s.copy(); t.Placement=App.Placement(V(),App.Rotation(V(*up),V(0,0,1))).multiply(t.Placement)
 bb=t.BoundBox;t.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
 t.exportStep(O+name+'.step')
 mesh=MeshPart.meshFromShape(Shape=t,LinearDeflection=.05,AngularDeflection=.15,Relative=False)
 mesh.write(O+name+'.stl')
 return {'volume_before':vol(s),'volume_after':vol(t),'valid':t.isValid(),'solids':len(t.Solids),'mesh_closed':mesh.isSolid(),'bbox':[t.BoundBox.XLength,t.BoundBox.YLength,t.BoundBox.ZLength]}
cube=Part.makeBox(10,10,10)
r={'controls':{'positive':vol(cube.common(cube)),'negative':vol(cube.common(move(cube,(500,0,0))))},'coupons':{}}
# Exact reference rail end section, no synthetic rail.
rail=A['rails']['MontanteA'];section=rail.Faces[3]
tool=section.extrude(V(0,600,0))
j=A['rails']['JuncaoA']
# Slice at bottom of actual junction; includes its actual intersecting second groove.
slab=Part.makeBox(60,8,40,V(-60,433.901999,0))
base=j.common(slab)
for c in [.18,.25,.30]:
 cutter=tool
 for dx,dz in [(x,z) for x in [-c,0,c] for z in [-c,0,c] if x or z]:
  cutter=cutter.fuse(move(tool,(dx,0,dz)))
 cp=base.cut(cutter).removeSplitter()
 name='cupom-luva-'+str(c).replace('.','p')
 r['coupons'][name]=dict(clearance_design=c,source_volume=vol(base),removed=vol(base)-vol(cp),nominal=vol(cp.common(rail)),positive=vol(cp.common(cp)),negative=vol(cp.common(move(rail,(500,0,0)))),export=export(cp,name,(1,0,0)))
# Full real bracket is the fit coupon: retains all engagement features and axial stop.
b=A['b']
faces=[f for f in b.Faces if abs(f.normalAt(0,0).x)>.999999 and abs(f.Area-7.7)<.01]
for c in [.18,.25,.30]:
 cp=b.copy()
 if c>.18:
  for f in faces:
   cutter=f.extrude(-f.normalAt(0,0)*(c-.18))
   cp=cp.cut(cutter)
 name='cupom-bracket-'+str(c).replace('.','p')
 r['coupons'][name]=dict(clearance_design=c,source_volume=vol(b),removed=vol(b)-vol(cp),nominal=vol(cp.common(rail)),positive=vol(cp.common(move(rail,(0,-3,0)))),negative=vol(cp.common(move(rail,(500,0,0)))),export=export(cp,name,(0,0,1)))
 json.dump(r,open(O+'coupons.json','w'),indent=2)
print('coupons done')
