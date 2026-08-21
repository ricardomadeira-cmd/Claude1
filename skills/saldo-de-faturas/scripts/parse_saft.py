#!/usr/bin/env python3
"""
Extract SalesInvoices from a SAF-T (PT) XML file that have at least one Line
with ProductCode exactly "Stay" or "ConsumptionItem" (the two literal values
used by this PMS's SAF-T export for accommodation and hotel-consumption
charges — other ProductCodes like "Quartos", "Bar", "Suplemento" are NOT
counted, even though some also relate to the stay).

For each qualifying invoice, also extracts explicit check-in/check-out dates
when available: "Stay" line descriptions are literally formatted as
"YYYY-MM-DD - YYYY-MM-DD" (one line per night), so multiple such lines are
combined into a single [earliest start, latest end] range.
"""
import xml.etree.ElementTree as ET


def _strip_ns(tag):
    return tag.split('}')[-1] if '}' in tag else tag


TARGET_PRODUCT_CODES = {'Stay', 'ConsumptionItem'}


def extract_invoices(saft_path):
    """Yield one dict per Invoice element that has a qualifying line."""
    tree = ET.parse(saft_path)
    root = tree.getroot()

    for elem in root.iter():
        if _strip_ns(elem.tag) != 'Invoice':
            continue

        invoice_no = None
        customer_id = None
        invoice_date = None
        lines = []

        for c in elem:
            tag = _strip_ns(c.tag)
            if tag == 'InvoiceNo':
                invoice_no = c.text
            elif tag == 'CustomerID':
                customer_id = c.text
            elif tag == 'InvoiceDate':
                invoice_date = c.text
            elif tag == 'Line':
                line_data = {}
                for lc in c:
                    ltag = _strip_ns(lc.tag)
                    if ltag in ('ProductCode', 'ProductDescription', 'Quantity',
                                'UnitPrice', 'TaxPointDate', 'Description',
                                'CreditAmount', 'DebitAmount'):
                        line_data[ltag] = lc.text
                lines.append(line_data)

        product_codes = {l.get('ProductCode') for l in lines}
        if not (product_codes & TARGET_PRODUCT_CODES):
            continue

        stay_lines = [l for l in lines if l.get('ProductCode') == 'Stay']
        consumption_lines = [l for l in lines if l.get('ProductCode') == 'ConsumptionItem']

        checkin, checkout = _extract_stay_range(stay_lines)

        # sequence_number matches the InvoiceExpress `sequence_number` field
        # (e.g. SAF-T "FT OS2014/126241" -> IE "OS2014/126241")
        sequence_number = invoice_no.split(' ')[-1] if invoice_no and ' ' in invoice_no else invoice_no

        yield {
            'invoice_no': invoice_no,
            'sequence_number': sequence_number,
            'customer_id': customer_id,
            'invoice_date': invoice_date,
            'has_stay': bool(stay_lines),
            'has_consumption': bool(consumption_lines),
            'stay_lines': stay_lines,
            'consumption_lines': consumption_lines,
            'checkin': checkin,
            'checkout': checkout,
        }


def _extract_stay_range(stay_lines):
    """Parse 'YYYY-MM-DD - YYYY-MM-DD' descriptions and combine into a
    [min(check-in), max(check-out)] range. Returns (None, None) if no
    stay lines or none parse."""
    starts, ends = [], []
    for l in stay_lines:
        desc = l.get('ProductDescription') or l.get('Description') or ''
        parts = [p.strip() for p in desc.split(' - ')]
        if len(parts) == 2 and len(parts[0]) == 10 and len(parts[1]) == 10:
            starts.append(parts[0])
            ends.append(parts[1])
    if starts and ends:
        return min(starts), max(ends)
    return None, None


if __name__ == '__main__':
    import sys
    import json

    path = sys.argv[1]
    count = 0
    for inv in extract_invoices(path):
        count += 1
        if count <= 5:
            print(json.dumps(inv, indent=2, ensure_ascii=False))
    print(f"\nTotal invoices with Stay/ConsumptionItem: {count}")
