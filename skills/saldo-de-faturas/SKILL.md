---
name: saldo-de-faturas
description: Identifica faturas do Hotel Oslo (com Stay/ConsumptionItem) genuinamente em dívida, cruzando SAF-T com o estado real "sent" no InvoiceExpress, e tenta associar cada uma a um Folio/check-in-checkout usando um export interno (Folios.ods). Usar sempre que for pedido "saldo de faturas", "faturas em dívida", "faturas por pagar" ou equivalente, sobretudo quando se quer distinguir estado do documento SAF-T de estado de pagamento real.
---

# Saldo de Faturas

## Objetivo

Produzir uma lista fiável de faturas realmente **em dívida** (não pagas), restrita
a faturas com estadia e/ou consumo, com uma coluna de check-in/checkout e,
quando possível, o número de Folio do sistema interno — sem inventar
correspondências quando a evidência não é suficiente.

## Porque este skill existe: o erro que corrige

O `InvoiceStatus` do SAF-T (tipicamente `"N"`) é o estado do **documento**
(normal / não anulado) — **não** diz se a fatura foi paga. Tratar `"N"` como
"não pago" infla brutalmente o valor em dívida (confirmado em produção: um
cálculo inicial deu ~€710.000 em ~2.900 faturas; o valor real, depois de
cruzar com o InvoiceExpress, era ~€84.000 em 352 faturas). **Nunca** saltar o
passo de cruzamento com o InvoiceExpress.

## Fluxo obrigatório

```text
Progresso
- [ ] Confirmar quais SAF-T (ano/mês) e qual export Folios estão disponíveis
- [ ] Obter TODAS as páginas de faturas status="sent" no InvoiceExpress, no
      intervalo de datas relevante, e guardar como JSON
- [ ] Extrair do(s) SAF-T as faturas com ProductCode "Stay" e/ou "ConsumptionItem"
- [ ] Correr run_saldo_faturas.py (cruzamento + check-in/checkout + Folio)
- [ ] Gerar o PDF com generate_report.py
- [ ] Rever candidatos "MAIS PRÓXIMO" e "AMBÍGUO" antes de entregar
- [ ] Entregar PDF com SendUserFile
```

Processar **por ano**, um SAF-T de cada vez, para não esgotar o contexto —
não tentar cruzar vários anos de uma vez a menos que o utilizador peça
explicitamente.

## Passo 1 — Faturas "sent" no InvoiceExpress

Chamar a ferramenta MCP de listagem de faturas do InvoiceExpress
(`list_invoices` ou equivalente disponível na sessão) com `status=["sent"]` e
o intervalo de datas do ano em causa (`due_date_from`/`due_date_to`, ou
equivalente). **Paginar até ao fim** — não assumir que a primeira página
contém tudo; confirmar sempre pela contagem total devolvida. Sem esta
verificação por status real, o resto do fluxo não tem valor.

Juntar todas as páginas, filtrar explicitamente por `status == "sent"`
(algumas listagens podem devolver outros estados misturados) e deduplicar por
`sequence_number`. Guardar o resultado como JSON, por exemplo:

```python
import json
with open('ie_sent_2025.json', 'w') as f:
    json.dump(all_sent_invoices, f)
```

## Passo 2 — Extrair faturas do SAF-T

Não é preciso correr nada à parte — `scripts/run_saldo_faturas.py` já chama
`scripts/parse_saft.py` internamente. Só interessa **confirmar que o(s) XML
do SAF-T do ano pedido estão disponíveis** (o utilizador normalmente anexa-os).

Regra de filtragem: só conta `ProductCode` exatamente `"Stay"` ou
`"ConsumptionItem"`. Outros códigos como `"Quartos"`, `"Bar"`, `"Suplemento"`,
`"Cafetaria ou Agua"` **não contam**, mesmo relacionados com a estadia — ver
`scripts/parse_saft.py` para a lista exata.

## Passo 3 — Correr o cruzamento

```bash
pip install reportlab  # se ainda não estiver instalado

python3 scripts/run_saldo_faturas.py \
  --saft caminho/SAF-T_2025_1_1.xml \
  --ie-sent ie_sent_2025.json \
  --folios caminho/Folios.ods \
  --year 2025 \
  --out saldo_2025.json
```

- `--saft` pode repetir-se para vários ficheiros do mesmo ano (ex. exports
  mensais).
- `--folios` aceita qualquer export `.ods` com a estrutura descrita em
  `scripts/load_folios.py` (colunas `FOLIO`, `REPORT SECTION`, `ROOM`,
  `Revenue`, `Source`, `Check-in`, `Correcção`, `Estabelecimento`, etc.). Se o
  utilizador não tiver este ficheiro, o script continua a funcionar — só não
  há coluna de Folio, fica apenas o check-in/checkout do SAF-T.
- O script escreve no stderr quantas faturas sobrevivem a cada etapa
  (SAF-T → cruzamento IE → resultado final). Usar isto para detetar
  problemas cedo (ex. 0 cruzamentos = provavelmente o dump `--ie-sent` não
  cobre o intervalo de datas certo).

## Passo 4 — Gerar o PDF

```bash
python3 scripts/generate_report.py --in saldo_2025.json --out saldo_faturas_2025.pdf --label 2025
```

## Regras de negócio (não alterar sem pedido explícito)

### Check-in/checkout
- Fatura com linha `Stay`: check-in/checkout vêm **diretamente** da descrição
  da linha (`"YYYY-MM-DD - YYYY-MM-DD"`), combinando várias linhas pela data
  mínima de início e máxima de fim. Isto é confirmado, não é estimativa.
- Fatura só com `ConsumptionItem` ("Taxa Turistica"): o check-in é
  **estimado** pela `TaxPointDate` (a taxa cobra-se no check-in). O checkout
  **nunca** é reportado nestes casos — a fórmula da taxa (1€/adulto/noite,
  máx. 3€/adulto) é ambígua entre "mais adultos, menos noites" e "menos
  adultos, mais noites", e não há como resolver isso só com o SAF-T.

### Correspondência de Folio (`scripts/match_folio.py`)
Aplicar por esta ordem, a primeira que se aplicar decide:
1. **Valor exato** (diferença < 1 cêntimo) entre o total bruto da fatura e o
   `Revenue` do Folios.ods na mesma data de check-in → mostrar **apenas** os
   candidatos exatos, descartar todos os outros por mais próximos que sejam.
   (Usar sempre o total **bruto**, com IVA — o `Revenue` do Folios.ods é
   bruto; comparar com o valor líquido do SAF-T dá falsos negativos.)
2. **Canal Airbnb**: se a fatura é da Airbnb e existe candidato com fonte
   `AirBnB`, mostrar só esse(s), mesmo sem valor exato.
3. **Grupo Expedia**: se a fatura é da Expedia (ou associada) e o candidato
   mais próximo em valor já é do grupo Expedia (Expedia, Hotels.com, Orbitz,
   Egencia, Expedia Affiliate Network, Travelocity, ebookers, CheapTickets,
   Wotif, Hotwire), mostrar só candidatos desse grupo. Se o mais próximo
   **não** for do grupo Expedia, esta regra não se aplica — não forçar um
   candidato Expedia pior só porque o cliente é Expedia.
4. Caso contrário: mostrar os 3 candidatos mais próximos, claramente
   identificados como não confirmados.

Quando o mesmo Folio (mesma data + mesmo valor exato) corresponde a mais do
que uma fatura, marcar como `AMBÍGUO (partilhado)` — não escolher
arbitrariamente qual fatura fica com o Folio.

## Regras não negociáveis

- Nunca tratar o estado do documento SAF-T como estado de pagamento. O único
  indicador de "não pago" é `status == "sent"` no InvoiceExpress, confirmado
  por chamada real à API/MCP nesse momento.
- Nunca atribuir um número de Folio sem correspondência exata de valor, ou
  sem correspondência de canal explicitamente justificada pelas regras acima.
  Um Folio errado é pior do que nenhum Folio.
- Nunca inventar checkout para faturas só com Taxa Turística.
- Processar SAF-T por ano — não tentar vários anos de uma vez sem pedido
  explícito do utilizador (evita esgotar o contexto em ficheiros SAF-T que
  são tipicamente dezenas de MB cada).

## Resposta ao utilizador

Entregar o PDF com `SendUserFile`. Resumir na conversa:
- total de faturas confirmadas em dívida e valor total;
- contagem por classificação (`CONFIRMADO` / `AMBÍGUO` / `MAIS PRÓXIMO`);
- qualquer limitação relevante (ex. período do Folios.ods não cobre todas as
  faturas, SAF-T de anos ainda não processados).
