#!/usr/bin/env python3
"""
repro-montagem.py — VERSÃO CORRIGIDA (2026-09-11, após auditoria do Astra)

O QUE ESTAVA ERRADO NA VERSÃO ANTERIOR
  A v1 chamava build_peca() do adv4.py, que RECONSTRÓI a peça adaptadora como uma
  fusão de caixas sintéticas (peça de ~11.522 mm³) em vez de carregar a peça
  OFICIAL (22.762,884649 mm³). Além disso o export dela sobrescrevia arquivos da
  composição. O Astra se recusou a executá-la e reportou:
    "build_peca() reconstrói uma peça de caixas e seu export sobrescreve arquivos
     da composição. Essa rotina não reproduz a peça corrigida oficial."

O QUE ESTA VERSÃO FAZ
  Carrega os arquivos REAIS do projeto, aplica as modificações da interface
  (rebaixo + furo M6), monta e MEDE — sem escrever em nenhum arquivo existente.

DATUM (reportado pelo Astra, sem ele os números não reproduzem):
  A peça isolada precisa de translação (0; +0,001999; -11,5) para coincidir com
  conjunto-fechado.step. O assento local Z=19,5 passa a Z=8,0 na montagem.
  O centro do furo novo local Y=85,4 passa a Y=85,401999.

USO (no host de bancada, dentro do squashfs-root do FreeCAD):
  SR=$HOME/.cache/qwen-mm-plugins/apps/freecad-1.1.1/squashfs-root
  runuser -u "${TCC_USER:-$USER}" -- env \
    LD_LIBRARY_PATH=$SR/usr/lib/x86_64-linux-gnu:$SR/usr/lib \
    QT_PLUGIN_PATH=$SR/usr/lib/x86_64-linux-gnu/qt5/plugins \
    $SR/usr/bin/freecadcmd repro-montagem.py

  Nada é escrito. Toda medição vem com controle positivo e negativo.
"""
import FreeCAD, Part, os, sys
from FreeCAD import Vector as V

W=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/'
P=W+'base-estrutura-20260911T053435Z/'

# ---------------- arquivos REAIS ----------------
PECA_OFICIAL   = P+'peca-dupla-plataformas.step'          # 22.762,884649 mm3 (original)
BRACKET        = P+'DIN Rail Bracket 4mm-component0.stl.brep'
PORTICO        = W+'portico-montantes-20260911T063439Z/exports/portico-montantes.FCStd'

# ---------------- parâmetros da interface (medidos, não inventados) ----------------
ENGATE   = 5.5      # mm que o trilho entra no bracket — PDF do autor: "5.5mm of the rail inserts"
ASSENTO  = 8.0      # Z no frame montado onde a base do bracket apoia
DATUM_Y  = 0.001999 # correção do Astra: sem ela a peça isolada não coincide
DATUM_Z  = -11.5    # assento local Z=19,5 -> Z=8,0
REBAIXO  = (39.5, 26.5, 12.0)   # pegada x profundidade x altura, acima de Z=19,5 (frame local)
FURO_R   = 3.175    # Ø6.35 = clearance M6
FURO_XY  = (-30.50, 85.40)      # centro local do furo (coincide com o eixo do bracket)

def iv(a, bb_shape):
    """Interseccao HONESTA: reporta ShapeType, nº de solidos e volume somado.
       NUNCA converte ausencia de solidos em 0.0 silenciosamente."""
    it = a.common(bb_shape)
    st = it.ShapeType
    ns = len(it.Solids)
    vol = sum(x.Volume for x in it.Solids)
    return vol, st, ns

def contato(a, b):
    """Contato por faces coincidentes (face.common). Só mede coincidência nominal."""
    tot=0.0; pares=0; F2=b.Faces
    for f1 in a.Faces:
        b1=f1.BoundBox
        for f2 in F2:
            b2=f2.BoundBox
            if b1.XMax<b2.XMin-1e-6 or b2.XMax<b1.XMin-1e-6: continue
            if b1.YMax<b2.YMin-1e-6 or b2.YMax<b1.YMin-1e-6: continue
            if b1.ZMax<b2.ZMin-1e-6 or b2.ZMax<b1.ZMin-1e-6: continue
            try:
                c=f1.common(f2)
                if c.Faces: tot+=sum(x.Area for x in c.Faces); pares+=1
            except Exception: pass
    return tot,pares

def carrega_solido(p, nome):
    s=Part.read(p)
    if not s.Solids:
        s=Part.makeSolid(s.Shells[0])
    assert s.isValid(), '%s: shape invalido' % nome
    print('  [%s] type=%s solids=%d isValid=%s vol=%.6f' % (nome, s.ShapeType, len(s.Solids), s.isValid(), s.Volume))
    return s

print('='*72)
print('REPRO-MONTAGEM (v2) — carrega arquivos REAIS, nao reconstroi caixas')
print('='*72)

# ---------------- 1. carregar ----------------
print('\n1. CARREGANDO')
peca0 = carrega_solido(PECA_OFICIAL, 'peca oficial')
brack = carrega_solido(BRACKET, 'bracket')
doc = FreeCAD.openDocument(PORTICO)
def byLab(n):
    for o in doc.Objects:
        if o.Label==n: return o.Shape
    raise KeyError(n)
MA = byLab('MontanteA')
bbA = MA.BoundBox
print('  [MontanteA] X %.3f..%.3f  Y %.3f..%.3f  Z %.3f..%.3f' % (
    bbA.XMin,bbA.XMax,bbA.YMin,bbA.YMax,bbA.ZMin,bbA.ZMax))
print('  vertical = Y (MontanteA mede 35 x 450 x 7.5 em X/Y/Z)')

# ---------------- 2. modificar a peca (em memoria, sem escrever) ----------------
print('\n2. MODIFICACOES NA PECA (em memoria)')
rebaixo = Part.makeBox(REBAIXO[0], REBAIXO[1], REBAIXO[2],
                       V(FURO_XY[0]-REBAIXO[0]/2.0, FURO_XY[1]-REBAIXO[1]/2.0, 19.5))
p1 = peca0.cut(rebaixo)
d_reb = peca0.Volume - p1.Volume
cil = Part.makeCylinder(FURO_R, 60.0, V(FURO_XY[0], FURO_XY[1], -5.0), V(0,0,1))
p2 = p1.cut(cil)
d_fur = p1.Volume - p2.Volume
print('  original          %.6f mm3' % peca0.Volume)
print('  - rebaixo         %.6f mm3 (removeu %.6f)' % (p1.Volume, d_reb))
print('  - furo M6         %.6f mm3 (removeu %.6f)' % (p2.Volume, d_fur))
# valores de referencia do Astra: 22762.884649 / 22746.077410 / 22647.902836 / 16.807239 / 98.174574
peca = p2

# ---------------- 3. CONTROLES DO MEDIDOR ----------------
print('\n3. CONTROLES DO MEDIDOR (obrigatorios na mesma rodada)')
c1 = Part.makeBox(10,10,10); c2 = Part.makeBox(10,10,10,V(0,0,0))     # identicos: 1000 mm3
c3 = Part.makeBox(10,10,10,V(50,0,0))                                  # distante
v_ctl_pos,_,n_p = iv(c1,c2); v_ctl_neg,_,n_n = iv(c1,c3)
print('  CTL+ volume  (cubo consigo mesmo): %.6f mm3  (%d solids)  %s' % (
    v_ctl_pos,n_p,'OK' if v_ctl_pos>999 else 'CEGO!'))
print('  CTL- volume  (cubo a 50mm):        %.6f mm3  (%d solids)  %s' % (
    v_ctl_neg,n_n,'OK' if v_ctl_neg<1e-9 else 'FALHOU'))
d1 = Part.makeBox(10,10,10); d2 = Part.makeBox(10,10,10,V(10,0,0))     # face comum: 100 mm2
ct_pos,_ = contato(d1,d2)
print('  CTL+ contato (cubos face comum):   %.6f mm2  %s' % (ct_pos,'OK' if abs(ct_pos-100)<1e-6 else 'FALHOU'))
ct_neg,_ = contato(d1,Part.makeBox(10,10,10,V(12,0,0)))
print('  CTL- contato (cubos a 2mm):        %.6f mm2  %s' % (ct_neg,'OK' if ct_neg<1e-9 else 'FALHOU'))

# ---------------- 4. POSICIONAR E MONTAR ----------------
print('\n4. MONTAGEM')
# bracket: rot 90 em Z, engate 5.5 na ponta inferior do trilho, base em Z=8
b = brack.copy(); b.rotate(V(), V(0,0,1), 90.0)
bb = b.BoundBox
b.translate(V(bbA.Center.x-bb.Center.x, bbA.YMin+ENGATE-bb.YMax, ASSENTO-bb.ZMin))
bB = b.BoundBox
print('  bracket: X %.3f..%.3f  Y %.3f..%.3f  Z %.3f..%.3f' % (bB.XMin,bB.XMax,bB.YMin,bB.YMax,bB.ZMin,bB.ZMax))
# peca: assento local Z=19.5 -> Z=8.0 ; eixo do furo local (-30.50, 85.40) no eixo do bracket
# (o furo M6 do bracket fica no centro X,Y dele apos o rot 90 em Z)
p = peca.copy()
p.translate(V(bB.Center.x - FURO_XY[0], bB.Center.y - FURO_XY[1], ASSENTO - 19.5))
pB = p.BoundBox
print('  peca   : X %.3f..%.3f  Y %.3f..%.3f  Z %.3f..%.3f' % (pB.XMin,pB.XMax,pB.YMin,pB.YMax,pB.ZMin,pB.ZMax))

# ---------------- 5. GATES ----------------
print('\n5. GATES')
v_bk, st_bk, n_bk = iv(b, MA)
print('  bracket x MontanteA: colisao %.6f mm3 (type=%s, %d solids)  dist %.6f' % (
    v_bk, st_bk, n_bk, b.distToShape(MA)[0]))
v_pk, st_pk, n_pk = iv(peca, b)          # peca SEM placement x bracket — deve FALHAR
pt, pr = contato(p, b)
print('  peca   x bracket   : CONTATO %.6f mm2 (%d pares)   colisao %.6f mm3 (type=%s, %d solids)' % (
    pt, pr, v_pk, st_pk, n_pk))
v_pt,_,n_pt = iv(p, MA)
print('  peca   x MontanteA : colisao %.6f mm3 (%d solids)' % (v_pt,n_pt))

# controles dos gates de montagem
b_bad = b.copy(); b_bad.translate(V(0,3.0,0))
v_cp,_,_ = iv(b_bad, MA)
print('  CTL+ montagem (bracket +3 Y): %.6f mm3  %s' % (v_cp,'OK' if v_cp>1 else 'CEGO!'))
b_far = b.copy(); b_far.translate(V(0,500.0,0))
v_cn,_,_ = iv(b_far, MA)
print('  CTL- montagem (bracket +500 Y): %.6f mm3  %s' % (v_cn,'OK' if v_cn<1e-9 else 'FALHOU'))

# ---------------- 6. VEREDITO ----------------
print('\n6. VEREDITO')
ref = {'original':22762.884649,'rebaixo':22746.077410,'furo':22647.902836,
       'contacto':791.664691,'ctl_pos':137.304423}
ok = True
def chk(nome, got, exp, tol=1e-3):
    global ok
    good = abs(got-exp)<=tol
    ok = ok and good
    print('  %-28s got %.6f  esp %.6f  %s' % (nome, got, exp, 'OK' if good else 'DIVERGE'))
chk('vol original', peca0.Volume, ref['original'])
chk('vol so rebaixo', p1.Volume, ref['rebaixo'])
chk('vol rebaixo+furo', p2.Volume, ref['furo'])
chk('contato peca x bracket', pt, ref['contacto'], 1e-2)
chk('CTL+ bracket +3Y', v_cp, ref['ctl_pos'], 1e-2)
print()
print('  RESULTADO: %s' % ('REPRODUZ os numeros do dossie/Astra' if ok else 'DIVERGE — investigar'))
print('  (nenhum arquivo foi escrito)')
print('  STATUS: %s' % ('PASS' if ok else 'FAIL'))
# NAO usar sys.exit() aqui: o freecadcmd com stdout em pipe bufferiza, e o exit
# antecipado engole TODO o output do script (observado em 2026-09-11 — o log saiu
# com 562 bytes, so o banner do FreeCAD). Sair normalmente garante o flush.
