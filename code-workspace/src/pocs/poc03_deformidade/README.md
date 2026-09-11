# PoC-03: Deformidade lateral

| | |
|---|---|
| **Ideia isolada** | deformidade do corpo sem referencia dimensional nao e medida, e o requisito de deformidade fica sem base observavel |
| **Pergunta** | as vistas laterais tornam a deformidade mensuravel? |
| **Hipotese** | iluminacao lateral com referencia pixel a milimetro torna a deformidade observavel e comparavel |
| **Metodo** | calibrar a relacao pixel a milimetro por posicao fixa; medir o corpo nas vistas laterais; avaliar acuracia e erro dimensional |
| **Criterio de passagem** | meta de acuracia para deformidade (>= 90%) e erro dimensional declarado com a calibracao |
| **Evidencia** | matriz de confusao da deformidade + calibracao documentada + log do ensaio |
| **Limite atual** | nao ha vistas laterais nem calibracao no rig atual; a unica escala disponivel e uma estimativa, nao uma calibracao |
| **Dependencias** | RF-04, RNF-02; RNF-11 e RNF-14 sao expansao (calibracao e precisao em mm) |
| **Codigo** | `medicao.py` |
