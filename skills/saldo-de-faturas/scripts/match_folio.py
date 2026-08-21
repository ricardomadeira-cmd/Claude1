#!/usr/bin/env python3
"""
Match a confirmed-unpaid invoice (SAF-T + InvoiceExpress "sent") against the
Folios.ods export, to try to identify the underlying guest Folio and/or a
confident check-in/checkout, following business rules given by the client:

  1. EXACT MATCH FIRST: if any Folios.ods candidate's amount matches the
     invoice's gross total to the cent, show ONLY the exact match(es) —
     discard every non-exact candidate, however close.
  2. AIRBNB CHANNEL: if the invoice's client is Airbnb and (after rule 1
     found no exact match) a candidate sourced from Airbnb exists, show
     ONLY the Airbnb-sourced candidate(s), even without an exact amount.
  3. EXPEDIA-GROUP CHANNEL: if the invoice's client is Expedia (or an
     Expedia-group brand) and the single closest-value candidate already
     belongs to the Expedia group (Expedia, Hotels.com, Orbitz, Egencia,
     Expedia Affiliate Network, Travelocity, ebookers, CheapTickets,
     Wotif, Hotwire), show ONLY Expedia-group candidates. If the closest
     candidate is NOT Expedia-group, this rule does not apply (a worse,
     wrong-channel match is not to be preferred just because it's Expedia).
  4. Otherwise: fall back to the top 3 closest-by-amount candidates,
     labelled as unconfirmed reference only.

Classification labels: CONFIRMADO, AMBÍGUO, AMBÍGUO (partilhado),
MAIS PRÓXIMO (canal Airbnb), MAIS PRÓXIMO (grupo Expedia),
MAIS PRÓXIMO (não confirmado), SEM CANDIDATOS.
"""

EXPEDIA_GROUP_SOURCES = {
    'expedia', 'hotels.com', 'orbitz', 'egencia', 'expedia affiliate network',
    'travelocity', 'ebookers', 'cheaptickets', 'wotif', 'hotwire',
}

AMOUNT_TOLERANCE = 0.01


def is_airbnb_client(name):
    return bool(name) and 'airbnb' in name.lower()


def is_expedia_client(name):
    return bool(name) and 'expedia' in name.lower()


def is_airbnb_source(src):
    return bool(src) and 'airbnb' in src.lower()


def is_expedia_source(src):
    return bool(src) and src.lower() in EXPEDIA_GROUP_SOURCES


def find_stay_candidates(folio_rows, checkin_date, gross_total, limit=None):
    """Candidates from 'Stays' section matching the check-in date, ranked by
    |revenue_gross - gross_total|."""
    out = []
    for r in folio_rows:
        if r.report_section == 'Stays' and r.checkin == checkin_date and r.revenue_gross is not None:
            out.append({
                'folio': r.folio, 'room': r.room, 'revenue': r.revenue_gross,
                'diff': abs(r.revenue_gross - gross_total),
                'estabelecimento': r.estabelecimento, 'source': r.source,
            })
    out.sort(key=lambda x: x['diff'])
    return out[:limit] if limit else out


def find_taxa_candidates(folio_rows, checkin_date, tax_total, limit=None):
    """Candidates from 'Taxa Turistica' section: group by Folio (using the
    'Correcção' column as the true check-in date — see load_folios docstring),
    sum revenue per Folio, rank by |sum - tax_total|."""
    from collections import defaultdict
    by_folio = defaultdict(list)
    for r in folio_rows:
        if r.report_section != 'Taxa Turistica':
            continue
        date_only = r.correcao[:10] if r.correcao else None
        if date_only == checkin_date and r.revenue_gross is not None:
            by_folio[r.folio].append(r)

    out = []
    for folio, entries in by_folio.items():
        total = sum(r.revenue_gross for r in entries)
        out.append({
            'folio': folio, 'total_tax': total, 'diff': abs(total - tax_total),
            'n_entries': len(entries), 'estabelecimento': entries[0].estabelecimento,
        })
    out.sort(key=lambda x: x['diff'])
    return out[:limit] if limit else out


def classify_and_filter(client_name, candidates, match_type):
    """Apply the 4 business rules above. Returns (filtered_candidates, label)."""
    if not candidates:
        return [], 'SEM CANDIDATOS'

    exact = [c for c in candidates if c['diff'] < AMOUNT_TOLERANCE]
    if exact:
        return exact, ('CONFIRMADO' if len(exact) == 1 else 'AMBÍGUO')

    get_source = (lambda c: c.get('source')) if match_type == 'stay' else (lambda c: None)

    if is_airbnb_client(client_name):
        airbnb_cands = [c for c in candidates if is_airbnb_source(get_source(c))]
        if airbnb_cands:
            return airbnb_cands, 'MAIS PRÓXIMO (canal Airbnb)'

    if is_expedia_client(client_name):
        top = candidates[0]
        if is_expedia_source(get_source(top)):
            expedia_cands = [c for c in candidates if is_expedia_source(get_source(c))]
            return expedia_cands, 'MAIS PRÓXIMO (grupo Expedia)'

    return candidates[:3], 'MAIS PRÓXIMO (não confirmado)'


def detect_cross_invoice_sharing(classified_invoices):
    """Given a list of {invoice, label, candidates} dicts (post
    classify_and_filter), flag CONFIRMADO entries whose single exact Folio
    is also claimed (same checkin_date + folio) by another invoice — these
    become 'AMBÍGUO (partilhado)' since we can't tell which invoice the
    Folio really belongs to."""
    claims = {}
    for item in classified_invoices:
        if item['label'] == 'CONFIRMADO':
            key = (item['invoice']['checkin_date'], item['candidates'][0]['folio'])
            claims.setdefault(key, []).append(item['invoice']['sequence_number'])

    for item in classified_invoices:
        if item['label'] == 'CONFIRMADO':
            key = (item['invoice']['checkin_date'], item['candidates'][0]['folio'])
            others = [s for s in claims.get(key, []) if s != item['invoice']['sequence_number']]
            if others:
                item['label'] = 'AMBÍGUO (partilhado)'
                item['shared_with'] = others
    return classified_invoices
