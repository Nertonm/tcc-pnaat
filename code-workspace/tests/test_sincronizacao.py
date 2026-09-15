"""Testes da calibracao trigger -> captura (PoC-03).

Cada teste nomeia o que ele falsifica. Os dois ultimos sao guardas de mutacao: se a
geometria for invertida ou se a velocidade divergir do orcamento, eles FALHAM.
"""
from __future__ import annotations

import math
import random

import pytest

from pocs.expansao_sincronizacao.delay import (
    Amostra,
    ResultadoCalibracao,
    ajusta,
    carrega_delay,
    delay_ideal_s,
    janela_presenca_s,
    ladder,
    offset_mm,
    orcamento,
    tau_da_vista,
    velocidade_maxima_mm_s,
    velocidade_maxima_por_presenca,
)

D = 150.0        # mm, trigger -> centro da ROI
V = 100.0        # mm/s
K = 0.5          # mm/px


def sinteticas(velocidade=V, distancia=D, escala=K, ruido_px=0.0, n=12, semente=1):
    """Amostras coerentes com o modelo: offset_px(tau) = (v*tau - d)/k."""
    rnd = random.Random(semente)
    taus = [0.6 + 0.15 * i for i in range(n)]
    return [
        Amostra(passagem=1, tau_s=t, offset_px=(velocidade * t - distancia) / escala
                + (rnd.gauss(0, ruido_px) if ruido_px else 0.0))
        for t in taus
    ]


def test_offset_e_zero_no_delay_ideal():
    assert offset_mm(V, delay_ideal_s(D, V), D) == pytest.approx(0.0, abs=1e-9)


def test_ajuste_recupera_velocidade_escala_e_delay():
    """A reta de uma rajada entrega v, mm/px e tau* sem encoder."""
    aj = ajusta(sinteticas())
    assert aj.n == 12
    assert aj.r2 == pytest.approx(1.0, abs=1e-6)
    assert aj.escala_mm_por_px(D) == pytest.approx(K, rel=1e-6)
    assert aj.velocidade_mm_s(D) == pytest.approx(V, rel=1e-6)
    assert aj.tau_otimo_s() == pytest.approx(delay_ideal_s(D, V), rel=1e-6)


def test_ajuste_tolera_ruido_de_meio_pixel():
    aj = ajusta(sinteticas(ruido_px=0.5, n=30, semente=7))
    assert aj.velocidade_mm_s(D) == pytest.approx(V, rel=0.05)
    assert aj.tau_otimo_s() == pytest.approx(delay_ideal_s(D, V), rel=0.05)


def test_geometria_invertida_reprova():
    """GUARDA DE MUTACAO: offset com sinal trocado nao pode passar como calibracao valida."""
    invertidas = [Amostra(a.passagem, a.tau_s, -a.offset_px) for a in sinteticas()]
    r = ResultadoCalibracao(distancia_mm=D, tolerancia_mm=2.0, amostras=invertidas)
    veredito, motivos = r.veredito()
    assert veredito == "FAIL"
    assert any("intercepto" in m for m in motivos)


def test_velocidade_incompativel_com_o_orcamento_reprova():
    """GUARDA DE MUTACAO: acima da velocidade maxima a captura nao cabe entre itens."""
    passo = 80.0          # item de 60 mm + 20 mm de folga
    t_vista, rearme, margem = 0.077, 0.05, 0.02
    v_max = velocidade_maxima_mm_s(3, t_vista, rearme, passo, margem)
    assert v_max == pytest.approx(passo / (3 * t_vista + rearme + margem), rel=1e-9)
    assert orcamento(3, t_vista, rearme, passo, v_max, margem).cabendo is True
    assert orcamento(3, t_vista, rearme, passo, v_max * 1.05, margem).cabendo is False


def test_velocidade_maxima_e_o_minimo_entre_os_limites():
    """O teto operacional e o menor entre o orcamento de captura e a janela de presenca."""
    v_orcamento = velocidade_maxima_mm_s(3, 0.077, 0.05, 80.0, 0.02)
    assert v_orcamento == pytest.approx(80.0 / 0.301, rel=1e-6)          # 265,8 mm/s
    # presenca folgada (exige 20 ms): o teto vem do orcamento de captura
    assert min(v_orcamento, velocidade_maxima_por_presenca(60.0, 0.02)) == pytest.approx(v_orcamento)
    # debounce apertado (exige 300 ms de presenca estavel): agora a presenca manda
    v_presenca = velocidade_maxima_por_presenca(60.0, 0.30)
    assert v_presenca == pytest.approx(200.0)
    assert min(v_orcamento, v_presenca) == pytest.approx(v_presenca)


def test_janela_de_presenca_cai_com_a_velocidade():
    assert janela_presenca_s(60.0, 100.0) == pytest.approx(0.6)
    assert janela_presenca_s(60.0, 200.0) == pytest.approx(0.3)


def test_ladder_cobre_a_faixa_pedida():
    faixa = ladder(1.5, 0.5, 5)
    assert faixa[0] == pytest.approx(1.0)
    assert faixa[-1] == pytest.approx(2.0)
    assert len(faixa) == 5
    assert all(b > a for a, b in zip(faixa, faixa[1:]))


def test_veredito_pass_com_dispersao_dentro_da_tolerancia():
    r = ResultadoCalibracao(distancia_mm=D, tolerancia_mm=2.0, amostras=sinteticas(ruido_px=1.0, n=20))
    veredito, motivos = r.veredito()
    assert veredito == "PASS", motivos
    assert r.aprovadas() > 0


def test_veredito_fail_quando_a_dispersao_estoura_a_tolerancia():
    r = ResultadoCalibracao(distancia_mm=D, tolerancia_mm=0.5, amostras=sinteticas(ruido_px=6.0, n=20))
    veredito, motivos = r.veredito()
    assert veredito == "FAIL"
    assert any("dispersao" in m for m in motivos)


def test_ajuste_recusa_entrada_degenerada():
    with pytest.raises(ValueError):
        ajusta([Amostra(1, 1.0, 0.0), Amostra(1, 1.0, 1.0)])          # < 3 amostras
    repetidas = [Amostra(1, 1.0, float(i)) for i in range(4)]          # tau sem variancia
    with pytest.raises(ValueError):
        ajusta(repetidas)


def test_tau_otimo_do_ajuste_bate_com_a_formula_fechada():
    aj = ajusta(sinteticas(ruido_px=0.2, n=25, semente=3))
    assert math.isclose(aj.tau_otimo_s(), D / V, rel_tol=0.02)


def test_contagem_separa_amostras_de_passagens():
    """Quadros de uma rajada sao correlacionados: 12 amostras em 3 passagens nao sao 12 independentes."""
    amostras = [Amostra(passagem=p, tau_s=0.1 * i, offset_px=float(i))
                for p in (1, 2, 3) for i in range(1, 5)]
    r = ResultadoCalibracao(distancia_mm=D, tolerancia_mm=2.0, amostras=amostras)
    assert len(r.amostras) == 12
    assert r.passagens_com_amostra() == 3
    assert r.para_dict()["passagens_com_amostra"] == 3


def test_delay_do_arquivo_e_fail_closed(tmp_path):
    """O consumidor do delay nao pode inventar default: ausente/invalido tem de estourar."""
    with pytest.raises(FileNotFoundError):
        carrega_delay(tmp_path / "nao-existe.json")

    sem_vistas = tmp_path / "sem-vistas.json"
    sem_vistas.write_text('{"tau_s": 1.0}')
    with pytest.raises(ValueError):
        carrega_delay(sem_vistas)

    bom = tmp_path / "delay.json"
    bom.write_text('{"schema": "delay-trigger.v1", "vistas": {"topo": {"tau_s": 1.5}}}')
    dados = carrega_delay(bom)
    assert tau_da_vista(dados, "topo") == pytest.approx(1.5)

    with pytest.raises(KeyError):                      # vista nao calibrada nao vira zero
        tau_da_vista(dados, "lateral1")

    bom.write_text('{"vistas": {"topo": {"tau_s": -1}}}')   # tau negativo e erro de ensaio
    with pytest.raises(ValueError):
        tau_da_vista(carrega_delay(bom), "topo")
