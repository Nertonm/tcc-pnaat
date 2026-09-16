"""O documento de rastreabilidade cobre TODO requisito declarado (P3-5)."""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "code-workspace/scripts/rastreabilidade.py"


def test_todo_requisito_tem_linha_de_rastreabilidade():
    assert SCRIPT.is_file(), "gerador de rastreabilidade ausente"
    p = subprocess.run([sys.executable, str(SCRIPT), "--conferir"],
                       capture_output=True, text=True, cwd=RAIZ)
    assert p.returncode == 0, p.stdout + p.stderr


def test_documento_gerado_existe_e_tem_tabela():
    doc = RAIZ / "docs/rastreabilidade.md"
    assert doc.is_file(), "docs/rastreabilidade.md ausente: rode o gerador"
    texto = doc.read_text(encoding="utf-8")
    assert "| requisito | titulo | status |" in texto
    assert "sem prova" in texto or "coberto" in texto
