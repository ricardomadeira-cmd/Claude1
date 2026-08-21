# Saldo de Faturas

Ver [SKILL.md](SKILL.md) para o fluxo completo e as regras de negócio. Este
ficheiro é só um resumo rápido de execução manual.

## Scripts

| Script | Função |
|---|---|
| `scripts/parse_saft.py` | Extrai do SAF-T as faturas com `ProductCode` "Stay"/"ConsumptionItem", incluindo check-in/checkout quando presente na descrição da linha "Stay". |
| `scripts/parse_ods.py` | Parser genérico de `.ods` (linhas cruas, lida com repetição de linhas/colunas do formato ODS). |
| `scripts/load_folios.py` | Carrega um export tipo "Folios.ods" para uma lista estruturada (`FolioRow`), detetando a linha de cabeçalho real. |
| `scripts/estimate_stay_dates.py` | Determina a coluna check-in/checkout de uma fatura (confirmado a partir do SAF-T, ou estimativa com nota quando só há Taxa Turística). |
| `scripts/match_folio.py` | Motor de correspondência de Folio com as regras de valor exato / canal Airbnb / grupo Expedia. |
| `scripts/run_saldo_faturas.py` | Orquestrador: junta tudo, produz um JSON de resultado. |
| `scripts/generate_report.py` | Gera o PDF final a partir do JSON de resultado. |

## Execução rápida

```bash
pip install reportlab

# 1. Ter à mão: XML(s) do SAF-T do ano, um JSON com as faturas
#    status="sent" do InvoiceExpress (obtido via MCP, ver SKILL.md), e o
#    Folios.ods (opcional, mas recomendado).

python3 scripts/run_saldo_faturas.py \
  --saft SAF-T_2025_1_1.xml \
  --ie-sent ie_sent_2025.json \
  --folios Folios.ods \
  --year 2025 \
  --out saldo_2025.json

python3 scripts/generate_report.py --in saldo_2025.json --out saldo_faturas_2025.pdf --label 2025
```

## Formato esperado de `--ie-sent`

Uma lista JSON (ou `{"invoices": [...]}`) de objetos com pelo menos:

```json
{
  "sequence_number": "OS2014/126241",
  "client_name": "Consumidor Final",
  "due_date": "2025-09-20 01:00:00 +0100",
  "total": 128.06,
  "status": "sent"
}
```

Corresponde diretamente ao formato devolvido pela ferramenta MCP de listagem
de faturas do InvoiceExpress.
