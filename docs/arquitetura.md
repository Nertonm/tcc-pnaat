# Arquitetura proposta

## Fluxo do núcleo

```text
evento de presença → captura multi-view (2 laterais + topo)
→ classificação por domínio (tampa nas laterais, corpo nas laterais, check dimensional no topo)
→ fusão por domínio → evento rastreável → registro local → dashboard e alertas
```

A arquitetura é proposta. Ela não comprova compatibilidade de hardware, sincronização, desempenho ou operação industrial.

## Componentes e funções

| Componente | Função prevista | Limite ou expansão |
|---|---|---|
| Sensor de presença + microcontrolador (ESP32) | Marca o evento de observação e inicia a janela de captura. | Sensor alternativo é avaliado na PoC-01 (D-20). |
| Multi-view (2 laterais + topo) | Captura mais de uma vista do item com identificador e timestamp. | Quantidade e posição de vistas são definidas por PoC (D-03). |
| Classificação por domínio | As duas vistas laterais decidem tampa e corpo; a vista de topo é um check dimensional independente (D-23). | Exige dataset e métricas por classe. |
| Fusão por domínio | Combina vistas dentro de cada domínio e preserva discordâncias. Defeito em qualquer domínio reprova o item (D-04). | Não substitui análise humana para casos ambíguos. |
| Nó de observação | Associa captura, localização, timestamp e resultado em evento rastreável. | Hub local e múltiplos nós são expansão. |
| Registro local | Persiste eventos e evita duplicidade por reenvio. | Contrato de persistência é validado na PoC-05. |
| Dashboard e alertas | Apresenta defeito, momento, localização, esteira, nó e evidência. | Não aciona a esteira nem atuação física. |

## Contrato mínimo do evento

Cada evento deve conter:

- `item_id` ou identificador de captura;
- timestamp com fuso;
- origem e localização;
- esteira, quando aplicável;
- vistas disponíveis;
- classe, confiança e qualidade do registro;
- referência ou hash da evidência;
- versão do contrato.

## Expansões controladas

MQTT, hub local, múltiplos nós, integração industrial, atuação física e confirmações mecânicas são extensões. Nenhuma delas deve ser apresentada como implementada ou necessária para validar o núcleo do projeto.

