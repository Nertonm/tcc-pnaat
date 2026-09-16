"""Treina o detector de CORPO (YOLOv8n) e avalia: val + smoke nas nossas imagens de deformidade.

Dataset: $PNAAT_CORPO_DATASET_DATA ou $PNAAT_MODELOS/corpo-detector-roi/dataset (uma classe
`corpo_deformidade` + negativos). A variante de 2 classes do `monta_corpo.py` entra por --data.
Base: yolov8n.pt COCO (transfer learning). GPU se disponivel.
"""
from __future__ import annotations

import json
import pathlib
import sys
from pathlib import Path
import os as _os
from pathlib import Path as _Path
try:
    from treino.caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO
except ModuleNotFoundError:
    from caminhos import RAIZ_REPO as _RAIZ_REPO, PNAAT_DADOS, PNAAT_MODELOS, PIPELINE, CONTRATO

# o default tem de ser a saida de `monta_corpo_detector.py`; a variante de 2 classes
# (`monta_corpo.py`, saida `corpo-dataset/`) entra com --data explicito.
DS = str(_os.environ.get("PNAAT_CORPO_DATASET_DATA")
         or (PNAAT_MODELOS / "corpo-detector-roi" / "dataset" / "data.yaml"))
# runs ficam com os modelos, nao na arvore de dado externo
PROJ = str(PNAAT_MODELOS / "corpo-runs")
NOME = "corpo"
EPOCAS = 80
IMGSZ = 416
LOTE = 16
SEED = 7


def main() -> int:
    import torch
    from ultralytics import YOLO

    dev = 0 if torch.cuda.is_available() else "cpu"
    print(f"dispositivo: {dev}" + (f" ({torch.cuda.get_device_name(0)})" if dev == 0 else ""), flush=True)
    print(f"dataset: {DS} | epocas {EPOCAS} | imgsz {IMGSZ} | lote {LOTE}", flush=True)

    if not Path(DS).is_file():
        print(f"dataset de corpo ausente: {DS}")
        print("monte antes: python treino/monta_corpo_detector.py (ou monta_corpo.py)")
        return 2

    m = YOLO("yolov8n.pt")
    m.train(data=DS, epochs=EPOCAS, imgsz=IMGSZ, batch=LOTE, device=dev, seed=SEED,
            project=PROJ, name=NOME, exist_ok=True, patience=20, plots=False, verbose=True)

    pesos = pathlib.Path(PROJ) / NOME / "weights" / "best.pt"
    print("\npesos:", pesos, pesos.stat().st_size if pesos.exists() else "AUSENTE", flush=True)
    if not pesos.is_file():
        print("ABORTADO: treino terminou sem best.pt; sem peso nao ha o que avaliar")
        return 3

    # avaliacao no val do proprio dataset
    r = YOLO(str(pesos)).val(data=DS, imgsz=IMGSZ, device=dev, verbose=False)
    print(f"val: mAP50={r.box.map50:.4f} mAP50-95={r.box.map:.4f}", flush=True)

    # smoke nas NOSSAS imagens de deformidade (9 frames) + normais do rig (5)
    base = _RAIZ_REPO / "dataset/nosso"
    alvos = sorted((base / "tampa").glob("deformidade_frame_*.jpg"))[:9]
    normais = sorted((base / "rig").glob("*.jpg"))[:5]
    det = YOLO(str(pesos))
    res = {"deformidade_propria": [], "normal_proprio": []}
    for rotulo, lista in (("deformidade_propria", alvos), ("normal_proprio", normais)):
        print(f"\n== {rotulo} ({len(lista)} imagens) ==", flush=True)
        for p in lista:
            r = det.predict(str(p), conf=0.25, imgsz=IMGSZ, device=dev, verbose=False)[0]
            n = 0 if r.boxes is None else len(r.boxes)
            if n == 0:
                print(f"   {p.name[:38]:<40} sem deteccao", flush=True)
                res[rotulo].append({"img": p.name, "det": None})
                continue
            i = int(max(range(n), key=lambda k: float(r.boxes.conf[k])))
            cls = str(r.names[int(r.boxes.cls[i])])
            conf = float(r.boxes.conf[i])
            print(f"   {p.name[:38]:<40} {cls:<12} conf={conf:.2f}", flush=True)
            res[rotulo].append({"img": p.name, "det": cls, "conf": conf})

    (pathlib.Path(PROJ) / NOME / "smoke-proprio.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("\nresumo do smoke salvo em", pathlib.Path(PROJ) / NOME / "smoke-proprio.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
