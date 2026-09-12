import FreeCAD as App, Part, math, json, zipfile
from FreeCAD import Vector as V
from pathlib import Path
W=Path('"${TCC_HOME:-$HOME/tcc-pnaat/github}/cad-workspace"'); O=W/'lote-impressao-20260911'
def read(p):
 s=Part.read(str(p)); assert s.isValid() and len(s.Solids)==1 and s.Volume>0; return s
def mv(s,v):
 t=s.copy();t.translate(V(*v));return t
def iv(a,b):
 c=a.common(b); v=c.Volume; ss=sum(t.Volume for t in c.Solids)
 assert c.isNull() or c.isValid()
 assert math.isfinite(v) and v>=-1e-7 and abs(v-ss)<1e-5, (v,ss,c.ShapeType)
 return dict(volume=v,solids=len(c.Solids),raw_volume=v)
p=read(W/'interface-peca-bracket-20260911/peca-assento-nivelado-furo-M6.step');p=mv(p,(0,.001999,-11.5))
b=read(W/'interface-peca-bracket-20260911/bracket-rot90Z-no-trilho.step')
x,y=-30.5,85.401999
washer=Part.makeCylinder(6,1.6,V(x,y,-8.1)).cut(Part.makeCylinder(3.2,1.6,V(x,y,-8.1)))
pts=[V(x+10/math.sqrt(3)*math.cos(i*math.pi/3),y+10/math.sqrt(3)*math.sin(i*math.pi/3),-13.1) for i in range(6)]
nut=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,5)).cut(Part.makeCylinder(3,5,V(x,y,-13.1)))
head=Part.makeCylinder(5,6,V(x,y,12)); shaft=Part.makeCylinder(3,30,V(x,y,-18))
cube=Part.makeBox(10,10,10)
r={'controls':{'positive':iv(cube,cube),'negative':iv(cube,mv(cube,(50,0,0)))},'placement':[0,.001999,-11.5],'pieces':{}}
for n,s in [('peca',p),('bracket',b),('arruela',washer),('porca',nut),('cabeca',head),('haste',shaft)]:
 r['pieces'][n]={'volume':s.Volume,'bbox':str(s.BoundBox),'valid':s.isValid()}
for n,s in [('arruela',washer),('porca',nut),('cabeca',head),('haste',shaft)]:
 r[n]={'peca':iv(s,p),'bracket':iv(s,b),'positive_self':iv(s,s),'negative':iv(mv(s,(500,0,0)),p)}
r['peca_bracket']=iv(p,b)
r['washer_positive_1mm']=iv(mv(washer,(0,0,1)),p)
r['membrane_ray']=[[e.BoundBox.ZMin,e.BoundBox.ZMax] for e in p.common(Part.makeLine(V(x+3.18,y,-30),V(x+3.18,y,40))).Edges]
r['ray_controls']=[cube.common(Part.makeLine(V(5,5,-5),V(5,5,15))).Length,cube.common(Part.makeLine(V(50,5,-5),V(50,5,15))).Length]
p.exportStep(str(O/'peca-furo-M6-posicao-uso.step'))
d=App.newDocument('Astra2_M6')
for n,s in [('Peca_furo_M6',p),('Bracket_impresso',b),('COMPRAR_Arruela_6p4_12_1p6',washer),('COMPRAR_Porca_M6_DIN934_envelope',nut),('COMPRAR_Cabeca_ISO4762_envelope',head),('COMPRAR_Haste_M6x30_sem_rosca',shaft)]:
 o=d.addObject('PartDesign::Feature',n);o.Shape=s
import Import
Import.export(d.Objects,str(O/'conjunto-fixacao-M6-posicao-uso.step'))
d.recompute();d.saveAs(str(O/'conjunto-fixacao-M6-posicao-uso.FCStd'))
json.dump(r,open(str(O/'astra2-m6.json'),'w'),indent=2)
print(json.dumps(r),flush=True)
