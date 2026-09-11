import os
import Part, FreeCAD
from FreeCAD import Vector as V
P=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/base-estrutura-20260911T053435Z/'
g = Part.read(P+'G-clamp_Tripod-component0.stl.brep')
b = Part.read(P+'DIN Rail Bracket 4mm-component0.stl.brep')
bb=g.BoundBox; yseat=bb.YMax; xface=bb.XMin; GA=6.0; ALT=20.0
def box(x,y,z,p): return Part.makeBox(x,y,z,V(*p))
def move(s,ang=90,t=(-30.5,80.0009994506836,10)):
    s=s.copy(); s.rotate(V(),V(0,0,1),ang); s.translate(V(*t)); return s
b2 = b.fuse(box(35,16,3.1,(-13,-8,-5))).cut(box(11,10,5,(11,-5,1.001)))
b2 = b2.cut(Part.makeCylinder(2.2,12,V(15.6,0,-6),V(0,0,1))).removeSplitter()

peca = box(66.0,GA,ALT,(xface-GA,yseat,0.0)).fuse(box(GA,41.0,ALT,(xface-GA,bb.YMin,0.0))).removeSplitter()
for fx in (-45.0,-16.0):
    peca = peca.cut(Part.makeCylinder(1.7,26.0,V(fx,yseat-8.0,10.0),V(0,1,0)))
for fz in (4.0,16.0):
    peca = peca.cut(Part.makeCylinder(1.7,26.0,V(xface-10.0,42.0,fz),V(1,0,0)))
peca = peca.cut(Part.makeCylinder(3.175,20.0,V(-30.5,yseat-8.0,10.0),V(0,1,0)))
peca = peca.cut(Part.makeCylinder(3.175,20.0,V(xface-10.0,42.0,10.0),V(1,0,0)))

enc = move(b2)
eb = enc.BoundBox
print('encaixe APOS move(b2): bbox X %.3f..%.3f Y %.3f..%.3f Z %.3f..%.3f' % (
    eb.XMin,eb.XMax,eb.YMin,eb.YMax,eb.ZMin,eb.ZMax))
pb = peca.BoundBox
print('peca                : bbox X %.3f..%.3f Y %.3f..%.3f Z %.3f..%.3f' % (
    pb.XMin,pb.XMax,pb.YMin,pb.YMax,pb.ZMin,pb.ZMax))
print('  topo da peca (Y) = %.3f   base do encaixe (Y) = %.3f   gap = %.6f' % (
    pb.YMax, eb.YMin, eb.YMin-pb.YMax))
print()
# onde estao as faces do encaixe com Y minimo (a base)?
print('=== faces do encaixe com Y <= %.3f ===' % (eb.YMin+0.001))
for i,f in enumerate(enc.Faces):
    fbb=f.BoundBox
    if fbb.YMin <= eb.YMin+0.001:
        c=f.CenterOfMass
        print('  face %2d: area %8.3f  centro (%.2f, %.2f, %.2f)  bbox Y %.3f..%.3f' % (
            i, f.Area, c.x,c.y,c.z, fbb.YMin,fbb.YMax))
print()
print('=== faces da peca com Y >= %.3f (o topo do braco H) ===' % (pb.YMax-0.001))
for i,f in enumerate(peca.Faces):
    fbb=f.BoundBox
    if fbb.YMax >= pb.YMax-0.001:
        c=f.CenterOfMass
        print('  face %2d: area %8.3f  centro (%.2f, %.2f, %.2f)  bbox Y %.3f..%.3f' % (
            i, f.Area, c.x,c.y,c.z, fbb.YMin,fbb.YMax))
print()
print('=== a face Z do encaixe: o encaixe cobre quais X e Z na base? ===')
for i,f in enumerate(enc.Faces):
    fbb=f.BoundBox
    if abs(fbb.YMin-eb.YMin)<0.001 and fbb.XLength>1:
        print('  face %d: X %.2f..%.2f  Z %.2f..%.2f  area %.3f' % (i,fbb.XMin,fbb.XMax,fbb.ZMin,fbb.ZMax,f.Area))
