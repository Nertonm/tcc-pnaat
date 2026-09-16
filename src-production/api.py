#!/usr/bin/env python3
"""API local do hub PNAAT: o site le daqui, e o unico caminho de leitura/escrita do registro.

Por que existe: o registro ja grava, o painel ja responde e o relatorio ja apresenta; faltava o
elo que o site consome. Sem ele o site teria de inventar numero na tela, que e o defeito que o
`site/js/data.js` (mocks) representava.

Regras que valem nesta fronteira:

  * **uma origem**: este servidor serve a API (`/api/...`) e os arquivos do site (`/site`), na mesma
    porta. Assim o navegador nao precisa de CORS nem de servidor extra. O front, porem, CARREGA
    Tailwind e Lucide de CDN externo (site/index.html); a promessa de "sem CDN" vale para a API,
    nao para a pagina;
  * **leitura pela conexao read-only** (`mode=ro`): GET nao pode mutar o registro por acidente;
  * **escrita por um unico caminho**: POST passa pela API do `Registro`, que e quem valida. A API
    nao faz INSERT na mao;
  * **ausencia declarada**: consulta sem base devolve `null` + motivo, nunca 0 (zero na tela se le
    como "nenhum defeito");
  * **erro e JSON**: rota desconhecida responde JSON, nao a pagina de erro do `http.server`;
  * **fail-closed na evidencia**: sem caminho gravado ou arquivo ausente, 404; a tela mostra
    ausencia em vez de imagem quebrada silenciosa.

    python3 api.py --db hub.db --porta 8080 [--site site]
"""

from __future__ import annotations

import argparse
import hmac
import json
import mimetypes
import os
import re
import socket
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from consultas_site import (
    caminho_da_evidencia,
    capturas_recentes,
    gatilhos_recentes,
    item_detalhe,
    itens_de_serie,
    lotes_resumo,
    total_de_capturas,
)
from painel import Painel
from registro import EventoInvalido, Registro

#: adaptador de camera/modelo (servico vivo em :8099). A API NAO abre a camera: o dono da camera
#: continua sendo um processo so, e este servidor so fala com ele.
ADAPTADOR = os.environ.get("PNAAT_MODEL_API", "http://127.0.0.1:8093")

#: servico da camera do rig (dono da camera) e ponte serial do gatilho
RIG = os.environ.get("PNAAT_RIG", "http://127.0.0.1:8090").rstrip("/")
PONTE = os.environ.get("PNAAT_PONTE", "http://127.0.0.1:8094").rstrip("/")
DETECTOR = os.environ.get("PNAAT_DETECTOR", "http://127.0.0.1:8093").rstrip("/")

#: teto do listado do site: acima disso o LIMIT deixa de ser controle de custo
LIMITE_MAXIMO = 500

#: teto do delay de captura aceito pelo rig (mesmo do servico da camera)
DELAY_MAXIMO_MS = 30000

#: nome de arquivo aceito na rota de serie: o rig produz um JPEG por camera + o manifest.
#: Padrao (nao lista fixa) porque o nome da camera e dado do RIG: lista fixa amarrava o hub a
#: instalacao e ainda repetia nome de host dentro do repositorio.
#: cameras de captura do rig (o atraso e configurado por camera)
CAMERAS_DE_CAPTURA = ("csi", "usb", "espcam")

#: pasta das series do rig (mesma maquina do hub). Configuravel: o caminho e dado da instalacao.
SERIES_DIR = Path(
    os.environ.get("PNAAT_SERIES_DIR")
    or (Path.home() / "pnaat-dataset" / "series-3-cameras")
)

#: entrega do modelo do detector (pasta imutavel do produtor: peso, meta e contrato de runtime)
#: pasta dos pesos do detector (mesma maquina do rig). Configuravel: o caminho e dado da instalacao.
MODELOS_DIR = Path(
    os.environ.get("PNAAT_MODELOS_DIR") or (Path.home() / "pnaat-v0-yolo" / "models")
)

#: entrega do modelo do detector (pasta imutavel do produtor: peso, meta e contrato de runtime)
ENTREGA_MODELOS = Path(
    os.environ.get("PNAAT_ENTREGA_MODELOS")
    or (Path.home() / "pnaat-v0-yolo" / "ENTREGA-v7a")
)

ARQUIVO_DE_SERIE = re.compile(
    r"(?:manifest\.json|[A-Za-z0-9][A-Za-z0-9._-]{0,63}\.jpg)"
)

#: teto do corpo de escrita (o gatilho manda um JSON pequeno)
LIMITE_CORPO = 65536
VERSAO_API = "hub-api.v1"
ESTADOS_DE_GATILHO = ("aceito", "duplicado", "falso", "invalido")
FONTES_DE_GATILHO = ("e18_d80nk", "vl53l0x", "ambos_correlacionados", "nao_declarada")
TIPOS_ESTATICOS = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
}
#: evidencia so pode ser imagem: a rota serve bytes de arquivo apontado pelo BANCO, e o banco e dado
TIPOS_DE_IMAGEM = (".jpg", ".jpeg", ".png")


def _evidencia_valida(caminho: str | None, raiz: Path) -> Path | None:
    """Devolve o arquivo quando ele e imagem E esta DENTRO da raiz de evidencias declarada.

    Por que a trava existe (achado da revisao de ponta a ponta): o caminho vem de
    `inspecao_vista.caminho_evidencia`, que e dado do banco. Sem fronteira, uma linha apontando para
    `/etc/passwd` fazia a API servir o arquivo; a sonda devolveu HTTP 200 com 2435 bytes dele. Com
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
    """Erro com codigo HTTP e motivo; nunca 500 generico para entrada do usuario."""

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
            return {
                "adaptador": alvo,
                "porta_aberta": True,
                "latencia_ms": round((time.monotonic() - inicio) * 1000, 1),
                "verificado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
    except OSError as exc:
        return {
            "adaptador": alvo,
            "porta_aberta": False,
            "latencia_ms": None,
            "motivo": f"{type(exc).__name__}: {str(exc)[:120]}",
            "verificado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }


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
        valores = {
            l.split(":")[0]: int(l.split()[1]) for l in mem.splitlines() if ":" in l
        }
        total, livre = valores.get("MemTotal"), valores.get("MemAvailable")
        if total and livre:
            memoria = {
                "usada_mb": round((total - livre) / 1024),
                "total_mb": round(total / 1024),
            }
    else:
        faltando.append("memoria")
    termico = _le_arquivo("/sys/class/thermal/thermal_zone0/temp")
    if termico:
        temperatura = round(int(termico) / 1000.0, 1)
    else:
        faltando.append("temperatura")
    try:
        uso = os.statvfs(raiz)
        armazenamento = {
            "livre_mb": round(uso.f_bavail * uso.f_frsize / 2**20),
            "total_mb": round(uso.f_blocks * uso.f_frsize / 2**20),
        }
    except OSError:
        faltando.append("armazenamento")
    return {
        "cpu_carga_1min": cpu,
        "memoria": memoria,
        "temperatura_c": temperatura,
        "armazenamento": armazenamento,
        "sem_leitura": faltando,
    }


def _ultimo_heartbeat(painel: Painel) -> dict | None:
    r = painel.conexao.execute(
        "SELECT ponto_id, timestamp, status, fila_pendente, latencia_envio_ms FROM heartbeat_no"
        " ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    if r is None:
        return None
    return {
        "ponto_id": r["ponto_id"],
        "timestamp": r["timestamp"],
        "status": r["status"],
        "fila_pendente": r["fila_pendente"],
        "latencia_envio_ms": r["latencia_envio_ms"],
    }


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
    return (
        "/api/evidencia?" + urlencode({"item": item_id, "vista": vista})
        if arquivo
        else None
    )


def _captura_para_site(c, raiz: Path) -> dict:
    """Contrato que o `site/js/api.js` consome.

    `status_item` e `status_vista` sao coisas diferentes e por isso tem nomes diferentes: o item diz
    se a peca passou (o que a tela mostra como OK/Defeito/Inconclusivo), a vista diz o que aquela
    linha decidiu no seu dominio. Chamar as duas de `status` fazia a linha `corpo/ok` de um item
    `defeito` passar por defeito; exatamente o rotulo que mente.

    `tem_evidencia` e `evidencia_url` saem da checagem do ARQUIVO, nao do campo do banco: a revisao
    mostrou uma linha com caminho gravado e arquivo ausente sendo anunciada como evidencia e
    entregando 404 no navegador.
    """
    arquivo = _evidencia_valida(c.caminho_evidencia, raiz)
    return {
        "id": c.id,
        "item_id": c.item_id,
        "vista": c.vista,
        "dominio": c.dominio,
        "papel": c.papel,
        "status_item": c.status_final,
        "status_vista": c.status_vista,
        "codigo_defeito": c.codigo_defeito,
        "confianca": c.confianca,
        "latencia_ms": c.latencia_ms,
        "lote": c.lote_id,
        "qualidade_registro": c.qualidade_registro,
        "motivo_inconclusivo": c.motivo_inconclusivo,
        "timestamp_trigger": c.timestamp_trigger,
        "timestamp_captura": c.timestamp_captura,
        "discordancia_lateral": bool(c.discordancia_lateral),
        "evidencia_url": _url_evidencia(c.item_id, c.vista, arquivo),
        "tem_evidencia": arquivo is not None,
    }


# ------------------------------------------------------------------ rotas de leitura


def _rota_health(ctx: dict) -> dict:
    painel = Painel.abrir(ctx["db"])
    try:
        itens = int(painel.conexao.execute("SELECT COUNT(*) FROM item").fetchone()[0])
        ultimo = _ultimo_heartbeat(painel)
    finally:
        painel._cx.close()
    banco = {
        "caminho": str(ctx["db"]),
        "existe": ctx["db"].exists(),
        "bytes": ctx["db"].stat().st_size if ctx["db"].exists() else 0,
        "itens": itens,
    }
    camera = _sonda_camera()
    servicos = [
        {
            "nome": "API do hub",
            "detalhe": f"{VERSAO_API} em :{ctx['porta_real']}",
            "estado": "ok",
        },
        {
            "nome": "Banco do registro",
            "detalhe": str(ctx["db"]),
            "estado": "ok" if banco["existe"] else "sem banco",
        },
        {
            "nome": "Classificador de vista (adaptador)",
            "detalhe": camera["adaptador"],
            "estado": "conectado" if camera["porta_aberta"] else "sem resposta",
        },
        {
            "nome": "Raiz de evidencias",
            "detalhe": str(ctx["evidencias"]),
            "estado": "servindo" if ctx["evidencias"].is_dir() else "ausente",
        },
        {"nome": "Site", "detalhe": str(ctx["site"]), "estado": "servido nesta origem"},
    ]
    return {
        "api": VERSAO_API,
        "banco": banco,
        "camera": camera,
        "servicos": servicos,
        "heartbeat": ultimo,
        "hardware": _saude_local(ctx["site"]),
        "evidencias": str(ctx["evidencias"]),
        "agora": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


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
        return {
            "sem_base": True,
            "motivo": "o registro nao tem nenhum item: nao ha medicao por "
            "tras de um zero aqui",
            "contagem_por_estado": {},
            "aprovados": None,
            "total": None,
            "por_lote": [],
            "tendencia": [],
            "defeitos_frequentes": [],
            "inconclusivos_por_motivo": [],
            "distribuicao_por_dominio": [],
        }
    return {
        "sem_base": False,
        "contagem_por_estado": estados,
        "aprovados": aprovados,
        "total": sum(estados.values()),
        "nota_aprovacao": "inconclusivo NAO entra em aprovados: so `ok` aprova",
        "por_lote": lotes,
        "tendencia": tendencia,
        "defeitos_frequentes": defect,
        "inconclusivos_por_motivo": incons,
        "distribuicao_por_dominio": dominios,
    }


def _rota_capturas(ctx: dict, consulta: dict) -> dict:
    bruto = (consulta.get("limite") or ["50"])[0]
    try:
        limite = int(bruto)
    except (TypeError, ValueError) as exc:
        raise ErroDeApi(
            400, "filtro_invalido", f"limite tem de ser inteiro, recebido {bruto!r}"
        ) from exc
    if limite < 1:
        raise ErroDeApi(
            400, "filtro_invalido", f"limite tem de ser >= 1, recebido {limite}"
        )
    # teto explicito: sem ele `?limite=1000000000` varre o registro inteiro e o LIMIT deixa de ser
    # controle de custo. O teto vai no payload, senao ninguem entende por que recebeu menos.
    limite = min(limite, LIMITE_MAXIMO)
    vista = (consulta.get("vista") or [None])[0]
    estado = (consulta.get("estado") or [None])[0]
    painel = Painel.abrir(ctx["db"])
    try:
        try:
            linhas = capturas_recentes(
                painel, limite=limite, vista=vista, estado=estado
            )
        except ValueError as exc:
            raise ErroDeApi(400, "filtro_invalido", str(exc)) from exc
        base = total_de_capturas(painel)
    finally:
        painel._cx.close()
    capturas = [_captura_para_site(c, ctx["evidencias"]) for c in linhas]
    return {
        "capturas": capturas,
        "total": len(capturas),
        "base": base,
        "filtros": {
            "limite": limite,
            "limite_maximo": LIMITE_MAXIMO,
            "vista": vista,
            "estado": estado,
        },
        "nota": "lista vazia com base > 0 significa que o filtro nao casou, nao que nada foi "
        "inspecionado",
    }


def _rota_item(ctx: dict, item_id: str) -> dict:
    painel = Painel.abrir(ctx["db"])
    try:
        detalhe = item_detalhe(painel, item_id)
    finally:
        painel._cx.close()
    if detalhe is None:
        raise ErroDeApi(
            404, "item_desconhecido", f"nao ha item {item_id!r} no registro"
        )
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
            "inconclusivos_por_lote": [
                asdict(x) for x in painel.inconclusivos_por_lote()
            ],
            "correcoes_para_auditoria": [
                asdict(x) for x in painel.correcoes_para_auditoria()
            ],
            "separacoes_nao_confirmadas": [
                asdict(x) for x in painel.separacoes_nao_confirmadas()
            ],
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
        raise ErroDeApi(
            404,
            "sem_evidencia_registrada",
            f"{item}/{vista} nao tem caminho de evidencia no registro",
        )
    raiz: Path = ctx["evidencias"]
    try:
        alvo = Path(caminho).resolve()
    except OSError:
        alvo = None
    if alvo is None or not _dentro_de(alvo, raiz):
        raise ErroDeApi(
            403,
            "evidencia_fora_da_raiz",
            f"o registro aponta para fora da raiz de evidencias ({raiz})",
        )
    arquivo = _evidencia_valida(caminho, raiz)
    if arquivo is None:
        raise ErroDeApi(
            404,
            "arquivo_de_evidencia_ausente",
            f"o registro aponta {caminho} e o arquivo nao esta la como imagem",
        )
    return arquivo.read_bytes(), TIPOS_ESTATICOS.get(
        arquivo.suffix.lower(), "application/octet-stream"
    )


# ------------------------------------------------------------------ rota de escrita


def _chamar_servico(
    base: str,
    rota: str,
    *,
    metodo: str = "GET",
    timeout: float = 10.0,
    nome: str = "servico",
) -> dict:
    """Chama o rig/ponte e devolve o JSON dele. Falha vira erro DECLARADO, nunca resposta vazia."""
    url = f"{base}{rota}"
    pedido = urllib.request.Request(url, method=metodo)
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
            bruto = resposta.read()
    except urllib.error.HTTPError as exc:
        detalhe = exc.read(200).decode("utf-8", "replace")
        raise ErroDeApi(
            502, f"{nome}_recusou", f"{url} respondeu {exc.code}: {detalhe}"
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise ErroDeApi(
            503,
            f"{nome}_sem_resposta",
            f"{url} nao respondeu (servico fora do ar): {type(exc).__name__}: {str(exc)[:80]}",
        ) from exc

    try:
        return json.loads(bruto.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ErroDeApi(
            502,
            f"{nome}_resposta_ilegivel",
            f"{url} devolveu algo que nao e JSON: {str(exc)[:120]}",
        ) from exc


def _chamar_rig(rota: str, *, metodo: str = "GET", timeout: float = 10.0) -> dict:
    return _chamar_servico(RIG, rota, metodo=metodo, timeout=timeout, nome="rig")


def _chamar_ponte(
    rota: str = "/status", *, metodo: str = "GET", timeout: float = 8.0
) -> dict:
    # ATENCAO: "/" na ponte devolve a PAGINA HTML; o snapshot JSON (serial, sensor, delay) esta em
    # "/status". Ler "/" fazia o painel do gatilho falhar para sempre com resposta ilegivel.

    return _chamar_servico(
        PONTE, rota, metodo=metodo, timeout=timeout, nome="ponte_gatilho"
    )


def _registrar_execucao_de_bancada(
    ctx: dict, motivo: str, item_id: str | None = None
) -> dict:
    """Grava a execucao de bancada como evento de gatilho.

    A bancada nao pode ser invisivel no registro: sem isto, o teste manual nao aparece na contagem e o
    operador conclui que o gatilho nunca disparou. A fonte fica 'nao_declarada' (o vocabulario do
    esquema nao tem 'manual') e o motivo diz que e execucao de bancada; quem agrega filtra por motivo.
    """
    if item_id is not None and not _ITEM_ID_VALIDO(item_id):
        raise ErroDeApi(400, "item_invalido", f"item_id fora do padrao: {item_id!r}")
    registro = Registro.abrir(ctx["db"])
    try:
        try:
            evento_id = _escrever_com_retentativa(
                registro.registrar_gatilho,
                _agora_iso(),
                "aceito",
                fonte="nao_declarada",
                item_id=item_id,
                motivo=motivo,
            )
        except EventoInvalido as exc:
            raise ErroDeApi(400, "execucao_recusada_pelo_registro", str(exc)) from exc
    finally:
        registro.fechar()
    return {"gatilho_id": evento_id, "motivo": motivo}


def _escrever_com_retentativa(
    acao, *args, tentativas: int = 3, espera_s: float = 0.3, **kwargs
):
    """Executa uma escrita aguardando o lock do registro.

    O registro tem UM escritor por vez (lock do arquivo). Quando o rig esta gravando, a tentativa
    unica devolvia 503 e o evento do gatilho se perdia. Aqui a espera e curta e crescente; se ainda
    assim nao der, o erro sobe e a rota responde 409 declarado.
    """
    for tentativa in range(1, tentativas + 1):
        try:
            return acao(*args, **kwargs)
        except sqlite3.OperationalError as erro:
            if "locked" not in str(erro).lower() or tentativa == tentativas:
                raise
            time.sleep(espera_s * tentativa)


def _rota_gatilho(ctx: dict, corpo: dict) -> dict:

    # validacao SEMANTICA do gatilho, aqui e nao no preambulo do POST: a rota de correcao nao tem
    # instante no corpo, e o preambulo vale para as duas.
    instante = corpo.get("timestamp")
    if not isinstance(instante, str):
        raise ErroDeApi(
            400,
            "timestamp_invalido",
            f"timestamp tem de ser texto ISO com fuso, recebido {type(instante).__name__}",
        )
    try:
        lido = datetime.fromisoformat(instante)
    except ValueError as exc:
        raise ErroDeApi(
            400, "timestamp_invalido", f"timestamp nao e ISO 8601: {instante!r}"
        ) from exc
    if lido.tzinfo is None:
        raise ErroDeApi(
            400,
            "timestamp_sem_fuso",
            f"timestamp sem fuso: {instante!r} (o registro exige fuso)",
        )

    # tipo errado aqui e erro do CLIENTE: nao pode virar 503 de banco indisponivel
    for campo in ("ponto_id", "debounce_ms"):
        valor = corpo.get(campo)
        if valor is not None and not isinstance(valor, int):
            raise ErroDeApi(
                400,
                "campo_com_tipo_errado",
                f"{campo} tem de ser inteiro, recebido {type(valor).__name__}",
            )
    """RF-01.1: grava UM evento de gatilho pelo caminho unico (a API do Registro)."""
    estado = corpo.get("estado")
    if estado not in ESTADOS_DE_GATILHO:
        raise ErroDeApi(
            400,
            "estado_fora_do_vocabulario",
            f"estado precisa estar em {list(ESTADOS_DE_GATILHO)}; recebido {estado!r}",
        )
    fonte = corpo.get("fonte", "nao_declarada")
    if fonte not in FONTES_DE_GATILHO:
        raise ErroDeApi(
            400,
            "fonte_fora_do_vocabulario",
            f"fonte precisa estar em {list(FONTES_DE_GATILHO)}; recebido {fonte!r}",
        )
    timestamp = corpo.get("timestamp")
    if not timestamp:
        raise ErroDeApi(
            400, "timestamp_ausente", "evento de gatilho sem instante nao e rastreavel"
        )
    registro = Registro.abrir(ctx["db"])
    try:
        try:
            gatilho_id = _escrever_com_retentativa(
                registro.registrar_gatilho,
                timestamp,
                estado,
                fonte=fonte,
                ponto_id=corpo.get("ponto_id"),
                item_id=corpo.get("item_id"),
                motivo=corpo.get("motivo"),
                debounce_ms=corpo.get("debounce_ms"),
            )
        except EventoInvalido as exc:
            raise ErroDeApi(400, "gatilho_recusado_pelo_registro", str(exc)) from exc
    finally:
        registro.fechar()
    return {"gatilho_id": gatilho_id, "estado": estado, "fonte": fonte}


def _agora_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _ITEM_ID_VALIDO(item_id: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", str(item_id or "")))


def _rota_modelo(ctx: dict) -> dict:
    """Contrato do modelo servido + estado vivo do detector.

    Nao julga o modelo: devolve o que a entrega declara (nome, sha, classes, limiares, metricas e
    limitacoes) e o que o detector responde agora (carregado, qual peso). A divergencia entre o nome
    de classe do contrato e o que o peso emite aparece na tela como fato, nao como detalhe escondido.
    """
    caminho = ENTREGA_MODELOS / "modelo.json"
    contrato, erro_contrato = None, None
    if caminho.is_file():
        try:
            contrato = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            erro_contrato = f"{type(exc).__name__}: {exc}"
    else:
        erro_contrato = f"entrega ausente: {caminho}"

    saude, erro_detector = None, None
    try:
        with urllib.request.urlopen(DETECTOR + "/health", timeout=6) as resposta:
            saude = json.loads(resposta.read().decode())
    except (
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:  # detector fora e estado, nao excecao do painel:
        # mensagem em linguagem clara, com o detalhe tecnico entre parenteses (o painel e para operador)
        causa = (
            "conexao recusada" if "refused" in str(exc).lower() else type(exc).__name__
        )
        erro_detector = f"nao respondeu ({causa})"

    return {
        "contrato": contrato,
        "entrega": str(caminho),
        "erro_contrato": erro_contrato,
        "saude": saude,
        "erro_detector": erro_detector,
        "servido": (saude or {}).get("model_name"),
        "declarado_no_contrato": (contrato or {}).get("arquivo"),
    }


def _deteccao_da_serie(destino: Path, manifesto: dict) -> dict:
    """Fail closed: resultado somente ligado aos bytes desta serie; nunca infere USB/ESP."""
    import hashlib

    caminho = destino / "deteccao.json"
    if not caminho.exists():
        return {"estado": "aguardando", "motivo": "aguardando resultado do detector"}
    try:
        d = json.loads(caminho.read_text(encoding="utf-8"))

        def exige(condicao, motivo):
            if not condicao:
                raise ValueError(motivo)

        def sha(p):
            exige(p.is_file() and not p.is_symlink(), "arquivo ausente ou link")
            return hashlib.sha256(p.read_bytes()).hexdigest()

        exige(isinstance(d, dict) and isinstance(manifesto, dict), "documento invalido")
        exige(
            d.get("serie") == destino.name == manifesto.get("serie"),
            "identidade da serie diverge",
        )
        for campo in ("trigger_n", "origem_trigger"):
            exige(
                d.get(campo) is not None and d.get(campo) == manifesto.get(campo),
                campo + " diverge",
            )
        exige(
            d.get("manifest_sha256") == sha(destino / "manifest.json"),
            "hash do manifesto diverge",
        )
        fontes = {f["nome"] for f in manifesto["fontes"]}
        hashes = d.get("fontes_sha256")
        exige(
            isinstance(hashes, dict) and set(hashes) == fontes and bool(fontes),
            "fontes divergem",
        )
        for nome, digest in hashes.items():
            exige(
                isinstance(nome, str)
                and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\.jpg", nome),
                "nome de fonte invalido",
            )
            exige(digest == sha(destino / nome), "hash da fonte diverge: " + nome)
        jpeg = d.get("jpeg")
        exige(jpeg in fontes and jpeg.endswith("-csi.jpg"), "foto analisada nao e CSI")
        exige(d.get("jpeg_sha256") == hashes[jpeg], "hash JPEG diverge")
        modelo = d.get("modelo", "")
        exige(
            isinstance(modelo, str)
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}\.pt", modelo),
            "modelo invalido",
        )
        exige(
            d.get("modelo_sha256") == sha(MODELOS_DIR / modelo),
            "hash do modelo diverge",
        )
        # Vocabulario canonico do projeto: ok | defeito | inconclusivo (o rig publica assim).
        # Legado (aprovado/reprovado) segue aceito para documentos antigos; a UI mostra o canonico.
        exige(
            isinstance(d.get("veredito"), dict)
            and d["veredito"].get("veredito")
            in ("ok", "defeito", "inconclusivo", "aprovado", "reprovado"),
            "veredito invalido",
        )
        return {
            "estado": "verificado",
            **{
                k: d.get(k)
                for k in (
                    "jpeg",
                    "modelo",
                    "modelo_sha256",
                    "jpeg_sha256",
                    "manifest_sha256",
                    "detectado_em",
                    "veredito",
                    "inference_ms",
                )
            },
        }
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return {"estado": "erro", "motivo": "resultado nao validado: " + str(exc)}


def _series_locais(limite: int = 40) -> list[dict]:
    """Lista as series que EXISTEM na pasta, com o que cada uma tem; parciais incluidas.

    O rig so publica serie completa; quem falhou no meio vira pasta orfa e desaparece da tela. Aqui a
    leitura e do sistema de arquivos: a foto que foi tirada continua visivel, com a vista que falta
    declarada.
    """
    if not SERIES_DIR.is_dir():
        raise ErroDeApi(
            503,
            "pasta_de_series_ausente",
            f"a pasta de series do rig nao existe nesta instalacao: {SERIES_DIR}",
        )

    series: list[dict] = []
    for destino in sorted(
        (d for d in SERIES_DIR.iterdir() if d.is_dir()), reverse=True
    )[:limite]:
        fotos, faltando = [], []
        manifest = destino / "manifest.json"
        declarado = {}
        atrasos_configurados, medido_por_camera, parcial, faltando_no_manifesto = (
            None,
            {},
            None,
            [],
        )
        dados: dict = {}
        if manifest.is_file():
            try:
                dados = json.loads(manifest.read_text(encoding="utf-8"))
                declarado = {
                    f.get("nome"): f.get("camera")
                    for f in (dados.get("fontes") or [])
                    if isinstance(f, dict)
                }
                # configurado x medido: o painel compara os dois em vez de afirmar um so
                atrasos_configurados = dados.get("atraso_por_camera_ms")
                parcial = dados.get("parcial")
                faltando_no_manifesto = dados.get("faltando") or []
                for fonte in dados.get("fontes") or []:
                    if isinstance(fonte, dict) and fonte.get("camera"):
                        # o rig nomeia a camera com o prefixo da instalacao (ex.: <host>-csi): a chave
                        # publicada e o PAPEL (csi/usb/espcam), o mesmo vocabulario da configuracao
                        nome = str(fonte["camera"])
                        papel = next(
                            (
                                c
                                for c in CAMERAS_DE_CAPTURA
                                if nome == c or nome.endswith("-" + c)
                            ),
                            nome,
                        )
                        medido_por_camera[papel] = {
                            "atraso_efetivo_ms": fonte.get("atraso_efetivo_ms"),
                            "atraso_configurado_ms": fonte.get("atraso_configurado_ms"),
                            "pedido_em_epoch": fonte.get("pedido_em_epoch"),
                        }
            except (OSError, json.JSONDecodeError):
                declarado = {}

        for arquivo in sorted(destino.iterdir()):
            if not arquivo.is_file() or not ARQUIVO_DE_SERIE.fullmatch(arquivo.name):
                continue
            if arquivo.suffix == ".json":
                continue
            fotos.append(
                {
                    "arquivo": arquivo.name,
                    "camera": declarado.get(arquivo.name),
                    "bytes": arquivo.stat().st_size,
                    "quando": datetime.fromtimestamp(
                        arquivo.stat().st_mtime, UTC
                    ).isoformat(timespec="seconds"),
                    "url": f"/api/series/{destino.name}/{arquivo.name}",
                }
            )

        with_manifest = manifest.is_file()
        for nome in sorted(declarado):
            if nome and not (destino / nome).is_file():
                faltando.append(declarado[nome] or nome)
        if not fotos:
            faltando = faltando or ["nenhuma foto"]

        series.append(
            {
                "serie": destino.name,
                "completa": bool(
                    with_manifest
                    and len(fotos) == 3
                    and not parcial
                    and not faltando_no_manifesto
                    and not faltando
                ),
                "tem_manifesto": with_manifest,
                "deteccao": _deteccao_da_serie(destino, dados),
                "fotos": fotos,
                "faltantes": faltando,
                "atraso_por_camera_ms": atrasos_configurados,
                "atraso_medido_por_camera": medido_por_camera,
                "trigger_n": (dados.get("trigger_n") if manifest.is_file() else None),
                "origem_trigger": (
                    dados.get("origem_trigger") if manifest.is_file() else None
                ),
                "parcial": parcial,
                "faltando_no_manifesto": faltando_no_manifesto,
                "motivo": (
                    None
                    if with_manifest and faltando == []
                    else (
                        "sem manifesto: captura interrompida"
                        if not with_manifest
                        else f"fotos declaradas e ausentes: {faltando}"
                    )
                ),
            }
        )
    return series


def _rota_series_locais(consulta: dict) -> dict:
    bruto = (consulta.get("limite") or ["40"])[0]
    try:
        limite = int(bruto)
    except (TypeError, ValueError) as exc:
        raise ErroDeApi(
            400, "filtro_invalido", f"limite tem de ser inteiro, recebido {bruto!r}"
        ) from exc
    limite = max(1, min(limite, LIMITE_MAXIMO))
    series = _series_locais(limite)
    return {
        "series": series,
        "total": len(series),
        "pasta": str(SERIES_DIR),
        "completas": sum(1 for s in series if s["completa"]),
        "parciais": sum(1 for s in series if not s["completa"]),
    }


def _rota_serie_local(resto: str) -> tuple[bytes, str]:
    """Serve a foto de uma serie local, com a mesma fronteira das outras rotas de arquivo."""
    partes = [p for p in resto.split("/") if p]
    if len(partes) != 2:
        raise ErroDeApi(400, "caminho_invalido", "use /api/series/<serie>/<arquivo>")
    serie, arquivo = partes
    if not re.fullmatch(
        r"[0-9A-Za-z._-]{1,64}", serie
    ) or not ARQUIVO_DE_SERIE.fullmatch(arquivo):
        raise ErroDeApi(400, "serie_ou_arquivo_invalido", f"{serie!r}/{arquivo!r}")
    raiz = SERIES_DIR.resolve()
    alvo = (raiz / serie / arquivo).resolve()
    if raiz not in alvo.parents or not alvo.is_file():
        raise ErroDeApi(404, "foto_ausente", f"{alvo} nao esta la como arquivo")
    tipo = TIPOS_ESTATICOS.get(alvo.suffix.lower(), "image/jpeg")
    return alvo.read_bytes(), tipo


def _rota_gatilhos(ctx: dict, consulta: dict) -> dict:
    """Historico de eventos de gatilho: e o comportamento do trigger que o site nao mostrava."""
    bruto = (consulta.get("limite") or ["50"])[0]
    try:
        limite = int(bruto)
    except (TypeError, ValueError) as exc:
        raise ErroDeApi(
            400, "filtro_invalido", f"limite tem de ser inteiro, recebido {bruto!r}"
        ) from exc
    limite = max(1, min(limite, LIMITE_MAXIMO))

    painel = Painel.abrir(ctx["db"])
    try:
        eventos = gatilhos_recentes(painel, limite=limite)
    finally:
        painel._cx.close()
    return {"gatilhos": eventos, "total": len(eventos)}


def _rota_rig_serie(resto: str) -> tuple[bytes, str]:
    """Serve a imagem da serie que o rig capturou, validando serie/arquivo antes de buscar.

    A validacao aqui e a fronteira: o hub nao repassa caminho cru para o rig, so aceita serie com
    carimbo numerico e arquivo da lista fechada que o proprio rig produz.
    """
    partes = [p for p in resto.split("/") if p]
    if len(partes) != 2:
        raise ErroDeApi(400, "caminho_invalido", "use /api/rig-serie/<serie>/<arquivo>")
    serie, arquivo = partes
    if not re.fullmatch(r"[0-9-]{6,32}", serie) or not ARQUIVO_DE_SERIE.fullmatch(
        arquivo
    ):
        raise ErroDeApi(400, "serie_ou_arquivo_invalido", f"{serie!r}/{arquivo!r}")

    url = f"{RIG}/series-3-cameras/{serie}/{arquivo}"
    try:
        with urllib.request.urlopen(url, timeout=15.0) as resposta:
            dados = resposta.read()
            tipo = resposta.headers.get("Content-Type") or (
                "application/json" if arquivo.endswith(".json") else "image/jpeg"
            )
    except urllib.error.HTTPError as exc:
        raise ErroDeApi(
            404,
            "arquivo_da_serie_ausente",
            f"o rig respondeu {exc.code} para {serie}/{arquivo}",
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise ErroDeApi(
            503, "rig_sem_resposta", f"{url} nao respondeu: {str(exc)[:120]}"
        ) from exc
    return dados, tipo


def _rota_itens_ingeridos(ctx: dict, consulta: dict) -> dict:
    """Itens cuja evidencia veio de uma serie do rig (caminho com `/series/`), com as fotos serviveis."""
    bruto = (consulta.get("limite") or ["20"])[0]
    try:
        limite = int(bruto)
    except (TypeError, ValueError) as exc:
        raise ErroDeApi(
            400, "filtro_invalido", f"limite tem de ser inteiro, recebido {bruto!r}"
        ) from exc
    limite = max(1, min(limite, LIMITE_MAXIMO))

    painel = Painel.abrir(ctx["db"])
    try:
        itens = itens_de_serie(painel, limite=limite)
    finally:
        painel._cx.close()
    return {"itens": itens, "total": len(itens)}


def _rota_rig_leitura(alvo: str) -> dict:
    """Leituras do rig/ponte que a aba de debug consome (lista fechada, sem caminho livre)."""
    if alvo == "estado":
        # o rig devolve os campos direto; embrulhar num nivel a mais fazia o painel ler vazio
        return _chamar_rig("/estado")
    if alvo == "series":
        # o rig JA devolve {"series": [...]}: embrulhar de novo fazia o site ler um nivel a mais
        return _chamar_rig("/dataset-series")
    if alvo == "historico":
        return {"historico": _chamar_rig("/historico")}
    if alvo == "delay-camera":
        # o atraso por camera e do rig (a ponte guarda so o dela, em RAM); devolver so o mapa
        dados = _chamar_rig("/delay-por-camera")
        return dados.get("delay_por_camera_ms") or dados
    if alvo == "gatilho":
        # a ponte serial e quem sabe do sensor, da serial e do delay; devolve os campos direto
        # (mesma classe de erro que o comentario do /dataset-series acima registra)
        return _chamar_ponte("/status")
    raise ErroDeApi(
        404, "leitura_desconhecida", f"leitura de rig desconhecida: {alvo!r}"
    )


def _delay_na_ponte(ponte: dict) -> tuple[object, object]:
    """Le o delay do snapshot da ponte, onde ele vive ANINHADO em `trigger`.

    A ponte publica `trigger.delay_ms`/`trigger.delay_saved_at`; ler na raiz devolvia None, e a
    confirmacao de volta ficaria falsa para sempre.
    """
    gatilho = ponte.get("trigger") if isinstance(ponte, dict) else None
    if not isinstance(gatilho, dict):
        return None, None
    return gatilho.get("delay_ms"), gatilho.get("delay_saved_at")


def _rota_rig_delay(ctx: dict, corpo: dict) -> dict:
    """Configura o delay de captura, LE DE VOLTA e registra QUEM mudou.

    O delay define a janela de captura: mudar sem autor nem trilha e o mesmo defeito que a correcao do
    operador nao pode ter. Trilha = JSONL append-only ao lado do banco.
    """
    bruto = corpo.get("ms")
    try:
        ms = int(bruto)
    except (TypeError, ValueError) as exc:
        raise ErroDeApi(
            400, "delay_invalido", f"ms tem de ser inteiro, recebido {bruto!r}"
        ) from exc
    if not 0 <= ms <= DELAY_MAXIMO_MS:
        raise ErroDeApi(
            400, "delay_invalido", f"ms fora de [0,{DELAY_MAXIMO_MS}]: {ms}"
        )

    operador = " ".join(str(corpo.get("operador") or "").split())
    if not operador or len(operador) > 64 or any(c < " " for c in operador):
        raise ErroDeApi(
            400,
            "operador_ausente",
            "informe quem muda o delay (1 a 64 caracteres imprimiveis): sem autor nao e trilha",
        )

    camera_pedida = " ".join(str(corpo.get("camera") or "").split()).lower()
    if not camera_pedida:
        raise ErroDeApi(
            400, "camera_ausente", "escolha uma camera ou 'todas' explicitamente"
        )
    if camera_pedida != "todas" and camera_pedida not in CAMERAS_DE_CAPTURA:
        raise ErroDeApi(
            400,
            "camera_desconhecida",
            f"camera {camera_pedida!r} nao existe; validas: {sorted(CAMERAS_DE_CAPTURA)} + ['todas']",
        )
    camera = None if camera_pedida == "todas" else camera_pedida

    # A autoridade do delay por camera e o rig. A ponte so guarda o ramo ESP-CAM em RAM;
    # usa-la como 'anterior' para CSI/USB produzia uma trilha semanticamente falsa.
    estado_antes = _chamar_rig("/delay-por-camera", timeout=15.0)
    por_camera_antes = estado_antes.get("delay_por_camera_ms") or {}
    anterior = (
        dict(por_camera_antes) if camera is None else por_camera_antes.get(camera)
    )
    consulta = f"/configurar-delay?ms={ms}" + (f"&camera={camera}" if camera else "")
    resposta_rig = _chamar_rig(consulta, timeout=15.0)
    ponte = _chamar_ponte("/status")  # ponte e apenas leitura do ramo ESP-CAM
    vigente, salvo_em = _delay_na_ponte(ponte)

    trilha = Path(ctx["db"]).parent / "mudancas-de-delay.jsonl"
    with trilha.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(
                {
                    "quando": _agora_iso(),
                    "operador": operador,
                    "camera": camera_pedida,
                    "anterior_ms": anterior,
                    "novo_ms": ms,
                    "lido_de_volta_ponte_espcam_ms": vigente,
                    "origem": "aba de debug do site",
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    # A confirmacao depende de QUEM guarda o valor. Por camera a autoridade e o rig (ele agenda a
    # captura); o  da ponte e so o ramo dela (ESP-CAM). Comparar a leitura da ponte com um
    # pedido por camera devolvia "confirmado: False" com a mudanca aplicada; confirmacao que mente.
    if camera:
        lido_por_camera = resposta_rig.get("delay_por_camera_ms") or {}
        confirmado = lido_por_camera.get(camera) == ms
        leitura = {"por_camera_ms": lido_por_camera, "ponte_ms": vigente}
    else:
        lido_por_camera = resposta_rig.get("delay_por_camera_ms") or {}
        confirmado = all(lido_por_camera.get(c) == ms for c in CAMERAS_DE_CAPTURA)
        leitura = {"por_camera_ms": lido_por_camera, "ponte_ms": vigente}

    return {
        "pedido_ms": ms,
        "camera": camera_pedida,
        "rig": resposta_rig,
        "operador": operador,
        "anterior_ms": anterior,
        "delay_ramo_ponte_espcam_ms": vigente,
        "delay_salvo_em": salvo_em,
        "leitura_de_volta": leitura,
        "confirmado": confirmado,
        "trilha": str(trilha),
    }


def _rota_rig_teste_trigger(ctx: dict, corpo: dict) -> dict:
    """Execucao de bancada: pede ao rig o trigger de teste nas 3 cameras e registra o evento."""
    resposta = _chamar_rig("/teste-trigger-3-cameras", timeout=15.0)

    if not resposta.get("ok"):
        # o rig responde ok:false SEM levantar HTTP (ponte fora, por exemplo): declarar falha
        raise ErroDeApi(
            502,
            "teste_do_gatilho_recusado_pelo_rig",
            f"o rig nao aceitou o teste: {resposta.get('erro') or 'sem motivo'} "
            f"{resposta.get('detalhe') or ''}".strip(),
        )

    item_id = corpo.get("item_id") or None
    evento = _registrar_execucao_de_bancada(
        ctx,
        f"teste de gatilho na bancada (debug){'; item ' + item_id if item_id else ''}",
        item_id=item_id,
    )
    return {"rig": resposta, "evento": evento}


def _rota_rig_captura(ctx: dict, corpo: dict) -> dict:
    """Captura manual: uma foto de cada fonte (nao e o fluxo do trigger) + evento registrado."""
    parametros = []
    for campo in ("trigger_n", "trigger_em"):
        valor = corpo.get(campo)
        if valor is None:
            continue
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise ErroDeApi(
                400,
                "trigger_invalido",
                f"{campo} tem de ser numero, recebido {valor!r}",
            )
        parametros.append(f"{campo}={valor}")
    consulta = ("?" + "&".join(parametros)) if parametros else ""

    resposta = _chamar_rig(f"/capturar-3-cameras{consulta}", timeout=40.0)
    serie = resposta.get("serie") or resposta.get("serie_id")
    faltando = resposta.get("fotos_parciais") or resposta.get("faltantes")

    if not resposta.get("ok"):
        # captura parcial: o rig responde HTTP 200 com ok:false. Registrar 'aceito' aqui seria declarar
        # sucesso sobre uma captura que o proprio rig negou (e a serie fica no disco, incompleta).
        motivo = (
            f"captura manual RECUSADA pelo rig (debug)"
            f"{'; serie ' + str(serie) if serie else ''}"
            f"{'; fotos_parciais: ' + json.dumps(faltando, ensure_ascii=False) if faltando else ''}"
            f"; {resposta.get('erro') or 'sem motivo declarado'}"
        )
        registro = Registro.abrir(ctx["db"])
        try:
            evento_id = _escrever_com_retentativa(
                registro.registrar_gatilho,
                _agora_iso(),
                "invalido",
                fonte="nao_declarada",
                motivo=motivo[:400],
            )
        finally:
            registro.fechar()
        return {
            "rig": resposta,
            "serie": serie,
            "parcial": True,
            "evento": {"gatilho_id": evento_id, "motivo": motivo[:200]},
        }

    evento = _registrar_execucao_de_bancada(
        ctx,
        f"captura manual na bancada (debug){'; serie ' + str(serie) if serie else ''}",
    )
    return {"rig": resposta, "serie": serie, "parcial": False, "evento": evento}


def _rota_correcao(ctx: dict, corpo: dict) -> dict:
    """Decisao do operador sobre um item (D-30), gravada pelo unico caminho de escrita.

    A resposta nao ecoa o pedido: ela e o que o banco devolveu depois do INSERT, junto com a decisao
    vigente lida de novo. Sem isso, "registrado" seria afirmacao da API sobre si mesma.
    """
    for campo in ("item_id", "decisao_corrigida", "corrigido_por"):
        if not corpo.get(campo):
            raise ErroDeApi(
                400, "campo_ausente", f"{campo} e obrigatorio para registrar a decisao"
            )

    if not isinstance(corpo.get("corrigido_por"), str):
        raise ErroDeApi(
            400,
            "campo_com_tipo_errado",
            f"corrigido_por tem de ser texto, recebido {type(corpo.get('corrigido_por')).__name__}",
        )

    registro = Registro.abrir(ctx["db"])
    try:
        try:
            gravado = _escrever_com_retentativa(
                registro.corrigir,
                corpo["item_id"],
                corpo["decisao_corrigida"],
                corpo["corrigido_por"],
            )
        except EventoInvalido as exc:
            # item que nao existe e 404 (o recurso pedido nao esta la); o resto e 400 (pedido invalido)
            if "inexistente" in str(exc):
                raise ErroDeApi(404, "item_inexistente", str(exc)) from exc
            raise ErroDeApi(400, "correcao_recusada_pelo_registro", str(exc)) from exc

        # leitura de volta pelo mesmo caminho que a tela usa
        vigente = registro.correcao_vigente(str(gravado["item_id"]))
    finally:
        registro.fechar()

    if vigente is None:
        raise ErroDeApi(
            500,
            "correcao_nao_confirmada",
            "o INSERT nao aparece na leitura de volta: nao afirmo gravacao sem confirmar",
        )
    return {"correcao": vigente, "decisao_efetiva": vigente["decisao_corrigida"]}


# ------------------------------------------------------------------ servidor


def criar_servidor(
    db: Path | str,
    site: Path | str,
    porta: int = 8080,
    evidencias: Path | str | None = None,
    *,
    host: str = "127.0.0.1",
    token: str | None = None,
) -> ThreadingHTTPServer:
    """Servidor que serve a API e o site na MESMA origem (sem CORS, sem build). O front carrega
    Tailwind/Lucide de CDN externo; ver a nota no topo do arquivo.

    `evidencias` e a fronteira de leitura de arquivo: sem ela declarada, vale o diretorio do banco.
    Nada fora dessa raiz e servido, mesmo que o banco aponte para la.
    """
    db = Path(db).resolve()
    site = Path(site)
    token = token or None
    if host not in {"127.0.0.1", "::1", "localhost"} and token is None:
        raise ValueError("token obrigatorio quando a API escuta fora do loopback")
    if not site.is_dir():
        raise FileNotFoundError(f"diretorio do site nao existe: {site}")
    raiz_evidencias = Path(evidencias).resolve() if evidencias else db.parent
    raiz_evidencias.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        server_version = VERSAO_API
        protocol_version = "HTTP/1.1"

        def log_message(
            self, formato, *args
        ):  # ruido do http.server fora do jeito padrao
            pass

        # -------------------------------------------------- apoio

        def _contexto(self) -> dict:
            return {
                "db": db,
                "site": site,
                "porta_real": self.server.server_address[1],
                "evidencias": raiz_evidencias,
            }

        def _responde(self, codigo: int, corpo: bytes, tipo: str) -> None:
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(corpo)

        def _json(
            self, codigo: int, dados, ok: bool = True, erro: str = "", detalhe: str = ""
        ) -> None:
            corpo = (
                {"ok": ok, "dados": dados}
                if ok
                else {"ok": False, "erro": erro, "detalhe": detalhe}
            )
            self._responde(
                codigo,
                json.dumps(corpo, ensure_ascii=False, default=_serial).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        def _estatico(self, caminho_url: str) -> None:
            relativo = caminho_url.lstrip("/") or "index.html"
            alvo = (site / relativo).resolve()
            try:
                alvo.relative_to(site.resolve())  # travessia de diretorio barrada aqui
            except ValueError:
                raise ErroDeApi(404, "caminho_fora_do_site", relativo)
            if alvo.is_dir():
                alvo = alvo / "index.html"
            if not alvo.is_file():
                raise ErroDeApi(404, "arquivo_do_site_ausente", relativo)
            tipo = TIPOS_ESTATICOS.get(
                alvo.suffix.lower(),
                mimetypes.guess_type(str(alvo))[0] or "application/octet-stream",
            )
            self._responde(200, alvo.read_bytes(), tipo)

        # -------------------------------------------------- verbos

        def _autoriza_post(self) -> None:
            """Exige bearer token quando a API foi configurada com controle remoto."""
            if token is None:
                return
            cabecalho = self.headers.get("Authorization", "")
            recebido = cabecalho.removeprefix("Bearer ").strip()
            if not hmac.compare_digest(recebido, token):
                raise ErroDeApi(
                    401, "nao_autorizado", "POST exige Authorization: Bearer <token>"
                )

        def _metodo_nao_suportado(self, metodo: str) -> None:
            """Resposta JSON para verbo fora do contrato.

            O `BaseHTTPRequestHandler` respondia 501 com a pagina HTML dele, contradizendo a promessa
            do modulo ("erro e JSON: rota desconhecida responde JSON, nao a pagina de erro").
            """
            self._json(
                405,
                None,
                ok=False,
                erro="metodo_nao_suportado",
                detalhe=f"{metodo} nao entra nesta API (use GET ou POST)",
            )

        def do_DELETE(self) -> None:
            self._metodo_nao_suportado("DELETE")

        def do_PUT(self) -> None:
            self._metodo_nao_suportado("PUT")

        def do_PATCH(self) -> None:
            self._metodo_nao_suportado("PATCH")

        def do_OPTIONS(self) -> None:
            self._metodo_nao_suportado("OPTIONS")

        def do_HEAD(self) -> None:
            self._metodo_nao_suportado("HEAD")

        def do_TRACE(self) -> None:
            self._metodo_nao_suportado("TRACE")

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
                        self._json(200, _rota_item(ctx, rota[len("/api/item/") :]))
                    elif rota == "/api/lotes":
                        self._json(200, _rota_lotes(ctx))
                    elif rota == "/api/qualidade":
                        self._json(200, _rota_qualidade(ctx))
                    elif rota.startswith("/api/rig/"):
                        self._json(200, _rota_rig_leitura(rota[len("/api/rig/") :]))
                    elif rota == "/api/gatilhos":
                        self._json(200, _rota_gatilhos(ctx, consulta))
                    elif rota == "/api/series":
                        self._json(200, _rota_series_locais(consulta))
                    elif rota.startswith("/api/series/"):
                        dados, tipo = _rota_serie_local(rota[len("/api/series/") :])
                        self._responde(200, dados, tipo)
                    elif rota == "/api/modelo":
                        self._json(200, _rota_modelo(ctx))
                    elif rota == "/api/itens-ingeridos":
                        self._json(200, _rota_itens_ingeridos(ctx, consulta))
                    elif rota.startswith("/api/rig-serie/"):
                        dados, tipo = _rota_rig_serie(rota[len("/api/rig-serie/") :])
                        self._responde(200, dados, tipo)
                    elif rota == "/api/evidencia":
                        dados, tipo = _rota_evidencia(ctx, consulta)
                        self._responde(200, dados, tipo)
                    else:
                        raise ErroDeApi(404, "rota_desconhecida", rota)
                else:
                    self._estatico(rota)
            except ErroDeApi as exc:
                self._json(
                    exc.codigo, None, ok=False, erro=exc.erro, detalhe=exc.detalhe
                )
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc).lower():
                    self._json(
                        409,
                        None,
                        ok=False,
                        erro="registro_ocupado",
                        detalhe=(
                            "o registro aceita um escritor por vez e ele esta ocupado "
                            "(o rig esta gravando); tente de novo em instantes"
                        ),
                    )
                else:
                    self._json(
                        503,
                        None,
                        ok=False,
                        erro="banco_indisponivel",
                        detalhe=f"{type(exc).__name__}: {str(exc)[:160]}",
                    )
            except sqlite3.Error as exc:
                self._json(
                    503,
                    None,
                    ok=False,
                    erro="banco_indisponivel",
                    detalhe=f"{type(exc).__name__}: {str(exc)[:160]}",
                )
            except Exception as exc:  # noqa: BLE001
                self._json(
                    500,
                    None,
                    ok=False,
                    erro="falha_interna",
                    detalhe=f"{type(exc).__name__}: {str(exc)[:160]}",
                )

        def do_POST(self) -> None:
            rota = urlparse(self.path).path
            ctx = self._contexto()
            try:
                if rota not in (
                    "/api/gatilho",
                    "/api/correcao",
                    "/api/rig/delay",
                    "/api/rig/teste-trigger",
                    "/api/rig/captura",
                ):
                    raise ErroDeApi(404, "rota_desconhecida", rota)
                self._autoriza_post()
                if (
                    self.headers.get("Transfer-Encoding") or ""
                ).lower().strip() == "chunked":
                    raise ErroDeApi(
                        411,
                        "transfer_encoding_nao_suportado",
                        "envie o corpo com Content-Length, sem chunked",
                    )

                declarado = self.headers.get("Content-Length")
                if declarado is None:
                    raise ErroDeApi(411, "tamanho_ausente", "informe Content-Length")

                try:
                    tamanho = int(declarado)
                except ValueError as exc:
                    raise ErroDeApi(
                        400,
                        "tamanho_invalido",
                        f"Content-Length nao numerico: {declarado!r}",
                    ) from exc

                # negativo prende a thread no read (-1 le ate o socket fechar): recusa, nao atende
                if tamanho < 0 or tamanho > LIMITE_CORPO:
                    raise ErroDeApi(
                        400,
                        "tamanho_invalido",
                        f"Content-Length fora de [0,{LIMITE_CORPO}]: {tamanho}",
                    )

                bruto = self.rfile.read(tamanho) if tamanho else b"{}"
                try:
                    corpo = json.loads(bruto.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ErroDeApi(400, "json_invalido", str(exc)) from exc
                if not isinstance(corpo, dict):
                    raise ErroDeApi(
                        400, "json_precisa_ser_objeto", type(corpo).__name__
                    )

                if rota == "/api/gatilho":
                    self._json(200, _rota_gatilho(ctx, corpo))
                elif rota == "/api/correcao":
                    self._json(200, _rota_correcao(ctx, corpo))
                elif rota == "/api/rig/delay":
                    self._json(200, _rota_rig_delay(ctx, corpo))
                elif rota == "/api/rig/teste-trigger":
                    self._json(200, _rota_rig_teste_trigger(ctx, corpo))
                else:
                    self._json(200, _rota_rig_captura(ctx, corpo))
            except ErroDeApi as exc:
                self._json(
                    exc.codigo, None, ok=False, erro=exc.erro, detalhe=exc.detalhe
                )
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc).lower():
                    self._json(
                        409,
                        None,
                        ok=False,
                        erro="registro_ocupado",
                        detalhe=(
                            "o registro aceita um escritor por vez e ele esta ocupado "
                            "(o rig esta gravando); tente de novo em instantes"
                        ),
                    )
                else:
                    self._json(
                        503,
                        None,
                        ok=False,
                        erro="banco_indisponivel",
                        detalhe=f"{type(exc).__name__}: {str(exc)[:160]}",
                    )
            except sqlite3.Error as exc:
                self._json(
                    503,
                    None,
                    ok=False,
                    erro="banco_indisponivel",
                    detalhe=f"{type(exc).__name__}: {str(exc)[:160]}",
                )
            except Exception as exc:  # noqa: BLE001
                self._json(
                    500,
                    None,
                    ok=False,
                    erro="falha_interna",
                    detalhe=f"{type(exc).__name__}: {str(exc)[:160]}",
                )

    servidor = ThreadingHTTPServer((host, porta), Handler)
    servidor.api_token = token
    return servidor


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="API local do hub PNAAT (site + registro)")
    ap.add_argument("--db", default="hub.db", help="banco do registro")
    ap.add_argument(
        "--site",
        default=str(Path(__file__).resolve().parent / "site"),
        help="diretorio do site servido na mesma origem",
    )
    ap.add_argument(
        "--evidencias",
        default="",
        help="raiz de onde imagens de evidencia podem ser lidas (padrao: pasta do banco)",
    )
    ap.add_argument("--porta", type=int, default=8080)
    ap.add_argument(
        "--host",
        default="127.0.0.1",
        help="endereco de bind; fora do loopback exige --token",
    )
    ap.add_argument(
        "--token",
        default=os.environ.get("PNAAT_API_TOKEN"),
        help="bearer token para POSTs; tambem pode vir de PNAAT_API_TOKEN",
    )
    a = ap.parse_args(argv)
    try:
        servidor = criar_servidor(
            Path(a.db),
            Path(a.site),
            a.porta,
            Path(a.evidencias) if a.evidencias else None,
            host=a.host,
            token=a.token,
        )
    except (ValueError, FileNotFoundError) as erro:
        # erro de configuracao do operador nao pode virar traceback: a API nem chegou a servir
        print(f"erro de configuracao: {erro}", file=sys.stderr)
        return 2
    print(
        f"{VERSAO_API}: http://{a.host}:{servidor.server_address[1]}/  (site em {a.site})"
    )
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
