#!/usr/bin/env python3
"""
Generate PDF report of unpaid invoices (>90 days) from SAFT data.
"""

import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("⚠️  reportlab not installed. Install: pip install reportlab")
    exit(1)

def load_unpaid_invoices():
    """Load SAFT-based unpaid invoices."""
    path = Path('/tmp/claude-0/-home-user-Claude1/6c51b181-91d0-53b2-8f26-92f079fce276/scratchpad/invoices_unpaid_stay_consumption_90days.json')
    with open(path, 'r') as f:
        return json.load(f)

def generate_pdf(invoices, output_path='facturas_dívida_pendentes.pdf'):
    """Generate PDF report of unpaid invoices."""
    if not invoices:
        print("❌ No invoices to generate")
        return False

    # Group by customer
    by_customer = defaultdict(list)
    for inv in invoices:
        cust = inv.get('customer_name', 'Unknown')
        by_customer[cust].append(inv)

    # Sort invoices by due date within each customer
    for cust in by_customer:
        by_customer[cust].sort(key=lambda x: x.get('invoice_date', ''), reverse=True)

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=0.4*inch,
        bottomMargin=0.4*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#c41e3a'),  # Red for debt/overdue
        spaceAfter=6,
        alignment=1,
        fontName='Helvetica-Bold'
    )
    title = Paragraph('Facturas em Dívida - Pendentes de Pagamento', title_style)
    elements.append(title)

    # Subtitle with details
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=6,
        alignment=1,
    )
    total_amount = sum(inv.get('total', 0) for inv in invoices)
    subtitle = Paragraph(
        f'Invoices >90 days overdue | Total: €{total_amount:,.2f}',
        subtitle_style
    )
    elements.append(subtitle)

    # Generation date
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=1,
    )
    date_text = Paragraph(
        f'Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
        date_style
    )
    elements.append(date_text)
    elements.append(Spacer(1, 0.15 * inch))

    # Summary table
    summary_data = [
        ['Métrica', 'Valor'],
        ['Total de Facturas', str(len(invoices))],
        ['Total em Dívida', f'€{total_amount:,.2f}'],
        ['Clientes Únicos', str(len(by_customer))],
    ]

    summary_table = Table(summary_data, colWidths=[2.5*inch, 2.0*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Customer details
    elements.append(Paragraph('Detalhes por Cliente', styles['Heading2']))
    elements.append(Spacer(1, 0.1 * inch))

    # Sort customers by amount owed (descending)
    sorted_customers = sorted(by_customer.items(), key=lambda x: sum(inv.get('total', 0) for inv in x[1]), reverse=True)

    # Detailed table for each customer (limit to top 50 customers to keep PDF manageable)
    for customer_idx, (customer, customer_invoices) in enumerate(sorted_customers[:50]):
        if customer_idx > 0 and customer_idx % 5 == 0:  # Page break every 5 customers
            elements.append(PageBreak())

        customer_total = sum(inv.get('total', 0) for inv in customer_invoices)

        # Customer header
        cust_style = ParagraphStyle(
            'CustomerHeader',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=4,
            fontName='Helvetica-Bold'
        )
        cust_header = Paragraph(
            f'{customer} - €{customer_total:,.2f} ({len(customer_invoices)} facturas)',
            cust_style
        )
        elements.append(cust_header)

        # Customer invoices table
        table_data = [['Factura', 'Data', 'Dias Vencido', 'Tipo', 'Total (€)']]

        for inv in customer_invoices[:20]:  # Limit to 20 invoices per customer in table
            invoice_no = inv.get('invoice_no', 'N/A')
            invoice_date = inv.get('invoice_date', 'N/A')
            days_overdue = inv.get('days_overdue_estimate', 0)
            item_type = []
            if inv.get('has_stay'):
                item_type.append('Estadia')
            if inv.get('has_consumption'):
                item_type.append('Consumo')

            table_data.append([
                invoice_no,
                invoice_date,
                str(days_overdue),
                ', '.join(item_type) if item_type else 'Outro',
                f"{inv.get('total', 0):.2f}"
            ])

        if len(customer_invoices) > 20:
            table_data.append(['...', '...', '...', '...', '...'])

        table = Table(table_data, colWidths=[1.2*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch])
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
        elements.append(Spacer(1, 0.12 * inch))

    # Footer
    elements.append(Spacer(1, 0.2 * inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=0,
    )
    footer = Paragraph(
        f'<b>Resumo Final:</b> {len(invoices)} facturas em dívida | Valor total: €{total_amount:,.2f} | {len(by_customer)} clientes',
        footer_style
    )
    elements.append(footer)

    # Generate PDF
    try:
        doc.build(elements)
        print(f"✓ PDF gerado com sucesso: {output_path}")
        print(f"  - Total de facturas: {len(invoices)}")
        print(f"  - Valor total: €{total_amount:,.2f}")
        print(f"  - Clientes: {len(by_customer)}")
        return True
    except Exception as e:
        print(f"✗ Erro ao gerar PDF: {e}")
        return False

if __name__ == '__main__':
    print("🔍 Loading unpaid invoices from SAFT...")
    invoices = load_unpaid_invoices()
    print(f"✓ Loaded {len(invoices)} invoices")

    print("\n📄 Generating PDF...")
    success = generate_pdf(invoices)

    if success:
        pdf_path = Path('/tmp/claude-0/-home-user-Claude1/6c51b181-91d0-53b2-8f26-92f079fce276/scratchpad/facturas_dívida_pendentes.pdf')
        print(f"\n✓ File ready at: {pdf_path}")
