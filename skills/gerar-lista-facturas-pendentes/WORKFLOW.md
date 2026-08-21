# Workflow Completo: Gerar PDF de Facturas Pendentes

## Overview

Este documento descreve o workflow completo para gerar um relatório PDF de facturas pendentes, filtrando por tipo de item (stay/consumption) e identificando aquelas em dívida.

## Fluxo de Dados

```
InvoiceXpress MCP
    ↓
List Invoices (unpaid)
    ↓
Filtrar por Stay/Consumption
    ↓
Skill: gerar-lista-facturas-pendentes
    ↓
PDF Report
    ↓
SendUserFile (ao utilizador)
```

## Passo 1: Chamar MCP InvoiceXpress

```
Ferramenta: mcp__InvoiceExpress_MCP__list_invoices
Parâmetros: 
  - state: "sent" (para facturas não pagas)
  - Opcionalmente: due_date_from, due_date_to para filtrar por data
```

### Resposta Esperada

```json
{
  "invoices": [
    {
      "id": 1001,
      "invoice_number": "FT/2024/001",
      "client": {
        "id": 101,
        "name": "Hotel Oslo"
      },
      "status": "sent",
      "due_date": "2024-08-15",
      "total": 1500.00,
      "items": [
        {
          "type": "stay",
          "description": "Estadia",
          "properties": {
            "check_in": "2024-07-15",
            "check_out": "2024-07-18"
          }
        },
        {
          "type": "consumption",
          "description": "Consumo de bar"
        }
      ]
    }
  ]
}
```

## Passo 2: Processar com a Skill

### Option A: Via Script (Recomendado)

```python
import json
import subprocess

# 1. Obter facturas do MCP (resultado anterior)
invoices = result['invoices']

# 2. Converter para JSON lines
json_lines = '\n'.join(json.dumps(inv) for inv in invoices)

# 3. Passar para skill
process = subprocess.Popen(
    ['python3', 'skills/gerar-lista-facturas-pendentes/main.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

stdout, stderr = process.communicate(input=json_lines)
print(stdout)
if stderr:
    print("Erros:", stderr)
```

### Option B: Via Bash Pipeline

```bash
# Gerar JSON lines
python3 get_invoices.py | \
  python3 skills/gerar-lista-facturas-pendentes/main.py

# Resultado: facturas_pendentes.pdf
```

## Passo 3: Enviar PDF ao Utilizador

```python
from tools import SendUserFile

SendUserFile(
    files=['facturas_pendentes.pdf'],
    caption='Relatório de Facturas Pendentes',
    status='normal'
)
```

## Análise de Dados

### Estrutura de Dados da Factura

Cada factura deve conter:
- `invoice_number`: Número da factura (string)
- `client.name`: Nome do cliente (string)
- `due_date`: Data de vencimento (ISO 8601)
- `total`: Valor total (float)
- `items`: Array de itens
  - Cada item deve ter `type` com um dos valores: `"stay"`, `"consumption"`
  - Items com `type="stay"` devem ter `properties.check_in` e `properties.check_out`

### Filtragem

A skill filtra automaticamente:
- ✅ Facturas com items `type="stay"` (Estadia)
- ✅ Facturas com items `type="consumption"` (Consumo)
- ❌ Outras facturas são descartadas

### Estatísticas do PDF

O relatório inclui:
- **Título:** "Facturas Pendentes de Pagamento"
- **Tabela com colunas:**
  - Número da Factura
  - Nome do Cliente
  - Data de Vencimento
  - Tipo (Estadia/Consumo)
  - Datas ou Detalhes
  - Total em euros
- **Resumo:** Total de facturas, valor total, número de clientes

## Exemplo Completo

### Input (JSON lines)

```json
{"id": 1001, "invoice_number": "FT/2024/001", "client": {"name": "Hotel Oslo"}, "status": "sent", "due_date": "2024-08-15", "total": 1500.00, "items": [{"type": "stay", "properties": {"check_in": "2024-07-15", "check_out": "2024-07-18"}}, {"type": "consumption"}]}
{"id": 1002, "invoice_number": "FT/2024/002", "client": {"name": "Pousada Montanha"}, "status": "sent", "due_date": "2024-08-20", "total": 800.00, "items": [{"type": "stay", "properties": {"check_in": "2024-07-20", "check_out": "2024-07-22"}}]}
```

### Output

```
✓ PDF gerado com sucesso: facturas_pendentes.pdf
  - Total de facturas: 2
  - Valor total: €2.300,00
  - Clientes: 2
```

### PDF Content

O PDF conterá uma tabela formatada com:
- FT/2024/001 | Hotel Oslo | 2024-08-15 | Estadia, Consumo | 15-18 Jul | €1.500,00
- FT/2024/002 | Pousada Montanha | 2024-08-20 | Estadia | 20-22 Jul | €800,00
- TOTAL: €2.300,00

## Requisitos

- Python 3.7+
- `reportlab` para geração de PDF: `pip install reportlab`
- Acesso ao MCP InvoiceXpress
- Claude Code com ferramentas MCP habilitadas

## Performance

- **Número de facturas típico:** 10-1000
- **Tempo de processamento:** 1-5 segundos
- **Tamanho do PDF:** 50-500 KB
- **Memória utilizada:** < 100 MB

## Filtragem Avançada

### Por Status (no MCP)

```
estado "sent" = não pago (padrão)
estado "settled" = pago
estado "draft" = rascunho
estado "canceled" = cancelado
```

### Por Data (no MCP)

```
due_date_from: "2024-01-01"
due_date_to: "2024-12-31"

invoice_date_from: "2024-01-01"
invoice_date_to: "2024-12-31"
```

## Troubleshooting

### "Nenhuma factura encontrada"

**Causa:** Facturas não têm items do tipo "stay" ou "consumption"

**Solução:** Verificar estrutura de items nas facturas do MCP

### "reportlab não disponível"

**Solução:** `pip install reportlab`

### PDF vazio ou com poucas facturas

**Verificar:** 
- Se o estado do MCP é realmente "sent" (não pago)
- Se as facturas têm items do tipo "stay" ou "consumption"
- Se o formato dos dados é correto

## Notas Técnicas

- A skill usa stdin/stdout para máxima flexibilidade
- Suporta até ~5000 facturas por execução
- Quebra de páginas automática se necessário
- Formatação responsiva com tabelas bem estruturadas
- Cores padrão corporate (azul #1f4788 para headers)

## Integração com Claude Code

### Como Skill

Se registada como skill no Claude Code, pode ser invocada com:

```
/gerar-lista-facturas-pendentes
```

Isso requer a configuração adequada no arquivo SKILL.md da skill.

### Como Script Manual

```bash
# Obter facturas
python3 get_ie_invoices.py > invoices.jsonl

# Gerar PDF
cat invoices.jsonl | python3 skills/gerar-lista-facturas-pendentes/main.py

# Enviar ao utilizador
# SendUserFile(['facturas_pendentes.pdf'])
```
