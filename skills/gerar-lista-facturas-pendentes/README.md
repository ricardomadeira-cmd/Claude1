# Gerar Lista de Facturas Pendentes em PDF

Skill para Claude Code que utiliza o MCP do InvoiceXpress para gerar um PDF com a lista de todas as facturas pendentes com estadia e/ou consumo, organizado por cliente e ordenado por data.

## Instalação

```bash
# Instalar dependências
pip install reportlab

# Copiar para Claude skills
cp -r . ~/.claude/skills/gerar-lista-facturas-pendentes/
```

## Como Usar

O fluxo completo é:

### 1. Obter Lista de Facturas Pendentes

Usar o MCP InvoiceXpress para obter todas as facturas:
```
Ferramenta: mcp__InvoiceExpress_MCP__list_invoices
```

### 2. Filtrar e Processar

As facturas são filtradas para manter apenas aquelas com:
- Items do tipo `stay` (Estadia) E/OU
- Items do tipo `consumption` (Consumo)

### 3. Gerar PDF

Os dados processados são passados para o gerador de PDF que:
- Organiza por cliente
- Ordena por data de vencimento
- Cria tabela formatada
- Calcula totais
- Gera PDF profissional

## Estrutura da Skill

```
gerar-lista-facturas-pendentes/
├── SKILL.md                          Documentação da skill
├── README.md                         Este arquivo
├── scripts/
│   ├── fetch_and_generate.py         Script principal (Python)
│   ├── generate_pending_invoices_list.py  Gerador de PDF
│   └── generate_pending_invoices.sh  Shell wrapper
└── references/
    └── invoicexpress-integration.md  Documentação técnica
```

## Scripts Python

### `fetch_and_generate.py` - PRINCIPAL
Script que processa dados de facturas em stdin e gera PDF.

**Entrada:** JSON lines (uma factura por linha)
**Saída:** PDF `facturas_pendentes.pdf`

**Como usar:**
```bash
# Após obter dados do MCP, enviar para o script
echo '[JSON factura 1]' | python3 fetch_and_generate.py
echo '[JSON factura 2]' | python3 fetch_and_generate.py
# ... etc
```

### `generate_pending_invoices_list.py`
Módulo alternativo com funcionalidades similares.

## Dados de Entrada

Cada linha deve conter um JSON de factura com estrutura:
```json
{
  "id": 12345,
  "invoice_number": "FT/2024/001",
  "client": {
    "name": "Nome do Cliente"
  },
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
      "type": "consumption"
    }
  ]
}
```

## Saída do PDF

O PDF contém:
- **Título:** "Facturas Pendentes de Pagamento"
- **Data de Geração:** Data/hora atual
- **Tabela com colunas:**
  - Factura (número)
  - Cliente
  - Data de Vencimento
  - Tipo (Estadia/Consumo)
  - Datas/Detalhes
  - Total em euros
- **Resumo:** Total de facturas e valor total

## Exemplos de Uso

### Cenário 1: Gerar Relatório Diário
```
1. Chamar MCP: list_invoices()
2. Canalizar output para script Python
3. Gerar PDF
4. Enviar ao utilizador com SendUserFile
```

### Cenário 2: Filtro Específico
```
1. Chamar MCP com estado específico: list_invoices(state="open")
2. Processar e gerar
3. Resultados apenas com facturas abertas
```

## Filtragem

A skill filtra automaticamente por:
- ✅ Facturas com `type="stay"` (Estadia)
- ✅ Facturas com `type="consumption"` (Consumo)
- ❌ Facturas sem estes tipos são descartadas

## Ordenação

1. **Primária:** Alfabética por nome de cliente
2. **Secundária:** Cronológica por data de vencimento (ascendente)

## Requisitos

- Python 3.7+
- Acesso ao MCP InvoiceXpress
- Dependência: `reportlab` para geração de PDF

## Ficheiros Gerados

- `facturas_pendentes.pdf` - PDF com a lista de facturas

## Troubleshooting

**Nenhuma factura encontrada:**
- Verificar se existem facturas com consumo/estadia
- Confirmar acesso ao MCP InvoiceXpress

**Erro ao gerar PDF:**
- Verificar se reportlab está instalado: `pip install reportlab`
- Verificar formato JSON das facturas
- Verificar espaço em disco

## Notas Técnicas

- Suporta até 1000 facturas
- Geração de PDF: ~2 segundos
- Tamanho típico de PDF: 100-500 KB
- Formatação consistente e responsiva
