#!/usr/bin/env python3
"""API local do hub PNAAT: o site le daqui, e o unico caminho de leitura/escrita do registro.

Por que existe: o registro ja grava, o painel ja responde e o relatorio ja apresenta — faltava o
elo que o site consome. Sem ele o site teria de inventar numero na tela, que e o defeito que o
`site/js/data.js` (mocks) representava.

Regras que valem nesta fronteira:

  * **uma origem**: este servidor serve a API (`/api/...`) e os arquivos do site (`/site`), na mesma
    porta. Assim o navegador nao precisa de CORS, e o site nao depende de CDN nem de servidor extra;
  * **leitura pela conexao read-only** (`mode=ro`): GET nao pode mutar o registro por acidente;
  * **escrita por um unico caminho**: POST passa pela API do `Registro`, que e quem valida. A API
    nao faz INSERT na mao;
  * **ausencia declarada**: consulta sem base devolve `null` + motivo, nunca 0 (zero na tela se le
    como "nenhum defeito");
  * **erro e JSON**: rota desconhecida responde JSON, nao a pagina de erro do `http.server`;
  * **fail-closed na evidencia**: sem caminho gravado ou arquivo ausente, 404 — a tela mostra
    ausencia em vez de imagem quebrada silenciosa.

    python3 api.py --db hub.db --porta 8080 [--site ../site]
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import socket
import sqlite3
import time
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from consultas_site import (caminho_da_evidencia, capturas_recentes, item_detalhe, lotes_resumo,
                            total_de_capturas)
from painel import Painel
from registro import EventoInvalido, Registro

#: adaptador de camera/modelo (servico vivo em :8099). A API NAO abre a camera: o dono da camera
#: continua sendo um processo so, e este servidor so fala com ele.
ADAPTADOR = os.environ.get("PNAAT_MODEL_API", "http://127.0.0.1:8099")
VERSAO_API = "hub-api.v1"
ESTADOS_DE_GATILHO = ("aceito", "duplicado", "falso", "invalido")
FONTES_DE_GATILHO = ("e18_d80nk", "vl53l0x", "ambos_correlacionados", "nao_declarada")
TIPOS_ESTATICOS = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                   ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
                   ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
                   ".jpeg": "image/jpeg", ".ico": "image/x-icon"}
#: evidencia so pode ser imagem: a rota serve bytes de arquivo apontado pelo BANCO, e o banco e dado
TIPOS_DE_IMAGEM = (".jpg", ".jpeg", ".png")


def _evidencia_valida(caminho: str | None, raiz: Path) -> Path | None:
    """Devolve o arquivo quando ele e imagem E esta DENTRO da raiz de evidencias declarada.

    Por que a trava existe (achado da revisao de ponta a ponta): o caminho vem de
    `inspecao_vista.caminho_evidencia`, que e dado do banco. Sem fronteira, uma linha apontando para
    `/etc/passwd` fazia a API servir o arquivo — a sonda devolveu HTTP 200 com 2435 bytes dele. Com
    a raiz declarada, o que esta fora nao e lido; o que nao e imagem nao e servido; e o que nao
    existe nao vira URL (imagem quebrada silenciosa na tela).
    """
    if not caminho:
        return None
    try:
        alvo = Path(caminho).resolve()
    except OSError:
        return None
    try:
        alvo.relative_to(raiz)
    except ValueError:
        return None
    if not alvo.is_file() or alvo.suffix.lower() not in TIPOS_DE_IMAGEM:
        return None
    return alvo


class ErroDeApi(Exception):
    """Erro com codigo HTTP e motivo — nunca 500 generico para entrada do usuario."""

    def __init__(self, codigo: int, erro: str, detalhe: str = "") -> None:
        super().__init__(detalhe or erro)
        self.codigo = codigo
        self.erro = erro
        self.detalhe = detalhe


# ------------------------------------------------------------------ sondas

def _sonda_camera(url: str | None = None, timeout: float = 0.35) -> dict:
    """Diz se a PORTA do adaptador responde. Nao prova inferencia: isso e o `/analisar`.

    Separar liveness (TCP) de funcao (inferencia) evita o classico "servico active = saudavel": aqui
    o campo se chama `porta_aberta` e o que ele afirma e exatamente isso.
    """
    alvo = url or ADAPTADOR
    pedaco = urlparse(alvo)
    host = pedaco.hostname or "127.0.0.1"
    porta = pedaco.port or 80
    inicio = time.monotonic()
    try:
        with socket.create_connection((host, porta), timeout=timeout):
            return {"adaptador": alvo, "porta_aberta": True,
                    "latencia_ms": round((time.monotonic() - inicio) * 1000, 1),
                    "verificado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    except OSError as exc:
        return {"adaptador": alvo, "porta_aberta": False, "latencia_ms": None,
                "motivo": f"{type(exc).__name__}: {str(exc)[:120]}",
                "verificado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z")}


def _le_arquivo(caminho: str) -> str | None:
    try:
        return Path(caminho).read_text().strip()
    except OSError:
        return None


def _saude_local(raiz: Path) -> dict:
    """Hardware da Pi. Campo sem fonte fica `None` COM motivo: nao se inventa leitura."""
    faltando: list[str] = []
    cpu = memoria = temperatura = armazenamento = None
    carga = _le_arquivo("/proc/loadavg")
    if carga:
        cpu = float(carga.split()[0])
    else:
        faltando.append("carga")
    mem = _le_arquivo("/proc/meminfo")
    if mem:
        valores = {l.split(":")[0]: int(l.split()[1]) for l in mem.splitlines() if ":" in l}
        total, livre = valores.get("MemTotal"), valores.get("MemAvailable")
        if total and livre:
            memoria = {"usada_mb": round((total - livre) / 1024), "total_mb": round(total / 1024)}
    else:
        faltando.append("memoria")
    termico = _le_arquivo("/sys/class/thermal/thermal_zone0/temp")
    if termico:
        temperatura = round(int(termico) / 1000.0, 1)
    else:
        faltando.append("temperatura")
    try:
        uso = os.statvfs(raiz)
        armazenamento = {"livre_mb": round(uso.f_bavail * uso.f_frsize / 2**20),
                         "total_mb": round(uso.f_blocks * uso.f_frsize / 2**20)}
    except OSError:
        faltando.append("armazenamento")
    return {"cpu_carga_1min": cpu, "memoria": memoria, "temperatura_c": temperatura,
            "armazenamento": armazenamento, "sem_leitura": faltando}


def _ultimo_heartbeat(painel: Painel) -> dict | None:
    r = painel.conexao.execute(
        "SELECT ponto_id, timestamp, status, fila_pendente, latencia_envio_ms FROM heartbeat_no"
        " ORDER BY timestamp DESC LIMIT 1").fetchone()
    if r is None:
        return None
    return {"ponto_id": r["ponto_id"], "timestamp": r["timestamp"], "status": r["status"],
            "fila_pendente": r["fila_pendente"], "latencia_envio_ms": r["latencia_envio_ms"]}


# ------------------------------------------------------------------ serializacao

def _serial(obj):
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"nao sei serializar {type(obj).__name__}")


def _dentro_de(alvo: Path, raiz: Path) -> bool:
    try:
        alvo.relative_to(raiz)
        return True
    except ValueError:
        return False


def _url_evidencia(item_id: str, vista: str, arquivo: Path | None) -> str | None:
    """URL da evidencia SO quando ha arquivo VALIDO: URL sem arquivo produz imagem quebrada."""
    return f"/api/evidencia?item={item_id}&vista={vista}" if arquivo else None


def _captura_para_site(c, raiz: Path) -> dict:
    """Contrato que o `site/js/api.js` consome.

    `status_item` e `status_vista` sao coisas diferentes e por isso tem nomes diferentes: o item diz
    se a peca passou (o que a tela mostra como OK/Defeito/Inconclusivo), a vista diz o que aquela
    linha decidiu no seu dominio. Chamar as duas de `status` fazia a linha `corpo/ok` de um item
    `defeito` passar por defeito — exatamente o rotulo que mente.

    `tem_evidencia` e `evidencia_url` saem da checagem do ARQUIVO, nao do campo do banco: a revisao
    mostrou uma linha com caminho gravado e arquivo ausente sendo anunciada como evidencia e
    entregando 404 no navegador.
    """
    arquivo = _evidencia_valida(c.caminho_evidencia, raiz)
    return {"id": c.id, "item_id": c.item_id, "vista": c.vista, "dominio": c.dominio,
            "papel": c.papel, "status_item": c.status_final, "status_vista": c.status_vista,
            "codigo_defeito": c.codigo_defeito, "confianca": c.confianca,
            "latencia_ms": c.latencia_ms, "lote": c.lote_id,
            "qualidade_registro": c.qualidade_registro, "motivo_inconclusivo": c.motivo_inconclusivo,
            "timestamp_trigger": c.timestamp_trigger, "timestamp_captura": c.timestamp_captura,
            "discordancia_lateral": bool(c.discordancia_lateral),
            "evidencia_url": _url_evidencia(c.item_id, c.vista, arquivo),
            "tem_evidencia": arquivo is not None}


# ------------------------------------------------------------------ rotas de leitura

def _rota_health(ctx: dict) -> dict:
    painel = Painel.abrir(ctx["db"])
    try:
        itens = int(painel.conexao.execute("SELECT COUNT(*) FROM item").fetchone()[0])
        ultimo = _ultimo_heartbeat(painel)
    finally:
        painel._cx.close()
    banco = {"caminho": str(ctx["db"]), "existe": ctx["db"].exists(),
             "bytes": ctx["db"].stat().st_size if ctx["db"].exists() else 0, "itens": itens}
    camera = _sonda_camera()
    servicos = [
        {"nome": "API do hub", "detalhe": f"{VERSAO_API} em :{ctx['porta_real']}", "estado": "ok"},
        {"nome": "Banco do registro", "detalhe": str(ctx["db"]),
         "estado": "ok" if banco["existe"] else "sem banco"},
        {"nome": "Classificador de vista (adaptador)",
         "detalhe": camera["adaptador"],
         "estado": "conectado" if camera["porta_aberta"] else "sem resposta"},
        {"nome": "Raiz de evidencias", "detalhe": str(ctx["evidencias"]),
         "estado": "servindo" if ctx["evidencias"].is_dir() else "ausente"},
        {"nome": "Site", "detalhe": str(ctx["site"]), "estado": "servido nesta origem"},
    ]
    return {"api": VERSAO_API, "banco": banco, "camera": camera, "servicos": servicos,
            "heartbeat": ultimo, "hardware": _saude_local(ctx["site"]),
            "evidencias": str(ctx["evidencias"]),
            "agora": time.strftime("%Y-%m-%dT%H:%M:%S%z")}


def _rota_resumo(ctx: dict) -> dict:
    painel = Painel.abrir(ctx["db"])
    try:
        estados = painel.contagem_por_estado()
        aprovados = painel.aprovados()
        lotes = [asdict(l) for l in lotes_resumo(painel)]
        tendencia = [asdict(t) for t in painel.tendencia_por_hora()]
        defect = [asdict(d) for d in painel.defeitos_frequentes()]
        incons = [asdict(i) for i in painel.inconclusivos_por_lote()]
        dominios = [asdict(d) for d in painel.distribuicao_por_dominio()]
    finally:
        painel._cx.close()
    if not estados:
        return {"sem_base": True, "motivo": "o registro nao tem nenhum item: nao ha medicao por "
                                            "tras de um zero aqui",
                "contagem_por_estado": {}, "aprovados": None, "total": None, "por_lote": [],
                "tendencia": [], "defeitos_frequentes": [], "inconclusivos_por_motivo": [],
                "distribuicao_por_dominio": []}
    return {"sem_base": False, "contagem_por_estado": estados, "aprovados": aprovados,
            "total": sum(estados.values()),
            "nota_aprovacao": "inconclusivo NAO entra em aprovados: so `ok` aprova",
            "por_lote": lotes, "tendencia": tendencia, "defeitos_frequentes": defect,
            "inconclusivos_por_motivo": incons, "distribuicao_por_dominio": dominios}


def _rota_capturas(ctx: dict, consulta: dict) -> dict:
    limite = int((consulta.get("limite") or ["50"])[0])
    vista = (consulta.get("vista") or [None])[0]
    estado = (consulta.get("estado") or [None])[0]
    painel = Painel.abrir(ctx["db"])
    try:
        try:
            linhas = capturas_recentes(painel, limite=limite, vista=vista, estado=estado)
        except ValueError as exc:
            raise ErroDeApi(400, "filtro_invalido", str(exc)) from exc
        base = total_de_capturas(painel)
    finally:
        painel._cx.close()
    capturas = [_captura_para_site(c, ctx["evidencias"]) for c in linhas]
    return {"capturas": capturas, "total": len(capturas), "base": base,
            "filtros": {"limite": limite, "vista": vista, "estado": estado},
            "nota": "lista vazia com base > 0 significa que o filtro nao casou, nao que nada foi "
                    "inspecionado"}


def _rota_item(ctx: dict, item_id: str) -> dict:
    painel = Painel.abrir(ctx["db"])
    try:
        detalhe = item_detalhe(painel, item_id)
    finally:
        painel._cx.close()
    if detalhe is None:
        raise ErroDeApi(404, "item_desconhecido", f"nao ha item {item_id!r} no registro")
    dados = asdict(detalhe)
    dados["vistas"] = [_captura_para_site(v, ctx["evidencias"]) for v in detalhe.vistas]
    dados["correcoes"] = [asdict(c) for c in detalhe.correcoes]
    dados["aprovado"] = detalhe.status_final == "ok"
    return dados


def _rota_lotes(ctx: dict) -> dict:
    painel = Painel.abrir(ctx["db"])
    try:
        lotes = [asdict(l) for l in lotes_resumo(painel)]
    finally:
        painel._cx.close()
    return {"lotes": lotes, "total": len(lotes)}


def _rota_qualidade(ctx: dict) -> dict:
    painel = Painel.abrir(ctx["db"])
    try:
        dados = {
            "latencia_por_vista": [asdict(x) for x in painel.latencia_por_vista()],
            "saturacao_por_vista": [asdict(x) for x in painel.saturacao_por_vista()],
            "gatilho_por_fonte": [asdict(x) for x in painel.gatilho_por_fonte()],
            "perda_de_deteccao": asdict(painel.perda_de_deteccao()),
            "discordancia_lateral": asdict(painel.discordancia_lateral()),
            "inconclusivos_por_lote": [asdict(x) for x in painel.inconclusivos_por_lote()],
            "correcoes_para_auditoria": [asdict(x) for x in painel.correcoes_para_auditoria()],
            "separacoes_nao_confirmadas": [asdict(x) for x in painel.separacoes_nao_confirmadas()],
            "saude_dos_nos": [asdict(x) for x in painel.saude_dos_nos(janela_h=24)],
            "correlacao_ambiental": asdict(painel.correlacao_ambiental()),
        }
    finally:
        painel._cx.close()
    return dados


def _rota_evidencia(ctx: dict, consulta: dict) -> tuple[bytes, str]:
    item = (consulta.get("item") or [None])[0]
    vista = (consulta.get("vista") or [None])[0]
    if not item or not vista:
        raise ErroDeApi(400, "parametros_faltando", "informe item e vista")
    painel = Painel.abrir(ctx["db"])
    try:
        caminho = caminho_da_evidencia(painel, item, vista)
    finally:
        painel._cx.close()
    if not caminho:
        raise ErroDeApi(404, "sem_evidencia_registrada",
                        f"{item}/{vista} nao tem caminho de evidencia no registro")
    raiz: Path = ctx["evidencias"]
    try:
        alvo = Path(caminho).resolve()
    except OSError:
        alvo = None
    if alvo is None or not _dentro_de(alvo, raiz):
        raise ErroDeApi(403, "evidencia_fora_da_raiz",
                        f"o registro aponta para fora da raiz de evidencias ({raiz})")
    arquivo = _evidencia_valida(caminho, raiz)
    if arquivo is None:
        raise ErroDeApi(404, "arquivo_de_evidencia_ausente",
                        f"o registro aponta {caminho} e o arquivo nao esta la como imagem")
    return arquivo.read_bytes(), TIPOS_ESTATICOS.get(arquivo.suffix.lower(), "application/octet-stream")


# ------------------------------------------------------------------ rota de escrita

def _rota_gatilho(ctx: dict, corpo: dict) -> dict:
    """RF-01.1: grava UM evento de gatilho pelo caminho unico (a API do Registro)."""
    estado = corpo.get("estado")
    if estado not in ESTADOS_DE_GATILHO:
        raise ErroDeApi(400, "estado_fora_do_vocabulario",
                        f"estado precisa estar em {list(ESTADOS_DE_GATILHO)}; recebido {estado!r}")
    fonte = corpo.get("fonte", "nao_declarada")
    if fonte not in FONTES_DE_GATILHO:
        raise ErroDeApi(400, "fonte_fora_do_vocabulario",
                        f"fonte precisa estar em {list(FONTES_DE_GATILHO)}; recebido {fonte!r}")
    timestamp = corpo.get("timestamp")
    if not timestamp:
        raise ErroDeApi(400, "timestamp_ausente", "evento de gatilho sem instante nao e rastreavel")
    registro = Registro.abrir(ctx["db"])
    try:
        try:
            gatilho_id = registro.registrar_gatilho(
                timestamp, estado, fonte=fonte, ponto_id=corpo.get("ponto_id"),
                item_id=corpo.get("item_id"), motivo=corpo.get("motivo"),
                debounce_ms=corpo.get("debounce_ms"))
        except EventoInvalido as exc:
            raise ErroDeApi(400, "gatilho_recusado_pelo_registro", str(exc)) from exc
    finally:
        registro.fechar()
    return {"gatilho_id": gatilho_id, "estado": estado, "fonte": fonte}


# ------------------------------------------------------------------ servidor

def criar_servidor(db: Path | str, site: Path | str, porta: int = 8080,
                   evidencias: Path | str | None = None) -> ThreadingHTTPServer:
    """Servidor que serve a API e o site na MESMA origem (sem CORS, sem CDN, sem build).

    `evidencias` e a fronteira de leitura de arquivo: sem ela declarada, vale o diretorio do banco.
    Nada fora dessa raiz e servido, mesmo que o banco aponte para la.
    """
    db = Path(db).resolve()
    site = Path(site)
    if not site.is_dir():
        raise FileNotFoundError(f"diretorio do site nao existe: {site}")
    raiz_evidencias = Path(evidencias).resolve() if evidencias else db.parent
    raiz_evidencias.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        server_version = VERSAO_API
        protocol_version = "HTTP/1.1"

        def log_message(self, formato, *args):        # ruido do http.server fora do jeito padrao
            pass

        # -------------------------------------------------- apoio

        def _contexto(self) -> dict:
            return {"db": db, "site": site, "porta_real": self.server.server_address[1],
                    "evidencias": raiz_evidencias}

        def _responde(self, codigo: int, corpo: bytes, tipo: str) -> None:
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(corpo)

        def _json(self, codigo: int, dados, ok: bool = True, erro: str = "", detalhe: str = "") -> None:
            corpo = {"ok": ok, "dados": dados} if ok else {"ok": False, "erro": erro, "detalhe": detalhe}
            self._responde(codigo, json.dumps(corpo, ensure_ascii=False,
                                              default=_serial).encode("utf-8"),
                           "application/json; charset=utf-8")

        def _estatico(self, caminho_url: str) -> None:
            relativo = caminho_url.lstrip("/") or "index.html"
            alvo = (site / relativo).resolve()
            try:
                alvo.relative_to(site.resolve())            # travessia de diretorio barrada aqui
            except ValueError:
                raise ErroDeApi(404, "caminho_fora_do_site", relativo)
            if alvo.is_dir():
                alvo = alvo / "index.html"
            if not alvo.is_file():
                raise ErroDeApi(404, "arquivo_do_site_ausente", relativo)
            tipo = TIPOS_ESTATICOS.get(alvo.suffix.lower(),
                                       mimetypes.guess_type(str(alvo))[0] or "application/octet-stream")
            self._responde(200, alvo.read_bytes(), tipo)

        # -------------------------------------------------- verbos

        def do_GET(self) -> None:
            pedaco = urlparse(self.path)
            rota, consulta = pedaco.path, parse_qs(pedaco.query)
            ctx = self._contexto()
            try:
                if rota.startswith("/api/"):
                    if rota == "/api/health":
                        self._json(200, _rota_health(ctx))
                    elif rota == "/api/resumo":
                        self._json(200, _rota_resumo(ctx))
                    elif rota == "/api/capturas":
                        self._json(200, _rota_capturas(ctx, consulta))
                    elif rota.startswith("/api/item/"):
                        self._json(200, _rota_item(ctx, rota[len("/api/item/"):]))
                    elif rota == "/api/lotes":
                        self._json(200, _rota_lotes(ctx))
                    elif rota == "/api/qualidade":
                        self._json(200, _rota_qualidade(ctx))
                    elif rota == "/api/evidencia":
                        dados, tipo = _rota_evidencia(ctx, consulta)
                        self._responde(200, dados, tipo)
                    else:
                        raise ErroDeApi(404, "rota_desconhecida", rota)
                else:
                    self._estatico(rota)
            except ErroDeApi as exc:
                self._json(exc.codigo, None, ok=False, erro=exc.erro, detalhe=exc.detalhe)
            except sqlite3.Error as exc:
                self._json(503, None, ok=False, erro="banco_indisponivel",
                           detalhe=f"{type(exc).__name__}: {str(exc)[:160]}")
            except Exception as exc:                                     # noqa: BLE001
                self._json(500, None, ok=False, erro="falha_interna",
                           detalhe=f"{type(exc).__name__}: {str(exc)[:160]}")

        def do_POST(self) -> None:
            rota = urlparse(self.path).path
            ctx = self._contexto()
            try:
                if rota != "/api/gatilho":
                    raise ErroDeApi(404, "rota_desconhecida", rota)
                tamanho = int(self.headers.get("Content-Length") or 0)
                if tamanho > 65536:
                    raise ErroDeApi(413, "corpo_grande_demais", str(tamanho))
                bruto = self.rfile.read(tamanho) if tamanho else b"{}"
                try:
                    corpo = json.loads(bruto.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ErroDeApi(400, "json_invalido", str(exc)) from exc
                if not isinstance(corpo, dict):
                    raise ErroDeApi(400, "json_precisa_ser_objeto", type(corpo).__name__)
                self._json(200, _rota_gatilho(ctx, corpo))
            except ErroDeApi as exc:
                self._json(exc.codigo, None, ok=False, erro=exc.erro, detalhe=exc.detalhe)
            except sqlite3.Error as exc:
                self._json(503, None, ok=False, erro="banco_indisponivel",
                           detalhe=f"{type(exc).__name__}: {str(exc)[:160]}")
            except Exception as exc:                                     # noqa: BLE001
                self._json(500, None, ok=False, erro="falha_interna",
                           detalhe=f"{type(exc).__name__}: {str(exc)[:160]}")

    return ThreadingHTTPServer(("0.0.0.0", porta), Handler)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="API local do hub PNAAT (site + registro)")
    ap.add_argument("--db", default="hub.db", help="banco do registro")
    ap.add_argument("--site", default=str(Path(__file__).resolve().parent.parent / "site"),
                    help="diretorio do site servido na mesma origem")
    ap.add_argument("--evidencias", default="",
                    help="raiz de onde imagens de evidencia podem ser lidas (padrao: pasta do banco)")
    ap.add_argument("--porta", type=int, default=8080)
    a = ap.parse_args(argv)
    servidor = criar_servidor(Path(a.db), Path(a.site), a.porta,
                              Path(a.evidencias) if a.evidencias else None)
    print(f"{VERSAO_API}: http://0.0.0.0:{servidor.server_address[1]}/  (site em {a.site})")
    print(f"banco: {a.db} | adaptador de camera: {ADAPTADOR}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nencerrando")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
