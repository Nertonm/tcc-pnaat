import Part, Mesh, zipfile, re, os
from FreeCAD import Vector as V
import FreeCAD as App

OUT='/tmp/r07'; os.makedirs(OUT, exist_ok=True)
B=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/references/vendor/'
RAWB=B+'din-rail-parts/raw/'

def m3mf(path):
    z=zipfile.ZipFile(path)
    xml=z.read([n for n in z.namelist() if n.endswith('.model')][0]).decode('utf-8','replace')
    vs=[(float(a),float(b),float(c)) for a,b,c in re.findall(r'<vertex x="([-\d.eE]+)" y="([-\d.eE]+)" z="([-\d.eE]+)"', xml)]
    ts=[tuple(int(x) for x in m.groups()) for m in re.finditer(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', xml)]
    me=Mesh.Mesh()
    for a,b,c in ts: me.addFacet(V(*vs[a]),V(*vs[b]),V(*vs[c]))
    me.removeDuplicatedPoints(); me.removeDuplicatedFacets(); me.fixDegenerations(); me.harmonizeNormals()
    sh=Part.Shape(); sh.makeShapeFromMesh(me.Topology,0.02)
    sol=Part.makeSolid(sh.Shells[0])
    if sol.Volume<0: sol.reverse()
    return sol

def load_stl(p):
    m=Mesh.Mesh(p); m.removeDuplicatedPoints(); m.harmonizeNormals()
    sh=Part.Shape(); sh.makeShapeFromMesh(m.Topology,0.02)
    try:
        s=Part.makeSolid(sh.Shells[0])
        if s.Volume>0: return s
    except Exception: pass
    return sh

g = load_stl('/tmp/cenaF/01-g-clamp.stl')

# ================= CANTONEIRA (peca nova, aproveita os DOIS furos do clamp) =================
# furo do clamp eixo Y: (X-30.5, Z10) na face Y=67
# furo do clamp eixo X: (Y42,   Z10) na face X=-66
ABA_H = Part.makeBox(66.0, 5.0, 20.0, V(-66.0, 67.0, 0.0))     # assenta na face +Y
ABA_V = Part.makeBox(5.0, 35.0, 20.0, V(-71.0, 32.0, 0.0))     # encosta na face -X
cant = ABA_H.fuse(ABA_V).removeSplitter()
# furos de fixacao da cantoneira ao clamp
cant = cant.cut(Part.makeCylinder(3.175, 12.0, V(-30.5, 64.0, 10.0), V(0,1,0)))   # eixo Y -> 1/4"
cant = cant.cut(Part.makeCylinder(3.175, 12.0, V(-73.0, 42.0, 10.0), V(1,0,0)))   # eixo X -> 1/4"
# furos para o Redux (furos dele: 51mm entre centros, Ø2.8 -> passo Ø3.4 selftap)
for fx in (-30.5-25.5, -30.5+25.5):
    cant = cant.cut(Part.makeCylinder(1.7, 12.0, V(fx, 66.0, 10.0), V(0,1,0)))
print('CANTONEIRA: bbox X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f  vol %.0f' % (
    cant.BoundBox.XMin,cant.BoundBox.XMax,cant.BoundBox.YMin,cant.BoundBox.YMax,
    cant.BoundBox.ZMin,cant.BoundBox.ZMax,cant.Volume))

# ================= REDUX rotacionado (furos para Y) =================
dux = m3mf(RAWB+'din-clip-redux-selftap.3mf')
dux.rotate(V(0,0,0), V(1,0,0), -90.0)     # Z(furos) -> Y ; altura 7.6 em Y
db = dux.BoundBox
print('REDUX apos rot(X,-90): X %.2f..%.2f (%.1f)  Y %.2f..%.2f (%.1f)  Z %.2f..%.2f (%.1f)' % (
    db.XMin,db.XMax,db.XLength, db.YMin,db.YMax,db.YLength, db.ZMin,db.ZMax,db.ZLength))
# posicionar sobre a aba horizontal (Y=72), centrado no eixo do clamp
dux.translate(V(-30.5-(db.XMin+db.XMax)/2.0, 72.0-db.YMin, 10.0-(db.ZMin+db.ZMax)/2.0))

# ================= TRILHO: vertical, engatado no Redux =================
rail = Part.read('/tmp/dinr135-007.5.step')
rail.rotate(V(0,0,0), V(1,1,1), 120.0)
rb = rail.BoundBox
cx=(rb.XMin+rb.XMax)/2.0; cz=(rb.ZMin+rb.ZMax)/2.0
rail.translate(V(-30.5-cx, 72.0-rb.YMin, 10.0-cz))

for nome, sh in [('01-g-clamp',g),('02-cantoneira',cant),('03-redux',dux),('04-trilho-ts35',rail)]:
    sh.exportStl('%s/%s.stl'%(OUT,nome))
    b=sh.BoundBox
    print('%-18s X %7.2f..%7.2f  Y %7.2f..%7.2f  Z %7.2f..%7.2f'%(nome,b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax))

print()
print('--- INTERFERENCIAS ---')
pares=[('cantoneira x clamp',cant,g),('redux x clamp',dux,g),('redux x cantoneira',dux,cant),
       ('trilho x cantoneira',rail,cant),('trilho x redux (encaixe)',rail,dux)]
for nome,s1,s2 in pares:
    try:
        it=s1.common(s2); vol=it.Volume if it.Solids else 0.0
        print('  %-30s %10.3f mm3'%(nome,vol))
    except Exception as e:
        print('  %-30s ERRO %s'%(nome,str(e)[:40]))
