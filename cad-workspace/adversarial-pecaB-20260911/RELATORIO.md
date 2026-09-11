# Rodada adversarial — peça de 2 plataformas + encaixe separado

Data: 2026-09-11 · Diretório: `adversarial-pecaB-20260911/`
Status: **checador validado (4/4 mutações) · peça NÃO aprovada para impressão**

## 1. O que foi testado

A peça de duas plataformas (caminho B) e o **encaixe separado** que pode ser
montado em qualquer das duas plataformas.

| peça | sólidos | válido | volume |
|---|---|---|---|
| PECA (2 plataformas, sem encaixe fundido) | 1 | sim | 11 522,2 mm³ |
| ENCAIXE (separado) | 1 | sim | 11 490,7 mm³ |

## 2. Contatos medidos (método corrigido) e por eixo

| par | área de contato | eixos |
|---|---|---|
| clamp × peça | 881,009 mm² | X e Y |
| **encaixe × peça** | **354,509 mm²** | Y (assentamento) |
| trilho × encaixe | 45,520 mm² | Y (topo da seção) |

## 3. A rodada derrubou TRÊS coisas — todas minhas

### 3.1 O medidor de contato era cego (v1)
`face.common(face)` retorna **vazio** para faces coplanares com normais opostas.
Por isso o contato encaixe×peça media **0,000** e o defeito passou como "ok".
**Correção:** área por penetração calibrada (penetra 0,02 mm e divide o volume).
**Auto-teste do medidor:** dois cubos de 20 mm com face comum → **400,000 mm²**
(exato); separados 2 mm → 0,000.

### 3.2 O check de coaxialidade usava `CenterOfMass` (v2)
O centro de massa de faces **parciais** não é o centro do furo → lia desvio de
0,06/0,07 mm em furos corretos, e **reprovava a própria referência**.
**Correção:** usar o **eixo do cilindro** (`Surface.Center` + `Surface.Axis`).

### 3.3 Duas mutações estavam mal construídas (v3)
- M2 deslocava o corpo mas cortava os furos em coordenada **absoluta** — a mutação
  não era real (a peça continuava com os furos no lugar).
- M4 removia material em vez de **dividir** a peça (resultava em 1 sólido).

**Lição:** um check que reprova o caso bom é tão inútil quanto um que aprova o
caso ruim. Toda bateria precisa da **referência** (tem de passar) e das
**mutações** (têm de falhar) — senão é teatro.

## 4. Bateria final (v4) — o que ficou provado

| caso | área | coaxial | sólidos | veredito |
|---|---|---|---|---|
| **REFERÊNCIA** | 354,509 | True | True | **PASSA** ✓ |
| M1 encaixe sem os furos | 354,509 | **False** | True | FALHA ✓ |
| M2 furo deslocado (acompanha o corpo) | 355,671 | **False** | True | FALHA ✓ |
| M3 encaixe afastado 0,3 mm | **0,000** | True | True | FALHA ✓ |
| M4 peça partida em 2 sólidos | 334,000 | True | **False** | FALHA ✓ |

```
referencia passa          : True
mutacoes detectadas       : 4/4
```
Cada mutação é pega pelo check **certo**, e a referência não é reprovada.

## 5. O achado de projeto que a rodada consolidou

```
CLAMP 0° (boca horizontal)      plataforma H → CIMA    → funciona ✓
CLAMP 90° em Z (boca p/ cima)   plataforma H → lado
                                plataforma V → BAIXO   → nenhuma serve ✗
```

Quando o clamp gira 90°, as duas plataformas **trocam de papel** (a que era
lateral fica horizontal) — mas a que fica horizontal **aponta para baixo**.
O furo lateral **aponta** para cima, mas está numa face cuja normal aponta para
baixo: o encaixe cairia sob o clamp.

**Portanto:** a peça de duas plataformas resolve o caso em que o clamp **não
gira**. Ela não substitui um clamp que precise girar.

**O que realmente limita a versatilidade é o clamp**, não a peça:
- mordente de ~10 mm → a esteira tem de ter borda dessa ordem
- boca única em +X → a superfície tem de ser alcançável nesse eixo

## 6. O que isto NÃO é

- Não é aprovação para impressão. Nenhuma tolerância de impressão foi modelada
  (as canaletas seguem a fêmea exata do trilho).
- Nenhum cálculo de carga, fluência, fadiga ou flambagem.
- A seção real da esteira continua **nunca medida**.
- O mount DIN do Raspberry Pi e o mount da câmera **ainda não foram integrados**
  ao pórtico (o `camera-mount-din-v6` está validado, mas solto).

## 7. Arquivos
```
adv4.py           checador final (referencia + 4 mutacoes) — reproduzível
medidor.py        auto-teste do medidor (400,000 mm²)
gap.py            diagnostico do gap que revelou o ponto cego
```

Nenhum commit, push ou merge. Nada foi impresso.
