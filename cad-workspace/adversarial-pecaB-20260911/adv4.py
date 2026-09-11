import os
import Part, FreeCAD, json
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

def mkEnc(dy=0.0, dz=0.0, holes=True, drill_after_move=False):
    """CORRIGIDO: se drill_after_move, os furos sao cortados DEPOIS do deslocamento
       (posicao relativa ao corpo) — e assim que uma peca fabricada errada sairia."""
    e = move(b2).translate(V(0,(yseat+GA)-67.0+dy,dz))
    if holes:
        off_y = dz if drill_after_move else 0.0
        for fx in (-45.0,-16.0):
            e = e.cut(Part.makeCylinder(1.7,40.0,V(fx+off_y,yseat+2.0,10.0),V(0,1,0)))
    return e

def eixos(s, raio, tol=0.05, eixo_esperado=None):
    out=[]
    for f in s.Faces:
        if f.Surface.__class__.__name__!='Cylinder': continue
        cy=f.Surface
        if abs(cy.Radius-raio)>tol: continue
        c=cy.Center; d=cy.Axis
        if eixo_esperado=='Y' and abs(abs(d.y)-1.0)>0.01: continue
        if eixo_esperado=='X' and abs(abs(d.x)-1.0)>0.01: continue
        out.append((round(c.x,2), round(c.z,2)))
    return sorted(set(out))
def area_por_penetracao(s1, s2, passo=0.02):
    t=s1.copy(); t.translate(V(0,-passo,0)); return t.common(s2).Volume/passo

def bateria(nome, peca_, enc_, deve_falhar):
    area=area_por_penetracao(enc_,peca_)
    coax=set(eixos(peca_,1.70,eixo_esperado='Y'))==set(eixos(enc_,1.70,eixo_esperado='Y'))
    sol=(len(peca_.Solids)==1) and (len(enc_.Solids)==1)
    val=peca_.isValid() and enc_.isValid()
    ok=(area>300.0) and coax and sol and val
    falhou = not ok
    flag=''
    if deve_falhar and not falhou: flag='  <<< MUTACAO NAO PEGA'
    if (not deve_falhar) and falhou: flag='  <<< FALSO POSITIVO'
    print('  %-40s area %7.3f coax %-5s sol %-5s -> %s%s' % (
        nome, area, coax, sol, 'PASSA' if ok else 'FALHA', flag))
    return ok

print('#### BATERIA ADVERSARIAL v4 — mutacoes corrigidas ####')
print()
r={}
r['ref']=bateria('REFERENCIA (deve passar)',      build_peca(True), mkEnc(), False)
r['M1'] =bateria('M1 encaixe SEM furos',           build_peca(True), mkEnc(holes=False), True)
r['M2'] =bateria('M2 encaixe com furo deslocado (furo acompanha o corpo)',
                  build_peca(True), mkEnc(dz=1.0, drill_after_move=True), True)
r['M3'] =bateria('M3 encaixe afastado 0,3mm',      build_peca(True), mkEnc(dy=0.3), True)
p4 = build_peca(True).cut(Part.makeBox(2.0,200.0,200.0,V(-40.0,-100,-100)))
r['M4'] =bateria('M4 peca partida em 2 solidos',   p4, mkEnc(), True)
print()
print('solids em M4 = %d (mutacao valida se >1)' % len(p4.Solids))
print('REFERENCIA passou: %s' % r['ref'])
print('mutacoes detectadas: %d/4' % sum(1 for k in ('M1','M2','M3','M4') if not r[k]))
