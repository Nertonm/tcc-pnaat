import Part, FreeCAD as App, json, math
from FreeCAD import Vector as V
from pathlib import Path
W=Path('"${TCC_HOME:-$HOME/tcc-pnaat/github}/cad-workspace"'); O=W/'lote-impressao-20260911'
def mv(s,v):
 t=s.copy();t.translate(V(*v));return t
def iv(a,b):
 c=a.common(b);v=c.Volume;ss=sum(t.Volume for t in c.Solids)
 assert c.isNull() or c.isValid()
 assert math.isfinite(v) and abs(v-ss)<1e-5,(v,ss)
 return v
cube=Part.makeBox(10,10,10)
r={'controls':[iv(cube,cube),iv(cube,mv(cube,(500,0,0)))]}
src=Part.read(str(W/'portico-montantes-20260911T063439Z/inputs/dinr135-007.5.step'))
profile=Part.Face(src.slice(V(1,0,0),2)[0]);r['rail_section']={'area':profile.Area,'edges':len(profile.Edges)}
# Original length X -> model vertical Y. Flange at source Y=7.5 -> left side of case rail.
profile.rotate(V(),V(0,0,1),90)
rail=profile.extrude(V(0,30,0)); rail.translate(V(-rail.BoundBox.XMin,-10-rail.BoundBox.YMin,-rail.BoundBox.ZMin))
r['case']={}
for n,xwall,zroof,zlow in [('case-pi5-base',67.9266,67.2498,33.6825),('case-pi5-tampa',67.8896,63.0499,27.5501)]:
 s=Part.read(str(O/('orientada-'+n+'.step')))
 # Locate using upper hook roof; rail flange top 0.18 below roof, lateral face 0.18 off back wall.
 t=mv(rail,(xwall+.18,0,zroof-.18-35))
 r['case'][n]={'placement_rail_min':[xwall+.18,-10,zroof-.18-35],'collision':iv(s,t),'positive_inward':iv(s,mv(t,(-1,0,0))),'negative_far':iv(s,mv(t,(500,0,0))), 'bbox':str(t.BoundBox)}
 print(n,r['case'][n],flush=True)
 # 2D local profile shows the collision rather than spatial sweeping
 wires=s.slice(V(0,1,0),s.BoundBox.YLength*.5)
 segments=[[list(v.Point) for v in e.Vertexes] for w in wires for e in w.Edges]
 rp=t.slice(V(0,1,0),5)
 r['case'][n]['section_case']=segments;r['case'][n]['section_rail']=[[list(v.Point) for v in e.Vertexes] for w in rp for e in w.Edges]
 t.exportStep(str(O/(n+'-trilho-datum-auditoria.step')))
json.dump(r,open(str(O/'astra2-case.json'),'w'),indent=2)
print(json.dumps({k:v for k,v in r.items() if k!='case'}),flush=True)
