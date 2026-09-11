#!/usr/bin/env python3
"""Classifica imagens das garrafas via Gemini (REST direto, pool de chaves, resumivel).

Le as chaves do arquivo de credenciais do agente (PNAAT_AGENTE_AUTH; nao imprime
segredos), roda direto na API Gemini
(sem passar pelo fallback do aux), rotaciona chaves/modelos em 429/503 e grava 1 JSON
por imagem. Re-execucoes pulam imagens ja classificadas (classe != erro).

Uso:
  python3 classificar_rest.py --dir D --out O [--limit N] [--sleep 2] [--retries 6]
"""
from __future__ import annotations
import os

import argparse
import base64
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

def auth_path() -> Path:
    """Arquivo de credenciais do agente (caminho no ambiente, nunca no repo)."""
    caminho = os.environ.get("PNAAT_AGENTE_AUTH")
    if not caminho:
        raise SystemExit("defina PNAAT_AGENTE_AUTH (arquivo de credenciais do agente)")
    return Path(caminho)
CLASSES = ["normal", "tampa_ausente", "tampa_mal_rosqueada", "deformidade"]
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MODELS = ["gemini-3.6-flash", "gemini-2.5-flash"]

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


def load_keys() -> list[str]:
    d = json.loads(auth_path().read_text())
    return [e["access_token"] for e in d["credential_pool"]["gemini"] if e.get("access_token")]


def parse(text: str) -> dict:
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


def call(key: str, model: str, img: Path) -> tuple[int, str]:
    mime = "image/jpeg" if img.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    payload = {"contents": [{"parts": [
        {"text": PROMPT},
        {"inline_data": {"mime_type": mime, "data": base64.b64encode(img.read_bytes()).decode()}},
    ]}], "generationConfig": {"maxOutputTokens": 2000, "temperature": 0.0}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            b = json.loads(r.read())
            parts = b.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            return r.status, "".join(p.get("text", "") for p in parts)
    except urllib.error.HTTPError as ex:
        return ex.code, ex.read().decode(errors="replace")[:200]
    except Exception as ex:  # noqa: BLE001
        return 0, f"excecao: {ex}"[:200]


def classify(img: Path, keys: list[str], retries: int) -> dict:
    attempt = 0
    last = {"classe": "erro", "confianca": 0.0, "observacao": "sem tentativa"}
    while attempt < retries:
        key = keys[attempt % len(keys)]
        model = MODELS[(attempt // len(keys)) % len(MODELS)]
        code, body = call(key, model, img)
        if code == 200:
            out = parse(body)
            if out["classe"] != "erro":
                return out
            last = out
        else:
            last = {"classe": "erro", "confianca": 0.0, "observacao": f"HTTP {code} {body}"[:200]}
        attempt += 1
        time.sleep(min(3 * attempt, 20))
    return last


def pool_disponivel() -> tuple[int, int]:
    """(chaves nao-exaustas, total). Evita gastar tempo batendo em pool esgotado (429)."""
    try:
        d = json.loads(auth_path().read_text())
        g = d["credential_pool"]["gemini"]
        ok = [e for e in g if str(e.get("last_status", "")).lower() != "exhausted"]
        return len(ok), len(g)
    except Exception:
        return 0, 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=2.0)
    ap.add_argument("--retries", type=int, default=6)
    ap.add_argument("--redo-erros", action="store_true", help="reprocessa tambem os erros antigos")
    ap.add_argument("--max-calls", type=int, default=0, help="limite de chamadas nesta execucao (0=ilimitado)")
    ap.add_argument("--ignorar-quota", action="store_true", help="nao aborta se o pool estiver exausto")
    args = ap.parse_args()

    disp, total = pool_disponivel()
    print(f"pool gemini: {disp}/{total} chaves disponiveis", flush=True)
    if disp == 0 and not args.ignorar_quota:
        print("QUOTA_ESGOTADA: todas as chaves do pool marcadas 'exhausted' (429). "
              "Nada a fazer agora; rode quando a cota diaria resetar ou use outra credencial.", flush=True)
        return 3

    keys = load_keys()
    print("chaves carregadas:", len(keys), flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    imgs = sorted(p for p in args.dir.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXT)

    pend = []
    for p in imgs:
        jf = args.out / (p.stem + ".json")
        if jf.exists() and not args.redo_erros:
            try:
                if json.loads(jf.read_text()).get("classe") not in (None, "erro"):
                    continue
            except Exception:
                pass
        pend.append(p)
    if args.limit:
        pend = pend[: args.limit]
    print("pendentes:", len(pend), flush=True)

    cont: dict[str, int] = {}
    chamadas = 0
    for p in pend:
        if args.max_calls and chamadas >= args.max_calls:
            print(f"limite de chamadas atingido ({args.max_calls})", flush=True)
            break
        chamadas += 1
        res = classify(p, keys, args.retries)
        (args.out / (p.stem + ".json")).write_text(json.dumps(
            {"arquivo": p.name, "origem": str(p), **res}, ensure_ascii=False, indent=1))
        cont[res["classe"]] = cont.get(res["classe"], 0) + 1
        print(f"{p.name}\t{res['classe']}\t{res['confianca']:.2f}", flush=True)
        time.sleep(args.sleep)
    print("RESUMO", json.dumps(cont, ensure_ascii=False), "total", len(pend))
    return 0


if __name__ == "__main__":
    sys.exit(main())