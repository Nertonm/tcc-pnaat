# PoC 06: resiliência observável

- Status: Pendente
- Pergunta binária: falhas de nó, rede, sensor e câmera recuperam sem crash?
- Hipótese: watchdog, fila, debounce e estados de qualidade permitem degradação explícita.
- Métrica: tempo de detecção, recuperação, perdas, duplicações e estado final.
- Go: cada hipótese passa ou gera no-go documentado; sem “não caiu” subjetivo.
- Setup: PoC 05 estável, uma falha por vez, blast radius mínimo.
- Evidência: protocolo antes do teste, logs e decisão.
- Dependências: RF-08/24, RNF-07/08/19, OPS-02..04.
- Resultado: não executado.
