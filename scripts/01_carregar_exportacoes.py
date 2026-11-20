"""Etapa 1 - Lê as exportações das cinco bases e gera dados_brutos/intermediarios/registros.json.

Entradas (pasta dados_brutos/, não versionada, e saída da etapa 0):
  dados_brutos/scopus.csv, dados_brutos/ieee.csv      exportações CSV
  dados_brutos/intermediarios/acm_1-50.txt, acm_51-84.txt, sbc_openlib.txt, arxiv.txt
Cada registro recebe: base, título, ano, DOI, resumo (+ palavras-chave do
autor quando a base fornece), veículo, tipo, autores e número de páginas.
"""
import csv, json, re, os
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENT = os.path.join(RAIZ, 'dados_brutos')
SAI = os.path.join(ENT, 'intermediarios')
os.makedirs(SAI, exist_ok=True)
csv.field_size_limit(10**9)
recs = []


def add(src, title, year, doi, abstract='', venue='', dtype='', authors='', pages=''):
    recs.append(dict(src=src, title=re.sub(r'\s+', ' ', title).strip(), year=str(year).strip(),
                     doi=(doi or '').strip().lower().replace('https://doi.org/', ''),
                     abstract=abstract or '', venue=venue, dtype=dtype, authors=authors, pages=pages))


def npag(a, b):
    try:
        return str(int(b) - int(a) + 1)
    except (TypeError, ValueError):
        return ''


# Scopus (CSV)
with open(os.path.join(ENT, 'scopus.csv'), encoding='utf-8-sig', newline='') as fh:
    for r in csv.DictReader(fh):
        add('Scopus', r['Title'], r['Year'], r['DOI'], r['Abstract'] + ' ' + r['Author Keywords'],
            r['Source title'], r['Document Type'], r['Authors'], npag(r['Page start'], r['Page end']))

# IEEE Xplore (CSV)
with open(os.path.join(ENT, 'ieee.csv'), encoding='utf-8-sig', newline='') as fh:
    for r in csv.DictReader(fh):
        add('IEEE', r['Document Title'], r['Publication Year'], r['DOI'], r['Abstract'] + ' ' + r['Author Keywords'],
            r['Publication Title'], r['Document Identifier'], r['Authors'], npag(r['Start Page'], r['End Page']))

# ACM Digital Library (lista de resultados em PDF)
ACM_TYPES = ('ARTICLE', 'RESEARCH-ARTICLE', 'POSTER', 'SHORT-PAPER', 'ABSTRACT')
MONTH = r'(January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})'
for f in ['acm_1-50.txt', 'acm_51-84.txt']:
    lines = [l.rstrip() for l in open(os.path.join(SAI, f), encoding='utf-8')]
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        nxt = [k for k in range(i + 1, min(i + 4, len(lines))) if re.fullmatch(MONTH, lines[k].strip() or 'x')]
        if s in ACM_TYPES and nxt:
            dtype = s
            year = re.fullmatch(MONTH, lines[nxt[0]].strip()).group(2)
            j = nxt[0] + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            tl = []
            while j < len(lines) and lines[j].strip():
                tl.append(lines[j].strip()); j += 1
            k = j; doi = ''; block = []
            while k < len(lines) and k < j + 40:
                if lines[k].strip() in ACM_TYPES:
                    k -= 1; break
                m = re.search(r'https://doi\.org/(\S+)', lines[k])
                block.append(lines[k].strip())
                if m:
                    doi = m.group(1); break
                k += 1
            ab = []; k2 = k + 1
            while k2 < len(lines) and k2 < k + 8 and lines[k2].strip() and not lines[k2].strip().startswith('Highlights'):
                ab.append(lines[k2].strip()); k2 += 1
            venue = ' '.join(b for b in block if '•' in b and 'doi.org' not in b)
            pm = re.search(r'Pages? (\d+)[–-](\d+)', ' '.join(block))
            add('ACM', ' '.join(tl), year, doi, ' '.join(ab), venue, dtype, ' '.join(block[:3]),
                npag(pm.group(1), pm.group(2)) if pm else '')
            i = k
        i += 1

# SBC OpenLib (lista de resultados em PDF; não traz resumo nem DOI)
lines = [l.rstrip() for l in open(os.path.join(SAI, 'sbc_openlib.txt'), encoding='utf-8')]
i = 0
while i < len(lines):
    s = lines[i].strip()
    if s in ('ANAIS DE EVENTO', 'PERIÓDICOS'):
        j = i + 1; blk = []
        while j < len(lines):
            t = lines[j].strip()
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', t):
                break
            if t and not t.startswith('http') and 'Resultado da busca' not in t:
                blk.append(t)
            j += 1
        year = lines[j].strip()[:4] if j < len(lines) else ''
        tl = []; rest = []
        for b in blk:  # título vai até a primeira linha com cara de autores ("Sobrenome, Nome; ...")
            if not rest and not re.search(r'^[^,;]{2,40}, [^;]+(;|$)', b):
                tl.append(b)
            else:
                rest.append(b)
        add('SOL', ' '.join(tl), year, '', ' ', ' '.join(x for x in rest if x.isupper()), s,
            ' '.join(x for x in rest if not x.isupper()))
        i = j
    i += 1

# arXiv (lista de resultados em PDF)
txt = open(os.path.join(SAI, 'arxiv.txt'), encoding='utf-8').read()
for m in re.finditer(r'\n\s*(\d+)\. arXiv:(\d{4}\.\d{5}).*?\n\s*\n(.*?)\n\s*Authors:(.*?)\n\s*Abstract:(.*?)(?=\n\s*Submitted)', txt, re.S):
    add('arXiv', m.group(3), '20' + m.group(2)[:2], 'arxiv:' + m.group(2), re.sub(r'\s+', ' ', m.group(5)),
        'arXiv', 'preprint', re.sub(r'\s+', ' ', m.group(4)))

json.dump(recs, open(os.path.join(SAI, 'registros.json'), 'w'), ensure_ascii=False)
c = Counter(r['src'] for r in recs)
print('Registros por base:', dict(c), '| total (A) =', sum(c.values()))
