# Triagem dos registros da busca: scripts e dados do TCC

Material suplementar do Trabalho de Conclusão de Curso **"Modernização de arquiteturas de software: migração de monólitos para microsserviços baseada em resiliência e desempenho"** (Instituto Federal de Educação, Ciência e Tecnologia do Maranhão — IFMA, 2026), de autoria de Rodrigo Salgado da Costa.

Este repositório disponibiliza os scripts de deduplicação, pré-classificação e amostragem, além das planilhas sanitizadas de triagem e de extração dos 11 estudos incluídos na síntese.

## Transparência metodológica e datas

- **Data da busca nas bases:** 12/11/2026
- **Data da revisão manual (Quadro 7, Apêndice A do TCC):** 13/11/2026
- **Reconstituição da etapa 3:** a regra de pré-classificação da etapa 3 (`scripts/03_pre_classificar.py`) foi reconstituída a partir da classificação original e reproduz exatamente a planilha de triagem gerada no estudo.

## Estrutura do repositório

- `scripts/` — scripts Python para ingestão local, deduplicação, pré-classificação por regras (`regex`), aplicação da revisão manual, sanitização e amostragem de falsos negativos.
- `dados/triagem.csv` — conjunto consolidado e sanitizado dos 878 registros únicos (sem resumos das editoras), incluindo a coluna `Pré-triagem (regex)` e as 30 decisões manuais do Quadro 7 (Apêndice A do TCC), com o motivo de cada uma, que totalizam 380 registros no tema. Colunas: `ID`, `Pré-triagem (regex)`, `Sua decisão`, `Motivo da decisão`, `Título`, `Ano`, `Bases`, `Estudo do TCC`, `DOI`.
- `dados/extracao_11_estudos.csv` — planilha de extração e mapeamento dos 11 estudos primários e secundários (E1–E11) utilizados no TCC (separador `;`, UTF-8), com as notas de qualidade AQ1–AQ5.
- `dados/amostra_falsos_negativos.csv` — amostra aleatória com semente fixa (`random.seed(42)`) de 50 registros dentre os 489 excluídos na pré-classificação automática, com suas respectivas decisões manuais.
- `dados_brutos/` — diretório intencionalmente vazio (ignorado pelo Git) destinado às exportações obtidas localmente por quem desejar reexecutar o pipeline completo.

## Aviso de direitos autorais e como reproduzir as exportações

Por força dos termos de uso da Scopus/Elsevier e dos direitos autorais das editoras sobre os resumos, este repositório **não** redistribui os arquivos brutos exportados (`scopus.csv`, `ieee.csv`, PDFs da ACM e demais exportações originais) nem a coluna `Resumo` do arquivo `dados/triagem.csv`. Estão publicados apenas metadados derivados permitidos (título, ano, DOI, bases, categoria de pré-triagem e decisão).

Para reproduzir integralmente o pipeline localmente, refaça as exportações nas 5 bases utilizando os parâmetros abaixo e salve os arquivos em `dados_brutos/`:

String comum às cinco bases:

```text
("monolith" OR "monolithic") AND ("microservice" OR "microservices") AND ("migration" OR "decomposition" OR "resilience" OR "performance")
```

| Base | Escopo real da busca | Data | String de busca | Registros exportados |
| --- | --- | --- | --- | --- |
| Scopus | Sem filtro de tipo de documento (incluiu 25 *conference reviews*, 19 livros e 1 errata) | 12/11/2026 | String comum em `TITLE-ABS-KEY` (título, resumo e palavras-chave), período 2015–2026; exportação CSV salva como `dados_brutos/scopus.csv` | 851 |
| IEEE Xplore | Sem filtro de tipo de documento | 12/11/2026 | String comum nos campos *Document Title*, *Abstract* e *Author Keywords*, período 2015–2026; exportação CSV salva como `dados_brutos/ieee.csv` | 378 |
| ACM Digital Library | *ACM Full-Text Collection* (não cobriu o *ACM Guide*) | 12/11/2026 | `[[Abstract: "monolith"] OR [Abstract: "monolithic"]] AND [[Abstract: "microservice"] OR [Abstract: "microservices"]] AND [[Abstract: "migration"] OR [Abstract: "decomposition"] OR [Abstract: "resilience"] OR [Abstract: "performance"]] AND [E-Publication Date: (01/01/2015 TO 11/30/2026)]`; lista de resultados salva em PDF como `dados_brutos/acm_1-50.pdf` e `dados_brutos/acm_51-84.pdf` | 84 |
| SBC OpenLib (SOL) | Busca na base nacional (21 registros exportados, sem resumo nem DOI; 13 permaneceram só com a SOL após a deduplicação) | 12/11/2026 | String comum na busca integrada da SOL; lista de resultados salva em PDF como `dados_brutos/sbc_openlib.pdf` | 21 |
| arXiv | Somente título (*Advanced Search*, campo `title`), 2015-01-01 a 2026-11-12, incluindo *cross-lists* | 12/11/2026 | `title="monolith" OR "monolithic"; AND title="microservice" OR "microservices"; AND title="migration" OR "decomposition" OR "resilience" OR "performance"`; lista de resultados salva em PDF como `dados_brutos/arxiv.pdf` | 8 |
| **Total bruto** | — | — | — | **1.342** |

### Resumo quantitativo do pipeline

1. **Registros exportados:** 1.342
2. **Duplicados removidos (`02_deduplicar.py`):** 464 (4 internos à mesma base + 460 entre bases diferentes), utilizando três critérios: (a) DOI idêntico; (b) título normalizado idêntico; (c) prefixo de título com 28 caracteres ou mais entre bases diferentes com diferença de até 1 ano.
3. **Registros únicos:** 878
4. **Classificados no tema pela pré-triagem (`regex`):** 359
5. **Revisão manual de casos limítrofes (Quadro 7, Apêndice A):** 30 registros revisados manualmente (`04_aplicar_revisao_manual.py`; 21 passaram para o tema e 9 ficaram fora), resultando em **380 registros no tema** (44,5% publicados entre 2024 e 2026: 169/380).

### Execução local

Requisitos: Python 3.8 ou superior (somente biblioteca padrão) e `pdftotext` (pacote `poppler-utils`).

```bash
bash scripts/00_extrair_texto_pdfs.sh
python3 scripts/01_carregar_exportacoes.py
python3 scripts/02_deduplicar.py
python3 scripts/03_pre_classificar.py
python3 scripts/04_aplicar_revisao_manual.py
python3 scripts/05_amostra_falsos_negativos.py
# depois de preencher decisao_manual (sim / limítrofe / não) na amostra:
python3 scripts/06_resultado_amostra.py
```

As etapas 00 a 03 exigem as exportações em `dados_brutos/`; os arquivos intermediários (textos dos PDFs, `registros.json` e `unicos.json`, que contêm resumos) são gravados em `dados_brutos/intermediarios/` e também não são versionados. As etapas 05 e 06 rodam apenas a partir de `dados/triagem.csv` e podem ser reexecutadas sem as exportações. O script 05 preserva as decisões já preenchidas na amostra.

## Limitações conhecidas e erros medidos

- **Ausência de termos de resiliência na pré-triagem:** a expressão regular não inclui termos de resiliência; 19 títulos contendo `resilien`, `fault toler`, `chaos` ou `circuit` foram classificados como `"Fora do tema"`.
- **Restrição linguística do regex:** o script busca exclusivamente o termo `"monolith"` em inglês, podendo omitir registros redigidos apenas em português ou com terminologia alternativa.
- **Erros medidos na categoria 2:** 5 dos 31 registros atribuídos à categoria 2 apresentaram classificação incorreta.
- **Estimativa de falsos negativos:** avaliada em amostra aleatória de 50 dos 489 registros excluídos (`random.seed(42)`), registrada em `dados/amostra_falsos_negativos.csv` com a decisão e a justificativa de cada item: 6 registros claramente pertinentes e 4 limítrofes, ou seja, de 12% a 20% de falsos negativos, o que equivale a cerca de 59 a 98 dos 489 registros excluídos (IC 95% de Wilson: 5,6%–23,8% para os claramente pertinentes e 11,2%–33,0% somando os limítrofes; cálculo em `scripts/06_resultado_amostra.py`).
- **Cobertura das bases:** a busca na ACM restringiu-se à *Full-Text Collection*; Scopus e IEEE não tiveram filtro de tipo de publicação; 13 registros da SOL não possuíam resumo disponível na exportação.

## Licenças

- **Código-fonte (`scripts/`):** licenciado sob a [Licença MIT](LICENSE).
- **Dados derivados (`dados/`):** licenciados sob [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-DATA).

## Como citar

Em formato ABNT (substituir `XXXXXXX`, URL e data de acesso após o arquivamento da versão `v1.0.0` no Zenodo):

> COSTA, Rodrigo Salgado da. **Triagem dos registros da busca**: scripts e dados do TCC. Versão 1.0. [*S. l.*]: Zenodo, 2026. DOI: [https://doi.org/10.5281/zenodo.XXXXXXX](https://doi.org/10.5281/zenodo.XXXXXXX). Disponível em: [https://doi.org/10.5281/zenodo.XXXXXXX](https://doi.org/10.5281/zenodo.XXXXXXX). Acesso em: DD mmm. 2026.

No corpo do texto do TCC (seção 3.5 ou 3.6):

> "Os scripts de deduplicação e pré-classificação, a planilha de triagem e o formulário de extração estão disponíveis em Costa (2026)."
