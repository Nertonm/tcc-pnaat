"""Expansao: sincronizacao fisica do rig (trigger, esteira e instante de captura).

O MAPA das PoCs registra `docs/pocs/03-sincronizacao-fisica` como sem codigo
("saiu do nucleo"), e `poc03_*` ja e deformidade lateral no codigo entregue.
Por isso este modulo vive fora da numeracao do nucleo: e a expansao, explicitamente.
"""
from pocs.expansao_sincronizacao.delay import (
    Ajuste,
    Amostra,
    Orcamento,
    ResultadoCalibracao,
    ajusta,
    delay_ideal_s,
    janela_presenca_s,
    ladder,
    offset_mm,
    orcamento,
    velocidade_maxima_mm_s,
    velocidade_maxima_por_presenca,
)

__all__ = [
    "Ajuste", "Amostra", "Orcamento", "ResultadoCalibracao", "ajusta", "delay_ideal_s",
    "janela_presenca_s", "ladder", "offset_mm", "orcamento",
    "velocidade_maxima_mm_s", "velocidade_maxima_por_presenca",
]
