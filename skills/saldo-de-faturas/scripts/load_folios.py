#!/usr/bin/env python3
"""
Load a Folios.ods-style export (internal PMS/front-desk report) into
structured rows keyed by column name.

Expected columns (Portuguese hotel PMS export, "Folios" report):
  EXECUTION DATE, LOOKUP DATE, REPORT SECTION, FOLIO, ROOM, Revenue,
  Source, Adults, Children, Check-in, User, Stay Month, Stay Year,
  Revenue (numeric), Estabelecimento, Quartos Ocupados, Adults, Children,
  Data Check-in, Correcção, Corrigido 3 noites, Dia, Estadia

REPORT SECTION values seen: "Stays", "Taxa Turistica", "No Shows",
"Alojamento", "Pequeno-almoço".

Key quirks discovered while reverse-engineering this export, relevant to
matching against SAF-T invoices:
  - The numeric "Revenue" column (2nd occurrence, positional index 14) is
    the GROSS amount actually charged/paid — this is what matches an
    InvoiceExpress invoice `total` (which includes VAT). The first
    "Revenue" column (index 5) is a display string with a currency symbol;
    do not use it for numeric comparison.
  - For "Stays" rows, the "Check-in" column (by name) holds the actual
    check-in date as YYYY-MM-DD.
  - For "Taxa Turistica" rows, "Check-in" is empty; the "Correcção" column
    holds the true check-in date instead (the LOOKUP DATE can lag by a
    few days if the tax was recorded/corrected later).
"""
from collections import namedtuple
from parse_ods import parse_ods_rows

REQUIRED_HEADER_COLUMNS = {'FOLIO', 'REPORT SECTION', 'ROOM'}


def find_header(rows):
    """Locate the real header row: the first row containing all of
    REQUIRED_HEADER_COLUMNS. Some exports have a metadata/junk row before it."""
    for row in rows:
        if REQUIRED_HEADER_COLUMNS.issubset(set(c for c in row if c)):
            return row
    raise ValueError(
        f"No header row found containing {REQUIRED_HEADER_COLUMNS}. "
        "Check the export format hasn't changed."
    )


FolioRow = namedtuple('FolioRow', [
    'report_section', 'folio', 'room', 'revenue_gross', 'source',
    'checkin', 'correcao', 'estabelecimento', 'raw',
])


def load_folios(path):
    """Return a list of FolioRow, one per non-empty data row."""
    rows = parse_ods_rows(path)
    header = find_header(rows)
    idx = {h: i for i, h in enumerate(header) if h}

    header_row_index = rows.index(header)
    data_rows = rows[header_row_index + 1:]

    def get(row, name):
        i = idx.get(name)
        if i is None or i >= len(row):
            return None
        return row[i]

    out = []
    for row in data_rows:
        if not get(row, 'FOLIO'):
            continue
        # positional index 14 is the numeric Revenue column (2nd "Revenue" header)
        revenue_gross = row[14] if len(row) > 14 else None
        try:
            revenue_gross = float(revenue_gross) if revenue_gross is not None else None
        except (TypeError, ValueError):
            revenue_gross = None

        out.append(FolioRow(
            report_section=get(row, 'REPORT SECTION'),
            folio=get(row, 'FOLIO'),
            room=get(row, 'ROOM'),
            revenue_gross=revenue_gross,
            source=get(row, 'Source'),
            checkin=get(row, 'Check-in'),
            correcao=get(row, 'Correcção'),
            estabelecimento=get(row, 'Estabelecimento'),
            raw=row,
        ))
    return out


if __name__ == '__main__':
    import sys
    from collections import Counter

    path = sys.argv[1]
    folio_rows = load_folios(path)
    print(f"Total rows: {len(folio_rows)}")
    sections = Counter(r.report_section for r in folio_rows)
    print(f"Report sections: {dict(sections)}")
    for r in folio_rows[:5]:
        print(r)
