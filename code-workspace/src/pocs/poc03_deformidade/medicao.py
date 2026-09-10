"""PoC-03: medida dimensional a partir das vistas laterais (pixel->mm)."""
from __future__ import annotations


def calibrar(pixels: float, milimetros: float) -> float:
    if pixels <= 0:
        raise ValueError("pixels deve ser > 0")
    return milimetros / pixels


def medir(pixels: float, fator_mm_por_px: float) -> float:
    return round(pixels * fator_mm_por_px, 4)


def dentro_tolerancia(medida: float, referencia: float, tolerancia: float = 0.5) -> bool:
    return abs(medida - referencia) <= tolerancia
