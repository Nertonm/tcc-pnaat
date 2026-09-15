from __future__ import annotations
import api
import pytest


def _ctx(tmp_path):
    return {"db": str(tmp_path / "hub.db")}


def test_delay_csi_uses_previous_value_from_rig_not_esp_bridge(monkeypatch, tmp_path):
    rig_calls = []
    def rig(path, timeout=0):
        rig_calls.append(path)
        if path == "/delay-por-camera":
            return {"delay_por_camera_ms": {"csi": 250, "usb": 0, "espcam": 1500}}
        assert path.startswith("/configurar-delay?ms=300&camera=csi"), path
        return {"delay_por_camera_ms": {"csi": 300, "usb": 0, "espcam": 1500}}
    monkeypatch.setattr(api, "_chamar_rig", rig)
    monkeypatch.setattr(api, "_chamar_ponte", lambda path: {"trigger": {"delay_ms": 1500}})
    r = api._rota_rig_delay(_ctx(tmp_path), {"ms": 300, "camera": "csi", "operador": "teste"})
    assert r["anterior_ms"] == 250
    assert r["confirmado"] is True
    assert rig_calls[0] == "/delay-por-camera"


def test_delay_all_is_explicitly_accepted(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "_chamar_ponte", lambda path: {"trigger": {"delay_ms": 900}})
    monkeypatch.setattr(api, "_chamar_rig", lambda path, timeout=0: {"delay_por_camera_ms": {"csi": 900, "usb": 900, "espcam": 900}})
    r = api._rota_rig_delay(_ctx(tmp_path), {"ms": 900, "camera": "todas", "operador": "teste"})
    assert r["camera"] == "todas"
    assert r["confirmado"] is True
