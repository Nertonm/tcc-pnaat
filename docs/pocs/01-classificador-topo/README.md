# PoC 01: classificador de topo

- Status: Proposto
- Pergunta binária: tampa ausente e mal rosqueada atingem os limiares preliminares?
- Hipótese: iluminação e enquadramento fixos permitem separar as classes no item parado.
- Métrica: acurácia por classe, matriz de confusão e IC.
- Go: acurácia preliminar ≥90%. No-go: abaixo do limiar ou dataset sem separação.
- Setup: câmera topo, iluminação definida, dataset documentado, modelo e versão.
- Casos: OK, ausente, mal rosqueada e fronteira.
- Evidência: manifest, matriz, configuração e log.
- Dependências: RF-02, RF-03, RNF-02, RNF-03, ML-01..03.
- Resultado esperado: registrar a métrica, a decisão e a evidência desta PoC.
