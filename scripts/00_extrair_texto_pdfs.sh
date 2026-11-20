#!/usr/bin/env bash
# Etapa 0 - Converte em texto as listas de resultados salvas em PDF
# (ACM Digital Library, SBC OpenLib e arXiv). Scopus e IEEE Xplore
# foram exportadas em CSV e não passam por esta etapa.
# Entradas: dados_brutos/*.pdf (exportações locais, não versionadas).
# Saídas:   dados_brutos/intermediarios/*.txt
# Requer: pdftotext (pacote poppler-utils).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p dados_brutos/intermediarios
for f in acm_1-50 acm_51-84 sbc_openlib arxiv; do
  pdftotext -layout "dados_brutos/$f.pdf" "dados_brutos/intermediarios/$f.txt"
  echo "dados_brutos/intermediarios/$f.txt"
done
