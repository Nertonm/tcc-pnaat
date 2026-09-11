import FreeCAD as App,Part,MeshPart,builtins,json,math,os
from FreeCAD import Vector as V
A=builtins.astra
O=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/validacao-astra-20260911/'
r={'controls':{'positive':Part.makeBox(10,10,10).Volume,'negative':Part.makeBox(10,10,10).common(Part.makeBox(10,10,10,V(500,0,0))).Volume},'exports':{}}
parts={'peca':(A['p'],(1,0,0),2),'bracket':(A['b'],(0,0,1),2),'clamp':(A['clamp'],(0,0,1),2),'sapata':(A['pad'],(0,0,1),2),'parafuso':(A['screw'],(0,0,1),2)}
parts.update({k:(A['rails'][k],(1,0,0) if k.startswith('Juncao') else (0,0,1),1) for k in ['JuncaoA','JuncaoB','ChavetaA','ChavetaB']})
for k,(s,up,q) in parts.items():
 t=s.copy();t.Placement=App.Placement(V(),App.Rotation(V(*up),V(0,0,1))).multiply(t.Placement)
 bb=t.BoundBox;t.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
 t.exportStep(O+'orientada-'+k+'.step')
 mesh=MeshPart.meshFromShape(Shape=t,LinearDeflection=.05,AngularDeflection=.15,Relative=False);mesh.write(O+'orientada-'+k+'.stl')
 r['exports'][k]={'quantity':q,'up':up,'volume_before':s.Volume,'volume_after':t.Volume,'mesh_volume':mesh.Volume,'mesh_closed':mesh.isSolid(),'valid':t.isValid(),'solids':len(t.Solids),'bbox':[t.BoundBox.XLength,t.BoundBox.YLength,t.BoundBox.ZLength]}
 json.dump(r,open(O+'exports.json','w'),indent=2)
# Bearing gauges: dimensional proposals only, no catalog geometry invented.
def mv(s,v):
 t=s.copy();t.translate(V(*v));return t
def test(s,target):
 return {'nominal':s.common(target).Volume,'positive_self':s.common(s).Volume,'negative':mv(s,(500,0,0)).common(target).Volume}
center=V(-30.5,85.401999,0)
washer=Part.makeCylinder(6,1.6,V(center.x,center.y,-8.1)).cut(Part.makeCylinder(3.2,1.6,V(center.x,center.y,-8.1)))
pts=[V(center.x+10/math.sqrt(3)*math.cos(i*math.pi/3),center.y+10/math.sqrt(3)*math.sin(i*math.pi/3),-13.1) for i in range(6)]
nut=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,5))
head=Part.makeCylinder(5,6,V(center.x,center.y,12))
r['fastener_gauges']={'washer_vs_piece':test(washer,A['pa']),'nut_vs_piece':test(nut,A['pa']),'head_vs_bracket':test(head,A['b'])}
r['recess_rays']=[]
for x in [-49,-45,-30.5,-16,-12]:
 for y in [72.2,72.5,72.9]:
  line=Part.makeLine(V(x,y,-1),V(x,y,25))
  r['recess_rays'].append({'x':x,'y':y,'segments':[[e.BoundBox.ZMin,e.BoundBox.ZMax] for e in A['p'].common(line).Edges]})
json.dump(r,open(O+'exports.json','w'),indent=2)
print('exports done')
