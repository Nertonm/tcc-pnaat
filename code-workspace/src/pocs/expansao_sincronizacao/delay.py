"""PoC-03: casamento entre trigger, velocidade da esteira e instante de captura.

O problema fisico: o sensor de presenca (E18-D80NK) fica a uma distancia `d` do centro
da ROI da camera. A garrafa anda a `v` mm/s. Se a captura dispara no instante exato do
trigger, a garrafa ainda esta `d` mm ANTES da ROI; se dispara tarde demais, ela ja passou.
O instante certo e `tau* = d / v`.

Modelo do que o instrumento de bancada mede:

    offset(tau) = v * tau - d

`offset` e a posicao da garrafa em relacao ao centro da ROI (negativo = ainda nao chegou,
positivo = ja passou). Isso e LINEAR em `tau`: uma unica passagem, com uma rajada de
quadros, gera muitas amostras `(tau, offset)` e a reta ajustada entrega:

  * a inclinacao  -> velocidade da esteira (no espaco da imagem);
  * a raiz        -> o atraso que centra a garrafa;
  * e, medindo `d` com uma regua, tambem a escala mm/pixel do enquadramento.

Ou seja: nao e preciso encoder nem conhecer o mm/pixel de antemao.

O segundo criterio ("todas as garrafas") e de orcamento: entre dois itens passam
`passo / v` segundos e a captura das vistas precisa caber nesse intervalo, com tempo de
re-armadura do trigger. A velocidade maxima sustentavel e o minimo entre o orcamento de
captura e a janela de presenca exigida pelo debounce do sensor.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass(frozen=True)
class Amostra:
    """Um ponto medido: a garrafa foi vista `offset_px` pixels depois do centro da ROI,
    quando a captura ocorreu `tau_s` segundos apos a borda do trigger."""

    passagem: int
    tau_s: float
    offset_px: float


@dataclass(frozen=True)
class Ajuste:
    """Reta offset_px(tau) = inclinacao * tau + intercepto (minimos quadrados)."""

    inclinacao_px_s: float
    intercepto_px: float
    n: int
    r2: float
    residuo_px: float

    def escala_mm_por_px(self, distancia_mm: float) -> float:
        """Escala da imagem a partir da distancia fisica trigger->ROI.

        offset_px(tau) = (v*tau - d)/k => inclinacao = v/k e intercepto = -d/k.
        Com `d` medido a regua, k = d / |intercepto|.
        """
        if self.intercepto_px >= 0:
            raise ValueError(
                "intercepto nao negativo: a garrafa nao chegou a ficar antes do centro da ROI; "
                "confira o sinal do offset e a distancia declarada"
            )
        return distancia_mm / abs(self.intercepto_px)

    def velocidade_mm_s(self, distancia_mm: float) -> float:
        return self.inclinacao_px_s * self.escala_mm_por_px(distancia_mm)

    def tau_otimo_s(self) -> float:
        """Raiz da reta: o atraso que coloca a garrafa no centro da ROI."""
        if self.inclinacao_px_s == 0:
            raise ValueError("inclinacao nula: sem movimento medido, o delay e indeterminado")
        return -self.intercepto_px / self.inclinacao_px_s


def offset_mm(velocidade_mm_s: float, tau_s: float, distancia_mm: float) -> float:
    """Posicao da garrafa em relacao ao centro da ROI (mm) para um dado atraso."""
    return velocidade_mm_s * tau_s - distancia_mm


def delay_ideal_s(distancia_mm: float, velocidade_mm_s: float) -> float:
    """tau* = d / v."""
    if velocidade_mm_s <= 0:
        raise ValueError("velocidade deve ser positiva")
    return distancia_mm / velocidade_mm_s


def ajusta(amostras: list[Amostra]) -> Ajuste:
    """Minimos quadrados de offset_px contra tau. Recusa entrada degenerada em vez de mentir."""
    n = len(amostras)
    if n < 3:
        raise ValueError(f"ajuste exige >= 3 amostras, recebeu {n}")
    soma_tau = sum(a.tau_s for a in amostras)
    soma_off = sum(a.offset_px for a in amostras)
    media_tau = soma_tau / n
    media_off = soma_off / n
    var_tau = sum((a.tau_s - media_tau) ** 2 for a in amostras)
    if var_tau == 0:
        raise ValueError("todas as amostras tem o mesmo tau: nao ha reta para ajustar")
    cov = sum((a.tau_s - media_tau) * (a.offset_px - media_off) for a in amostras)
    inclinacao = cov / var_tau
    intercepto = media_off - inclinacao * media_tau
    residuos = [a.offset_px - (inclinacao * a.tau_s + intercepto) for a in amostras]
    sq = sum(r * r for r in residuos)
    total = sum((a.offset_px - media_off) ** 2 for a in amostras)
    r2 = 1.0 - sq / total if total > 0 else 1.0
    return Ajuste(
        inclinacao_px_s=inclinacao,
        intercepto_px=intercepto,
        n=n,
        r2=r2,
        residuo_px=(sq / n) ** 0.5,
    )


def ladder(tau_centro_s: float, meia_largura_s: float, n: int) -> list[float]:
    """Plano de varredura discreta de atrasos (para quando nao houver rajada)."""
    if n < 3:
        raise ValueError("ladder exige >= 3 degraus")
    if meia_largura_s <= 0:
        raise ValueError("meia_largura deve ser positiva")
    passo = (2 * meia_largura_s) / (n - 1)
    return [tau_centro_s - meia_largura_s + i * passo for i in range(n)]


@dataclass(frozen=True)
class Orcamento:
    """Orcamento temporal entre dois itens: a captura cabe no intervalo entre passagens?"""

    intervalo_s: float
    captura_s: float
    rearme_s: float
    margem_s: float

    @property
    def folga_s(self) -> float:
        return self.intervalo_s - (self.captura_s + self.rearme_s + self.margem_s)

    @property
    def cabendo(self) -> bool:
        return self.folga_s >= 0


def orcamento(
    n_vistas: int,
    tempo_por_vista_s: float,
    tempo_rearme_s: float,
    passo_mm: float,
    velocidade_mm_s: float,
    margem_s: float = 0.02,
) -> Orcamento:
    """Passo = comprimento do item + folga entre itens, em mm."""
    if velocidade_mm_s <= 0 or passo_mm <= 0:
        raise ValueError("passo e velocidade devem ser positivos")
    captura = n_vistas * tempo_por_vista_s
    return Orcamento(
        intervalo_s=passo_mm / velocidade_mm_s,
        captura_s=captura,
        rearme_s=tempo_rearme_s,
        margem_s=margem_s,
    )


def velocidade_maxima_mm_s(
    n_vistas: int,
    tempo_por_vista_s: float,
    tempo_rearme_s: float,
    passo_mm: float,
    margem_s: float = 0.02,
) -> float:
    """Velocidade acima da qual a captura deixa de caber entre dois itens (perde garrafa)."""
    custo = n_vistas * tempo_por_vista_s + tempo_rearme_s + margem_s
    if custo <= 0:
        raise ValueError("custo de captura deve ser positivo")
    return passo_mm / custo


def janela_presenca_s(comprimento_mm: float, velocidade_mm_s: float) -> float:
    """Tempo em que o item permanece dentro do alcance do sensor."""
    if velocidade_mm_s <= 0:
        raise ValueError("velocidade deve ser positiva")
    return comprimento_mm / velocidade_mm_s


def velocidade_maxima_por_presenca(comprimento_mm: float, presenca_minima_s: float) -> float:
    """Debounce exige `presenca_minima_s` de leitura estavel; acima disso o trigger perde item."""
    if presenca_minima_s <= 0:
        raise ValueError("presenca minima deve ser positiva")
    return comprimento_mm / presenca_minima_s


@dataclass
class ResultadoCalibracao:
    """Consolidado de uma sessao de calibracao (base do JSON de evidencia)."""

    distancia_mm: float
    tolerancia_mm: float
    amostras: list[Amostra] = field(default_factory=list)
    ajuste: Ajuste | None = None
    motivos: list[str] = field(default_factory=list)
    _falhas: dict[str, str] = field(default_factory=dict, repr=False)

    def fecha(self) -> "ResultadoCalibracao":
        """Roda o ajuste e valida; nao levanta excecao: acumula motivos para o veredito."""
        if self.ajuste is not None:
            return self
        try:
            self.ajuste = ajusta(self.amostras)
        except ValueError as exc:
            self.motivos.append(str(exc))
        return self

    def _tenta(self, nome: str, fn):
        """Grandeza derivada que pode nao existir. Slot nomeado: chamada repetida nao duplica motivo."""
        try:
            return fn()
        except ValueError as exc:
            self._falhas[nome] = str(exc)
            return None

    def tau_otimo_s(self) -> float | None:
        self.fecha()
        if self.ajuste is None:
            return None
        return self._tenta("tau", self.ajuste.tau_otimo_s)

    def velocidade_mm_s(self) -> float | None:
        self.fecha()
        if self.ajuste is None:
            return None
        return self._tenta("velocidade", lambda: self.ajuste.velocidade_mm_s(self.distancia_mm))

    def escala_mm_por_px(self) -> float | None:
        self.fecha()
        if self.ajuste is None:
            return None
        return self._tenta("escala", lambda: self.ajuste.escala_mm_por_px(self.distancia_mm))

    def residuo_mm(self) -> float | None:
        self.fecha()
        escala = self.escala_mm_por_px()
        if self.ajuste is None or escala is None:
            return None
        return self.ajuste.residuo_px * escala

    def passagens_com_amostra(self) -> int:
        """Passagens distintas presentes nas amostras. Os quadros de uma rajada sao correlacionados:
        n_amostras alto NAO significa n observacoes independentes, e o relatorio diz os dois."""
        return len({a.passagem for a in self.amostras})

    def aprovadas(self) -> int:
        self.fecha()
        tau = self.tau_otimo_s()
        escala = self.escala_mm_por_px()
        if tau is None or escala is None:
            return 0
        return sum(
            1
            for a in self.amostras
            if abs(a.offset_px * escala) <= self.tolerancia_mm
        )

    def veredito(self) -> tuple[str, list[str]]:
        """PASS quando o ajuste existe, a dispersao cabe na tolerancia e o delay e utilizavel.

        Os motivos sao montados DEPOIS de todas as validacoes: copiar a lista antes perdia a
        razao da reprovacao das grandezas derivadas (defeito encontrado por teste).
        """
        self.fecha()
        if self.ajuste is None:
            return "FAIL", list(dict.fromkeys(self.motivos)) or ["sem ajuste"]

        self._falhas.clear()                       # recalcula do zero: sem acumular entre chamadas
        escala = self.escala_mm_por_px()
        tau = self.tau_otimo_s()
        residuo = self.residuo_mm()

        motivos: list[str] = list(self._falhas.values()) + list(self.motivos)
        if self.ajuste.n < 5:
            motivos.append(f"poucas amostras ({self.ajuste.n}); calibre com mais quadros")
        if self.ajuste.r2 < 0.9:
            motivos.append(f"ajuste fraco (r2={self.ajuste.r2:.3f}); modelo linear nao descreve o ensaio")
        if escala is None and not any("intercepto" in m for m in motivos):
            motivos.append("escala indeterminada")
        if residuo is None:
            motivos.append("residuo indeterminado")
        elif residuo > self.tolerancia_mm:
            motivos.append(
                f"dispersao {residuo:.2f} mm acima da tolerancia {self.tolerancia_mm:.2f} mm"
            )
        if tau is None:
            motivos.append("delay otimo indeterminado")
        elif tau < 0:
            motivos.append("delay otimo negativo: verifique o sinal do offset e a distancia declarada")

        self.motivos = list(dict.fromkeys(motivos))
        return ("PASS" if not self.motivos else "FAIL"), self.motivos

    def para_dict(self) -> dict:
        self.fecha()
        return {
            "distancia_mm": self.distancia_mm,
            "tolerancia_mm": self.tolerancia_mm,
            "n_amostras": len(self.amostras),
            "passagens_com_amostra": self.passagens_com_amostra(),
            "ajuste": asdict(self.ajuste) if self.ajuste else None,
            "tau_otimo_s": self.tau_otimo_s(),
            "velocidade_mm_s": self.velocidade_mm_s(),
            "escala_mm_por_px": self.escala_mm_por_px(),
            "residuo_mm": self.residuo_mm(),
            "aprovadas": self.aprovadas(),
            "veredito": self.veredito()[0],
            "motivos": self.veredito()[1],
        }


def carrega_delay(caminho: "Path | str") -> dict:
    """Le o delay calibrado. Fail-closed: ausente ou ilegivel nao vira default silencioso."""
    p = Path(caminho)
    if not p.exists():
        raise FileNotFoundError(
            f"delay nao calibrado em {p}: rode a calibracao (make calibrar-delay-bancada) antes de capturar"
        )
    dados = json.loads(p.read_text())
    if not isinstance(dados, dict) or "vistas" not in dados:
        raise ValueError(f"{p} sem a chave 'vistas': formato de delay invalido")
    return dados


def tau_da_vista(dados: dict, vista: str) -> float:
    """Atraso (s) de UMA vista. Cada camera tem sua distancia, portanto seu proprio atraso."""
    vistas = dados.get("vistas") or {}
    if vista not in vistas:
        calibradas = ", ".join(sorted(vistas)) or "nenhuma"
        raise KeyError(f"vista {vista!r} nao calibrada (calibradas: {calibradas})")
    tau = (vistas[vista] or {}).get("tau_s")
    if not isinstance(tau, (int, float)) or isinstance(tau, bool) or tau < 0:
        raise ValueError(f"tau_s invalido para a vista {vista!r}: {tau!r}")
    return float(tau)
