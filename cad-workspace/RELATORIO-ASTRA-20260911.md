# Relatório Astra — grip PNAAT — 2026-09-11

**Veredito: interface geométrica peça↔bracket reproduzida; lote NÃO liberado para impressão final.** Foram produzidos STEP/STL orientados para revisão e dois tipos de cupom, cada qual em três variantes. Resistência, fixadores reais, ajuste físico, integridade da origem do clamp e configuração final das luvas continuam bloqueados. Nenhum original foi alterado e nenhum comando de escrita Git foi executado.

## 1. Evidência e reprodução

Medições no FreeCAD 1.1.1 pelo MCP `qwen-mm-plugins-freecad`, com sólidos reais carregados dos STEP/BREP indicados. Diretório de evidência: [validacao-astra-20260911](validacao-astra-20260911/). A cena de inspeção é `interface-auditada.FCStd`, acompanhada de `interface-isometrica.png`.

Execute `00-load.py` no thread GUI via MCP `execute_code`. Depois execute os scripts `01-interface.py` a `06-additional.py`, em ordem, cada um com namespace próprio:

```python
exec(open('/home/<usuario>/tcc-pnaat/github/cad-workspace/validacao-astra-20260911/00-load.py').read(), {})
# Aguardar cada rodada terminar antes da próxima:
exec(open('/home/<usuario>/tcc-pnaat/github/cad-workspace/validacao-astra-20260911/01-interface.py').read(), {})
```

As rodadas geométricas podem usar `execute_code_async`, pois operam em cópias de shapes, sem alterar documentos. Verifique a conclusão pelo JSON correspondente; ausência de JSON não significa sucesso. Os scripts 02–06 seguem o mesmo comando, mudando o nome. Os JSON preservam valores completos; as tabelas abaixo arredondam. Os parâmetros de cupons e envelopes são **propostas de projeto**, não dimensões medidas de hardware comprado.

O medidor lê `common.Volume` diretamente, registra topologia e não converte ausência de sólidos em volume zero. No script 01, interseção inválida, volume não finito ou volume sem sólidos geram erro. Os controles usam caixas apenas como padrões de medição; nenhuma caixa substitui uma peça real. As diferenças de volume dos cortes são verificadas contra sólidos válidos nas rodadas correspondentes.

**Falhas de execução registradas:** a primeira chamada `get_objects` com nome vazio não encontrou documento; `list_documents` permitiu consultar `portico_montantes`. O primeiro script de overhang tentou acessar uma coordenada de tupla como `.z`; foi corrigido para `[2]`. Uma execução assíncrona posterior compartilhou variáveis globais e falhou com `KeyError`; a rodada inteira de orientações foi repetida com namespace isolado. Os arquivos de erro permanecem como histórico, não como medições. A tentativa inicial de visualização não importava `FreeCADGui`; foi corrigida, e a cena salva/inspecionada. O sandbox de shell falhou na inicialização em `.git`; as operações locais autorizadas foram realizadas com a escalada aprovada. Nada disso foi tratado como colisão zero.

## 2. Gates de interface

Fonte: `01-interface.py → interface.json`; lado B da adaptadora e peça×trilho: `06-additional.py → additional.json`. Volume em mm³, área em mm² e distância em mm.

| Gate | Resultado nominal | Controle positivo | Controle negativo | Veredito |
|---|---:|---:|---:|---|
| Medidor de volume: cubos | — | 500,000000 | 0,000000; distância 490 | PASS |
| Medidor de contato: faces de cubos | — | 100,000000 | 0,000000 | PASS |
| Peça isolada × bracket, SEM transformação | colisão 9854,226958 | auto-interseção 22647,902836 | 0,000000 | FAIL de montagem |
| Peça posicionada × bracket A | colisão 0,000000; distância 0 | deslocar peça +1 Z: 868,092385 | peça −500 Z: 0,000000 | PASS geométrico |
| Contato peça × bracket A | 791,664691 | padrão coplanar 100,000000 | afastar bracket: 0,000000 | PASS |
| Peça × bracket B espelhados | colisão 0,000000; contato 791,664691 | +1 Z: 868,092385 | −500 Z: 0,000000 | PASS geométrico; controle de contato do script 01 |
| Bracket × MontanteA | colisão 0,000000; distância 0 | bracket +3 Y: 137,304423 | +500 Y: 0,000000; distância 29,5 | PASS |
| Bracket × MontanteB | colisão 0,000000; distância 0 | bracket +3 Y: 137,304423 | +500 Y: 0,000000; distância 29,5 | PASS |
| Peça posicionada × MontanteA | 0,000000 | auto-interseção 22647,902836 | +500 X: 0,000000 | PASS apenas desse par |
| Luva A × trilho nominal | 0,000000; distância 0 | trilho +0,002 X: 1,185842 | +500 X: 0,000000 | FAIL de folga para fabricação |
| Luva B × trilho nominal | 0,000000; distância 0 | trilho +0,002 X: 1,185842 | +500 X: 0,000000 | FAIL de folga para fabricação |

**Datum indispensável:** a peça isolada deve receber translação `(0; +0,001999; −11,5)` para reproduzir `conjunto-fechado.step`. O assento local Z=19,5 passa a Z=8,0 na montagem. Os números do dossiê são reproduzidos nessa montagem; não são verdadeiros para os dois STEP isolados simplesmente importados sem placement. O centro do furo novo local Y=85,4 passa a Y=85,401999, coincidente com o eixo do bracket.

A vertical foi confirmada antes das rotações: o `MontanteA` mede **35 × 450 × 7,5 em X/Y/Z**, por `Shape.BoundBox` na rodada 01; controles de caixa acima. Logo o eixo longitudinal do montante é Y. Isso é confirmação do modelo, não levantamento da máquina.

Também reconstruí o bracket a partir do BREP vendor: `rotate(V(),V(0,0,1),90)`, seguido de `translate(V(railBB.Center.x-bb.Center.x, railBB.YMin+5.5-bb.YMax, 8-bb.ZMin))`. A soma `rebuilt.cut(delivered).Volume + delivered.cut(rebuilt).Volume` foi **0,000000**; sólido válido e único. Controles da mesma rodada: cubo consigo **1000,000000**, cubo distante **0,000000** (`vendor-rebuild.json`).

**Divergência com a checklist v2:** reproduzi o 1,185842 em +0,002 X do pedido, não os 29,646040 que a v2 atribui ao mesmo deslocamento. Não ajustei o resultado. A evidência desta rodada usa o objeto MontanteA/JuncaoA do arquivo identificado pelo carregador; a causa do número da v2 não foi demonstrada. Os valores da v2 não substituem a rodada atual.

O `repro-montagem.py` anterior não foi executado: `build_peca()` reconstrói uma peça de caixas e seu export sobrescreve arquivos da composição. Essa rotina não reproduz a peça corrigida oficial. Não interpretei o PASS da interface como PASS do grip completo com clamp ou de todos os pares do pórtico.

## 3. Furo, rebaixo e fixação

Fonte: `03-detail.py → detail.json`, `05-exports.py → exports.json`, confirmação de raios em `06-additional.py`. Controles do script 03: interseção positiva **1000 mm³**, negativa **0**; linha atravessando cubo **Z=0..10**, linha distante sem segmentos. Script 06 repete controle linear: **10 mm / 0 mm**.

| Geometria | Volume mm³ |
|---|---:|
| Original preservada | 22762,884649 |
| Só rebaixo | 22746,077410 |
| Rebaixo + furo | 22647,902836 |
| Removido pelo rebaixo | 16,807239 |
| Removido pelo furo | 98,174574 |

**Onde está o material do furo:** o cilindro Ø6,35 remove apenas **Z=5..8,1**, em X=−33,675..−27,325 e Y=82,225..88,575. A membrana atravessada tem **3,1 mm**. Na montagem, ela está em **Z=−6,5..−3,4**. Acima já existe um furo/rebaixo herdado; não há coluna maciça até o plano de assento. A linha no eixo está vazia depois da perfuração. A linha a +3,18 mm em X encontra material Z=5..8,1; a +3,3 mm encontra Z=5..12; a +6 mm encontra Z=5..19,5. As outras direções cardeais amostradas constam no JSON.

**Aguenta a tração? NÃO DETERMINADO.** Espessura e contato não fornecem carga admissível. Faltam força de uso, momento, pré-aperto do M6, propriedades da impressão e ensaio de arrancamento/fluência. Não foi realizado FEM nem adotada resistência genérica do PETG para aprovar o conjunto.

**Rebaixo:** a caixa de corte proposta no dossiê tem pegada 39,5 × 26,5, mas o material efetivamente removido ocupa somente X=−50,25..−10,75, Y=72,15..73,000999, Z=19,5..20. Não foram retirados 0,5 mm de toda a pegada. Na amostra mais crítica sobre o furo transversal central, X=−30,5/Y=72,5, os segmentos são Z=0..6,825 e Z=13,175..19,5: a cobertura superior remanescente é **6,325 mm**. Sobre os furos menores amostrados, a cobertura é **7,8 mm**. Essas seções não mostram uma parede fina criada pelo rebaixo. **Não equivalem a um mapa global de espessura mínima**, e esse gate permanece parcial; arestas de chanfro não devem ser confundidas com espessura estrutural de parede.

**Alternativa recomendada para detalhamento: M6 passante, cabeça no alojamento do bracket e arruela + porca metálica acessíveis por baixo da adaptadora.** Manter a peça corrigida sem cavar mais a membrana. Ø6,35 é passagem; não constitui rosca M6 direta. Um inserto exigiria especificação real de diâmetro de instalação, comprimento e parede, além de remover mais material. Não selecionei inserto sem esse dado.

Medi envelopes de proposta, não peças de catálogo: arruela Øexterno 12 / Øinterno 6,4 / espessura 1,6; porca com sextavado de 10 entre faces / altura 5; cabeça cilíndrica Ø10 / altura 6. Na montagem, arruela Z=−8,1..−6,5, porca Z=−13,1..−8,1 e cabeça Z=12..18, com eixo X=−30,5/Y=85,401999. A porca foi representada por envelope cheio, conservador para interferência; não contém rosca inventada.

| Envelope testado | Colisão nominal mm³ | Controle + mm³ | Controle − mm³ |
|---|---:|---:|---:|
| Arruela contra adaptadora | 0 | auto-interseção 129,483883 | 0 |
| Porca contra adaptadora | 0 | auto-interseção 433,012702 | 0 |
| Cabeça contra bracket | 0 | auto-interseção 471,238898 | 0 |

A arruela no referencial isolado apoia **80,927427 mm²** na face Z=5; ao penetrar +1 mm remove/intersecta **80,927427 mm³**, e distante resulta **0** (`detail.json`). O controle de contato coplanar está na rodada 01. Não dimensionei pressão admissível. Acesso de chave, caminho de inserção, comprimento comercial, choque com clamp/trilho e retenção da porca NÃO foram fechados. Portanto a alternativa tem espaço geométrico local medido, mas ainda não é uma BOM aprovada. Não alterei o STEP para alojar porca nem inserto.

## 4. Orientações e anisotropia

Fonte: `02-orientations.py → orientations.json`. O rótulo X+ significa **o eixo +X do arquivo-fonte apontando para +Z da impressora**, e não face +X na mesa. A rotação é `App.Rotation(V(*up),V(0,0,1))`, seguida de translação do mínimo da caixa para a origem. Para adaptadora e clamp usa-se o frame dos arquivos isolados; bracket usa o STEP já montado; junções/chavetas usam o frame do pórtico.

Área solicitada: soma da área real dos triângulos cujo normal unitário tem `nz < -sqrt(0.5)-1e-9`, excluindo triângulos inteiramente no Z mínimo (tolerância 1e-5 mm). Malha OCCT: deflexão linear 0,05 mm, angular 0,15 rad. **Não é área projetada, nem volume de suporte, nem detecção de pontes imprimíveis.** Faces quase a 45° e triangulação fazem a classificação variar; não atribuir significado estrutural às últimas casas. Diferenças pequenas A/B são da discretização/classificação, não evidência de alteração das peças. As áreas antigas da checklist usavam outra classificação e não foram adotadas.

Controles da mesma rodada: cubo apoiado **overhang 0 / apoio 100 mm²**; composto com outro cubo elevado **overhang 100 / apoio 100 mm²**. Os volumes dos padrões são **1000 / 2000 mm³** e todas as malhas dos padrões são fechadas. A caixa de cada candidato foi comparada aos limites fornecidos pelo usuário, 220 × 220 × 250 mm.

### Comparação medida — mm²

| Peça | X+ | X− | Y+ | Y− | Z+ | Z− |
|---|---:|---:|---:|---:|---:|---:|
| peca | 721.925 | 1379.042 | 1363.879 | 1385.884 | 1527.748 | 1531.546 |
| bracket | 190.263 | 190.263 | 76.353 | 159.697 | 238.775 | 330.874 |
| clamp | 580.787 | 976.539 | 1188.258 | 559.238 | 1097.989 | 1150.139 |
| sapata | 124.064 | 123.857 | 108.245 | 108.255 | 44.532 | 239.346 |
| parafuso | 619.341 | 620.441 | 619.144 | 619.145 | 42.012 | 255.895 |
| JuncaoA | 619.379 | 628.450 | 592.150 | 593.533 | 2949.321 | 2864.598 |
| JuncaoB | 615.774 | 624.845 | 592.150 | 593.533 | 2958.325 | 2873.603 |
| ChavetaA | 24.342 | 24.342 | 23.183 | 25.501 | 0.000 | 0.000 |
| ChavetaB | 23.183 | 23.183 | 23.182 | 25.501 | 0.000 | 0.000 |

### Escolha para revisão de fatiamento

| Peça | Quantidade | Orientação | Overhang mm² | Apoio mm² | Envelope de impressão mm | Cabe individualmente? |
|---|---:|---|---:|---:|---|---|
| peca | 2 | X+ | 721.925 | 770.239 | 20.000 × 75.402 × 66.000 | Sim |
| bracket | 2 | Z+ | 238.775 | 917.895 | 39.000 × 26.000 × 11.500 | Sim |
| clamp | 2 | Z+ | 1097.989 | 197.825 | 71.000 × 35.001 × 19.999 | Sim |
| sapata | 2 | Z+ | 44.532 | 257.869 | 19.998 × 19.998 × 7.996 | Sim |
| parafuso | 2 | Z+ | 42.012 | 231.101 | 19.798 × 19.798 × 71.304 | Sim |
| JuncaoA | 1 | X+ | 619.379 | 1048.589 | 25.450 × 43.000 × 43.000 | Sim |
| JuncaoB | 1 | X+ | 615.774 | 1048.589 | 25.450 × 43.000 × 43.000 | Sim |
| ChavetaA | 1 | Z+ | 0.000 | 82.243 | 6.200 × 14.600 × 5.000 | Sim |
| ChavetaB | 1 | Z+ | 0.000 | 82.243 | 6.200 × 14.600 × 5.000 | Sim |

- **Adaptadora X+:** menor overhang medido e apoio amplo. O plano das camadas fica YZ, contendo a vertical de uso Y e o eixo de tração do novo parafuso Z. Isso favorece esse caminho local; o outro parafuso, de eixo X, permanece transversal às camadas. Para o lado espelhado há `orientada-pecaB`, com −X da peça espelhada levado para +Z: é a orientação equivalente da plataforma externa. Não imprimir duas A supondo que isso resolve o lado B físico da esteira.
- **Bracket Z+:** Y+ reduziria overhang a 76,353, mas colocaria a direção vertical de uso Y através das camadas. Z+ mantém Y no plano das camadas, reduz altura e oferece base maior. Tração do M6 em Z ainda atravessa as camadas; não há orientação que elimine todos os modos. Suportes/ponte na canaleta precisam de revisão no fatiador. O BREP não inclui os suportes descartáveis do STL vendor.
- **Clamp Z+:** o arco do clamp e a abertura principal no plano XY ficam no plano das camadas. Y− tem menos overhang, mas passa a pôr esforços no eixo Y através das camadas. A escolha aceita suporte adicional para preservar esse caminho. A direção exata da reação da esteira não foi medida. **Arquivo de revisão apenas**, pelo gate de origem descrito abaixo.
- **Junções X+:** conserva a carga vertical Y no plano das camadas, com overhang muito menor que Z+. Y+ tem área um pouco menor, mas põe Y através das camadas. A carga/torção da travessa em X continua desfavorável; a orientação não aprova a junção. Os arquivos orientados conservam a folga nominal zero e estão **bloqueados para lote final**.
- **Chavetas Z+:** overhang zero e apoio amplo; a força vertical Y atua no plano das camadas. A espessura em Z é 5 mm, não 1 mm, por `exports.json`. Isso corrige a descrição do plano, mas não dimensiona cisalhamento nem pressão na chapa do trilho.
- **Sapata Z+:** menor overhang e base efetiva, ao contrário das orientações laterais sem apoio plano. Compressão axial e eventual arrancamento do encaixe devem ser ensaiados; sua compatibilidade com o parafuso não foi medida nesta revisão.
- **Parafuso Z+:** menor overhang, base do manípulo apoiada e eixo da rosca vertical. A força axial atravessa camadas; há risco de separação sob tração/torque. Os candidatos laterais têm apoio praticamente pontual e overhang maior. A escolha favorece fabricação, não prova resistência. A rosca não foi testada contra o clamp.

**Formato entregue:** STEP e STL `orientada-*`, na origem da mesa, um sólido válido por export e malha fechada. Volume BREP antes/depois está em `exports.json` (e `additional.json` para peça B); diferenças são arredondamento numérico de transformação rígida. STL é aproximação: por exemplo peça 22647,902836 → malha 22648,947266 mm³, chaveta 411,353527 → 411,212860 mm³. Não confundir essa aproximação com retirada de material. Os controles de volume estão em `exports.json` (1000 / 0). Não há G-code, tempo ou volume de suportes medidos.

O inventário do plano era de doze unidades e omitia os brackets; com os dois brackets, este escopo tem **quatorze unidades**, contado em `exports.json`. As duas adaptadoras são A+B, apesar de a entrada agregada `peca.quantity` representar duas. Os dois brackets são exemplares da mesma variante screw-through; a montagem espelhada foi testada geometricamente, sem garantir a seção física oposta da esteira. Cada peça cabe individualmente; **não foi validado o empacotamento simultâneo com brim, suportes e margens de máquina**. Mounts/case das câmeras não estão silenciosamente incluídos neste lote.

**Gate de origem do clamp — FAIL:** `06-additional.py` mede STL vendor não fechado, **2 componentes / 3218 facetas**, enquanto o BREP carregado é sólido válido e sua remalhagem fechada. Isso prova que o BREP exporta, não que a conversão anterior preservou toda a malha. Não reparei nem substituí o clamp pelo modelo joehann sem comparar suas interfaces. Sapata e parafuso derivam dos BREP existentes; não declarei a montagem roscada compatível.

## 5. Dois cupons e folgas

### Luva

O nominal da luva falhou no gate de folga. **Proponho 0,25 mm/lado como ponto de partida de ensaio**, com alternativas 0,18 e 0,30, sem promover esse valor a aprovado. O 0,18 é precedente geométrico do projeto, não calibração da K1C com o filamento atual.

`04-coupons.py` recorta a junção real: faixa Y=433,901999 até +8 mm, preservando a geometria existente, inclusive a interseção com a outra canaleta. A seção terminal real do MontanteA é extrudada e o cortador é a união de nove cópias transladadas em X/Z por −c, 0, +c. Trata-se de dilatação retangular nesses eixos, **não offset normal isotrópico** nas curvas. As variantes só calibram a canaleta vertical nesse recorte; ainda será necessário aplicar/medir a folga na canaleta da travessa e verificar travas e jogo da junção completa. A orientação X+ é a mesma proposta para a junção.

### Bracket

`03-detail.py` identifica faces antiparalelas de normal ±X, áreas **7,699998 mm²**, X=−48,180000305 e −12,819999695, na zona Y=92,901999..98,401999: **canal 35,360000610 mm**, contra largura do trilho **35,000000 mm**. A diferença é **folga positiva 0,180000305 mm/lado**, não aperto nominal. Isso não garante entrada após FDM, nem cobre tolerância real do trilho, primeira camada ou detritos de suporte.

O cupom é o **bracket completo**, para preservar batente, engate e rigidez, em Z+ como o candidato final. A variante 0,18 é o BREP intacto, sem suportes descartáveis. Para 0,25 e 0,30, extrudo cada face limitante lateral para dentro de sua parede em 0,07 e 0,12 mm e subtraio o material; não escalo a peça inteira nem altero o furo M6. Os demais contatos da seção permanecem nominais: esse ensaio mede alargamento lateral, não uma folga universal. Caso a restrição venha de outra superfície, o gate continua falhando e exige investigação, não mais alargamento automático.

### Artefatos e controles

Fonte: `04-coupons.py → coupons.json`. Cubo positivo 1000 / negativo 0 mm³ na mesma rodada. Todos os cupons resultaram em um sólido válido, STL fechado e volume preservado na rotação. As remoções abaixo são contra o recorte real da luva ou o bracket inteiro, não contra modelos sintéticos.

| Cupom | Volume de referência mm³ | Removido mm³ | Volume final mm³ | Colisão trilho | Controle positivo mm³ | Negativo mm³ |
|---|---:|---:|---:|---:|---:|---:|
| cupom-luva-0p18 | 8211.123893 | 142.117907 | 8069.005986 | 0.000000 | 8069.005986 | 0.000000 |
| cupom-luva-0p25 | 8211.123893 | 197.945981 | 8013.177911 | 0.000000 | 8013.177911 | 0.000000 |
| cupom-luva-0p3 | 8211.123893 | 238.015178 | 7973.108715 | 0.000000 | 7973.108715 | 0.000000 |
| cupom-bracket-0p18 | 10352.711976 | 0.000000 | 10352.711976 | 0.000000 | 137.304423 | 0.000000 |
| cupom-bracket-0p25 | 10352.711976 | 1.078000 | 10351.633976 | 0.000000 | 137.304423 | 0.000000 |
| cupom-bracket-0p3 | 10352.711976 | 1.847999 | 10350.863976 | 0.000000 | 137.304423 | 0.000000 |

No cupom de luva o positivo é auto-interseção; no de bracket é trilho deslocado −3 Y, equivalente ao bracket +3 Y. Negativos usam afastamento +500 X do trilho. Os arquivos `.step` e `.stl` têm os nomes da tabela no diretório de evidências; guardar a identificação externamente, pois não gravei texto na superfície de encaixe.

**Procedimento físico:** usar o trilho real, filamento e orientação do lote; medir a abertura impressa e a seção do trilho; testar entrada manual até o batente, deslizamento, retirada, trava e jogo. Registrar fotos, dimensões e força/método de inserção. Escolher a menor folga que permita montagem repetível sem forçar a parede, e depois verificar retenção/jogo no conjunto completo. Não foi especificado limite quantitativo de força ou jogo porque o projeto não o forneceu; esse critério precisa ser fechado antes de aceitar o ensaio.

**Uma oportunidade:** estes cupons são artefatos de calibração, não uma promessa de que cabem no cronograma. Se existe só um ciclo de impressão, os resultados não podem orientar peças que já foram impressas junto deles. Se existe uma janela com ciclos sucessivos, reservar primeiro o cupom e só então congelar o lote. Não assumi essa segunda oportunidade. Sem ensaio prévio, o gate de folga permanece BLOCKED; não forneci G-code nem chamei 0,25 de valor seguro.

## 6. Checklist adversarial: alcance real desta revisão

| Classe/itens | O que a geometria pode resolver | O que segue pendente |
|---|---|---|
| A, F; G1/G4/G6/G9 | Medidor com controles; rastrear arquivo efetivamente usado; placement; contato/colisão dos pares listados | Não foi auditado cada script histórico nem todo par do pórtico |
| C1/C2/C4/C7; G2/G7 | Folga nominal, faces do canal, candidatos de impressão, recortes reais de calibração, espessura da chaveta | Folga final física, qualidade de suporte, resistência e remanufatura |
| B2/B3/B5; H7 | Modelar e medir trava positiva, curso e interferências de antirrotação quando a arquitetura/fixadores estiverem definidos | Não foram modeladas aqui trava de largura, trava de mount/case ou nova antirrotação; torque e eficácia exigem ensaio |
| B1/B10/B12; H3/H6 | Localizar seções e caminho de carga, reservar envelope de retenção após especificar ancoragens | Massa, CG, pré-carga, resistência do ponto de esteira, fluência, estabilidade, flambagem, ensaio de remontagem e retenção anti-queda |
| B6/B7; E1–E9/E11; H3 | Com envelopes e layout medidos: acesso de ferramentas, suportes, rotas e interferências de trigger, LED, difusor, FPC e encoder | Esteira nunca medida; trigger/anteparo, encoder/rolete, iluminação e ESP-CAM sem integração; raio e conectores de FPC; acesso/refrigeração do Pi |
| B8/B9/B14; H1; E12 | CAD implementa arquitetura decidida | Decisão de duas/três câmeras, sensor e ajuste angular é de requisitos; não é resolvida por booleano |
| E2; H3 | FOV pode ser calculado quando sensor/lente, objeto e pose tiverem dados confiáveis | Não medi FOV, cobertura, distância de trabalho, garrafa ou largura real da esteira |
| C3/C6/C8/C10; H9 | Fatiamento posterior pode medir material/tempo e reservar sobressalentes | K1C/bico/filamento/umidade/mesa, calibração, disponibilidade e orçamento não verificados; não há lote fatiado |
| D; H2/H8; E10 | Manifesto novo de fontes/artefatos e separação da linhagem usada | Licenças/NOTICE, cadeia histórica completa, BOM de hardware e esquemático não foram resolvidos; geometria não decide licença |
| H4 | Exportar figuras e desenhos após congelar o projeto | Rubrica, vídeo, PDF do TCC e decisões editoriais não foram tratados |

## 7. O que não fechei

1. Resistência da membrana do M6 e das demais peças; nenhuma carga admissível foi afirmada.
2. Hardware real da alternativa passante, comprimento do parafuso, pré-aperto, ferramenta, inserção e compatibilidade com o clamp completo.
3. Espessura mínima global de todas as paredes e qualificação dos suportes FDM; medi seções locais e overhangs, não todo modo de fabricação.
4. Origem/manifold do clamp vendor, rosca clamp↔parafuso e encaixe parafuso↔sapata. Os arquivos orientados não resolvem esses gates.
5. Folga final das duas canaletas da junção, retenção/jogo após alteração e correlação dos cupons com a peça integral.
6. Reação da esteira, simetria dos lados, ancoragem anti-queda, massa/CG, carga, FOV, trigger, iluminação, encoder e FPC.
7. Lote simultâneo com suportes/brim, fatiamento/G-code, tempo e filamento; não há aprovação para consumir a oportunidade única.

Os PASS deste relatório são estritamente os gates geométricos identificados. Os STEP/STL entregues tornam as orientações e cupons revisáveis; **não convertem os gates abertos em autorização técnica de fabricação ou uso**.

**Conferência final:** recarregamento por `00-load.py` e repetição integral de `01-interface.py` concluídos (`repeat-complete.txt`), mantendo contato, colisões e controles relatados. Manifesto de saída: `validacao-astra-20260911/ARTIFACTS.sha256`.
