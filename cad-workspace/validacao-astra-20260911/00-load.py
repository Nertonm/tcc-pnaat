# Execute on the FreeCAD GUI thread via MCP execute_code. No originals are saved.
import os
import FreeCAD as App, Part, builtins
W=os.path.expanduser('~') + '/tcc-pnaat/github/cad-workspace/'
D=App.openDocument(W+'portico-montantes-20260911T063439Z/exports/portico-montantes.FCStd')
a={}
for k,f in [('p','peca-assento-nivelado-furo-M6.step'),('b','bracket-rot90Z-no-trilho.step'),('assembly','conjunto-fechado.step'),('recess','peca-assento-nivelado.step')]:
 a[k]=Part.read(W+'interface-peca-bracket-20260911/'+f)
for k,f in [('original','peca-dupla-plataformas.step'),('clamp','G-clamp_Tripod-component0.stl.brep'),('pad','clamp_protector.stl.brep'),('screw','screw_and_knurled_knobHD.stl.brep')]:
 a[k]=Part.read(W+'base-estrutura-20260911T053435Z/'+f)
a['rails']={k:D.getObject(k).Shape.copy() for k in ['MontanteA','MontanteB','Travessa','JuncaoA','JuncaoB','ChavetaA','ChavetaB']}
builtins.astra=a
print('Reference shapes loaded; run scripts 01 through 06 sequentially with exec(source, {}).')
