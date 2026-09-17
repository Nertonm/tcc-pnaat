"""Reprodução da demonstração sem destruir banco preexistente."""
import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_demo_cria_seis_itens_e_preserva_banco_existente(tmp_path):
    db = tmp_path / "demo" / "hub.db"
    cmd = [sys.executable, str(ROOT / "semear_demo.py"), str(db)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(db) as cx:
        assert cx.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 6
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    second = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    assert second.returncode == 2
    assert "já existe" in second.stderr
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
