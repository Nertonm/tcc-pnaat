# Workspace CAD

Pipeline mecânico do TCC PNAAT, separado da documentação normativa em `../docs/`.

- `cad/`: fontes CadQuery/FreeCAD e referências geométricas (as nossas).
- `data/g0/`: canários e templates de coleta, não medições físicas.
- o design mecânico canônico está em `../docs/design/grip-extensivel.md`.
- `reports/`: relatórios de referência com estado de evidência explícito.
- `scripts/`: validadores e geradores.
- `references/`: **obras de terceiros**, somente leitura; ver créditos abaixo.
- `exports/`: saída gerada (não versionada).

Os envelopes atuais são `reference_only`, `measured=false` e `fabrication_allowed=false` quando
indicado pelo relatório.

## Referências de terceiros: crédito e licenças

Este workspace usa peças de terceiros como **referência de projeto**, não só como inspiração: parte
do encaixe DIN deriva de obras com licença. O crédito completo, com autor, fonte, licença e o
estado de verificação de cada uma, está em **[`NOTICE.md`](NOTICE.md)**.

Resumo dos titulares: **Diyalec** (CC BY-SA 4.0) · **ADSRMedia** (CC BY-NC-SA 4.0) · **Dweller**
(CC BY-SA) · **G-Clamp fully printable / joehann** e o *G-Clamp Tripod* (CC BY-NC-SA) · **Shroamer**
(licença não verificada na fonte) · **herr_brain** · **Qwen** (Apache-2.0) · **Raspberry Pi
Foundation**. As fontes de pesquisa consultadas sem download estão listadas em
`reports/DEEP-RESEARCH-PI5-CAMERA-GRIP-R01.md`.

Três consequências que precisam estar à vista:

1. **Share-alike: o clip DIN é referência, não peça.** O clip do **DIN Rail Bracket Redux**
   (herr_brain, Printables `472505`) foi **consultado**, e a montagem DIN acabou **bloqueada**; a
   iteração viva (`iteracoes/camera-lateral-p5v04a-20260913T223424Z`) traz `REPORT-BLOCKED.md`: *"BLOQUEADO -
   montagem DIN não implementada"*. As 12 tentativas de `din-case` estão em `versoes-descartadas/`,
   todas com veredito (`REPROVADO`/`SUPERADO`/`DESCARTADO`). **O CAD entregue não herda o copyleft.**
   Se alguém reusar o artefato descartado `exports/concepts/optical-rig-r05/camera-mount-din-v6.step`,
   a obrigação vale para ele, isoladamente.

2. **Não comercial.** O bracket M6 e o standoff 2020 são NC. Acadêmico está coberto; comercial não.
3. **Obra derivada.** `build_base.py` funde o bracket M6 na nossa peça; a peça é obra derivada e
   isso precisa constar em qualquer entrega.

**A licença do CAD próprio ainda não foi decidida**, e a decisão depende do item 1.

## Onde fica cada coisa

    cad/                     FONTE CadQuery (.py). Nenhum STL/STEP aqui; conferido: 0 arquivos 3D.
    exports/                 SAIDA gerada de 3D (265 arquivos). Nao versionado.
    scripts/                 geradores e validadores que produzem exports/.
    <nome>-AAAAMMDD[T...]Z/  ITERACAO historica autocontida (~19 diretorios, 306 arquivos 3D).
                             Nao mexer: cada uma e um retrato fechado daquele dia.
    references/freecad/      referencia NOSSA metodo (versionada).
    reports/                 relatorios de pesquisa, com grau de evidencia explicito.
    NOTICE.md                credito e licencas das obras de terceiros.

**As obras de terceiros saíram do repositório** (eram 280 MB / 1327 arquivos, 0 rastreados): ficam
em `tcc-pnaat/_fora-do-repo/references-vendor/`. O que ficou aqui é o crédito
(`NOTICE.md`); a obrigação de atribuição é sobre declarar a autoria e a licença, não sobre guardar
o arquivo de terceiro dentro do nosso versionamento.

Motivo de a separação ser assim e não outra: as 306 peças de 3D estão em diretórios datados que são
**iterações históricas fechadas**; movê-las quebraria o retrato de cada dia. E os 265 de `exports/`
já estão no diretório de saída designado. Ou seja, a separação fonte↔saída já valia; o que faltava
era estar escrita.
