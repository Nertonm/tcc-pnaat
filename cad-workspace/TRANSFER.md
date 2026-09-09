# Registro de transferencia do CAD

Escopo publicado neste namespace: scripts CadQuery, dados G0 de canario e templates, documentacao de requisitos/arquitetura/PoCs, relatorios de referencia e instrucoes de reproducibilidade.

Excluidos por politica: `.git`, `.venv`, `exports/`, bytecode, prompts internos, instrucoes locais de agente e dados brutos.

Estado da verificacao no ambiente de origem:

- `validate_g0.py data/g0/canary.yaml`: PASS.
- `generate_canary.py`: BLOCKED; `cadquery` ausente no ambiente verificado.
- `validate_mesh.py`: BLOCKED; `trimesh` ausente no ambiente verificado.
- sintaxe Python dos scripts copiados: PASS.

Os arquivos CAD e envelopes permanecem candidatos de referencia. Nenhuma dimensao sintetica e uma medicao fisica ou autorizacao de fabricacao.
