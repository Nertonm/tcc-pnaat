import FreeCAD as App, Part, MeshPart, json, math, builtins, os
from FreeCAD import Vector as V
A=builtins.astra
O=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/validacao-astra-20260911/'
def metrics(s,up):
 rot=App.Rotation(V(*up),V(0,0,1))
 t=s.copy();t.Placement=App.Placement(V(),rot).multiply(t.Placement)
 bb=t.BoundBox
 mesh=MeshPart.meshFromShape(Shape=t,LinearDeflection=.05,AngularDeflection=.15,Relative=False)
 over=0.;support=0.
 for f in mesh.Facets:
  if max(abs(p[2]-bb.ZMin) for p in f.Points)<1e-5: support+=f.Area
  elif f.Normal.z < -math.sqrt(.5)-1e-9: over+=f.Area
 return dict(overhang=over,support=support,bbox=[bb.XLength,bb.YLength,bb.ZLength],fits=bb.XLength<=220 and bb.YLength<=220 and bb.ZLength<=250,volume=t.Volume,mesh_volume=mesh.Volume,closed=mesh.isSolid(),facets=mesh.CountFacets)
cube=Part.makeBox(10,10,10)
upper=Part.makeBox(10,10,10,V(20,0,20))
r={'controls':{'negative':metrics(cube,(0,0,1)),'positive':metrics(Part.makeCompound([cube,upper]),(0,0,1))},'parts':{}}
parts={'peca':A['p'],'bracket':A['b'],'clamp':A['clamp'],'sapata':A['pad'],'parafuso':A['screw']}
parts.update({k:A['rails'][k] for k in ['JuncaoA','JuncaoB','ChavetaA','ChavetaB']})
for k,s in parts.items():
 r['parts'][k]={'valid':s.isValid(),'closed':s.isClosed(),'solids':len(s.Solids),'candidates':{}}
 for n,u in [('X+',(1,0,0)),('X-',(-1,0,0)),('Y+',(0,1,0)),('Y-',(0,-1,0)),('Z+',(0,0,1)),('Z-',(0,0,-1))]:
  r['parts'][k]['candidates'][n]=metrics(s,u)
 json.dump(r,open(O+'orientations.json','w'),indent=2)
print('orientations done')
