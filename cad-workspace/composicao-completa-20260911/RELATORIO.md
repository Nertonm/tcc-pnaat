# Composição completa do pórtico — estado real

Data: 2026-09-11 · Diretório: `composicao-completa-20260911/`
**Status: montagem VISUAL. Case e mount foram posicionados à mão, NÃO verificados.**

## O que está na composição (18 objetos)

```
        TRAVESSA (600 mm)  +  JUNÇÃO A/B nos dois cantos
   ┌──────────────────────────────────────────────────┐
   │  [MOUNT CÂMERA CM3]              [CASE PI5 DIN]  │
   └──────┬───────────────────────────────────┬───────┘
          │ montante A                        │ montante B
          │ (450 mm)                          │ (450 mm)
     ┌────┴────┐                          ┌────┴────┐
     │ GRIP A  │  grampo+peça+encaixe     │ GRIP B  │
     └─────────┘                          └─────────┘
```

| parte | peça | origem | estado |
|---|---|---|---|
| montantes (×2) | trilho TS35, 450 mm | seção medida do STEP Winford | ✓ verificado no `portico-montantes` |
| travessa | trilho TS35, 600 mm | idem | ✓ verificado |
| junções (×2) | luva de canto | peça nova | ✓ 11/11 gates, 5/5 mutações |
| grips (×2) | G-clamp + peça 2 plataformas + encaixe | clamp do usuário + peça nova | ✓ contatos medidos |
| **mount câmera** | `camera-mount-din-v6` | validado contra CM3 completo (0,0434 mm³) | ⚠ **posicionado à mão** |
| **case Pi5** | Dyalec `thing:6335141` | STL de terceiro | ⚠ **posicionada à mão** |

## A acoplagem dos DOIS lados

Os dois montantes têm o **mesmo conjunto de grip** (grampo → peça → encaixe), um em
cada lado da esteira. No build validado a segunda montagem é uma **translação rígida
de +400 mm em X** — mesma orientação, lado oposto.

**Isso é uma premissa, não uma medição:** a orientação dela em relação aos **dois
lados reais** da esteira nunca foi validada (a máquina não foi medida). Se os dois
lados tiverem geometria diferente, o grip de um deles precisa ser revisto.

## O QUE NÃO ESTÁ VERIFICADO — e é importante

### 1. O mount da câmera não foi testado no trilho
Ele foi **rotacionado 90° em Z e colocado** sobre o montante A por posição
aproximada. **Nenhuma medição de contato ou colisão foi feita** entre o clip do
mount e o trilho do montante. O mount está validado **contra a câmera** (0,0434 mm³),
não contra o trilho.

### 2. A case do Pi não foi testada no trilho
Mesma situação: os dois STLs foram posicionados no montante B **visualmente**. Não
há medição de engate, folga ou interferência.

### 3. As alturas não foram decididas por requisito
O mount e a case foram colocados "no alto" e "no meio". **A altura do mount depende
do campo de visão**, e a posição do Pi depende do **alcance do cabo FPC de 200 mm** —
nenhum dos dois foi calculado aqui.

### 4. O caminho do FPC não foi traçado
A restrição de 200 mm do cabo (pi → câmera) **não foi verificada** nesta composição.

## O que fazer antes de tratar isto como projeto

1. **Verificar o encaixe** mount↔trilho e case↔trilho com os mesmos checks usados na
   junção (contato de face por eixo + colisão + teste negativo).
2. **Fixar as alturas por requisito**: FOV da câmera e alcance do FPC.
3. **Traçar o caminho do FPC** e provar que 200 mm alcança.
4. **Medir a esteira** — ainda é o bloqueio raiz.

## Arquivos
```
completa-iso.png · completa-frente.png · completa-lado.png
(cena aberta no FreeCAD do <host> como 'Completa', 18 objetos)
```

Nenhum commit, push ou merge. Nada impresso.
