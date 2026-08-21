#!/usr/bin/env python3
"""
Generate the "Saldo de Faturas" PDF report from a JSON result produced by
run_saldo_faturas.py.

Usage:
  python3 generate_report.py --in saldo_2025.json --out saldo_2025.pdf --label 2025
"""
import argparse
import json
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors

LABEL_COLORS = {
    'CONFIRMADO': colors.HexColor('#1a7a1a'),
    'AMBÍGUO': colors.HexColor('#b8860b'),
    'AMBÍGUO (partilhado)': colors.HexColor('#b8860b'),
    'SEM CANDIDATOS': colors.HexColor('#888888'),
}


def label_color(label):
    return LABEL_COLORS.get(label, colors.HexColor('#a83232'))  # MAIS PRÓXIMO variants


def build_pdf(results, output_path, period_label=''):
    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        topMargin=0.35 * inch, bottomMargin=0.35 * inch,
        leftMargin=0.4 * inch, rightMargin=0.4 * inch,
    )
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=15,
        textColor=colors.HexColor('#c41e3a'), spaceAfter=3, alignment=1, fontName='Helvetica-Bold')
    title = 'Saldo de Faturas — Facturas em Dívida'
    if period_label:
        title += f' ({period_label})'
    elements.append(Paragraph(title, title_style))

    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=8.5,
        textColor=colors.HexColor('#666666'), spaceAfter=3, alignment=1)
    elements.append(Paragraph(
        'Facturas com ProductCode "Stay"/"ConsumptionItem" no SAF-T, confirmadas como status "sent" '
        '(não pagas) no InvoiceExpress, com check-in/checkout e correspondência de Folio quando possível.',
        subtitle_style))

    date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=8, textColor=colors.grey,
        alignment=1, spaceAfter=8)
    elements.append(Paragraph(f'Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}', date_style))
    elements.append(Spacer(1, 0.1 * inch))

    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=7.5, leading=9)
    cand_style = ParagraphStyle('Cand', parent=styles['Normal'], fontSize=6.8, leading=8.5)

    table_data = [['Factura', 'Cliente', 'Check-in/out', 'Total (€)', 'Classificação', 'Candidato(s) de Folio']]

    total_amount = 0.0
    for item in sorted(results, key=lambda x: x['invoice']['invoice_date'] or ''):
        inv = item['invoice']
        label = item['label']
        cands = item['candidates']
        total_amount += inv['total']

        color = label_color(label)
        note_html = ''
        if label == 'AMBÍGUO (partilhado)' and item.get('shared_with'):
            note_html = f"<br/><font size=6 color='#666666'>Mesmo Folio também bate certo com: {', '.join(item['shared_with'])}</font>"

        class_style = ParagraphStyle('ClassX', parent=styles['Normal'], fontSize=8,
            fontName='Helvetica-Bold', textColor=color, leading=10)
        class_para = Paragraph(f"<b>{label}</b>{note_html}", class_style)

        lines = []
        for c in cands:
            if 'room' in c:
                l = (f"Folio {c['folio']} · quarto {c['room']} · €{c['revenue']:.2f} · "
                     f"diff €{c['diff']:.2f} · {c['estabelecimento']} · {c['source']}")
            else:
                l = f"Folio {c['folio']} · taxa €{c['total_tax']:.2f} · diff €{c['diff']:.2f} · {c['estabelecimento']}"
            if c['diff'] < 0.01:
                l = f"<b>{l}</b>"
            lines.append(l)
        if not lines:
            lines = ['Sem candidatos nesta data.']
        cand_para = Paragraph('<br/>'.join(lines), cand_style)

        note_dates = f"<br/><font size=6 color='#8a6d00'>{inv['note_dates']}</font>" if inv['note_dates'] else ''
        checkin_para = Paragraph(inv['checkin_checkout_column'] + note_dates, cell_style)

        table_data.append([
            Paragraph(inv['sequence_number'], cell_style),
            Paragraph(inv['client_name'], cell_style),
            checkin_para,
            f"{inv['total']:.2f}",
            class_para,
            cand_para,
        ])

    table = Table(table_data, colWidths=[1.0*inch, 1.35*inch, 1.6*inch, 0.7*inch, 1.6*inch, 4.45*inch], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f7f7')]),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.12 * inch))

    summary_style = ParagraphStyle('Summary', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')
    elements.append(Paragraph(f'Total: {len(results)} facturas | €{total_amount:,.2f}', summary_style))
    elements.append(Spacer(1, 0.1 * inch))

    legend_style = ParagraphStyle('Legend', parent=styles['Normal'], fontSize=7.5, textColor=colors.grey, leading=10)
    elements.append(Paragraph(
        '<b>Regras de correspondência de Folio:</b><br/>'
        '1) Se existir(em) candidato(s) com valor exato (ao cêntimo), mostram-se APENAS esses.<br/>'
        '2) Factura Airbnb + candidato de fonte "AirBnB": mostra-se APENAS esse(s), mesmo sem valor exato.<br/>'
        '3) Factura Expedia (ou associada) + candidato mais próximo já do grupo Expedia (Expedia, Hotels.com, '
        'Orbitz, Egencia, Expedia Affiliate Network, etc.): mostram-se APENAS candidatos desse grupo. '
        'Se o mais próximo não for do grupo Expedia, mantém-se a lista normal.<br/>'
        '4) Caso contrário, mostram-se os 3 candidatos mais próximos, como referência, sem confiança de correspondência.<br/><br/>'
        '<b>Check-in/checkout:</b> quando a factura tem linha "Stay" no SAF-T, as datas vêm diretamente da '
        'descrição da linha (confirmado, não é estimativa). Quando só há "Taxa Turistica", o check-in é '
        'estimado pela data de cobrança da taxa (cobrada no check-in); o checkout não é reportado porque a '
        'fórmula da taxa (1€/adulto/noite, máx. 3€/adulto) não permite distinguir com segurança "mais adultos, '
        'menos noites" de "menos adultos, mais noites".<br/><br/>'
        '<b>Classificação:</b> <b><font color="#1a7a1a">CONFIRMADO</font></b> = valor exato e único. '
        '<b><font color="#b8860b">AMBÍGUO</font></b> = valor exato mas partilhado por mais do que uma factura '
        'ou por vários Folios. <b><font color="#a83232">MAIS PRÓXIMO</font></b> = nenhum valor exato; '
        'mostra-se referência apenas.',
        legend_style,
    ))

    doc.build(elements)
    return len(results), total_amount


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='input', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--label', default='', help='Period label for the title, e.g. "2025"')
    args = ap.parse_args()

    with open(args.input) as f:
        results = json.load(f)

    n, total = build_pdf(results, args.out, period_label=args.label)
    print(f"✓ PDF gerado: {args.out}")
    print(f"  Facturas: {n} | Total: €{total:,.2f}")


if __name__ == '__main__':
    main()
