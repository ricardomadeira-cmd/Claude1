# JSON normalizado

Criar um único ficheiro JSON antes da exportação.

```json
{
  "period_from": "2026-07-21",
  "period_to": "2026-07-28",
  "invoices": [
    {
      "invoicexpress_id": "123456789",
      "invoice_number": "OS2014/140387",
      "document_type": "invoice",
      "rectifies_invoice_number": "",
      "invoice_date": "2026-07-21",
      "booking_number": "59-5952432",
      "customer_name": "ISAAC HERRERO IBANEZ",
      "currency": "EUR",
      "gross_total": "86.64",
      "lines": [
        {
          "description": "Quartos - 20/07/2026-...",
          "service_date": "2026-07-20",
          "nights": 1,
          "quantity": 1,
          "net_amount": "81.74",
          "gross_amount": "86.64",
          "tax_rate": "6"
        }
      ]
    }
  ]
}
```

## Obrigatórios

Por fatura:

- `invoice_number`
- `invoice_date`
- `booking_number`
- `customer_name`
- `currency`
- `gross_total`
- pelo menos uma linha de alojamento

Por linha:

- `service_date`
- `nights`
- `quantity`
- `gross_amount` ou, em alternativa, `net_amount` + `tax_rate`

## Tipos de documento

- `invoice` -> `F`
- `credit_note` -> `FR`

Para notas de crédito, preencher `rectifies_invoice_number` quando a relação for conhecida.
