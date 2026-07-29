#!/usr/bin/env python3
"""
Gera uma lista PDF de todas as facturas por pagar com estadia ou consumo.
Organiza por cliente e ordena por data.
"""

import json
import sys
from datetime import datetime
from typing import Optional
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors


def parse_invoice_data(invoice_dict: dict) -> Optional[dict]:
    """
    Extrai informações relevantes de uma factura.
    Retorna None se não tiver stays ou consumption items.
    """
    invoice_id = invoice_dict.get('id')
    client_name = invoice_dict.get('client', {}).get('name', 'Desconhecido')
    invoice_number = invoice_dict.get('invoice_number', 'N/A')
    due_date_str = invoice_dict.get('due_date', '')

    # Parse due date
    try:
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
    except:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except:
            due_date = None

    # Verificar se tem stays ou consumption items
    items = invoice_dict.get('items', [])
    has_stays = False
    has_consumption = False
    stay_dates = []

    for item in items:
        item_type = item.get('type', '').lower()

        if item_type == 'stay':
            has_stays = True
            # Tentar extrair datas da descrição
            description = item.get('description', '')
            properties = item.get('properties', {})

            if properties:
                if isinstance(properties, dict):
                    check_in = properties.get('check_in')
                    check_out = properties.get('check_out')
                    if check_in and check_out:
                        stay_dates.append(f"{check_in} a {check_out}")
                    elif check_in:
                        stay_dates.append(f"Entrada: {check_in}")

        elif item_type == 'consumption':
            has_consumption = True

    if not (has_stays or has_consumption):
        return None

    # Formatar datas de estadia
    stay_info = '; '.join(stay_dates) if stay_dates else ('Estadia' if has_stays else '')

    return {
        'invoice_id': invoice_id,
        'invoice_number': invoice_number,
        'client_name': client_name,
        'due_date': due_date,
        'due_date_str': due_date_str,
        'has_stays': has_stays,
        'has_consumption': has_consumption,
        'stay_info': stay_info,
        'total': invoice_dict.get('total', 0),
    }


def generate_pdf(invoices_data: list, output_path: str = 'pending_invoices.pdf'):
    """
    Gera um PDF com a lista de facturas pendentes.
    """
    # Ordenar por cliente e depois por data
    invoices_data.sort(key=lambda x: (x['client_name'], x['due_date'] or datetime.max.date()))

    # Agrupar por cliente
    by_client = defaultdict(list)
    for invoice in invoices_data:
        by_client[invoice['client_name']].append(invoice)

    # Criar documento PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=1,  # center
    )
    title = Paragraph('Facturas Pendentes de Pagamento', title_style)
    elements.append(title)

    # Data de geração
    generated_date = Paragraph(
        f'<i>Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}</i>',
        styles['Normal']
    )
    elements.append(generated_date)
    elements.append(Spacer(1, 0.2 * inch))

    # Tabela de facturas
    table_data = [['Factura', 'Cliente', 'Data de Vencimento', 'Tipo', 'Estadia/Consumo', 'Total']]

    for client_name in sorted(by_client.keys()):
        invoices = by_client[client_name]

        for invoice in invoices:
            item_type = []
            if invoice['has_stays']:
                item_type.append('Estadia')
            if invoice['has_consumption']:
                item_type.append('Consumo')

            table_data.append([
                invoice['invoice_number'],
                invoice['client_name'],
                invoice['due_date_str'][:10] if invoice['due_date_str'] else 'N/A',
                ', '.join(item_type),
                invoice['stay_info'],
                f"€ {invoice['total']:.2f}"
            ])

    # Estilo da tabela
    table = Table(table_data, colWidths=[1.0*inch, 1.5*inch, 1.2*inch, 0.8*inch, 1.2*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))

    elements.append(table)

    # Gerar PDF
    doc.build(elements)
    print(f"PDF gerado com sucesso: {output_path}")
    print(f"Total de facturas: {len(invoices_data)}")


def main():
    """
    Lê dados de facturas do stdin e gera PDF.
    """
    try:
        invoices_data = []

        # Ler dados do stdin (JSON lines format)
        for line in sys.stdin:
            if line.strip():
                invoice_dict = json.loads(line)
                parsed = parse_invoice_data(invoice_dict)
                if parsed:
                    invoices_data.append(parsed)

        if not invoices_data:
            print("Nenhuma factura com estadia ou consumo encontrada.", file=sys.stderr)
            sys.exit(1)

        # Gerar PDF
        output_file = 'facturas_pendentes.pdf'
        generate_pdf(invoices_data, output_file)

    except Exception as e:
        print(f"Erro ao processar facturas: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
