# Artefatos de revisão — não liberados para produção

Leia ../RELATORIO-ASTRA-20260911.md antes de usar os STL.

- `orientada-peca.stl` + `orientada-pecaB.stl`: uma de cada para a montagem espelhada estudada.
- `orientada-bracket.stl`, `orientada-clamp.stl`, `orientada-sapata.stl`, `orientada-parafuso.stl`: duas unidades por família no inventário proposto.
- `orientada-JuncaoA/B.stl`: FOLGA ZERO; referência orientada, não imprimir como peça final.
- `orientada-ChavetaA/B.stl`: uma de cada; sem resistência validada.
- `cupom-luva-*` e `cupom-bracket-*`: alternativas de calibração; não constituem folga aprovada.
- O clamp tem origem STL aberta; remalhagem fechada do BREP não encerra esse gate.
- STEP preserva o BREP; STL é uma aproximação triangulada, com volumes registrados.

Reprodução pelo MCP FreeCAD: executar `00-load.py` na GUI e, depois, scripts `01` a `06` em ordem, aguardando a conclusão de cada um. Cada script deve usar `exec(source, {})`. Não executar scripts diferentes num namespace global compartilhado.

`SOURCES.sha256` registra hashes das fontes lidas ao final da sessão; não é uma comparação de hashes antes/depois que não foi feita. `ARTIFACTS.sha256` referencia artefatos gerados, sem entrada autorreferente.
