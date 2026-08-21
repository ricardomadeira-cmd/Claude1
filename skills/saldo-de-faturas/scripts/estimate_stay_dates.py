#!/usr/bin/env python3
"""
Determine the check-in/checkout column value for a SAF-T invoice (as
returned by parse_saft.extract_invoices), with an honest confidence note.

Rule (given by the client):
  - If the invoice has ProductCode="Stay" line(s): the exact check-in and
    checkout are already embedded in the SAF-T line description(s) — no
    estimation needed, this is a confirmed fact from the source document.
  - If the invoice has ONLY ProductCode="ConsumptionItem" ("Taxa Turistica")
    lines: the tourist tax is charged at check-in, so its TaxPointDate is
    used as an ESTIMATED check-in. Checkout is deliberately NOT reported,
    because the tax formula (1€/adult/night, capped at 3€/adult) makes the
    line count/total ambiguous between "more adults, one night" and "fewer
    adults, several nights" — there is no way to resolve that from the SAF-T
    alone, so we say so explicitly rather than guess.
"""


def estimate(invoice):
    """invoice: one dict as yielded by parse_saft.extract_invoices.
    Returns dict with keys: column_value, confidence, note.
    """
    if invoice['has_stay'] and invoice['checkin'] and invoice['checkout']:
        return {
            'column_value': f"{invoice['checkin']} a {invoice['checkout']}",
            'confidence': 'Confirmado (SAF-T, linha Stay)',
            'note': '',
            'checkin_date': invoice['checkin'],
        }

    if invoice['has_stay'] and not invoice['checkin']:
        return {
            'column_value': 'Não determinável',
            'confidence': 'Sem dados',
            'note': "Linha 'Stay' presente mas sem datas legíveis na descrição.",
            'checkin_date': None,
        }

    # Only ConsumptionItem lines
    consumption_lines = invoice['consumption_lines']
    tax_point_dates = {l.get('TaxPointDate') for l in consumption_lines if l.get('TaxPointDate')}
    total_tax = sum(float(l.get('CreditAmount', 0) or 0) for l in consumption_lines)
    n_lines = len(consumption_lines)

    if len(tax_point_dates) == 1:
        checkin_est = next(iter(tax_point_dates))
        return {
            'column_value': f"Check-in estimado: {checkin_est}",
            'confidence': 'Estimativa (check-in apenas)',
            'note': (
                f"Sem linha 'Stay' no SAF-T. Check-in estimado pela TaxPointDate da Taxa "
                f"Turistica ({n_lines} linha(s) x 1,00€ = {total_tax:.2f}€), assumindo cobrança "
                f"no check-in. Checkout não determinável com segurança: o valor {total_tax:.2f}€ "
                f"é compatível tanto com {n_lines} adulto(s) x 1 noite como com menos adultos em "
                f"mais noites (tarifa 1€/adulto/noite, máx. 3€/adulto), pelo que o nº de noites é "
                f"ambíguo."
            ),
            'checkin_date': checkin_est,
        }

    return {
        'column_value': 'Não determinável',
        'confidence': 'Sem dados',
        'note': 'TaxPointDates inconsistentes entre linhas; não foi possível estimar check-in.',
        'checkin_date': None,
    }
