"""Etapa 4 - Aplica a revisão manual dos 30 registros "6 Conferir" a dados/triagem.csv.

A pré-classificação (etapa 3) marcou 30 registros em que a migração aparecia
apenas no resumo. O autor revisou esses registros um a um em 13/11/2026; as
decisões e os motivos estão no Quadro 7 (Apêndice A) do TCC e na lista abaixo.
Resultado: 21 registros passam para o tema e 9 ficam fora, de modo que o total
no tema vai de 359 (classificação automática) para 380.

Antes de gravar, o script confere que cada um dos 30 títulos casa com exatamente
um registro da categoria "6 Conferir" e com o mesmo ano. Se houver qualquer
divergência, grava um log de conferência em
dados_brutos/intermediarios/log_conferencia_quadro7.txt e encerra sem alterar
o CSV.
"""
import csv, os, re, sys, unicodedata
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, 'dados', 'triagem.csv')
LOG = os.path.join(RAIZ, 'dados_brutos', 'intermediarios', 'log_conferencia_quadro7.txt')
DATA_REVISAO = '13/11/2026'
COL_CAT = 'Pré-triagem (regex)'

# (título como aparece na triagem, ano, categoria decidida, motivo do Quadro 7)
REVISAO_MANUAL = [
    ('Advancing ATM through Info centric and Composable Service Architectures', '2026', '7 Fora do tema',
     'Arquitetura de controle de tráfego aéreo'),
    ('Evaluating Migration Strategies: A Scoring-Based Comparison of Big Bang and Incremental Approaches', '2026', '5 No tema: outros (processo, dados etc.)',
     'Escolha da estratégia de migração'),
    ('Exploring the Systematic Use of LLMs for Micro services Generation', '2026', '5 No tema: outros (processo, dados etc.)',
     'Geração de microsserviços com modelos de linguagem'),
    ('Microfrontends versus Monolithic Frontends: An Experimental Study on Performance in Web Applications', '2026', '7 Fora do tema',
     'Compara frontends, não microsserviços (limítrofe)'),
    ('Modular virtual distributed unit design for efficient cloud RAN deployment', '2026', '7 Fora do tema',
     'Função de rede 5G'),
    ('Semanti-MOP: Bridging the semantic gap in automated architecture refactoring via instability-aware Large Language Models', '2026', '4 No tema: técnica de decomposição',
     'Decomposição com otimização e modelos de linguagem'),
    ('Implementing Automatic Microservices Detection in Business Processes Using Association Rules', '2025', '4 No tema: técnica de decomposição',
     'Identificação de microsserviços'),
    ('Modularizing the Virtual Distributed Unit: Enabling Efficiency in Cloud-Native 5G RAN', '2025', '7 Fora do tema',
     'Função de rede 5G'),
    ('Pro Cloud-Native Java EE Apps: DevOps with MicroProfile, Jakarta EE 11 APIs, and Kubernetes', '2025', '7 Fora do tema',
     'Livro tutorial; a migração é apenas um capítulo'),
    ('Sustainable Cloud Migration: An Analysis of Environmental Impacts and Strategic Optimizations', '2025', '7 Fora do tema',
     'Migração para a nuvem e impacto ambiental'),
    ('TRANSFORMING SOFTWARE ARCHITECTURE: A STRANGLER FIG PATTERN APPROACH', '2025', '3 No tema: experiência ou estudo de caso',
     'Estudo de caso de migração'),
    ('Transactional Cloud Applications Go with the (Data)Flow', '2025', '7 Fora do tema',
     'Ambiente de execução transacional'),
    ('A Metrics-based Model for Estimating the Maintainability of Cloud-Based Enterprise Information Systems for Kenyan SMEs', '2024', '5 No tema: outros (processo, dados etc.)',
     'Modelo de manutenibilidade motivado pela migração (limítrofe)'),
    ('Adopting and Sustaining Microservice-Based Software Development', '2024', '5 No tema: outros (processo, dados etc.)',
     'Ganhos e dificuldades da adoção (limítrofe)'),
    ('Insights on Microservice Architecture Through the Eyes of Industry Practitioners', '2024', '3 No tema: experiência ou estudo de caso',
     'Levantamento com profissionais'),
    ('MSA-Lab: Integrated Design Platform for Model-driven Development of Microservices; [MSA-Lab: 模型驱动的微服务集成设计平台]', '2024', '4 No tema: técnica de decomposição',
     'Ferramenta de identificação e refatoração'),
    ('Use of clustering methods to solve the problem of identifying configuration items in IT project', '2024', '7 Fora do tema',
     'Gestão de configuração'),
    ('Approach for Fast Growing Software Systems using layered architecture. Scaling an architecture with minimal refactoring; [Abordagem para Sistemas de Software de Crescimento Rápido utilizando uma arquitetura por camadas. Escalar uma arquitetura com o mínimo de refactoring]', '2023', '5 No tema: outros (processo, dados etc.)',
     'Arquitetura para facilitar migração futura (limítrofe)'),
    ('Microservice Based Architecture: The Development of Rapid Prototyping Supportive Tools for Project Based Learning', '2023', '3 No tema: experiência ou estudo de caso',
     'Caso de migração'),
    ('Analysis and Design of Microservices Architecture with GraphlQL as an API Gateway for Higher Education Information System', '2022', '3 No tema: experiência ou estudo de caso',
     'Projeto de decomposição de um sistema acadêmico'),
    ('How Can We Cope with the Impact of Microservice Architecture Smells?', '2022', '2 No tema: estudo secundário',
     'Revisão sistemática; inclui problemas da migração'),
    ('Leveraging the Layered Architecture for Microservice Recovery', '2022', '4 No tema: técnica de decomposição',
     'Identificação de microsserviços'),
    ('MICROSERVICE ARCHITECTURE OF VIRTUAL TRAINING COMPLEXES; [МИКРОСЕРВИСНАЯ АРХИТЕКТУРА ВИРТУАЛЬНЫХ ТРЕНАЖЕРНЫХ КОМПЛЕКСОВ]', '2022', '3 No tema: experiência ou estudo de caso',
     'Transição em domínio específico (limítrofe)'),
    ('Performance Evaluation of Microservices Featuring Different Implementation Patterns', '2022', '1 No tema: comparação ou desempenho',
     'Comparação de desempenho com o monólito'),
    ('Serverless Software Engineering – and How to Get There.', '2022', '2 No tema: estudo secundário',
     'Revisão multivocal sobre técnicas de migração'),
    ('A Roadmap for Migration System-Architecture Decision by Neutrosophic-ANP and Benchmark for Enterprise Resource Planning Systems', '2021', '5 No tema: outros (processo, dados etc.)',
     'Modelo de decisão de migração'),
    ('Enhancing system quality attributes via microservices adoption', '2021', '5 No tema: outros (processo, dados etc.)',
     'Processo de migração orientado a qualidade'),
    ('Container mapping and its impact on performance in containerized cloud environments', '2020', '7 Fora do tema',
     'Contêineres sobre máquinas virtuais (limítrofe)'),
    ('Applying change impact analysis test to migration test case extraction based on IDAU and graph analysis techniques', '2019', '5 No tema: outros (processo, dados etc.)',
     'Testes na migração'),
    ('An experience report on the adoption of microservices in three Brazilian government institutions', '2018', '3 No tema: experiência ou estudo de caso',
     'Relato de migração com levantamento'),
]


def norm(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()


with open(ARQ, encoding='utf-8', newline='') as fh:
    leitor = csv.DictReader(fh)
    colunas = leitor.fieldnames
    rows = list(leitor)

problemas, casados = [], {}
for titulo, ano, decisao, motivo in REVISAO_MANUAL:
    achados = [i for i, r in enumerate(rows) if norm(r['Título']) == norm(titulo)]
    if len(achados) != 1:
        problemas.append(f'{len(achados)} registros com o título: {titulo}')
        continue
    r = rows[achados[0]]
    if not r[COL_CAT].startswith('6'):
        problemas.append(f'{r["ID"]} não está na categoria 6 ({r[COL_CAT]}): {titulo}')
    if r['Ano'] != ano:
        problemas.append(f'{r["ID"]} com ano {r["Ano"]} (esperado {ano}): {titulo}')
    casados[achados[0]] = (decisao, motivo)
n6 = sum(r[COL_CAT].startswith('6') for r in rows)
if n6 != len(REVISAO_MANUAL):
    problemas.append(f'A categoria 6 tem {n6} registros, mas a revisão manual lista {len(REVISAO_MANUAL)}')

if problemas or len(casados) != len(REVISAO_MANUAL):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'w', encoding='utf-8') as fh:
        fh.write('Divergências no casamento da revisão manual (Quadro 7):\n')
        fh.write('\n'.join(problemas) + '\n')
    sys.exit(f'{len(problemas)} divergência(s); nada foi gravado. Veja {LOG}')

for i, (decisao, motivo) in casados.items():
    rows[i]['Sua decisão'] = f'Revisão manual ({DATA_REVISAO}): {decisao}'
    rows[i]['Motivo da decisão'] = motivo

with open(ARQ, 'w', encoding='utf-8', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=colunas)
    w.writeheader()
    w.writerows(rows)


def categoria_final(r):
    return r['Sua decisão'].split(': ', 1)[1] if r['Sua decisão'] else r[COL_CAT]


final = Counter(categoria_final(r) for r in rows)
no_tema = [r for r in rows if categoria_final(r)[0] in '12345']
recentes = sum(r['Ano'] in ('2024', '2025', '2026') for r in no_tema)
print(f'Revisão manual aplicada a {len(casados)} registros')
for k in sorted(final):
    print(f'{final[k]:5d}  {k}')
print(f'No tema após a revisão manual: {len(no_tema)} | fora do tema: {len(rows) - len(no_tema)}')
print(f'No tema publicados entre 2024 e 2026: {recentes}/{len(no_tema)} ({recentes / len(no_tema):.1%})')
