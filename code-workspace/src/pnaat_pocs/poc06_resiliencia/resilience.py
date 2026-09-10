"""PoC-06: retry contado e alerta em falha de persistencia local.

Replay contar as tentativas; em esgotamento, sinalizar alerta (estado de qualidade falha).
"""
from __future__ import annotations

import time
from typing import Callable

from ..events import ObservationEvent


def retry_until_persist(
    persist: Callable[[ObservationEvent], str],
    event: ObservationEvent,
    max_retries: int = 3,
    delay_s: float = 0.0,
) -> dict:
    attempts = 0
    while attempts <= max_retries:
        attempts += 1
        try:
            outcome = persist(event)
        except Exception:
            outcome = "error"
        if outcome in ("stored", "exists"):
            return {"persisted": True, "attempts": attempts, "alert": False, "quality": "ok"}
        if delay_s:
            time.sleep(delay_s)
    return {"persisted": False, "attempts": attempts, "alert": True, "quality": "falha"}
