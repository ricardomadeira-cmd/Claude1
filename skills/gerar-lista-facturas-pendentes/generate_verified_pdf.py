#!/usr/bin/env python3
"""
Generate PDF report of VERIFIED unpaid invoices (status="sent" in InvoiceExpress,
cross-referenced with SAFT ProductCode "Stay"/"ConsumptionItem").
"""

import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

TODAY = datetime(2026, 8, 21)

def load_verified_invoices():
    path = Path('/tmp/claude-0/-home-user-Claude1/6c51b181-91d0-53b2-8f26-92f079fce276/scratchpad/final_verified_unpaid.json')
    with open(path, 'r') as f:
        return json.load(f)

def generate_pdf(invoices, output_path='facturas_dívida_verificadas.pdf'):
    if not invoices:
        print("❌ No invoices to generate")
        return False

    by_customer = defaultdict(list)
    for inv in invoices:
        by_customer[inv.get('client_name', 'Desconhecido')].append(inv)

    for cust in by_customer:
        by_customer[cust].sort(key=lambda x: x.get('due_date', ''))

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=0.4*inch, bottomMargin=0.4*inch,
        leftMargin=0.5*inch, rightMargin=0.5*inch
    )
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=17,
        textColor=colors.HexColor('#c41e3a'), spaceAfter=6, alignment=1, fontName='Helvetica-Bold')
    elements.append(Paragraph('Facturas em Dívida - Verificadas no InvoiceExpress', title_style))

    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=9,
        textColor=colors.HexColor('#666666'), spaceAfter=4, alignment=1)
    elements.append(Paragraph(
        'Status "sent" confirmado no InvoiceExpress + ProductCode "Stay"/"ConsumptionItem" confirmado no SAFT',
        subtitle_style))

    total_amount = sum(inv.get('total', 0) for inv in invoices)
    elements.append(Paragraph(
        f'Período: 2025-01-01 a 2026-08-21 | Total: €{total_amount:,.2f}',
        subtitle_style))

    date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=8,
        textColor=colors.grey, spaceAfter=10, alignment=1)
    elements.append(Paragraph(f'Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}', date_style))
    elements.append(Spacer(1, 0.1*inch))

    stay_only = [m for m in invoices if m['has_stay'] and not m['has_consumption']]
    consumption_only = [m for m in invoices if m['has_consumption'] and not m['has_stay']]
    both = [m for m in invoices if m['has_stay'] and m['has_consumption']]

    summary_data = [
        ['Métrica', 'Valor'],
        ['Total de Facturas Verificadas', str(len(invoices))],
        ['Total em Dívida', f'€{total_amount:,.2f}'],
        ['Clientes Únicos', str(len(by_customer))],
        ['Apenas Stay', f"{len(stay_only)} - €{sum(m['total'] for m in stay_only):,.2f}"],
        ['Apenas ConsumptionItem', f"{len(consumption_only)} - €{sum(m['total'] for m in consumption_only):,.2f}"],
        ['Stay + ConsumptionItem', f"{len(both)} - €{sum(m['total'] for m in both):,.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[2.8*inch, 3.0*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph('Detalhes por Cliente', styles['Heading2']))
    elements.append(Spacer(1, 0.08*inch))

    sorted_customers = sorted(by_customer.items(), key=lambda x: sum(i['total'] for i in x[1]), reverse=True)

    for idx, (customer, cust_invoices) in enumerate(sorted_customers):
        if idx > 0 and idx % 6 == 0:
            elements.append(PageBreak())

        cust_total = sum(inv['total'] for inv in cust_invoices)
        cust_style = ParagraphStyle('CustomerHeader', parent=styles['Heading3'], fontSize=10,
            textColor=colors.HexColor('#1f4788'), spaceAfter=3, fontName='Helvetica-Bold')
        elements.append(Paragraph(
            f'{customer} - €{cust_total:,.2f} ({len(cust_invoices)} facturas)', cust_style))

        table_data = [['Factura', 'Vencimento', 'Dias Atraso', 'Tipo (SAFT)', 'Total (€)']]
        for inv in cust_invoices:
            due_date_str = inv['due_date'][:10]
            days_overdue = inv.get('days_overdue', '')
            item_type = []
            if inv['has_stay']:
                item_type.append('Stay')
            if inv['has_consumption']:
                item_type.append('ConsumptionItem')

            table_data.append([
                inv['sequence_number'],
                due_date_str,
                str(days_overdue),
                ' + '.join(item_type),
                f"{inv['total']:.2f}"
            ])

        table = Table(table_data, colWidths=[1.3*inch, 1.0*inch, 0.9*inch, 1.6*inch, 0.9*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 1), (-2, -1), 'LEFT'),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.1*inch))

    elements.append(Spacer(1, 0.15*inch))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    elements.append(Paragraph(
        f'<b>Resumo Final (Verificado):</b> {len(invoices)} facturas confirmadas em dívida | '
        f'Valor total: €{total_amount:,.2f} | {len(by_customer)} clientes',
        footer_style))

    doc.build(elements)
    print(f"✓ PDF gerado: {output_path}")
    print(f"  Facturas: {len(invoices)}")
    print(f"  Valor: €{total_amount:,.2f}")
    print(f"  Clientes: {len(by_customer)}")
    return True

if __name__ == '__main__':
    invoices = load_verified_invoices()
    generate_pdf(invoices)
