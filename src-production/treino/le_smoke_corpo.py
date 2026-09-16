"""Le o resultado do smoke do detector de corpo nas imagens proprias."""
import json
import pathlib
import os as _os
from pathlib import Path as _Path
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO

# o smoke e gravado pelo treino junto dos runs do modelo, nao na arvore de dado externo
p = _Path(_os.environ.get("PNAAT_CORPO_SMOKE")
          or (PNAAT_MODELOS / "corpo-runs/corpo/smoke-proprio.json"))
if not p.is_file():
    raise SystemExit(f"smoke do corpo ausente: {p}; rode treino/treina_corpo.py antes")
d = json.load(open(p))
for chave in ("deformidade_propria", "normal_proprio"):
    itens = d.get(chave) or []
    print(f"== {chave} ({len(itens)} imagens) ==")
    for it in itens:
        det = it.get("det")
        if det:
            print("   %-42s %-14s conf=%.2f" % (it["img"][:42], det, it.get("conf") or 0.0))
        else:
            print("   %-42s sem deteccao" % it["img"][:42])
    detectados = sum(1 for it in itens if it.get("det") == "deformidade")
    print(f"   -> detectados como deformidade: {detectados}/{len(itens)}")
    print()
