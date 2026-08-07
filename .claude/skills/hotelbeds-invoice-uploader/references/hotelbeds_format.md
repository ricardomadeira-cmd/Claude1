# Formato Hotelbeds confirmado

## CSV principal

- Sem cabeçalho.
- 16 colunas.
- Separador: `;`.
- Decimal: vírgula.
- Datas: `dd-mm-yyyy`.
- Encoding: UTF-8 sem BOM.
- Line ending recomendado: CRLF.

## Ordem das colunas

1. `Invoice type`
2. `Nº invoice/ credit`
3. `Nº to rectify`
4. `Invoice date`
5. `Booking Nº`
6. `Services Description`
7. `Costumer Name`
8. `Service Date`
9. `Nº Days/ Nights`
10. `Quantity`
11. `Unit price`
12. `Currency`
13. `Tax`
14. `Tax Type`
15. `Line total`
16. `Invoice total`

## Exemplo de linha aceite como modelo

`F;OS2014/139303;;01-07-2026;59-5863226;Accommodation;TINE AHRENST RASMUSSEN;30-06-2026;1;1;220,00;EUR;6;VAT;220,00;220,00`

O exemplo ilustra estrutura, não deve ser reutilizado como dado.

## Valores por defeito

- Fatura: `F`.
- Nota de crédito: `FR`.
- Nº to rectify: vazio em faturas normais.
- Services Description: `Accommodation`.
- Nº Days/Nights: `1` por linha noturna.
- Quantity: `1` por linha noturna.
- Currency: `EUR`.
- Tax: `6`.
- Tax Type: `VAT`.
- Unit price / Line total / Invoice total: gross, com IVA incluído.
