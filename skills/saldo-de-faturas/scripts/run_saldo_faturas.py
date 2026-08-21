#!/usr/bin/env python3
"""
Orchestrator for the "Saldo de Faturas" skill.

Pipeline:
  1. Parse one or more SAF-T XML files -> invoices with ProductCode
     "Stay" and/or "ConsumptionItem" (parse_saft.py).
  2. Load a JSON dump of InvoiceExpress invoices with status="sent" (see
     SKILL.md for how to produce this via the MCP tool — this script does
     NOT call InvoiceExpress itself, since MCP tools are only callable from
     inside a Claude Code turn, not a standalone script).
  3. Cross-reference by sequence_number: keep only SAF-T invoices that are
     genuinely "sent" (unpaid) in InvoiceExpress right now. This is the
     step that matters most — a SAF-T invoice's own status field only says
     whether the document was cancelled, NOT whether it's been paid.
  4. For each confirmed-unpaid invoice, determine check-in/checkout
     (estimate_stay_dates.py) and attempt a Folio match against a
     Folios.ods-style export (match_folio.py), applying the exact-match
     and channel-priority rules.
  5. Emit a JSON result file consumed by generate_report.py.

Usage:
  python3 run_saldo_faturas.py \\
      --saft SAF-T_2025_1_1.xml [--saft ...] \\
      --ie-sent ie_sent_invoices.json \\
      --folios Folios.ods \\
      --year 2025 \\
      --out saldo_2025.json
"""
import argparse
import json
import sys

from parse_saft import extract_invoices
from estimate_stay_dates import estimate
from load_folios import load_folios
from match_folio import (
    find_stay_candidates, find_taxa_candidates, classify_and_filter,
    detect_cross_invoice_sharing,
)


def load_ie_sent(path):
    """Load InvoiceExpress invoices dumped as JSON. Accepts either a plain
    list or a {"invoices": [...]} wrapper (as list_invoices returns).
    Filters to status == "sent" defensively (a raw MCP dump for a broader
    query might contain other statuses too)."""
    with open(path) as f:
        data = json.load(f)
    invoices = data.get('invoices', data) if isinstance(data, dict) else data
    by_seq = {}
    for inv in invoices:
        if inv.get('status') == 'sent':
            by_seq[inv['sequence_number']] = inv
    return by_seq


def cross_reference(saft_invoices, ie_sent_by_seq, year=None):
    confirmed = []
    for inv in saft_invoices:
        if year and not (inv.get('invoice_date') or '').startswith(str(year)):
            continue
        ie_inv = ie_sent_by_seq.get(inv['sequence_number'])
        if not ie_inv:
            continue  # not confirmed "sent" in InvoiceExpress -> skip
        confirmed.append({**inv, 'ie_total': ie_inv['total'], 'ie_due_date': ie_inv['due_date'],
                          'ie_client_name': ie_inv['client_name']})
    return confirmed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--saft', action='append', required=True, help='SAF-T XML file (repeatable)')
    ap.add_argument('--ie-sent', required=True, help='JSON dump of InvoiceExpress status=sent invoices')
    ap.add_argument('--folios', required=True, help='Folios.ods (or equivalent PMS export)')
    ap.add_argument('--year', help='Restrict to invoices whose SAF-T InvoiceDate starts with this year')
    ap.add_argument('--out', required=True, help='Output JSON path')
    args = ap.parse_args()

    print(f"[1/4] Parsing {len(args.saft)} SAF-T file(s)...", file=sys.stderr)
    saft_invoices = []
    for path in args.saft:
        saft_invoices.extend(extract_invoices(path))
    print(f"      -> {len(saft_invoices)} invoices with Stay/ConsumptionItem", file=sys.stderr)

    print(f"[2/4] Loading InvoiceExpress status=sent dump...", file=sys.stderr)
    ie_sent_by_seq = load_ie_sent(args.ie_sent)
    print(f"      -> {len(ie_sent_by_seq)} invoices with status=sent", file=sys.stderr)

    print(f"[3/4] Cross-referencing (SAF-T Stay/ConsumptionItem ∩ IE sent)...", file=sys.stderr)
    confirmed = cross_reference(saft_invoices, ie_sent_by_seq, year=args.year)
    print(f"      -> {len(confirmed)} confirmed-unpaid invoices", file=sys.stderr)

    print(f"[4/4] Loading Folios export and matching...", file=sys.stderr)
    folio_rows = load_folios(args.folios)

    results = []
    for inv in confirmed:
        dates = estimate(inv)
        entry = {
            'sequence_number': inv['sequence_number'],
            'client_name': inv['ie_client_name'],
            'invoice_date': inv['invoice_date'],
            'due_date': inv['ie_due_date'],
            'total': inv['ie_total'],
            'checkin_checkout_column': dates['column_value'],
            'confidence_dates': dates['confidence'],
            'note_dates': dates['note'],
            'checkin_date': dates['checkin_date'],
        }

        if dates['checkin_date']:
            if inv['has_stay']:
                cands = find_stay_candidates(folio_rows, dates['checkin_date'], inv['ie_total'])
                match_type = 'stay'
            else:
                cands = find_taxa_candidates(folio_rows, dates['checkin_date'], inv['ie_total'])
                match_type = 'taxa'
            filtered, label = classify_and_filter(inv['ie_client_name'], cands, match_type)
            entry['candidates'] = filtered
            entry['label'] = label
        else:
            entry['candidates'] = []
            entry['label'] = 'SEM CANDIDATOS'

        results.append({'invoice': entry, 'label': entry['label'], 'candidates': entry['candidates']})

    results = detect_cross_invoice_sharing(results)

    with open(args.out, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n✓ {len(results)} invoices written to {args.out}", file=sys.stderr)


if __name__ == '__main__':
    main()
