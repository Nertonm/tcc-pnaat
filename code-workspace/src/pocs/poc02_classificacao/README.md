# PoC-02: Classificacao de tampa

| | |
|---|---|
| **Ideia isolada** | se as vistas nao separarem tampa ausente de tampa mal rosqueada, os requisitos de classificacao de tampa caem e o resto do sistema so registra o que nao sabe decidir |
| **Pergunta** | as vistas disponiveis separam tampa ausente e mal rosqueada? |
| **Hipotese** | a geometria da tampa (contorno, tilt e arco visivel) separa os casos sem depender de dados de defeito; a vista de topo serve de verificacao dimensional |
| **Metodo** | medir tilt, altura e arco visivel por vista; decidir por limiar calibrado; avaliar por classe com intervalo de confianca e taxa de falso positivo |
| **Criterio de passagem** | ausente >= 95% e mal rosqueada >= 90%, com IC; falso positivo <= 2% (ausente) e <= 5% (demais) |
| **Evidencia** | matriz de confusao por classe com n e IC, mais a imagem anotada de cada item com a medida que discriminou |
| **Limite atual** | depende de imagens das duas vistas laterais e da vista de topo, que ainda nao existem; sem itens defeituosos no conjunto nao ha matriz; os limiares de tilt e altura seguem provisorios ate fonte ou calibracao |
| **Dependencias** | RF-02, RF-03, RNF-02, RNF-03; D-23 (duas laterais decidem, topo verifica), D-24 (limiar precisa de fonte ou calibracao), D-25 (metrica), D-26 (fronteira e inconclusivo) |
| **Codigo** | `politica_tampa.py`, `classificacao.py`, `scripts/avaliar_poc02.py`, `scripts/calibrar_limiares_tampa.py` |
