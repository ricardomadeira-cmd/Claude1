#!/usr/bin/env python3
"""
Skill principal para gerar lista de facturas pendentes em PDF.

Este script é o orquestrador que:
1. Utiliza Claude Code internamente para chamar MCP tools
2. Recolhe dados de facturas
3. Filtra por tipo de item (stay/consumption)
4. Gera PDF com formatação
5. Devolve PDF ao utilizador

NOTA: Este script é invocado pelo Claude Code/prompt.
      As chamadas MCP são feitas através do contexto do Claude Code.
"""

import json
import sys
import os
from datetime import datetime
from typing import Optional, List, Dict
from collections import defaultdict
from pathlib import Path

# Detectar se reportlab está disponível
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("⚠ reportlab não está instalado. Instale com: pip install reportlab", file=sys.stderr)


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
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        except:
            try:
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
            item_type = str(item_data.get('type', '')).lower()

            if 'stay' in item_type:
                has_stays = True
                properties = item_data.get('properties', {})
                if isinstance(properties, dict):
                    check_in = properties.get('check_in')
                    check_out = properties.get('check_out')
                    if check_in and check_out:
                        stay_dates.append(f"{check_in} a {check_out}")
                    elif check_in:
                        stay_dates.append(f"Entrada: {check_in}")

            elif 'consumption' in item_type:
                has_consumption = True

        if not (has_stays or has_consumption):
            return None

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
        print(f"Erro ao processar factura: {e}", file=sys.stderr)
        return None


def generate_pdf(invoices_data: List[dict], output_path: str = 'facturas_pendentes.pdf') -> bool:
    """
    Gera um PDF com a lista de facturas pendentes.
    Retorna True se bem-sucedido, False caso contrário.
    """
    if not HAS_REPORTLAB:
        print("✗ reportlab não disponível. Não é possível gerar PDF.", file=sys.stderr)
        return False

    if not invoices_data:
        print("✗ Nenhuma factura encontrada para gerar PDF", file=sys.stderr)
        return False

    try:
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
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        styles = getSampleStyleSheet()
        elements = []

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=6,
            alignment=1,
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

        # Criar tabela
        table = Table(
            table_data,
            colWidths=[1.0*inch, 1.6*inch, 1.0*inch, 1.0*inch, 1.6*inch, 0.9*inch]
        )

        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 1), (-2, -2), 'LEFT'),
            ('ALIGN', (-1, 1), (-1, -2), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (-1, -1), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, -1), (-1, -1), 8),
        ]

        table.setStyle(TableStyle(table_style))
        elements.append(table)

        # Rodapé
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
        doc.build(elements)

        print(f"✓ PDF gerado com sucesso: {output_path}")
        print(f"  - Total de facturas: {len(invoices_data)}")
        print(f"  - Valor total: €{total_amount:.2f}")
        print(f"  - Clientes: {len(by_client)}")
        return True

    except Exception as e:
        print(f"✗ Erro ao gerar PDF: {e}", file=sys.stderr)
        return False


def process_invoices(invoices_list: List[dict]) -> List[dict]:
    """
    Processa lista de facturas e filtra as relevantes.
    """
    processed = []
    for invoice in invoices_list:
        parsed = parse_invoice(invoice)
        if parsed:
            processed.append(parsed)
    return processed


def main():
    """
    Entry point da skill.

    Lê invoices do stdin (JSON lines) ou argumentos.
    """
    invoices_data = []

    # Tentar ler do stdin
    if not sys.stdin.isatty():
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
                print(f"Erro ao fazer parse JSON: {e}", file=sys.stderr)
                continue

    if not invoices_data:
        print("⚠ Nenhuma factura para processar", file=sys.stderr)
        print("\nUso:")
        print("  echo '{json}' | python3 main.py")
        print("\nOu acione com os dados já disponíveis no contexto do Claude Code.", file=sys.stderr)
        return False

    # Gerar PDF
    output_path = 'facturas_pendentes.pdf'
    success = generate_pdf(invoices_data, output_path)

    if success and os.path.exists(output_path):
        print(f"\n✓ Ficheiro pronto: {output_path}")
        return True
    else:
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
