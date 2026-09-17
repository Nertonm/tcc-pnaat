---
tags: [type/reference]
aliases: []
lead: "D-24: limiares da tampa: o 2° publicado é de outra grandeza (ângulo do chuck, não tilt da tampa); calibração empírica é obrigatória."
created: 2026-09-11
modified: 2026-09-11
review_status: reviewed
---

# Limiares da tampa: fonte primária ou calibração empírica (D-24)

Data: 2026-09-11. Motivo: D-24 exige que todo limiar de aceitação tenha **fonte primária**
(`arquivo:linha`) ou **validação empírica registrada**. Estado anterior: `tilt_incerto=2,0°`,
`tilt_reprova=4,0°` e `altura_ausente_px=3,0` estavam no código **sem fonte**.

## Varredura declarada (regra 6 do protocolo)

Buscado em: `docs/reference/`, `docs/design/`, `docs/pocs/` (por nome e por conteúdo) e na web
(7 consultas sobre padrão de tampa/PCO 1881, ISBT, inspeção de tampa solta e detecção de tampa torta).
Status: `P` = primária/industrial com vínculo verificável · `S` = secundária/índice · `B` = guia de prática.

## O que existe de número publicado (e por que quase nada transfere)

| Fonte | Número | Status | Transfere para o nosso tilt? |
|---|---|---|---|
| Delta El Nile: *Preform/Closure Defect Manual* (PDF industrial), entrada CRITICAL "Application angle deviation (chuck approach > 2° tilt)", citando Bevcap Application Angle Standards §5.2 e PMMI/OMAC Capping §3.4 | **máx. 2° do vertical no momento do contato de aplicação** | `P` | **NÃO**: é o **ângulo de aproximação do chuck** (máquina), não o tilt final da tampa medido por visão. Grandezas diferentes. |
| Delta El Nile: bandas de referência **PCO 1881 / CSD, enchimento ambiente** | application torque 13-19 in·lbs · **application angle 760°-800°** · removal 5-14 in·lbs · strip > 25 in·lbs · selo ≥ 100 psi | `P` | **NÃO direto**: ângulo de **rotação** da aplicação e torque: exigem o lado da máquina/torquímetro, não visão. |
| Delta El Nile: mesmo manual, "Insufficient application torque (loose caps)" e "PCO 1881: 14 in-lbs minimum" | **14 in·lbs mínimo** de break-torque | `P` | **NÃO**: definição de "frouxa" por torque, não por ângulo. |
| **ISBT**: *Plastic Bottle Closure Qualification Test Manual* (PTC-00019, abr/2023); *Plastic Closure Ovality Guideline* (PTC-00022, dez/2024); *Capping and Inspection Equipment for Glass and Plastic Containers* (PTC-00012, mai/2014) |: | `P` (existência e ementa) | São os documentos normativos do domínio; a ISBT declara que os ensaios avaliam o **sistema de embalagem** e que **fornecedor e engarrafador devem acordar as especificações** → **não há tolerância angular universal publicada** para "tampa torta". |
| MDPI *Eng. Proc.* (2023), *Machine-Vision-Based Plastic Bottle Inspection* | 95% para tampa (ROI + Harris corners + linha de referência entre cantos extremos; **distância comparada com o limiar conhecido da tampa assentada**) | `S` | **É o precedente de MÉTODO**, não de número: o limiar vem de uma **referência de tampa assentada**: exatamente o caminho de calibração empírica. |
| Xie et al. (2017, IEEE ICCC): inspeção de PET por distância entre support ring e tampa | **99%** para tampa solta em PET | `S` | Método (medição de distância com limiar): reforça calibração, não dá o número. |
| Kumchoo & Chiracharit (2018): tampa solta e anel em vidro | **87%** | `S` | Referência de piso de desempenho em vidro. |
| A*STAR (2021): sensor capacitivo de integridade de tampa | detecta uncapped e **tilted**; LOD ~0,11 cm (contato) / 0,23 cm (não-contato) | `S` | Outro princípio físico; útil como ordem de grandeza do deslocamento detectável. |
| lekapackline: guia industrial de problemas de rosqueamento | "a cocked or tilted cap describes its angled position… **the angle alone does not prove the exact thread condition**"; "visible gap or abnormal cap height… is **not** a torque measurement" | `B` | **Sustenta a D-23**: tilt sozinho não conclui; o topo verifica dimensão/assentamento. |

## Veredito para D-24

1. **`tilt_incerto=2,0°` e `tilt_reprova=4,0°` não têm fonte transferível.** O único "2°" publicado é o
   **ângulo de aproximação do chuck**: outra grandeza. Adotá-lo como limite de tilt da tampa repetiria
   o erro do NCC (número de uma medição usado para descrever outra). Ficam como **parâmetros
   provisórios**, e **não** como critério de aceitação.
2. **`altura_ausente_px=3,0` não tem fonte alguma** (nem provisória): é limiar puramente empírico.
3. **Não existe tolerância angular universal** para "tampa mal rosqueada": a própria ISBT condiciona a
   especificação ao **sistema de embalagem acordado** entre fornecedor e engarrafador. Logo, **a única
   rota defensável é a calibração empírica no nosso conjunto**, com o limiar derivado de uma
   **referência de tampa assentada** (precedente MDPI/Xie), registrado com `n`, método e procedência.
4. O que **existe** e pode ser citado como requisito de sistema (não como nosso limiar): janela de
   torque/aplicação PCO 1881 do manual industrial e os manuais ISBT (PTC-00019 / PTC-00022 / PTC-00012).

## Protocolo de calibração (pré-registro, D-24b)

Script: `workspace/scripts/calibrar_limiares_tampa.py` (+ `tests/test_calibrar_limiares_tampa.py`).
Método: varredura determinística de candidatos, escolha pelo **índice de Youden** (sens + espec − 1) com
desempate por maior margem; saída com sensibilidade/especificidade e **limite inferior do IC95**, zona
cinzenta, `n` por classe, hash do CSV de entrada e data.

1. Medir a grandeza (tilt por vista lateral; altura/assentamento pelo topo) em itens rotulados.
2. **Bloco A** (primeira metade, aleatorizada): escolher o limiar e **congelar** (grava `limiares.json`).
3. **Bloco B** (segunda metade): validar o limiar congelado: o número do bloco B é o resultado.
4. Reportar: limiar, sens/espec com LB95, zona cinzenta e sobreposição.
5. Se a **zona cinzenta for larga** (as distribuições se sobrepõem), o veredito honesto é que **tilt
   sozinho não separa** `mal_rosqueada`: e a decisão passa a exigir a segunda lateral e/ou o check
   dimensional do topo (D-23), nunca um limiar apertado para maquiar o resultado.
6. `n` mínimo do script: 20 por classe para emitir limiar; abaixo disso ele **recusa** e reporta quanto falta.

## Consequências imediatas

- Recursos utilizados (números do manual industrial, ISBT, precedentes de método) entram em
  `docs/REFERENCIAS.md` com status `P`/`S`/`B` e a marca de "não transfere" onde for o caso.
- `politica_tampa.py`: os três limiares ficam marcados como **provisórios** até o bloco A da calibração.
- Nenhum relatório da PoC-02 pode citar esses valores como critério atendido antes da calibração.
