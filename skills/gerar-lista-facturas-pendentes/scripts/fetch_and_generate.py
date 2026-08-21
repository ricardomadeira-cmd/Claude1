#!/usr/bin/env python3
"""
Script que utiliza o MCP InvoiceXpress para obter facturas pendentes
e gera um PDF com a lista organizada por cliente e ordenada por data.

Este script é o orquestrador principal que:
1. Conecta ao MCP InvoiceXpress
2. Lista todas as facturas pendentes
3. Filtra por estadia e/ou consumo
4. Gera PDF com formatação
"""

import json
import sys
from datetime import datetime
from typing import Optional, List, Dict
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors


def parse_invoice(invoice_dict: dict) -> Optional[dict]:
    """
    Extrai informações relevantes de uma factura.
    Retorna None se não tiver stays ou consumption items.
    """
    try:
        invoice_id = invoice_dict.get('id')
        client_data = invoice_dict.get('client', {})

        if isinstance(client_data, dict):
            client_name = client_data.get('name', 'Desconhecido')
        else:
            client_name = str(client_data) if client_data else 'Desconhecido'

        invoice_number = invoice_dict.get('invoice_number', 'N/A')
        due_date_str = invoice_dict.get('due_date', '')
        status = invoice_dict.get('status', 'unknown')

        # Parse due date
        due_date = None
        try:
            if due_date_str:
                # Tenta formato ISO
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        except:
            try:
                # Tenta formato YYYY-MM-DD
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except:
                pass

        # Verificar se tem stays ou consumption items
        items = invoice_dict.get('items', [])
        has_stays = False
        has_consumption = False
        stay_dates = []

        for item in items:
            item_data = item if isinstance(item, dict) else {}
            item_type = item_data.get('type', '').lower() if isinstance(item_data.get('type'), str) else ''

            if item_type == 'stay':
                has_stays = True
                # Tentar extrair datas da descrição ou properties
                description = item_data.get('description', '')
                properties = item_data.get('properties', {})

                if isinstance(properties, dict):
                    check_in = properties.get('check_in')
                    check_out = properties.get('check_out')
                    if check_in and check_out:
                        stay_dates.append(f"{check_in} a {check_out}")
                    elif check_in:
                        stay_dates.append(f"Entrada: {check_in}")

                # Se não tem properties, tenta extrair da descrição
                if description and not stay_dates:
                    stay_dates.append(description)

            elif item_type == 'consumption' or 'consumption' in item_type.lower():
                has_consumption = True

        if not (has_stays or has_consumption):
            return None

        # Formatar datas de estadia
        stay_info = '; '.join(stay_dates) if stay_dates else ('Estadia' if has_stays else '')
        if has_consumption and not stay_info:
            stay_info = 'Consumo'

        total = float(invoice_dict.get('total', 0)) if invoice_dict.get('total') else 0

        return {
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'client_name': client_name,
            'due_date': due_date,
            'due_date_str': due_date_str[:10] if due_date_str else 'N/A',
            'has_stays': has_stays,
            'has_consumption': has_consumption,
            'stay_info': stay_info,
            'total': total,
            'status': status,
        }
    except Exception as e:
        print(f"Erro ao processar factura {invoice_dict.get('id', 'unknown')}: {e}", file=sys.stderr)
        return None


def generate_pdf(invoices_data: List[dict], output_path: str = 'facturas_pendentes.pdf') -> None:
    """
    Gera um PDF com a lista de facturas pendentes.
    """
    if not invoices_data:
        print("Nenhuma factura encontrada para gerar PDF", file=sys.stderr)
        return

    # Ordenar por cliente e depois por data
    invoices_data.sort(key=lambda x: (
        x['client_name'].lower(),
        x['due_date'] if x['due_date'] else datetime.max.date()
    ))

    # Agrupar por cliente
    by_client = defaultdict(list)
    for invoice in invoices_data:
        by_client[invoice['client_name']].append(invoice)

    # Criar documento PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=6,
        alignment=1,  # center
        fontName='Helvetica-Bold'
    )
    title = Paragraph('Facturas Pendentes de Pagamento', title_style)
    elements.append(title)

    # Data de geração
    generated_style = ParagraphStyle(
        'Generated',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=1,
    )
    generated_date = Paragraph(
        f'Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
        generated_style
    )
    elements.append(generated_date)
    elements.append(Spacer(1, 0.1 * inch))

    # Tabela de facturas
    table_data = [['Factura', 'Cliente', 'Vencimento', 'Tipo', 'Datas/Detalhes', 'Total (€)']]

    total_amount = 0
    for client_name in sorted(by_client.keys()):
        invoices = by_client[client_name]

        for invoice in invoices:
            item_type = []
            if invoice['has_stays']:
                item_type.append('Estadia')
            if invoice['has_consumption']:
                item_type.append('Consumo')

            total_amount += invoice['total']

            table_data.append([
                invoice['invoice_number'],
                invoice['client_name'],
                invoice['due_date_str'],
                ', '.join(item_type),
                invoice['stay_info'],
                f"{invoice['total']:.2f}"
            ])

    # Linha de totais
    table_data.append([
        '',
        '',
        '',
        '',
        'TOTAL:',
        f"{total_amount:.2f}"
    ])

    # Estilo da tabela
    num_rows = len(table_data)
    table = Table(
        table_data,
        colWidths=[1.0*inch, 1.6*inch, 1.0*inch, 1.0*inch, 1.6*inch, 0.9*inch]
    )

    table_style = [
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        # Data rows
        ('ALIGN', (0, 1), (-2, -2), 'LEFT'),
        ('ALIGN', (-1, 1), (-1, -2), 'RIGHT'),
        ('FONTSIZE', (0, 1), (-1, -2), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),

        # Grid
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),

        # Total row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (-1, -1), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
    ]

    table.setStyle(TableStyle(table_style))
    elements.append(table)

    # Rodapé com resumo
    elements.append(Spacer(1, 0.2 * inch))
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=0,
    )
    summary = Paragraph(
        f'<b>Resumo:</b> Total de {len(invoices_data)} facturas | Valor total: €{total_amount:.2f}',
        summary_style
    )
    elements.append(summary)

    # Gerar PDF
    try:
        doc.build(elements)
        print(f"✓ PDF gerado com sucesso: {output_path}")
        print(f"  - Total de facturas: {len(invoices_data)}")
        print(f"  - Valor total: €{total_amount:.2f}")
        print(f"  - Clientes: {len(by_client)}")
    except Exception as e:
        print(f"✗ Erro ao gerar PDF: {e}", file=sys.stderr)
        raise


def main():
    """
    Lê dados de facturas do stdin (uma por linha em JSON) e gera PDF.

    Esperado: Uma factura por linha no formato JSON.
    Cada linha contém um objeto JSON com os dados completos da factura.
    """
    try:
        invoices_data = []

        # Ler dados do stdin (JSON lines format)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                invoice_dict = json.loads(line)
                parsed = parse_invoice(invoice_dict)
                if parsed:
                    invoices_data.append(parsed)
            except json.JSONDecodeError as e:
                print(f"Erro ao fazer parse de linha JSON: {e}", file=sys.stderr)
                continue

        if not invoices_data:
            print("✗ Nenhuma factura com estadia ou consumo encontrada.", file=sys.stderr)
            sys.exit(1)

        # Gerar PDF
        output_file = 'facturas_pendentes.pdf'
        generate_pdf(invoices_data, output_file)

    except Exception as e:
        print(f"✗ Erro ao processar facturas: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
