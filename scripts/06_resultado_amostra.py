"""Etapa 6 - Calcula a taxa de falsos negativos depois que a amostra foi preenchida.

Uso: python3 scripts/06_resultado_amostra.py [caminho do CSV preenchido]
(padrão: dados/amostra_falsos_negativos.csv)

A coluna "decisao_manual" aceita:
  sim                     claramente pertinente ao tema (falso negativo)
  limítrofe / limitrofe   pertinência discutível
  não / nao / n           fora do tema
O script informa duas taxas: só os claramente pertinentes (limite inferior) e
somando os limítrofes (limite superior), cada uma com intervalo de confiança de
95% de Wilson e a extrapolação para os 489 registros "7 Fora do tema".
"""
import csv, math, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
arq = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'dados', 'amostra_falsos_negativos.csv')
TOTAL_FORA = 489

with open(arq, encoding='utf-8', newline='') as fh:
    rows = list(csv.DictReader(fh))


def resp(v):
    v = v.strip().lower()
    if v in ('sim', 's'):
        return 'sim'
    if v in ('limítrofe', 'limitrofe', 'l'):
        return 'limítrofe'
    if v in ('não', 'nao', 'n'):
        return 'não'
    return None


def wilson(x, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = x / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


faltam = [r['id_registro'] for r in rows if resp(r['decisao_manual']) is None]
lidos = [r for r in rows if resp(r['decisao_manual']) is not None]
if faltam:
    print(f'{len(faltam)} de {len(rows)} linhas sem resposta válida em "decisao_manual":', ', '.join(faltam[:20]),
          '...' if len(faltam) > 20 else '')
if not lidos:
    sys.exit('Nenhuma linha preenchida; nada a calcular.')

n = len(lidos)
sim = sum(resp(r['decisao_manual']) == 'sim' for r in lidos)
lim = sum(resp(r['decisao_manual']) == 'limítrofe' for r in lidos)
for rotulo, x in (('Claramente pertinentes', sim), ('Pertinentes + limítrofes', sim + lim)):
    lo, hi = wilson(x, n)
    print(f'\n{rotulo}: {x} de {n} ({x / n:.1%})')
    print(f'  IC 95% (Wilson): {lo:.1%} a {hi:.1%}')
    print(f'  Estimativa para os {TOTAL_FORA} registros: cerca de {round(x / n * TOTAL_FORA)} '
          f'(entre {round(lo * TOTAL_FORA)} e {round(hi * TOTAL_FORA)})')

for grupo in ('sim', 'limítrofe'):
    itens = [r for r in lidos if resp(r['decisao_manual']) == grupo]
    if itens:
        print(f'\nRegistros marcados como "{grupo}":')
        for r in itens:
            print(f'  {r["id_registro"]} ({r["ano"]}) {r["titulo"][:90]}')
