#!/usr/bin/env python3
"""Classifica imagens das garrafas via Gemini free tier (auxiliary.vision).

Usa o cliente auxiliar do agente (pool de credenciais Gemini, rotacao automatica).
Escreve um JSON por imagem em --out e imprime um resumo.

Uso:
  PNAAT_AGENTE_LIB=<lib do agente> <python do agente> \
    classificar_gemini.py --dir DIR --out DIR [--shard i n] [--limit N] [--sleep 4]
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import sys
from pathlib import Path

# A lib do agente vem do ambiente (PNAAT_AGENTE_LIB); o diretorio de dados do agente
# ja e herdado do host, entao o repo nao guarda nenhum dos dois.
_LIB_AGENTE = os.environ.get('PNAAT_AGENTE_LIB')
if _LIB_AGENTE:
    sys.path.insert(0, _LIB_AGENTE)

from agent.auxiliary_client import async_call_llm, extract_content_or_reasoning  # noqa: E402

CLASSES = ["normal", "tampa_ausente", "tampa_mal_rosqueada", "deformidade"]
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

PROMPT = (
    "Você inspeciona garrafas em uma linha de envase. Olhe a imagem e classifique o item.\n"
    "Responda SOMENTE com um JSON (sem texto antes ou depois), no formato exato:\n"
    '{"classe": "normal|tampa_ausente|tampa_mal_rosqueada|deformidade", '
    '"confianca": 0.0-1.0, "observacao": "curta"}\n'
    "Definições: normal = tampa presente e bem rosqueada, corpo sem deformidade; "
    "tampa_ausente = sem tampa no gargalo; tampa_mal_rosqueada = tampa torta/desalinhada/"
    "frisada; deformidade = amassado/entortamento no corpo. "
    "Se não houver garrafa visível, use classe \"normal\" com confianca 0.0 e explique na observacao."
)


def image_part(p: Path) -> dict:
    mime = "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def parse_json(text: str) -> dict:
    if not text:
        return {"classe": "erro", "confianca": 0.0, "observacao": "resposta vazia"}
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {"classe": "erro", "confianca": 0.0, "observacao": text[:200]}
    try:
        d = json.loads(m.group(0))
    except Exception:
        return {"classe": "erro", "confianca": 0.0, "observacao": m.group(0)[:200]}
    c = str(d.get("classe", "erro")).strip().lower()
    if c not in CLASSES:
        c = "erro"
    return {"classe": c, "confianca": float(d.get("confianca", 0) or 0), "observacao": str(d.get("observacao", ""))[:200]}


async def classify(p: Path, retries: int = 2) -> dict:
    messages = [{"role": "user", "content": [{"type": "text", "text": PROMPT}, image_part(p)]}]
    last = None
    for _ in range(retries):
        try:
            resp = await async_call_llm(task="vision", messages=messages, temperature=0.0,
                                        max_tokens=2000, timeout=120)
            out = parse_json(extract_content_or_reasoning(resp))
            if out["classe"] != "erro":
                return out
            last = out
        except Exception as e:  # noqa: BLE001
            last = {"classe": "erro", "confianca": 0.0, "observacao": f"excecao: {e}"[:200]}
        await asyncio.sleep(3)
    return last


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--shard", nargs=2, type=int, default=None, metavar=("I", "N"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=4.0)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    imgs = sorted(p for p in args.dir.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXT)
    if args.shard:
        i, n = args.shard
        imgs = [p for k, p in enumerate(imgs) if k % n == i]
    if args.limit:
        imgs = imgs[: args.limit]

    cont = {}
    for p in imgs:
        res = await classify(p)
        (args.out / (p.stem + ".json")).write_text(json.dumps(
            {"arquivo": p.name, "origem": str(p), **res}, ensure_ascii=False, indent=1))
        cont[res["classe"]] = cont.get(res["classe"], 0) + 1
        print(f"{p.name}\t{res['classe']}\t{res['confianca']:.2f}", flush=True)
        await asyncio.sleep(args.sleep)

    print("RESUMO", json.dumps(cont, ensure_ascii=False), "total", len(imgs))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))