# Exemplo de Uso - Gerar Lista de Facturas Pendentes

## Cenário Completo

Este documento mostra como usar a skill dentro de uma sessão do Claude Code para gerar a lista PDF de facturas pendentes.

## Passo 1: Obter Lista de Facturas do MCP

Primeiro, precisamos chamar o MCP InvoiceXpress para obter a lista de facturas.

### Via Claude Code (Recomendado)

```python
# Usando tools MCP disponíveis em Claude Code
# Chamar: mcp__InvoiceExpress_MCP__list_invoices

# Sem parâmetros, retorna todas as facturas:
result = mcp_invoicexpress.list_invoices()

# Com filtros (opcional):
result = mcp_invoicexpress.list_invoices(state="open")
result = mcp_invoicexpress.list_invoices(state="pending")
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
        "name": "Cliente A"
      },
      "status": "open",
      "due_date": "2024-08-15",
      "total": 1500.00,
      "items": [
        {
          "type": "stay",
          "description": "Estadia",
          "properties": {
            "check_in": "2024-07-15",
            "check_out": "2024-07-18",
            "nights": 3
          }
        },
        {
          "type": "consumption",
          "description": "Mini bar",
          "quantity": 5,
          "unit_price": 10.00
        }
      ]
    },
    {
      "id": 1002,
      "invoice_number": "FT/2024/002",
      "client": {
        "id": 102,
        "name": "Cliente B"
      },
      "status": "open",
      "due_date": "2024-08-20",
      "total": 800.00,
      "items": [
        {
          "type": "stay",
          "properties": {
            "check_in": "2024-07-20",
            "check_out": "2024-07-22"
          }
        }
      ]
    }
  ]
}
```

## Passo 2: Processar Dados e Gerar PDF

Depois de obter os dados do MCP, processar com o script Python da skill:

```python
import json
import subprocess

# 1. Obter facturas (resultado anterior)
invoices = result['invoices']

# 2. Enviar para o script de processamento
# Opção A: Via stdin
for invoice in invoices:
    print(json.dumps(invoice))

# Opção B: Usar o script main.py
process = subprocess.Popen(
    ['python3', 'skills/gerar-lista-facturas-pendentes/main.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

input_data = '\n'.join(json.dumps(inv) for inv in invoices)
stdout, stderr = process.communicate(input=input_data)

print(stdout)
if stderr:
    print("Erros:", stderr)
```

## Passo 3: Devolver Ficheiro ao Utilizador

Após gerar o PDF, enviar ao utilizador:

```python
# Usar SendUserFile para entregar o PDF
# Assumindo que 'facturas_pendentes.pdf' foi gerado

from tools import SendUserFile

SendUserFile(
    files=['facturas_pendentes.pdf'],
    caption='Relatório de Facturas Pendentes',
    status='normal'
)
```

## Fluxo Completo em Python

```python
#!/usr/bin/env python3
"""
Script completo que chama MCP, processa e gera PDF.
"""

import json
import subprocess
import sys
from pathlib import Path

def main():
    # 1. Chamar MCP InvoiceXpress
    print("📥 Obtendo lista de facturas do InvoiceXpress...")
    
    # Nota: Em Claude Code, isto seria:
    # invoices_response = mcp_invoicexpress.list_invoices()
    # invoices = invoices_response.get('invoices', [])
    
    # Para demo, usar dados de exemplo:
    invoices = get_sample_invoices()
    
    # 2. Processar com script da skill
    print("⚙️  Processando facturas...")
    
    # Serializar facturas para JSON lines
    json_lines = '\n'.join(json.dumps(inv) for inv in invoices)
    
    # Chamar script Python
    script_path = 'skills/gerar-lista-facturas-pendentes/main.py'
    
    try:
        result = subprocess.run(
            ['python3', script_path],
            input=json_lines,
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        if result.stderr:
            print("Avisos:", result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            print(f"❌ Erro ao gerar PDF (código: {result.returncode})", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao chamar script: {e}", file=sys.stderr)
        return False
    
    # 3. Verificar se PDF foi gerado
    pdf_path = Path('facturas_pendentes.pdf')
    if pdf_path.exists():
        print(f"✅ PDF gerado: {pdf_path}")
        print(f"📊 Tamanho: {pdf_path.stat().st_size / 1024:.1f} KB")
        return True
    else:
        print("❌ PDF não foi gerado", file=sys.stderr)
        return False


def get_sample_invoices():
    """Dados de exemplo para testes."""
    return [
        {
            "id": 1001,
            "invoice_number": "FT/2024/001",
            "client": {"id": 101, "name": "Hotel Oslo"},
            "status": "open",
            "due_date": "2024-08-15",
            "total": 1500.00,
            "items": [
                {
                    "type": "stay",
                    "properties": {
                        "check_in": "2024-07-15",
                        "check_out": "2024-07-18"
                    }
                },
                {
                    "type": "consumption",
                    "description": "Mini bar"
                }
            ]
        },
        {
            "id": 1002,
            "invoice_number": "FT/2024/002",
            "client": {"id": 102, "name": "Pousada X"},
            "status": "open",
            "due_date": "2024-08-20",
            "total": 800.00,
            "items": [
                {
                    "type": "stay",
                    "properties": {
                        "check_in": "2024-07-20",
                        "check_out": "2024-07-22"
                    }
                }
            ]
        }
    ]


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
```

## Integração em Claude Code

### Como Skill

Se registada como skill no Claude Code:

```
/gerar-lista-facturas-pendentes
```

### Como Script via MCP

Usando o MCP InvoiceXpress diretamente:

```
1. Chamar: mcp__InvoiceExpress_MCP__list_invoices
2. Processar resultado com main.py
3. Devolver com SendUserFile
```

## Exemplos de Saída

### Console Output

```
✓ PDF gerado com sucesso: facturas_pendentes.pdf
  - Total de facturas: 5
  - Valor total: €4,200.50
  - Clientes: 3
```

### Conteúdo do PDF

```
╔════════════════════════════════════════════════════════════════╗
║   Facturas Pendentes de Pagamento                             ║
║   Gerado em 29/07/2024 às 14:35                               ║
╠════════════╦═════════════╦════════════╦═══════╦════════════╦══╣
║ Factura    ║ Cliente     ║ Vencimento ║ Tipo  ║ Datas     ║ Total║
╠════════════╬═════════════╬════════════╬═══════╬════════════╬══╣
║ FT/2024/001║ Hotel Oslo  ║ 2024-08-15 ║ Estadia/║ 15-18 Jul ║ €1.500║
║ FT/2024/002║ Hotel Oslo  ║ 2024-08-20 ║ Estadia║ 20-22 Jul ║ €800  ║
║ FT/2024/003║ Pousada X   ║ 2024-08-10 ║ Consumo║           ║ €500  ║
╠════════════╩═════════════╩════════════╩═══════╩════════════╩══╣
║ TOTAL:                                                  €4.200 ║
╚══════════════════════════════════════════════════════════════╝

Resumo: Total de 5 facturas | Valor total: €4,200.50
```

## Troubleshooting

### Nenhuma factura encontrada

```
⚠ Nenhuma factura para processar
```

**Solução:** Verificar se existem facturas com consumo ou estadia no InvoiceXpress.

### Erro ao gerar PDF

```
✗ reportlab não disponível
```

**Solução:** Instalar `pip install reportlab`

### JSON Parse Error

```
Erro ao fazer parse JSON
```

**Solução:** Verificar formato dos dados retornados pelo MCP.

## Performance

- **Número de facturas típico:** 10-100
- **Tempo de processamento:** 1-2 segundos
- **Tamanho do PDF:** 100-500 KB
- **Memória utilizada:** < 50 MB

## Notas

- ✅ Filtra automaticamente facturas com stay/consumption
- ✅ Organiza por cliente automaticamente
- ✅ Ordena por data de vencimento
- ✅ Calcula totais
- ✅ Gera PDF profissional formatado
- ⚠️ Requer reportlab instalado
- ⚠️ Requer acesso MCP InvoiceXpress
