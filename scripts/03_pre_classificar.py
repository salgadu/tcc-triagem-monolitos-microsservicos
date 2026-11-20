"""Etapa 3 - Pré-classificação por termos (regex) e geração de dados/triagem.csv.

As regras abaixo foram reconstituídas a partir da classificação original usada
no TCC; a execução reproduz exatamente a planilha de triagem do estudo.

A pré-classificação é um APOIO à triagem por título e resumo, não uma decisão
de inclusão. Ela separa os registros que tratam do tema (migração ou
decomposição de monólitos, ou comparação monólito x microsserviços) dos que
apenas usam os termos da busca em outro contexto, e agrupa os registros no
tema por tipo. As colunas "Sua decisão" e "Motivo da decisão" ficam em branco
aqui e são preenchidas pela etapa 4 (revisão manual dos 30 registros
"6 Conferir", Quadro 7 / Apêndice A do TCC).

Por restrições de licença das bases (Scopus/Elsevier e editoras), o arquivo
público dados/triagem.csv NÃO inclui resumos, tipo de documento nem veículo:
traz apenas ID, categoria, decisão, título, ano, bases, estudo do TCC e DOI.

Regras, aplicadas em ordem (títulos e resumos sem acento e em minúsculas):
  1. NO TEMA (pelo título) se:
       (título cita monólito/legado E (cita microsserviços OU um termo de migração))
       OU (título cita microsserviços E um termo forte de migração/decomposição)
  2. Fora do tema pelo título, mas o RESUMO cita migração/decomposição/
     refatoração/modernização 2+ vezes E "monolith" 2+ vezes -> "6 Conferir"
  3. Demais registros -> "7 Fora do tema"
  Registros no tema recebem a primeira categoria que casar:
       2 Estudo secundário        (revisão, mapeamento, survey...)
       4 Técnica de decomposição  (decompos, identif, extract, cluster...)
       1 Comparação/desempenho    (performance, scalab, compar, vs...)
       3 Experiência/caso         (case study, lessons, challenges...)
       5 Outros                   (processo, dados, arquitetura etc.)
O total "no tema" (categorias 1 a 5) antes da revisão manual é 359.
"""
import csv, json, re, os, unicodedata
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAI = os.path.join(RAIZ, 'dados_brutos', 'intermediarios')
DADOS = os.path.join(RAIZ, 'dados')
os.makedirs(DADOS, exist_ok=True)
U = json.load(open(os.path.join(SAI, 'unicos.json')))


def n(t):
    return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()


# ---- expressões regulares ----------------------------------------------
MONO = r'monolith|monolit|legacy'
MS = r'micro-?servi[cç]|microsservi'
MIG = (r'migrat|migra[cç]|decompos|refactor|moderni[sz]|extract|identif|transition|transform|re-?architect|split|'
       r'partition|strangl|break(ing)? (up|down)|candidate|boundar|from monolith|to microservice|evolution|evolving|'
       r'adoption|adopt')
MIG_FORTE = r'migrat|migra[cç]|decompos|refactor|moderni[sz]|re-?architect|strangl|identif|extract|candidate|boundar|partition'
SEC = r'systematic|literature review|mapping study|survey|state of the art|state-of-the-art|review|tertiary|grey literature|overview'
DEC = r'decompos|identif|extract|candidate|cluster|partition|boundar|refactor|split'
PERF = r'performanc|scalab|latenc|\bvs\.?\b|versus|compar|cost|energy|benchmark|evaluat'
EXP = (r'case study|experience|lessons|industrial|challenge|benefit|smell|anti-pattern|issues|problems|empirical|'
       r'practice|step migration|industr')

ROTULO = {'P': '1 No tema: comparação ou desempenho', 'S': '2 No tema: estudo secundário',
          'E': '3 No tema: experiência ou estudo de caso', 'D': '4 No tema: técnica de decomposição',
          'O': '5 No tema: outros (processo, dados etc.)', 'A': '6 Conferir: só o resumo indica migração',
          'X': '7 Fora do tema'}


def classificar(u):
    t = n(u['title']); a = n(u['abstract'])
    no_tema = bool((re.search(MONO, t) and (re.search(MS, t) or re.search(MIG, t)))
                   or (re.search(MS, t) and re.search(MIG_FORTE, t)))
    resumo_forte = len(re.findall(r'migrat|decompos|refactor|moderni[sz]', a)) >= 2 and len(re.findall(r'monolith', a)) >= 2
    if not no_tema:
        return 'A' if resumo_forte else 'X'
    if re.search(SEC, t): return 'S'
    if re.search(DEC, t): return 'D'
    if re.search(PERF, t): return 'P'
    if re.search(EXP, t): return 'E'
    return 'O'


# ---- marcação dos estudos do TCC encontrados nas exportações -------------
def norm(t):
    return re.sub(r'[^a-z0-9]+', ' ', n(t)).strip()


ESTUDOS_TCC = {
    'E1': ('10.1109/mcc.2017.4250931', 'Processes, Motivations, and Issues for Migrating to Microservices'),
    'E2': ('10.1016/j.jss.2018.09.082', 'pains and gains of microservices'),
    'E3': ('10.1109/cinti.2018.8928192', 'Comparative Review of Microservices and Monolithic Architectures'),
    'E4': ('10.1007/978-3-030-06019-0_10', 'From Monolith to Microservices: A Classification of Refactoring Approaches'),
    'E5': ('10.3390/app10175797', 'From Monolithic Systems to Microservices: A Comparative Study of Performance'),
    'E6': ('10.1109/access.2022.3152803', 'Monolithic vs. Microservice Architecture: A Performance and Scalability Evaluation'),
    'E7': ('10.5753/sbrc.2022.222363', 'Avaliação de Desempenho de Dois Padrões de Resiliência'),
    'E8': ('10.1109/tse.2023.3287297', 'Decomposition of Monolith Applications Into Microservices Architectures: A Systematic Review'),
    'E9': ('10.5753/cibse.2024.28435', 'Migration of Monolithic Systems to Microservices using AI'),
    'E10': (None, 'Resilient Microservices: A Systematic Review of Recovery Patterns'),
    'E11': (None, 'Resiliência em microsserviços'),
}
for u in U:
    u['cat'] = classificar(u)
    nt = norm(u['title'])
    u['estudo'] = next((k for k, (doi, frag) in ESTUDOS_TCC.items()
                        if norm(frag) in nt or (doi and u['doi'] == doi)), '')

ordem = sorted(U, key=lambda u: (ROTULO[u['cat']], -int(u['year'] or 0), u['title']))
COLUNAS = ['ID', 'Pré-triagem (regex)', 'Sua decisão', 'Motivo da decisão', 'Título', 'Ano', 'Bases',
           'Estudo do TCC', 'DOI']
assert 'Resumo' not in COLUNAS
with open(os.path.join(DADOS, 'triagem.csv'), 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(COLUNAS)
    for i, u in enumerate(ordem, 1):
        w.writerow([f'R{i:03d}', ROTULO[u['cat']], '', '', u['title'], u['year'], ' + '.join(u['srcs']), u['estudo'],
                    u['doi'].replace('arxiv:', 'arXiv:')])

c = Counter(ROTULO[u['cat']] for u in U)
for k in sorted(c):
    print(f'{c[k]:5d}  {k}')
print('No tema (categorias 1 a 5):', sum(v for k, v in c.items() if k[0] in '12345'))
print('Estudos do TCC nas exportações:', sorted((u['estudo'] for u in U if u['estudo']), key=lambda s: int(s[1:])))
print('Ausentes das exportações:', [k for k in ESTUDOS_TCC if k not in {u['estudo'] for u in U}])
