"""Etapa 5 - Sorteia a amostra para estimar os falsos negativos da pré-classificação.

Falso negativo: registro que a regra pôs em "7 Fora do tema", mas que, lido por
uma pessoa, trata do tema (migração ou decomposição de monólitos, ou comparação
monólito x microsserviços).

Amostra: 50 registros sorteados com random.seed(42) entre os 489 registros da
categoria "7 Fora do tema" da classificação automática, na ordem em que aparecem
em dados/triagem.csv. Como a semente é fixa, qualquer pessoa obtém a mesma
amostra, e o sorteio não depende dos resumos (que não são publicados).

Saída: dados/amostra_falsos_negativos.csv, com as colunas
  semente, id_registro, titulo, ano, doi, bases, decisao_manual, justificativa
Preencha "decisao_manual" com sim, limítrofe ou não e rode 06_resultado_amostra.py.
Se o arquivo já existir, as decisões e justificativas já preenchidas são mantidas.
"""
import csv, os, random

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIAGEM = os.path.join(RAIZ, 'dados', 'triagem.csv')
SAIDA = os.path.join(RAIZ, 'dados', 'amostra_falsos_negativos.csv')
SEMENTE = 42
N = 50
COLUNAS = ['semente', 'id_registro', 'titulo', 'ano', 'doi', 'bases', 'decisao_manual', 'justificativa']

with open(TRIAGEM, encoding='utf-8', newline='') as fh:
    rows = list(csv.DictReader(fh))
fora = [r for r in rows if r['Pré-triagem (regex)'].startswith('7')]

random.seed(SEMENTE)
sorteados = random.sample(fora, N)

anteriores = {}
if os.path.exists(SAIDA):
    with open(SAIDA, encoding='utf-8', newline='') as fh:
        anteriores = {r['id_registro']: r for r in csv.DictReader(fh)}

with open(SAIDA, 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(COLUNAS)
    for r in sorteados:
        prev = anteriores.get(r['ID'], {})
        w.writerow([SEMENTE, r['ID'], r['Título'], r['Ano'], r['DOI'], r['Bases'],
                    prev.get('decisao_manual', ''), prev.get('justificativa', '')])

preenchidos = sum(bool(anteriores.get(r['ID'], {}).get('decisao_manual', '').strip()) for r in sorteados)
print(f'Amostra: {len(sorteados)} sorteados (semente {SEMENTE}) de {len(fora)} registros "7 Fora do tema"')
print(f'Decisões manuais preenchidas: {preenchidos}/{len(sorteados)}')
