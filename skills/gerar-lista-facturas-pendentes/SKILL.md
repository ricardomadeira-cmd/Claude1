# Gerar Lista de Facturas Pendentes em PDF

Uma Skill que utiliza o MCP do InvoiceXpress para criar uma lista PDF de todas as facturas que estão por pagar na conta, filtrando apenas aquelas com **estadia e/ou consumo** (itens relacionados com o Hotel Oslo).

## Funcionalidades

- ✅ Lista todas as facturas pendentes de pagamento
- ✅ Filtra apenas facturas com items de estadia (`stay`) e/ou consumo (`consumption`)
- ✅ Inclui datas de estadia quando disponíveis
- ✅ Organiza facturas por cliente
- ✅ Ordena por data de vencimento
- ✅ Gera PDF formatado com tabla e informações estruturadas

## Dados Incluídos no PDF

Para cada factura:
- **Número de Factura**: ID da factura
- **Cliente**: Nome do cliente responsável
- **Data de Vencimento**: Quando a factura vence
- **Tipo**: Estadia e/ou Consumo
- **Datas de Estadia**: Período da estadia (se disponível)
- **Total**: Valor da factura em euros

## Instalação

```bash
# Instalar dependências para PDF
pip install reportlab

# Copiar skill para o diretório do Claude
cp -r . ~/.claude/skills/gerar-lista-facturas-pendentes/
```

## Uso

A skill utiliza o MCP do InvoiceXpress para:

1. **Listar todas as facturas pendentes** usando `list_invoices` com estado `pending`
2. **Filtrar por tipo de item** - manter apenas facturas com `stay` ou `consumption` items
3. **Extrair datas de estadia** das propriedades dos items
4. **Organizar dados** por cliente e data
5. **Gerar PDF** com formatação e tabela estruturada

## Fluxo

```
Requisição do Utilizador
        ↓
MCP InvoiceXpress: list_invoices()
        ↓
Filtrar facturas com estadia/consumo
        ↓
Extrair e processar dados
        ↓
Gerar PDF com reportlab
        ↓
Entregar PDF ao utilizador
```

## Exemplo de Saída

O PDF contém uma tabela com colunas:
- Factura
- Cliente  
- Data de Vencimento
- Tipo (Estadia/Consumo)
- Datas de Estadia
- Total

## Notas Técnicas

- Suporta facturas em qualquer estado (pending, open, etc)
- Valida a presença de `stay` ou `consumption` items
- Trata datas em múltiplos formatos
- Gera PDF com estilo consistente e legível
- Implementado em Python com reportlab
