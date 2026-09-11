# Vídeos de evidência

Os vídeos são armazenados externamente quando forem grandes ou contiverem dados que não devem entrar
no Git. Esta pasta guarda o índice reproduzível, não apenas um link solto.

Para cada vídeo aprovado, crie um manifest a partir de
`../manifests/manifest.template.yaml` e registre:

- identificador único, data/hora UTC, operador e setup;
- PoC, pergunta técnica e critério mostrado;
- estado (`MEASURED` durante a coleta; `VALIDATED` somente após revisão do critério);
- comando exato, commit Git e versões relevantes;
- caminho/URL externa e SHA-256 do arquivo original;
- entradas usadas e hashes dos artefatos de saída;
- limitações vistas no take e próxima integração;
- confirmação de que a URL não listada abre em janela anônima.

Não versionar vídeo, dataset ou imagem sensível sem revisar tamanho, licença e privacidade. Não chamar
controle sintético de defeito real. O roteiro completo, mapa dos arquivos, pré-voo, gravação e
diagnóstico ficam em `code-workspace/src/pocs/ROTEIRO-GRAVACAO.md`.

## Convenção sugerida

```text
evidencias/manifests/EVID-2026-001-pocfinal.yaml
armazenamento externo/EVID-2026-001-pocfinal/video.mp4
armazenamento externo/EVID-2026-001-pocfinal/SHA256SUMS
```

O nome identifica a evidência; revisão ou nova tomada recebe novo identificador. Não sobrescreva uma
tomada anterior, pois isso quebra o hash e a rastreabilidade.
