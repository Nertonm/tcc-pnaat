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

def build_peca(holes=True):
    p = box(66.0,GA,ALT,(xface-GA,yseat,0.0)).fuse(box(GA,41.0,ALT,(xface-GA,bb.YMin,0.0))).removeSplitter()
    p = p.cut(Part.makeCylinder(3.175,20.0,V(-30.5,yseat-8.0,10.0),V(0,1,0)))
    p = p.cut(Part.makeCylinder(3.175,20.0,V(xface-10.0,42.0,10.0),V(1,0,0)))
    if holes:
        for fx in (-45.0,-16.0):
            p = p.cut(Part.makeCylinder(1.7,26.0,V(fx,yseat-8.0,10.0),V(0,1,0)))
        for fz in (4.0,16.0):
            p = p.cut(Part.makeCylinder(1.7,26.0,V(xface-10.0,42.0,fz),V(1,0,0)))
    return p
peca = build_peca(True)
def mkEnc(dy=0.0, dz=0.0, holes=True):
    e = move(b2).translate(V(0,(yseat+GA)-67.0+dy,dz))
    if holes:
        for fx in (-45.0,-16.0):
            e = e.cut(Part.makeCylinder(1.7,40.0,V(fx,yseat+2.0,10.0),V(0,1,0)))
    return e
enc = mkEnc()

def area_by_penetration(s1, s2, direcao, passo=0.02):
    """area de contato: penetra s1 em s2 por 'passo' na direcao dada e divide o volume"""
    t = s1.copy(); t.translate(direcao*passo)
    return t.common(s2).Volume / passo

print('#### MEDIDOR CORRIGIDO — area por penetracao calibrada (passo 0.02mm) ####')
print()
print('--- auto-teste do medidor (dois cubos de 20mm com face comum) ---')
c1 = Part.makeBox(20,20,20,V(0,0,0)); c2 = Part.makeBox(20,20,20,V(0,20,0))
print('  esperado 400.000 mm2 (face 20x20) | medido %.3f mm2' % area_by_penetration(c2,c1,V(0,-1,0)))
c3 = Part.makeBox(20,20,20,V(0,22,0))
print('  cubos separados 2mm -> esperado 0.000 | medido %.3f' % area_by_penetration(c3,c1,V(0,-1,0)))
print()
print('--- contatos reais (por penetracao na direcao correta) ---')
r = Part.read(P+'inputs/dinr135-007.5.step'); r.rotate(V(),V(1,0,0),90); r.translate(V(7.5,0,0))
rt = move(r).translate(V(0,(yseat+GA)-67.0,0))
print('  encaixe x peca   (penetra -Y): %9.3f mm2' % area_by_penetration(enc, peca, V(0,-1,0)))
print('  trilho  x encaixe(penetra -Y): %9.3f mm2' % area_by_penetration(rt, enc, V(0,-1,0)))
print('  clamp   x peca   (penetra -Y): %9.3f mm2' % area_by_penetration(peca, g, V(0,-1,0)))
print()
print('--- MUTACOES (os testes negativos que antes davam "cego") ---')
e_noh = mkEnc(holes=False)
print('  M1 encaixe SEM furos vs peca COM furos : %9.3f mm2' % area_by_penetration(e_noh, peca, V(0,-1,0)))
print('  M2 encaixe COM furos vs peca SEM furos : %9.3f mm2' % area_by_penetration(enc, build_peca(False), V(0,-1,0)))
e_off = mkEnc(dz=1.0)
print('  M3 encaixe deslocado 1mm em Z          : %9.3f mm2' % area_by_penetration(e_off, peca, V(0,-1,0)))
e_gap = mkEnc(dy=0.3)
print('  M4 encaixe afastado 0.3mm (gap)        : %9.3f mm2' % area_by_penetration(e_gap, peca, V(0,-1,0)))
