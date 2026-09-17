"""Gate mínimo dos artefatos obrigatórios da Entrega 6.

O teste não tenta avaliar a qualidade da prosa. Ele impede regressões objetivas: remover um
artefato, voltar a deixar o README sem uma etapa exigida ou publicar um diagrama que contradiga os
pinos do firmware deve falhar na suíte normal do produto.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
README = (REPO / "README.md").read_text(encoding="utf-8")
HARDWARE = (REPO / "docs" / "hardware.md").read_text(encoding="utf-8")
ARQUITETURA = (REPO / "docs" / "arquitetura.md").read_text(encoding="utf-8")
ELETRICA = (REPO / "docs" / "diagramas" / "interligacao-eletrica.mmd").read_text(
    encoding="utf-8"
)
FIRMWARE_TRIGGER = (
    REPO / "src-production" / "firmware" / "trigger-node" / "esp" / "main.py"
).read_text(encoding="utf-8")
DOCUMENTOS_OPERACIONAIS = tuple(
    REPO / caminho
    for caminho in (
        "README.md",
        "docs/hardware.md",
        "docs/operacao-pipeline.md",
        "docs/replicacao-ponta-a-ponta.md",
        "src-production/firmware/README.md",
        "src-production/firmware/trigger-node/README.md",
        "src-production/firmware/trigger-node/esp/README.md",
    )
)


def test_codigo_fonte_e_esquematicos_estao_versionados():
    assert (REPO / "src-production" / "api.py").is_file()
    assert (REPO / "ESP32S3-Trigger.zip").is_file()
    assert "flowchart" in ELETRICA


def test_arquitetura_separa_proposta_de_implementada():
    assert "## Arquitetura proposta" in ARQUITETURA
    assert "## Arquitetura implementada" in ARQUITETURA
    assert ARQUITETURA.count("```mermaid") >= 1


def test_readme_cobre_todas_as_etapas_exigidas():
    termos_obrigatorios = (
        "Pré-requisitos",
        "Instalação passo a passo",
        "Configurar a instalação",
        "Ligação elétrica do trigger",
        "Sequência de montagem mecânica",
        "Operar as rotas existentes",
        "Verificação e reprodutibilidade",
    )
    for termo in termos_obrigatorios:
        assert termo in README, f"README sem a etapa obrigatória: {termo}"

    assert "make -C src-production verificar" in README
    assert "/api/health" in README


def test_pinagem_documentada_coincide_com_firmware():
    pino_entrada = re.search(r"^PRESENCE_PIN\s*=\s*(\d+)", FIRMWARE_TRIGGER, re.MULTILINE)
    pino_saida = re.search(r"^CAPTURE_OUT_PIN\s*=\s*(\d+)", FIRMWARE_TRIGGER, re.MULTILINE)
    assert pino_entrada and pino_saida
    assert f"GPIO{pino_entrada.group(1)}" in ELETRICA
    assert f"GPIO{pino_saida.group(1)}" in ELETRICA
    assert f"`GPIO{pino_entrada.group(1)}`" in README
    assert "medir a tensão" in README
    assert "## 2. Pinagem e interfaces" in HARDWARE


def test_documentacao_operacional_nao_manda_executar_arvore_removida():
    """Documentos históricos podem citar PoCs; manuais operacionais não podem depender delas."""
    proibidos = ("cd code-workspace", "src/pocs/", "make simular-poc01")
    for caminho in DOCUMENTOS_OPERACIONAIS:
        conteudo = caminho.read_text(encoding="utf-8")
        for trecho in proibidos:
            assert trecho not in conteudo, f"comando removido em {caminho.relative_to(REPO)}: {trecho}"


def test_topologia_do_trigger_nao_confunde_entrada_local_com_no_dedicado():
    assert "GPIO27" in ELETRICA and "UART/USB do trigger" in ELETRICA
    assert "CMD_TRIG" in ELETRICA
    assert "GPIO13 da ESP32-CAM é somente uma entrada local alternativa" in HARDWARE
