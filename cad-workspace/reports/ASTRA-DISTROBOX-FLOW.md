# Fluxo: Codex Astra + FreeCAD MCP no distrobox `trabalho`

Objetivo: o agente (Astra) dirige um FreeCAD real via MCP `qwen-mm-plugins-freecad`
dentro do `distrobox trabalho` == o habilitado, não o (fora do repo).

## Estado atual (2026-09-09, corrigido)

- MCP registrado no Codex global (`~/.codex/config.toml`), tag `qwen-mm-plugins-freecad-v1.1.0`.
- Args foram corrigidos: `qwen-mm-plugins[freecad] @ git+...` agora é UMA string
  (antes o `@` foi registrado como arg separado => `uvx --from "qwen-mm-plugins[freecad]"`
  sozinho => "no versions of qwen-mm-plugins[freecad]" => Connection closed). FIX APLICADO.
- FreeCAD canônico: o gerenciado pelo próprio MCP (`qwen-mm-plugins-freecad --launch-app --gui`, AppImage 1.1.1 com addon incluso). O Flatpak GUI não se sustenta; o wrapper usa o AppImage do MCP.
- RPC: `127.0.0.1:9875`, NÃO persistente. O wrapper sobe via `--launch-app --gui` antes de rolar o agente.

## Como rodar

```bash
# 1. (uma vez) garantir uvx + addon
distrobox enter trabalho -- bash -lc "codex mcp list"   # mostra qwen-mm-plugins-freecad enabled
# 2. resolver o MCP ponta a ponta
runuser -u nerton -- /home/<usuario>/tcc-pnaat/github/cad-workspace/tools/r03-astra.sh --status
# 3. rodar o agente sobre um prompt
runuser -u nerton -- /home/<usuario>/tcc-pnaat/github/cad-workspace/tools/r03-astra.sh prompts/codex-r03-freecad-mcp.md
```

## Fases (gate human-in-the-loop)

1. **RPC up** (wrapper sobe o Flatpak GUI se 9875 cair). Se o usuário não precisar ver a
   janela em cada rodada, pode subir headless, mas o GUI é o canônico para validar.
2. **Astra roda** com MCP => cria/edita `.FCStd` nativo em `exports/concepts/optical-rig-r03/`.
3. **Readback determinístico** (fora do Astra): abrir o FCStd no THSU / FreeCAD e verificar
   o contrato óptico (pórtico aberto, C_TOP/C_LEFT/C_RIGHT, FOV, sem U/V/W). NÃO confiar
   no OK do Astra: é ele que gera E valida = auto-confirmação. Separar gerador e verificador.

## Problemas encontrados e fix

| Sintoma | Causa | Fix |
|---|---|---|
| `Connection closed` no `codex mcp add/test` | args MCP com `@` separado | juntar `pkg @ git+...` numa string; ver config.toml |
| Porta 9875 cai | FreeCAD não persistente | wrapper `r03-astra.sh` sobe RPC + valida antes de rolar |
| Quota 503 `usage limit` | limite OpenAI no plano | aguardar retorno / usar fallback; nunca retry em loop sem sleep |
| Processos Astra órfãos 5h+ | retry/envios pendurados | `process kill`; wrapper não deixa retry automático |
| Duas instâncias FreeCAD | Flatpak GUI vs AppImage do MCP | padronizar no AppImage do MCP via wrapper; `QWEN_MM_AUTOLAUNCH=1` |

## Regras de execução

- NUNCA deixar o Astra validar o próprio CAD. Readback/contrato é feito por command não-LLM.
- Depois do Astra criar o FCStd, rodar um checker que lê o documento e falha se:
  - não há DATUMS/app::part com XYZ; existir U/V/W;
  - não há C_TOP/C_LEFT/C_RIGHT ou cones FOV;
  - pórtico fechado (volume intersectando o corredor óptico).
- Custo: benchmark Parametric CAD Bench mostra que geometria é a fraqueza de TODOS os modelos
  (mesmo GPT-5.6). Harness/´ritmo de verificação` muda ~10%. Não esperar precisão de G1 da IA.
