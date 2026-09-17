"""Dependencia importada tem de estar declarada no pyproject (achado P2-8).

Regra: import de terceiro em modulo de runtime precisa aparecer em `dependencies` ou em um extra.
Import tardio (dentro de funcao) conta: o caminho quebra na chamada, nao na instalacao.
"""

import ast
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PYPROJECT = RAIZ / "pyproject.toml"

#: modulo importado -> nome de distribuicao (o que aparece no pyproject)
DISTRIBUICAO = {
    "PIL": "pillow",
    "cv2": "opencv-python-headless",
    "numpy": "numpy",
    "scipy": "scipy",
    "torch": "torch",
    "torchvision": "torchvision",
    "ultralytics": "ultralytics",
    "sklearn": "scikit-learn",
}
#: terceiros que podem faltar sem quebrar o runtime instalado (extra obrigatorio se usados)
FONTES = sorted(p for p in RAIZ.glob("*.py"))


def _declaradas() -> set[str]:
    dado = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    nomes = set()
    for bruto in dado["project"].get("dependencies", []):
        nomes.add(bruto.split("==")[0].split(">")[0].split("[")[0].strip().lower())
    for extra in dado["project"].get("optional-dependencies", {}).values():
        for bruto in extra:
            nomes.add(bruto.split("==")[0].split(">")[0].split("[")[0].strip().lower())
    return nomes


def _importados(caminho: Path) -> set[str]:
    raiz = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    achados = set()
    for no in ast.walk(raiz):
        if isinstance(no, ast.Import):
            achados.update(apelido.name.split(".")[0] for apelido in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            achados.add(no.module.split(".")[0])
    return achados


def test_todo_terceiro_importado_esta_declarado():
    declaradas = _declaradas()
    faltando: dict[str, str] = {}
    for caminho in FONTES:
        for modulo in _importados(caminho):
            distribuicao = DISTRIBUICAO.get(modulo)
            if distribuicao and distribuicao not in declaradas:
                faltando[caminho.name] = distribuicao
    assert not faltando, f"nao declarado no pyproject: {faltando}"


def test_leitura_declara_pil_e_scipy():
    declaradas = _declaradas()
    assert "pillow" in declaradas and "scipy" in declaradas
