"""Etapa 2 - Remove duplicados entre bases e gera dados_brutos/intermediarios/unicos.json.

Dois registros são o mesmo estudo quando:
  (a) têm o mesmo DOI; ou
  (b) têm o mesmo título normalizado (minúsculas, sem acentos e sem pontuação); ou
  (c) o título normalizado de um (com 28 caracteres ou mais) é o início do
      título do outro, vêm de bases diferentes e os anos diferem em no máximo 1
      (captura subtítulos cortados e versões traduzidas).
Em cada grupo fica o registro da base com dados mais completos
(Scopus > IEEE > ACM > SOL > arXiv), e a coluna "Bases" lista todas.
"""
import json, re, os, unicodedata, bisect
from collections import Counter, defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAI = os.path.join(RAIZ, 'dados_brutos', 'intermediarios')
recs = json.load(open(os.path.join(SAI, 'registros.json')))


def norm(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()


parent = list(range(len(recs)))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x


def union(a, b):
    a, b = find(a), find(b)
    if a != b:
        parent[max(a, b)] = min(a, b)


bydoi = defaultdict(list); bytitle = defaultdict(list)
for i, r in enumerate(recs):
    r['nt'] = norm(r['title'])
    if r['doi'] and not r['doi'].startswith('arxiv:'):
        bydoi[r['doi']].append(i)
    bytitle[r['nt']].append(i)
for g in list(bydoi.values()) + list(bytitle.values()):
    for x in g[1:]:
        union(g[0], x)

nts = sorted(set(r['nt'] for r in recs))
for i, r in enumerate(recs):
    if len(r['nt']) >= 28:
        k = bisect.bisect_left(nts, r['nt'])
        for cand in nts[k:k + 4]:
            if cand != r['nt'] and cand.startswith(r['nt'] + ' '):
                j = bytitle[cand][0]
                if recs[j]['src'] != r['src'] and abs(int(recs[j]['year'] or 0) - int(r['year'] or 0)) <= 1:
                    print('  duplicado por prefixo:', r['src'], r['title'][:60], '<->', recs[j]['src'], recs[j]['title'][:60])
                    union(i, j)

groups = defaultdict(list)
for i in range(len(recs)):
    groups[find(i)].append(i)

pri = {'Scopus': 0, 'IEEE': 1, 'ACM': 2, 'SOL': 3, 'arXiv': 4}
U = []
for g in groups.values():
    g = sorted(g, key=lambda i: pri[recs[i]['src']])
    c = dict(recs[g[0]])
    c['srcs'] = sorted(set(recs[i]['src'] for i in g), key=lambda s: pri[s])
    c['n'] = len(g)
    if not c['abstract'].strip():
        for i in g:
            if recs[i]['abstract'].strip():
                c['abstract'] = recs[i]['abstract']; break
    U.append(c)
json.dump(U, open(os.path.join(SAI, 'unicos.json'), 'w'), ensure_ascii=False)

pairs = Counter()
for g in groups.values():
    if len(g) > 1:
        pairs[' + '.join(sorted(set(recs[i]['src'] for i in g), key=lambda s: pri[s]))] += len(g) - 1
print('A =', len(recs), '| duplicados (B) =', len(recs) - len(U), '| únicos =', len(U))
print('Duplicados por combinação de bases:', pairs.most_common())
