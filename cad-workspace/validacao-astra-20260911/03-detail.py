import os
import FreeCAD as App, Part, json, builtins, math
from FreeCAD import Vector as V
A=builtins.astra
O=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/validacao-astra-20260911/'
def shifted(s,v):
 t=s.copy();t.translate(V(*v));return t
def iv(a,b):
 c=a.common(b)
 if not c.isNull() and not c.isValid():raise RuntimeError('invalid boolean')
 v=c.Volume
 if not math.isfinite(v) or (not c.Solids and abs(v)>1e-7):raise RuntimeError('ambiguous volume')
 return v
def ray(s,x,y):
 it=s.common(Part.makeLine(V(x,y,-20),V(x,y,40)))
 return [[e.BoundBox.ZMin,e.BoundBox.ZMax] for e in it.Edges]
cube=Part.makeBox(10,10,10)
r={'controls':{'volume_positive':iv(cube,cube),'volume_negative':iv(cube,shifted(cube,(500,0,0))),'ray_positive':ray(cube,5,5),'ray_negative':ray(cube,500,500)},'volumes':{},'rays':{}}
for k in ['original','recess','p']:r['volumes'][k]=A[k].Volume
for label,rem in [('recess',A['original'].cut(A['recess'])),('hole',A['recess'].cut(A['p']))]:
 r[label]={'volume':rem.Volume,'bbox':[rem.BoundBox.XMin,rem.BoundBox.YMin,rem.BoundBox.ZMin,rem.BoundBox.XMax,rem.BoundBox.YMax,rem.BoundBox.ZMax]}
for dx,dy in [(0,0),(3.18,0),(3.3,0),(0,3.3),(-3.3,0),(0,-3.3),(6,0),(0,6),(-6,0),(0,-6)]:
 r['rays'][str((dx,dy))]=ray(A['p'],-30.5+dx,85.4+dy)
# Measured bearing envelope, a design gauge only, not an invented catalog part.
washer=Part.makeCylinder(6,1.6,V(-30.5,85.4,3.4)).cut(Part.makeCylinder(3.2,1.6,V(-30.5,85.4,3.4)))
r['washer_envelope']={'OD_proposed':12,'ID_proposed':6.4,'height_proposed':1.6,'nominal':iv(washer,A['p']),'positive_1mm':iv(shifted(washer,(0,0,1)),A['p']),'negative_500mm':iv(shifted(washer,(500,0,0)),A['p'])}
r['bearing_area']=washer.Faces[-1].Area if False else sum(f.common(g).Area for f in washer.Faces for g in A['p'].Faces if f.BoundBox.intersect(g.BoundBox))
# Channel planes, not chamfers.
r['channel_faces']=[]
for i,f in enumerate(A['b'].Faces):
 n=f.normalAt(0,0)
 if abs(n.x)>.999999 and abs(f.Area-7.7)<.01:r['channel_faces'].append(dict(index=i,area=f.Area,x=f.CenterOfMass.x,normal=list(n),ymin=f.BoundBox.YMin,ymax=f.BoundBox.YMax))
r['channel_width']=max(x['x'] for x in r['channel_faces'])-min(x['x'] for x in r['channel_faces'])
r['rail_width']=A['rails']['MontanteA'].BoundBox.XLength
json.dump(r,open(O+'detail.json','w'),indent=2)
print('detail done')
