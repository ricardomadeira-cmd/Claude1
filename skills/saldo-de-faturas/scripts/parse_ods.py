#!/usr/bin/env python3
"""
Parse an .ods spreadsheet's first sheet into rows of raw cell values.

Handles ODS's row/column repetition compression (table:number-rows-repeated,
table:number-columns-repeated), which a naive XML read would otherwise miss
or blow up into ~1M near-empty rows.
"""
import zipfile
import xml.etree.ElementTree as ET

TABLE = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
TEXT = '{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
OFFICE = '{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

NS = {
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
}


def _cell_value(cell):
    vtype = cell.get(f'{OFFICE}value-type')
    if vtype == 'float':
        return cell.get(f'{OFFICE}value')
    if vtype == 'date':
        return cell.get(f'{OFFICE}date-value')
    if vtype in ('string', 'percentage', 'currency'):
        v = cell.get(f'{OFFICE}value')
        if v is not None:
            return v
    texts = [''.join(p.itertext()) for p in cell.findall(f'{TEXT}p')]
    return '\n'.join(texts) if texts else None


def parse_ods_rows(path, sheet_name=None, drop_empty_trailing_rows=True):
    """Return every non-empty row of the first (or named) sheet as a list of
    raw string values (rows are NOT assumed to have a uniform width).

    This makes no assumption about which row is the header — some exports
    (e.g. Folios.ods) have a metadata row before the real header row, so
    header detection is left to the caller (see load_folios.find_header).
    """
    with zipfile.ZipFile(path) as z:
        with z.open('content.xml') as f:
            content = f.read()

    root = ET.fromstring(content)
    if sheet_name:
        table = None
        for t in root.findall('.//table:table', NS):
            if t.get(f'{TABLE}name') == sheet_name:
                table = t
                break
    else:
        table = root.find('.//table:table', NS)

    if table is None:
        raise ValueError(f"Sheet not found: {sheet_name}")

    rows_out = []
    for row in table.findall(f'{TABLE}table-row'):
        row_repeat = int(row.get(f'{TABLE}number-rows-repeated', '1'))
        row_cells = []
        for cell in row.findall(f'{TABLE}table-cell') + row.findall(f'{TABLE}covered-table-cell'):
            repeat = int(cell.get(f'{TABLE}number-columns-repeated', '1'))
            val = _cell_value(cell)
            row_cells.extend([val] * repeat)

        if drop_empty_trailing_rows:
            while row_cells and row_cells[-1] is None:
                row_cells.pop()

        for _ in range(row_repeat):
            if any(row_cells):
                rows_out.append(row_cells)

    return rows_out


if __name__ == '__main__':
    import sys

    path = sys.argv[1]
    rows = parse_ods_rows(path)
    print(f"Non-empty rows: {len(rows)}")
    for r in rows[:5]:
        print(r)
