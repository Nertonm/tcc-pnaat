# Evidencias

Esta pasta guarda a cadeia de evidencia do projeto sem confundir meta com medicao.

Regra: fotos, videos, PDFs de instrumento e dados brutos ficam fora do Git por padrao. Versione apenas metadados sanitizados, hashes SHA-256 e referencias aprovadas.

Cada registro deve informar estado (`MEASURED`, `DERIVED`, `SPECULATIVE`, `BLOCKED` ou `VALIDATED`), data, setup, instrumento, operador, arquivo externo e hash. Uma evidencia nao autoriza fabricacao sozinha.

Subpastas: `fotos/`, `medicoes/`, `manifests/` e `videos/`.
