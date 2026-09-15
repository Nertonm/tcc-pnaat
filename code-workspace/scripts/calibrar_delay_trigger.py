#!/usr/bin/env python3
"""PoC-03: calibra o atraso trigger -> captura e casa a velocidade da esteira com o trigger.

O que ele entrega, por passagem e no consolidado:
  * a reta `offset(tau)` medida na imagem (uma rajada de quadros por borda de trigger);
  * a velocidade da esteira e a escala mm/px, tiradas da propria reta;
  * o atraso `tau*` que centra a garrafa na ROI (gravado em ~/poc03/delay.json com --aplicar);
  * o envelope operacional: acima de qual velocidade a captura deixa de caber entre itens
    (perde garrafa) e qual presenca minima o debounce do sensor exige.

Disciplina de recursos (nao negociavel neste repo):
  * a porta serial tem UM dono: o supervisor da PoC-01. Aqui a leitura e PASSIVA do log;
  * a camera tem UM leitor (thread unica) -- nao abrir /dev/videoN em dois processos.

Modos:
  --fonte log       bancada real: segue ~/poc01/stream.log e a camera
  --fonte simulado  sem hardware: quadros sinteticos passam pela MESMA deteccao e ajuste,
                    permitindo conferir o metodo contra uma verdade conhecida

    python3 scripts/poc03_calibra_delay.py --fonte simulado --distancia-mm 150
    python3 scripts/poc03_calibra_delay.py --fonte log --distancia-mm 150 --passagens 5 --aplicar
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import threading
import time
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from pocs.expansao_sincronizacao.delay import (  # noqa: E402
    Amostra,
    ResultadoCalibracao,
    janela_presenca_s,
    orcamento,
    velocidade_maxima_mm_s,
    velocidade_maxima_por_presenca,
)

CASA = Path.home() / "poc03"
STREAM = Path.home() / "poc01" / "stream.log"


class Quadro:
    __slots__ = ("bgr", "ts")

    def __init__(self, bgr, ts: float) -> None:
        self.bgr = bgr
        self.ts = ts


class LeitorCamera:
    """Leitor UNICO da camera: guarda o ultimo quadro e o instante de captura."""

    def __init__(self, indice: int, largura: int, altura: int, fps: int) -> None:
        self.cap = cv2.VideoCapture(indice, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(f"nao foi possivel abrir a camera {indice}")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, largura)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, altura)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._quadro: Quadro | None = None
        self._lock = threading.Lock()
        self._parar = threading.Event()
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()

    def _loop(self) -> None:
        while not self._parar.is_set():
            ok, bgr = self.cap.read()
            if not ok:
                time.sleep(0.005)
                continue
            with self._lock:
                self._quadro = Quadro(bgr, time.monotonic())

    def ultimo(self) -> Quadro | None:
        with self._lock:
            return self._quadro

    def novo(self, ts_min: float) -> Quadro | None:
        """Quadro mais novo que `ts_min`. Sem isso a rajada reamostra o mesmo frame (tau duplicado)."""
        with self._lock:
            q = self._quadro
        if q is None or q.ts <= ts_min:
            return None
        return q

    def fecha(self) -> None:
        self._parar.set()
        self._th.join(timeout=1.0)
        self.cap.release()


class CameraSimulada:
    """Camera sintetica: a garrafa e uma barra clara que anda `v` mm/s (escala `k` mm/px)."""

    def __init__(self, largura: int, altura: int, distancia_mm: float, escala_mm_px: float,
                 velocidade_mm_s: float, y_banda: tuple[int, int], ruido_px: float,
                 largura_item_px: int, semente: int = 11) -> None:
        self.w, self.h = largura, altura
        self.distancia, self.k, self.v = distancia_mm, escala_mm_px, velocidade_mm_s
        self.y1, self.y2 = y_banda
        self.ruido = ruido_px
        self.item_px = largura_item_px
        self.x_centro = largura / 2.0
        self.rnd = np.random.default_rng(semente)
        self.t0 = time.monotonic()
        self.fundos = self._fundo()

    def _fundo(self) -> np.ndarray:
        base = np.full((self.h, self.w, 3), 40, dtype=np.int16)
        base += self.rnd.integers(-4, 5, base.shape, dtype=np.int16)
        return np.clip(base, 0, 255).astype(np.uint8)

    def referencia(self) -> Quadro:
        return Quadro(self.fundos.copy(), time.monotonic())

    def x_centro_em(self, tau_s: float) -> float:
        """No instante do trigger a garrafa esta `d` mm antes do centro da ROI."""
        return self.x_centro - self.distancia / self.k + (self.v / self.k) * tau_s

    def le(self) -> Quadro:
        tau = time.monotonic() - self.t0
        bgr = self.fundos.copy()
        cx = self.x_centro_em(tau) + float(self.rnd.normal(0.0, self.ruido))
        x1 = int(round(cx - self.item_px / 2))
        x2 = x1 + self.item_px
        cv2.rectangle(bgr, (max(0, x1), self.y1), (min(self.w - 1, x2), self.y2), (190, 190, 190), -1)
        return Quadro(bgr, time.monotonic())


def _conta(motivos: dict | None, chave: str) -> None:
    if motivos is not None:
        motivos[chave] = motivos.get(chave, 0) + 1


def detecta_offset_px(quadro: np.ndarray, referencia: np.ndarray, banda: tuple[int, int],
                      limiar: int, x_centro_px: float, sentido: int = 1,
                      motivos: dict | None = None) -> float | None:
    """Centroide horizontal do que mudou em relacao a esteira vazia (mm/px vem do ajuste).

    limiar <= 0 liga o limiar automatico (media + 3 sigma da propria diferenca): acompanha a
    iluminacao da bancada em vez de exigir um numero fixo escolhido no escuro.
    sentido = +1 para item andando da esquerda para a direita; -1 inverte, mantendo valido o
    modelo offset(tau) = v*tau - d nos dois sentidos de esteira.

    Recusa duas situacoes em vez de produzir numero errado:
      * banda sem massa significativa (nao ha item);
      * item tocando a borda do quadro -> o centroide mediria so o pedaco visivel, e o ajuste
        passaria a mentir. Isso acontece quando o trigger esta FORA do campo de visao.
    """
    y1, y2 = banda
    atual = cv2.cvtColor(quadro[y1:y2], cv2.COLOR_BGR2GRAY).astype(np.int16)
    fundo = cv2.cvtColor(referencia[y1:y2], cv2.COLOR_BGR2GRAY).astype(np.int16)
    diferenca = np.abs(atual - fundo)
    corte = float(limiar) if limiar and limiar > 0 else float(diferenca.mean() + 3.0 * diferenca.std())
    colunas = (diferenca > corte).astype(np.float32).sum(axis=0)
    massa = float(colunas.sum())
    if massa < 20.0:
        _conta(motivos, "sem_item")
        return None
    if colunas[0] > 0 or colunas[-1] > 0:
        _conta(motivos, "cortado_na_borda")
        return None
    xs = np.arange(colunas.size, dtype=np.float32)
    centroide = float((xs * colunas).sum() / massa)
    return sentido * (centroide - x_centro_px)


def le_eventos(caminho: Path, desde: int) -> tuple[list[dict], int]:
    """Leitor PASSIVO do stream do supervisor: nunca abre a serial."""
    if not caminho.exists():
        return [], desde
    texto = caminho.read_text(errors="replace")
    novos = texto[desde:]
    eventos = []
    for linha in novos.splitlines():
        if "EV " not in linha:
            continue
        partes = linha.split(" EV ", 1)[1].split()
        if not partes or partes[0] != "OPEN":
            continue
        dados = {}
        for p in partes[1:]:
            if "=" in p:
                chave, valor = p.split("=", 1)
                dados[chave] = valor
        eventos.append(dados)
    return eventos, len(texto)


def roda_simulado(args) -> tuple[ResultadoCalibracao, dict]:
    # A verdade fisica do simulador e SEPARADA da distancia declarada ao ajuste: e isso que
    # permite mutar a declaracao (mentir a regua) e exigir que o oraculo reprove.
    distancia_sim = args.sim_distancia if args.sim_distancia else args.distancia_mm
    sim = CameraSimulada(
        largura=args.largura, altura=args.altura, distancia_mm=distancia_sim,
        escala_mm_px=args.sim_escala, velocidade_mm_s=args.sim_velocidade,
        y_banda=(int(args.banda_y1 * args.altura), int(args.banda_y2 * args.altura)),
        ruido_px=args.sim_ruido, largura_item_px=args.sim_largura_item,
    )
    referencia = sim.referencia().bgr
    x_centro_px = args.x_centro * args.largura
    resultado = ResultadoCalibracao(distancia_mm=args.distancia_mm, tolerancia_mm=args.tolerancia_mm)
    motivos: dict = {}

    for passagem in range(1, args.passagens + 1):
        sim.t0 = time.monotonic()
        time.sleep(args.sim_atraso_trigger)      # simula o atraso do sensor + serial
        instante = time.monotonic()
        for i in range(args.quadros_por_passagem):
            time.sleep(1.0 / args.fps)
            q = sim.le()
            offset = detecta_offset_px(
                q.bgr, referencia,
                (int(args.banda_y1 * args.altura), int(args.banda_y2 * args.altura)),
                args.limiar, x_centro_px, args.sentido_sinal, motivos,
            )
            if offset is not None:
                resultado.amostras.append(
                    Amostra(passagem=passagem, tau_s=q.ts - instante, offset_px=offset)
                )
    verdade = {
        "velocidade_mm_s": args.sim_velocidade,
        "escala_mm_por_px": args.sim_escala,
        "distancia_mm": distancia_sim,
        "tau_ideal_s": distancia_sim / args.sim_velocidade,
        "rejeicoes": motivos,
    }
    return resultado, verdade


def roda_bancada(args) -> tuple[ResultadoCalibracao, dict]:
    """Caminho do ENSAIO: eventos vem do log do supervisor (leitura passiva) e os quadros vem da
    camera real -- ou de uma camera sintetica, para validar todo o encanamento sem hardware."""
    casa = CASA
    casa.mkdir(parents=True, exist_ok=True)
    simulada = args.camera_modo == "simulado"
    banda = (int(args.banda_y1 * args.altura), int(args.banda_y2 * args.altura))
    x_centro_px = args.x_centro * args.largura

    cam = None
    sim = None
    if simulada:
        distancia_sim = args.sim_distancia if args.sim_distancia else args.distancia_mm
        sim = CameraSimulada(
            largura=args.largura, altura=args.altura, distancia_mm=distancia_sim,
            escala_mm_px=args.sim_escala, velocidade_mm_s=args.sim_velocidade,
            y_banda=banda, ruido_px=args.sim_ruido, largura_item_px=args.sim_largura_item,
        )
        referencia = sim.referencia().bgr
        print("camera SIMULADA: o log do supervisor e real; os quadros sao sinteticos")
    else:
        cam = LeitorCamera(args.camera, args.largura, args.altura, args.fps)
        time.sleep(0.7)                                   # primeira exposicao estabiliza
        referencia = None
        while referencia is None:
            q = cam.ultimo()
            if q is not None:
                referencia = q.bgr.copy()
            time.sleep(0.05)
        alvo = casa / "referencia-esteira-vazia.jpg"
        cv2.imwrite(str(alvo), referencia)
        print(f"referencia (esteira vazia) gravada em {alvo}")

    if args.referencia and Path(args.referencia).exists():
        referencia = cv2.imread(str(args.referencia))
        print(f"referencia carregada de {args.referencia}")

    resultado = ResultadoCalibracao(distancia_mm=args.distancia_mm, tolerancia_mm=args.tolerancia_mm)
    log = Path(args.log) if args.log else STREAM
    if args.desde_inicio or not log.exists():
        offset_log = 0
    else:
        offset_log = log.stat().st_size       # so passagens NOVAS: historico nao e ensaio
        print(f"ignorando {offset_log} bytes de historico do log (use --desde-inicio para replay)")
    passagens, sem_amostra = 0, 0
    motivos: dict = {}
    try:
        print(f"aguardando {args.passagens} passagens no trigger (log: {log})...")
        limite = time.monotonic() + args.timeout
        while passagens < args.passagens and time.monotonic() < limite:
            eventos, offset_log = le_eventos(log, offset_log)
            for _ in eventos:
                if passagens >= args.passagens:
                    break                      # o lote pode trazer mais eventos que o pedido
                passagens += 1
                if simulada:
                    sim.t0 = time.monotonic()      # a fisica do item comeca na borda do trigger
                instante = time.monotonic()
                coletados = 0
                guardados = 0
                for _i in range(args.quadros_por_passagem):
                    time.sleep(1.0 / args.fps)
                    if simulada:
                        q = sim.le()
                    else:
                        q = cam.novo(instante)     # so quadros POSTERIORES: sem tau duplicado
                        if q is None:
                            continue
                    off = detecta_offset_px(q.bgr, referencia, banda, args.limiar, x_centro_px,
                                            args.sentido_sinal, motivos)
                    if off is None:
                        continue
                    resultado.amostras.append(
                        Amostra(passagem=passagens, tau_s=q.ts - instante, offset_px=off)
                    )
                    coletados += 1
                    if guardados < args.guardar_quadros and not simulada:
                        cv2.imwrite(str(casa / f"p{passagens:02d}-tau{q.ts - instante:.3f}.jpg"), q.bgr)
                        guardados += 1
                if coletados == 0:
                    sem_amostra += 1
                print(f"passagem {passagens}: {coletados} amostras"
                      + (f", {guardados} quadros guardados" if guardados else ""))
            time.sleep(0.05)
        if sem_amostra:
            print(f"ATENCAO: {sem_amostra} passagem(ns) sem nenhuma amostra. Se todas falharam, "
                  f"veja exposicao/fps e a banda --y e se o item passa dentro da banda escolhida.")
        extra = {"passagens_vistas": passagens, "passagens_sem_amostra": sem_amostra,
                 "rejeicoes": motivos}
        if simulada:                     # camera sintetica carrega a verdade junto
            extra.update({
                "velocidade_mm_s": args.sim_velocidade,
                "escala_mm_por_px": args.sim_escala,
                "distancia_mm": distancia_sim,
                "tau_ideal_s": distancia_sim / args.sim_velocidade,
            })
        return resultado, extra
    finally:
        if cam is not None:
            cam.fecha()


def relatorio(args, resultado: ResultadoCalibracao, extra: dict) -> dict:
    veredito, motivos = resultado.veredito()
    velocidade = resultado.velocidade_mm_s()
    escala = resultado.escala_mm_por_px()
    tau = resultado.tau_otimo_s()

    linha = [f"{'=' * 68}", f"PoC-03 calibracao trigger -> captura   Veredito: {veredito}"]
    if resultado.ajuste:
        linha.append(
            f"  amostras {resultado.ajuste.n} em {resultado.passagens_com_amostra()} passagem(ns)"
            f"  r2 {resultado.ajuste.r2:.4f}  residuo {resultado.ajuste.residuo_px:.2f} px"
        )
    linha.append(f"  distancia declarada {args.distancia_mm:.1f} mm")
    if velocidade is not None:
        linha.append(f"  velocidade medida   {velocidade:.1f} mm/s ({velocidade * 60 / 1000:.2f} m/min)")
    if escala is not None:
        linha.append(f"  escala da imagem    {escala:.4f} mm/px")
    if tau is not None:
        linha.append(f"  ATRASO DE CAPTURA   {tau * 1000:.1f} ms   ->  apos a borda do trigger")
        linha.append(f"  residuo em mm       {resultado.residuo_mm():.3f} mm (tolerancia {args.tolerancia_mm:.2f})")
        if resultado.amostras:
            tau_min = min(a.tau_s for a in resultado.amostras)
            tau_max = max(a.tau_s for a in resultado.amostras)
            linha.append(f"  janela observada    {tau_min * 1000:.0f} .. {tau_max * 1000:.0f} ms")
            if tau > tau_max:
                linha.append("  ! o atraso otimo cai FORA da janela observada: e extrapolacao do ajuste.")
                linha.append("    aumente --janela (ou aproxime a camera) e recalibre para medir, nao extrapolar.")
    rejeicoes = extra.get("rejeicoes") or {}
    if rejeicoes:
        linha.append(f"  descartes            {rejeicoes}")
        linha.append("                       (corte na borda e normal no inicio da rajada; so")
        linha.append("                        vira problema se nenhum quadro valido sobrar)")
        if rejeicoes.get("cortado_na_borda") and veredito != "PASS":
            linha.append("  ! ensaio reprovado COM corte na borda: suspeite de trigger fora do")
            linha.append("    campo de visao -- aproxime a camera, use lente mais aberta ou")
            linha.append("    reduza a distancia trigger->ROI e recalibre.")
    for motivo in motivos:
        linha.append(f"  ! {motivo}")

    envelope: dict = {}
    v_orcamento = velocidade_maxima_mm_s(
        args.vistas, args.tempo_por_vista, args.rearme, args.passo_mm, args.margem
    )
    v_presenca = velocidade_maxima_por_presenca(args.comprimento_mm, args.presenca_minima)
    v_max = min(v_orcamento, v_presenca)
    linha.append("")
    linha.append(f"  envelope: v_max por orcamento de captura {v_orcamento:.0f} mm/s | "
                 f"por presenca {v_presenca:.0f} mm/s  =>  teto {v_max:.0f} mm/s")
    if velocidade is not None and velocidade > 0:
        orc = orcamento(args.vistas, args.tempo_por_vista, args.rearme, args.passo_mm,
                        velocidade, args.margem)
        envelope = {"velocidade_atual_mm_s": velocidade, "intervalo_s": orc.intervalo_s,
                    "folga_s": orc.folga_s, "cabendo": orc.cabendo,
                    "v_max_orcamento_mm_s": v_orcamento, "v_max_presenca_mm_s": v_presenca,
                    "v_max_global_mm_s": v_max,
                    "janela_presenca_s": janela_presenca_s(args.comprimento_mm, velocidade)}
        linha.append(f"  nesta velocidade: intervalo {orc.intervalo_s * 1000:.0f} ms, "
                     f"folga {orc.folga_s * 1000:.0f} ms, "
                     f"presenca {envelope['janela_presenca_s'] * 1000:.0f} ms -> "
                     f"{'OK' if orc.cabendo else 'PERDE GARRAFA'}")
        if velocidade > v_max:
            linha.append(f"  ! velocidade medida {velocidade:.0f} > teto {v_max:.0f}: reduza o PWM ou as vistas")
    linha.append(f"{'=' * 68}")
    print("\n".join(linha))

    evidencia = {
        "poc": "03-sincronizacao-fisica",
        "medido_em": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "fonte": args.fonte,
        "parametros": {
            "camera": args.camera, "largura": args.largura, "altura": args.altura, "fps": args.fps,
            "banda_y": [args.banda_y1, args.banda_y2], "x_centro": args.x_centro,
            "limiar": args.limiar, "distancia_mm": args.distancia_mm,
            "tolerancia_mm": args.tolerancia_mm, "vistas": args.vistas,
            "tempo_por_vista_s": args.tempo_por_vista, "rearme_s": args.rearme,
            "passo_mm": args.passo_mm, "margem_s": args.margem,
            "comprimento_mm": args.comprimento_mm, "presenca_minima_s": args.presenca_minima,
        },
        "calibracao": resultado.para_dict(),
        "envelope": envelope,
        "extra": extra,
    }
    CASA.mkdir(parents=True, exist_ok=True)
    destino = CASA / "evidencia-calibracao-delay.json"
    destino.write_text(json.dumps(evidencia, indent=2, ensure_ascii=False))
    print(f"evidencia: {destino}")

    if args.aplicar and veredito != "PASS":
        print("nada aplicado: veredito nao e PASS (nao se aplica delay de ensaio reprovado)")
    return evidencia


def aplica_delay(args, resultado: ResultadoCalibracao) -> bool:
    """Grava o atraso calibrado da vista no delay.json compartilhado (atomico, acumulando vistas).

    Cada camera tem a sua distancia ao trigger, logo o seu proprio atraso: o arquivo guarda um
    dicionario por vista, e calibrar uma vista nao apaga as outras.
    """
    veredito, _ = resultado.veredito()
    if not args.aplicar:
        return False
    if veredito != "PASS":
        print(f"nada aplicado: veredito {veredito}")
        return False
    tau = resultado.tau_otimo_s()
    if tau is None:
        print("nada aplicado: atraso indeterminado")
        return False

    CASA.mkdir(parents=True, exist_ok=True)
    destino = CASA / "delay.json"
    dados: dict = {"schema": "delay-trigger.v1", "vistas": {}}
    if destino.exists():
        try:
            anterior = json.loads(destino.read_text())
            if isinstance(anterior, dict) and isinstance(anterior.get("vistas"), dict):
                dados["vistas"] = anterior["vistas"]
                dados["schema"] = anterior.get("schema", dados["schema"])
        except json.JSONDecodeError:
            print("delay.json anterior ilegivel: sera reescrito com esta vista")

    dados["vistas"][args.vista] = {
        "tau_s": tau,
        "distancia_mm": args.distancia_mm,
        "velocidade_mm_s": resultado.velocidade_mm_s(),
        "escala_mm_por_px": resultado.escala_mm_por_px(),
        "residuo_mm": resultado.residuo_mm(),
        "tolerancia_mm": args.tolerancia_mm,
        "n_amostras": len(resultado.amostras),
        "passagens_com_amostra": resultado.passagens_com_amostra(),
        "sentido": args.sentido,
        "medido_em": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "fonte": args.fonte,
    }
    tmp = destino.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(dados, indent=2, ensure_ascii=False))
    tmp.replace(destino)
    print(f"vista {args.vista!r}: atraso {tau * 1000:.1f} ms aplicado em {destino}")
    return True


def main() -> int:
    p = argparse.ArgumentParser(description="Calibra atraso trigger->captura e casa a velocidade da esteira")
    p.add_argument("--fonte", choices=("log", "simulado"), default="log")
    p.add_argument("--distancia-mm", type=float, required=True,
                   help="distancia fisica do sensor de trigger ao centro da ROI (regua)")
    p.add_argument("--tolerancia-mm", type=float, default=2.0)
    p.add_argument("--passagens", type=int, default=5)
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--camera-modo", choices=("real", "simulado"), default="real",
                   help="no modo log: quadros da camera real ou de uma camera sintetica "
                        "(valida o encanamento do ensaio sem hardware)")
    p.add_argument("--vista", type=str, default="principal",
                   help="nome da vista (topo, lateral1, lateral2...): cada camera tem a sua "
                        "distancia ao trigger, logo o seu proprio atraso")
    p.add_argument("--sentido", choices=("esq-dir", "dir-esq"), default="esq-dir",
                   help="sentido do movimento do item na imagem")
    p.add_argument("--largura", type=int, default=640)
    p.add_argument("--altura", type=int, default=480)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--banda-y1", type=float, default=0.35)
    p.add_argument("--banda-y2", type=float, default=0.75)
    p.add_argument("--x-centro", type=float, default=0.5)
    p.add_argument("--limiar", type=int, default=25)
    p.add_argument("--quadros-por-passagem", type=int, default=20)
    p.add_argument("--janela", type=float, default=2.0,
                   help="duracao da rajada por passagem, em segundos; se > 0 vence --quadros-por-passagem")
    p.add_argument("--guardar-quadros", type=int, default=2)
    p.add_argument("--referencia", type=str, default="")
    p.add_argument("--desde-inicio", action="store_true",
                   help="no modo log, reprocessa o historico do log (replay/ensaio); sem isso o "
                        "instrumento ignora o historico e so calibra passagens NOVAS")
    p.add_argument("--log", type=str, default="",
                   help=f"caminho do log de eventos (padrao: {STREAM}); use outro arquivo para "
                        f"ensaios sem poluir o log do supervisor")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--aplicar", action="store_true")
    p.add_argument("--vistas", type=int, default=3)
    p.add_argument("--tempo-por-vista", type=float, default=0.077)
    p.add_argument("--rearme", type=float, default=0.5,
                   help="re-armadura do trigger apos cada item (s). Firmware poc01: "
                        "GUARD_MS=500 e ARM_MS=500 -> 0,5 s")
    p.add_argument("--passo-mm", type=float, default=80.0,
                   help="passo entre itens = comprimento + folga (mm)")
    p.add_argument("--margem", type=float, default=0.02)
    p.add_argument("--comprimento-mm", type=float, default=60.0)
    p.add_argument("--presenca-minima", type=float, default=0.10,
                   help="presenca estavel exigida pelo debounce (s). Firmware poc01: "
                        "STABLE_READS=5 x DEBOUNCE_MS=20 -> 0,10 s")
    p.add_argument("--sim-velocidade", type=float, default=100.0)
    p.add_argument("--sim-escala", type=float, default=0.5)
    p.add_argument("--sim-distancia", type=float, default=0.0,
                   help="verdade fisica do simulador; 0 = usar a mesma distancia declarada")
    p.add_argument("--sim-ruido", type=float, default=0.6)
    p.add_argument("--sim-largura-item", type=int, default=90)
    p.add_argument("--sim-atraso-trigger", type=float, default=0.0)
    args = p.parse_args()
    args.sentido_sinal = 1 if args.sentido == "esq-dir" else -1

    if args.janela and args.janela > 0:
        args.quadros_por_passagem = max(3, int(round(args.janela * args.fps)))

    if args.fonte == "simulado":
        resultado, extra = roda_simulado(args)
    else:
        resultado, extra = roda_bancada(args)

    relatorio(args, resultado, extra)

    if extra.get("tau_ideal_s"):        # camera sintetica: confere contra a verdade conhecida
        if not confere_oraculo(resultado, extra):
            print("nada aplicado: ensaio que nao confere com a verdade conhecida nao calibra nada")
            return 1

    aplica_delay(args, resultado)
    return 0


def confere_oraculo(resultado: ResultadoCalibracao, extra: dict) -> bool:
    """Confere o medido contra a verdade injetada (tolerancia declarada: 10%).

    Vale nos DOIS caminhos quando a camera e sintetica: e o que permite revisar o encanamento do
    ensaio (log real) sem hardware sem perder a referencia de verdade.
    """
    print(f"verdade injetada: v={extra['velocidade_mm_s']:.1f} mm/s  "
          f"k={extra['escala_mm_por_px']:.4f} mm/px  d={extra['distancia_mm']:.1f} mm  "
          f"tau*={extra['tau_ideal_s'] * 1000:.1f} ms")
    erros = []
    tau = resultado.tau_otimo_s()
    vel = resultado.velocidade_mm_s()
    if tau is not None:
        erros.append(abs(tau - extra["tau_ideal_s"]) / extra["tau_ideal_s"])
    if vel is not None:
        erros.append(abs(vel - extra["velocidade_mm_s"]) / extra["velocidade_mm_s"])
    if not erros:
        print("ORACULO: sem grandezas para conferir (a medicao nao produziu ajuste)")
        return False
    if max(erros) > 0.10:
        print(f"ORACULO: erro maximo {max(erros) * 100:.1f}% > 10% -> metodo/conferencia reprovados")
        return False
    print(f"ORACULO: erro maximo {max(erros) * 100:.1f}% (<= 10%) -> metodo confere com a verdade")
    return True


if __name__ == "__main__":
    raise SystemExit(main())
