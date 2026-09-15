"""Exporta as anotacoes do Label Studio para o repositorio (o controle).

Contrato:
  - o Label Studio e a superficie de trabalho; o REPOSITORIO e canonico
  - este script puxa, VALIDA e grava; nada entra sem passar na validacao
  - saida estavel (CSV) + recibo com contagens e sha, e o diff contra o ultimo recibo
  - idempotente: rodar de novo nao duplica nem reescreve o que nao mudou

Validacoes (reprovam a linha, com motivo registrado):
  - vista em {lateral, topo, inconclusiva}
  - classe em {normal, tampa_ausente, defeito_tampa, deformidade, inconclusivo}
  - caixas dentro de 0..100% e com area > 0
  - coerencia so com valores conhecidos
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DS = pathlib.Path(__file__).resolve().parents[2] / "dataset"
T = DS / "TRABALHO"
SAIDA = T / "anotacoes-ls.csv"
RECIBOS = T / "_exportacoes"
VISTAS = {"lateral", "topo", "inconclusiva"}
CLASSES = {"normal", "tampa_ausente", "defeito_tampa", "deformidade", "inconclusivo"}
COERENCIAS = {"concorda_com_a_fonte", "conflita_com_quase_duplicata", "rotulo_da_fonte_errado",
              "excluir_do_treino", "imagem_ruim"}
# projetos que contam: 3 = fila de trabalho | 4 = corpus (revisao das caixas das fontes)
PROJETOS_FIXOS = (3, 11, 13, 14, 19)   # fallback se o banco não responder
EXCLUIR = {4}                          # 4 = corpus (revisão das caixas das fontes), não é fila


def projetos_com_anotacao() -> tuple:
    """Descobre no banco os projetos que TÊM anotação.

    Lista fixa já falhou uma vez (projeto 22, 139 anotações, ficou de fora e o export saiu
    calado com dado velho). A fonte é o banco do Label Studio, somente leitura.
    """
    import sqlite3
    db = "/srv/label-studio/data/label_studio.sqlite3"
    try:
        con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
        ids = sorted(r[0] for r in con.execute(
            'select distinct t.project_id from task_completion tc '
            'join task t on t.id = tc.task_id where t.project_id is not null'))
        con.close()
        ids = [i for i in ids if i not in EXCLUIR]
        if ids:
            return tuple(ids)
        print('[export] banco sem projetos com anotação; usando fallback')
    except Exception as exc:  # noqa: BLE001
        print(f'[export] falha lendo o banco ({exc}); usando fallback fixo')
    return PROJETOS_FIXOS


PROJETOS = projetos_com_anotacao()

creds = dict(l.split("=", 1) for l in open("/srv/label-studio/credenciais.env").read().splitlines() if "=" in l)
TOKEN = creds["LABEL_STUDIO_USER_TOKEN"].strip()

# metadados do manifesto, para o export carregar dominio e bloco de origem
MANIFESTO = {}
with (DS / "MANIFEST.csv").open(newline="", encoding="utf-8") as _f:
    for _r in csv.DictReader(_f):
        _a = (_r.get("arquivo") or "")
        if _a.startswith("dataset/"):
            _a = _a[len("dataset/"):]
        MANIFESTO[_a] = {"bloco": _r.get("bloco") or "", "classe_fonte": _r.get("classe") or "",
                         "sessao": _r.get("sessao") or "", "sha256": _r.get("sha256") or ""}


def dominio_de(classe: str, caixas: list) -> str:
    """tampa para classes de tampa; corpo para deformidade ou caixa de corpo; 'indefinido' se nao der."""
    if classe in ("tampa_ausente", "defeito_tampa"):
        return "tampa"
    if classe == "deformidade":
        return "corpo"
    rotulos = {(c.get("rotulo") or "") for c in caixas}
    tem_corpo = bool(rotulos & {"corpo_deformidade", "corpo_regiao"})
    tem_tampa = "tampa" in rotulos
    if tem_corpo and tem_tampa:
        return "ambos"          # uma vista pode emitir evidencia dos dois dominios
    if tem_corpo:
        return "corpo"
    if tem_tampa:
        return "tampa"
    return "indefinido"


def baixa_export(projeto: int = 3):
    url = f"http://localhost:8091/api/projects/{projeto}/export?exportType=JSON"
    r = urllib.request.Request(url, headers={"Authorization": f"Token {TOKEN}"})
    with urllib.request.urlopen(r, timeout=300) as resp:
        return json.loads(resp.read().decode())


def rel_do_task(task) -> str:
    img = (task.get("data") or {}).get("image", "")
    # /data/local-files/?d=dataset/<rel>
    if "?d=" in img:
        img = img.split("?d=", 1)[1]
    return img.replace("dataset/", "", 1) if img.startswith("dataset/") else img


def extrai(task):
    """Devolve a linha canonica da primeira anotacao (a mais recente) do task."""
    anots = task.get("annotations") or []
    if not anots:
        return None
    a = sorted(anots, key=lambda x: x.get("updated_at") or x.get("created_at") or "")[-1]
    vista = classe = None
    estado_tampa = estado_corpo = None
    coer = []
    caixas = []
    obs = ""
    for r in a.get("result") or []:
        t = r.get("type")
        v = r.get("value") or {}
        if t == "choices":
            nome = r.get("from_name")
            vals = v.get("choices") or []
            if nome == "vista":
                vista = vals[0] if vals else None
            elif nome == "classe":
                classe = vals[0] if vals else None
            elif nome == "coerencia":
                coer = list(vals)
            elif nome == "estado_tampa":
                estado_tampa = vals[0] if vals else None
            elif nome == "estado_corpo":
                estado_corpo = vals[0] if vals else None
        elif t == "rectanglelabels":
            caixas.append({
                "rotulo": (v.get("rectanglelabels") or [None])[0],
                "x": v.get("x"), "y": v.get("y"), "width": v.get("width"), "height": v.get("height"),
            })
        elif t == "textarea":
            obs = (v.get("text") or [""])[0] if isinstance(v.get("text"), list) else (v.get("text") or "")
    distintos = set()
    for _a in anots:
        _cb = _a.get("completed_by")
        distintos.add(_cb.get("email", "") if isinstance(_cb, dict) else str(_cb))
    quem = ""
    cb = a.get("completed_by")
    if isinstance(cb, dict):
        quem = cb.get("email", "")
    elif cb is not None:
        quem = str(cb)
    rel = rel_do_task(task)
    meta = MANIFESTO.get(rel, {})
    return {
        "task_id": task.get("id"),
        "projeto": task.get("_projeto", ""),
        "imagem": rel,
        "dominio": dominio_de(classe or "", caixas),
        "bloco": meta.get("bloco", ""),
        "classe_fonte": meta.get("classe_fonte", ""),
        "sessao": meta.get("sessao", ""),
        "vista": vista or "",
        "classe": classe or "",
        "estado_tampa": estado_tampa or "",
        "estado_corpo": estado_corpo or "",
        "coerencia": ";".join(sorted(coer)),
        "caixas": json.dumps(caixas, ensure_ascii=False) if caixas else "",
        "anotador": quem,
        "quando": (a.get("updated_at") or a.get("created_at") or "")[:19],
        "observacao": obs[:200],
        "anotacoes_no_task": len(anots),
        "anotadores_distintos": ";".join(sorted(x for x in distintos if x)),
    }


def valida(linha):
    motivos = []
    if linha["vista"] not in VISTAS:
        motivos.append(f"vista invalida: {linha['vista']!r}")
    if linha["classe"] not in CLASSES:
        motivos.append(f"classe invalida: {linha['classe']!r}")
    for c in linha["coerencia"].split(";"):
        if c and c not in COERENCIAS:
            motivos.append(f"coerencia desconhecida: {c!r}")
    try:
        caixas = json.loads(linha["caixas"]) if linha["caixas"] else []
    except Exception:
        caixas = []
        motivos.append("caixas ilegiveis")
    if linha["classe"] in ("normal", "tampa_ausente", "defeito_tampa", "deformidade") and not caixas:
        motivos.append("classe de defeito/objeto sem nenhuma caixa")
    for c in caixas:
        for k in ("x", "y", "width", "height"):
            v = c.get(k)
            if v is None or not (0 <= float(v) <= 100):
                motivos.append(f"caixa com {k} fora de 0..100 ({v})")
                break
        if (c.get("width") or 0) <= 0 or (c.get("height") or 0) <= 0:
            motivos.append("caixa com area zero")
    return motivos


def main():
    print("== exportando do Label Studio ==")
    tarefas = []
    for pid in PROJETOS:
        try:
            lote = baixa_export(pid)
        except urllib.error.HTTPError as e:
            print(f"   projeto {pid} falhou:", e.code, e.read().decode()[:160])
            continue
        if isinstance(lote, dict):
            lote = lote.get("tasks", [])
        for t in lote:
            t["_projeto"] = pid
        print(f"   projeto {pid}: {len(lote)} tasks exportadas")
        tarefas += lote
    com_anot = [t for t in tarefas if t.get("annotations")]
    print(f"   tasks exportadas: {len(tarefas)} | com anotacao: {len(com_anot)}")

    linhas, rejeitadas = [], []
    for t in tarefas:
        l = extrai(t)
        if not l:
            continue
        motivos = valida(l)
        l["valido"] = "nao" if motivos else "sim"
        l["motivo"] = "; ".join(motivos)
        (rejeitadas if motivos else linhas).append(l)
    print(f"   validas: {len(linhas)} | reprovadas: {len(rejeitadas)}")
    for r in rejeitadas[:5]:
        print(f"     ! task {r['task_id']} ({r['imagem'][:40]}): {r['motivo'][:90]}")

    for l in linhas:
        l["divergencia"] = "sim" if (l["classe"] and l["classe_fonte"] and l["classe"] != l["classe_fonte"]) else ""
        l["anotacao_multipla"] = "sim" if int(l.get("anotacoes_no_task") or 0) > 1 else ""
    for l in rejeitadas:
        l.setdefault("divergencia", "")
        l.setdefault("anotacao_multipla", "")
    campos = ["task_id", "projeto", "imagem", "dominio", "bloco", "classe_fonte", "sessao", "vista", "classe",
              "divergencia", "anotacao_multipla", "estado_tampa", "estado_corpo", "coerencia", "caixas", "anotador", "anotadores_distintos", "anotacoes_no_task", "quando",
              "observacao", "valido", "motivo"]
    linhas_ordenadas = sorted(linhas + rejeitadas, key=lambda x: x["task_id"])
    T.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas_ordenadas)
    sha = hashlib.sha256(SAIDA.read_bytes()).hexdigest()[:16]
    if os.geteuid() == 0:
        import grp
        import pwd
        try:
            u = pwd.getpwnam("nerton")
            g = grp.getgrnam("nerton")
            for alvo in (SAIDA, RECIBOS):
                os.chown(alvo, u.pw_uid, g.gr_gid)
        except Exception:
            pass

    RECIBOS.mkdir(exist_ok=True)
    try:                                     # estado do LS no momento do export (trava de frescor)
        import sys as _sys
        _sys.path.insert(0, str(T))
        from fingerprint_ls import fingerprint as _fingerprint
        _fp_ls = _fingerprint()
    except Exception as _exc:                # sem isso o recibo perde a trava, mas o export continua
        print("   aviso: fingerprint do LS indisponivel:", _exc)
        _fp_ls = None
    anterior = sorted(RECIBOS.glob("recibo-*.json"))
    recibo = {
        "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "projetos": list(PROJETOS),
        "tasks_exportadas": len(tarefas),
        "com_anotacao": len(com_anot),
        "validas": len(linhas),
        "reprovadas": len(rejeitadas),
        "por_vista": {v: sum(1 for l in linhas if l["vista"] == v) for v in sorted(VISTAS)},
        "por_classe": {c: sum(1 for l in linhas if l["classe"] == c) for c in sorted(CLASSES)},
        "por_dominio": {d: sum(1 for l in linhas if l["dominio"] == d)
                        for d in sorted({l["dominio"] for l in linhas})},
        "arquivo": SAIDA.name,
        "sha256_16": sha,
        "fingerprint_ls": _fp_ls,
    }
    if anterior:
        try:
            ant = json.loads(anterior[-1].read_text(encoding="utf-8"))
            recibo["anterior"] = {"quando": ant.get("quando"), "validas": ant.get("validas"),
                                  "sha256_16": ant.get("sha256_16")}
            recibo["delta_validas"] = len(linhas) - int(ant.get("validas") or 0)
        except Exception:
            pass
    (RECIBOS / f"recibo-{datetime.now().strftime('%Y%m%dT%H%M%S')}.json").write_text(
        json.dumps(recibo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n   gravado: {SAIDA.relative_to(DS.parent)} (sha {sha})")
    print("   por vista:", recibo["por_vista"])
    print("   por classe:", recibo["por_classe"])
    if "delta_validas" in recibo:
        print(f"   delta de validas desde o ultimo recibo: {recibo['delta_validas']:+d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
