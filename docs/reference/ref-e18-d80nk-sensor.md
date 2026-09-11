# Ref: sensor E18-D80NK (IR difuso, NPN NO): nosso exemplar + datasheet

Ingest em 2026-09-11. Fontes: label do **nosso exemplar** (informado por Nerton) e datasheets de
terceiros. Status por claim: `P` datasheet verificado · `U` informado pelo usuário (nosso hardware) ·
`F` divergente/contraditório · `X` não confirmado.

## Nosso exemplar (o que está fisicamente em mãos)

| Campo | Valor | Status |
|---|---|---|
| Label impresso | **5VDC: 100mA** | `U` |
| Fios | **3**: **bege (= +5V)**, preto (sinal), azul (GND) | `U` (confirmado) |
| Tipo | sensor IR difuso de proximidade, corpo cilíndrico roscado | `U`/`P` |

✅ **Mapeamento do nosso exemplar CONFIRMADO** (informado por Nerton, 2026-09-11):
**bege = +5V** (equivale ao marrom do padrão), **preto = sinal**, **azul = GND**.
O datasheet de referência usa marrom no lugar do bege: em outro lote, **reconfirme por função**
(a cor não é convenção garantida entre fabricantes).

## Dados de datasheet (terceiros: divergências registradas)

| Especificação | Valores encontrados | Status |
|---|---|---|
| Tensão de alimentação | **5 VDC** (Handson, e-Gizmo); variantes de mercado anunciam 5-24 V e 10-30 V | `P` + `F` (variantes) |
| Consumo | **25-100 mA** (Handson); **100 mA** (e-Gizmo, como *load current*); `<25-30 mA` em anúncios de outra variante | `P` + `F` |
| Faixa de detecção | **3 cm a 80 cm**, ajustável por potenciômetro multi-volta | `P` |
| Tipo de saída | **NPN normalmente aberto (open collector)**, 3 fios | `P` |
| Lógica | **1 = sem detecção · 0 = objeto detectado** (ativo em nível BAIXO) | `P` |
| Objeto detectável | "transparente ou opaco" (declaração do fabricante) | `P` |
| Tempo de resposta | **< 2 ms** | `P` |
| Ângulo de detecção | ≤ 15° | `P` |
| Dimensões | Ø 17-18 mm × 45 mm (cabo 45 cm a 1 m) | `P` |
| Temperatura | −25 °C a 55 °C (um datasheet: 70 °C) | `P` + `F` |
| Luz ambiente | incandescente 3000 lx / solar 10000 lx máx. | `P` |

Fontes: Handson Technology *User Guide* (SKU SSR1069); e-Gizmo/Mechanotrix *Technical Manual* Rev 1.0
(modelo E18-D80NK-N); anúncios de variantes (ielectrony, besomi). As divergências são reais entre
lotes/vendedores: por isso o número que vale para o projeto é **o do nosso exemplar + a medição**.

## Consequências para o projeto (acionáveis)

1. **Orçamento de energia**: reservar **≥ 100 mA em 5 V** para o sensor. Alimentar do **rail 5 V**
   (USB da dev board) e **nunca** do pino 3,3 V. Se usar fonte de bancada, limitar corrente
   (~150 mA) no primeiro teste: protege contra inversão de polaridade.
2. **Nível lógico**: a saída é **open collector**. Dois casos possíveis, decididos por medição:
   - módulo **sem** pull-up interno → ligar direto ao GPIO com `PULL_UP` do ESP32 (3,3 V): o nível
     nunca excede 3,3 V ✔;
   - módulo **com** pull-up interno para 5 V → usar divisor (ex.: 2k2 série + 3k3 para GND) ou
     level shifter; **não** ligar direto.
3. **Lógica ativa em baixo confirmada pelo datasheet** (`0 = objeto detectado`): nossa conversão
   `present = (level == 0)` está correta.
4. **PET transparente é o caso difícil** apesar da folha de dados dizer "transparente ou opaco": a
   detecção difusa depende de superfície que devolva IR ao receptor. Testar **garrafa vazia e cheia**
   e registrar: é a evidência que a PoC exige.
5. **Pitfalls**: superfície muito reflexiva ou muito escura altera a distância efetiva; luz ambiente
   acima dos limites do datasheet aumenta falso disparo; o potenciômetro multi-volta exige ajuste
   fino e **registro** do ponto usado.

## Procedimento de identificação dos fios (antes de energizar)

1. **Mapeamento**: `bege = +5V`, `preto = sinal`, `azul = GND` (confirmado para o nosso exemplar).
2. **Fonte com limite de corrente** em 5 V / 150 mA. Ligue bege no +5 V e azul no GND.
   - LED do módulo acende e o consumo fica na faixa de dezenas de mA → polaridade correta.
   - Consumo no limite ou nada acende → **desligue imediatamente** e reconfira o mapeamento.
3. **Confirme o sinal**: multímetro VDC entre **preto** e GND: ~5 V livre, **~0 V com objeto a
   10-30 cm**.
4. Só depois ligue o preto no GPIO (com `PULL_UP`, ou com divisor se a medição do passo 3 mostrar
   que o pino sobe a 5 V).

## Critério de aceitação do componente

- **10 aproximações → 10 detecções** na distância de trabalho escolhida (começar em ~15 cm);
- mesmo resultado com **garrafa cheia** e **vazia** (ou registro explícito da diferença);
- consumo medido dentro do orçamento (≤ ~100 mA);
- distância e ponto do potenciômetro **registrados** (foto/marca no corpo).
