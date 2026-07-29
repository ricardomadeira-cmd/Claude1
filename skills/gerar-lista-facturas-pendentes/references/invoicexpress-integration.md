# Integração com InvoiceXpress MCP

## Ferramentas MCP Utilizadas

### 1. `list_invoices`
Obtém a lista de todas as facturas.

**Parâmetros:**
- `state` (opcional): Filtrar por estado (e.g., "open", "pending")
- Retorna: Lista de facturas com todos os detalhes

**Resposta Esperada:**
```json
{
  "invoices": [
    {
      "id": 12345,
      "invoice_number": "FT/2024/001",
      "client": {
        "id": 789,
        "name": "Hotel Oslo"
      },
      "status": "open",
      "due_date": "2024-08-15",
      "total": 1500.00,
      "items": [
        {
          "type": "stay",
          "description": "Estadia 15-18 Julho",
          "properties": {
            "check_in": "2024-07-15",
            "check_out": "2024-07-18"
          }
        },
        {
          "type": "consumption",
          "description": "Consumo de bar",
          "quantity": 5,
          "unit_price": 20.00
        }
      ]
    }
  ]
}
```

### 2. `get_invoice` (opcional, se necessário detalhe adicional)
Obtém detalhes completos de uma factura específica.

**Parâmetros:**
- `invoice_id`: ID da factura

## Fluxo de Integração

```
1. Chamar list_invoices()
   ├─ Obter todas as facturas
   └─ Retorna array de facturas

2. Para cada factura:
   ├─ Verificar se tem items com type="stay" ou type="consumption"
   ├─ Se sim, processar e adicionar à lista
   ├─ Extrair datas de stays (check_in/check_out)
   └─ Se não, descartar

3. Organizar resultados:
   ├─ Agrupar por client.name
   └─ Ordenar por due_date

4. Gerar PDF com os dados processados
```

## Estrutura de Dados

### Tipos de Items Relevantes

#### `stay` - Estadia
- **Propriedades:**
  - `check_in`: Data de entrada
  - `check_out`: Data de saída
  - Opcional: número de noites, tipo de quarto
- **Descrição:** Geralmente contém informações sobre a estadia
- **Como usar:** Extrair check_in e check_out para mostrar período

#### `consumption` - Consumo
- **Propriedades:**
  - `quantity`: Quantidade
  - `unit_price`: Preço unitário
  - Descrição clara do que foi consumido
- **Descrição:** Bar, restaurante, serviços extras, etc
- **Como usar:** Identificar que factura tem consumos

### Tipos de Items a Ignorar

- `service` - Serviços gerais
- `tax` - Impostos
- `discount` - Descontos
- Outros tipos não relacionados com estadia ou consumo

## Filtragem

### Critérios de Inclusão
Incluir factura se:
- Tem pelo menos UM item com `type="stay"` OU
- Tem pelo menos UM item com `type="consumption"`

### Critérios de Exclusão
Excluir factura se:
- Não tem items do tipo relevante
- Status é "closed" ou "cancelled" (opcional, depende de requisito)

## Tratamento de Dados

### Datas de Vencimento
- Formato esperado: ISO 8601 (YYYY-MM-DD)
- Fallback: Tenta formato alternativo
- Se parsing falhar: Mostrar "N/A"

### Cliente
- Usar `client.name` se disponível
- Fallback: `client_name` ou ID do cliente
- Ordenação: Alfabética por nome

### Valores
- Usar campo `total` da factura
- Formato: Número decimal com até 2 casas
- Moeda: EUR (€)

## Tratamento de Erros

```python
try:
    invoices = mcp.list_invoices()
    for invoice in invoices:
        # processar
except Exception as e:
    # log erro e continuar com próxima
```

## Performance

- **Número de facturas esperado:** 100-500
- **Tempo de processamento:** < 5 segundos
- **Tamanho de resposta:** Típico 1-5 MB

## Exemplo de Comando MCP

```
Usando o MCP InvoiceXpress:

1. mcp__InvoiceExpress_MCP__list_invoices
   Parameters: (sem filtros ou com filters específicos)
   
2. Processar cada factura com parse_invoice()

3. Passar dados processados para gerar_pdf()
```
