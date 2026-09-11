# PoC-07: Dashboard e visibilidade

| | |
|---|---|
| **Ideia isolada** | sem consulta rastreavel ate a evidencia, o dado coletado nao serve a operacao nem a manutencao |
| **Pergunta** | a equipe localiza defeito, momento, esteira e evidencia? |
| **Hipotese** | consulta por defeito, momento, posicao e no, com acesso a evidencia, torna o evento utilizavel |
| **Metodo** | consultar os eventos do ensaio por classe e periodo e percorrer o caminho ate a imagem correspondente |
| **Criterio de passagem** | todo evento do ensaio e consultavel por defeito, momento, posicao, no e evidencia |
| **Evidencia** | dashboard do ensaio + consulta do evento + caminho ate a imagem |
| **Limite atual** | o dashboard atual le o resultado do processamento e nao o registro, e ainda nao ha notificacao |
| **Dependencias** | RF-09, RNF-12; PoC-05 como fonte dos eventos |
| **Codigo** | `dashboard.py` |
