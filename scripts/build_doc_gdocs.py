#!/usr/bin/env python3
"""Gera o HTML da folha de apoio à caixa para importar no Google Docs (1 página A4)."""
import sys, json

C = {
    "azul": "#173F59",
    "cab": "#5D7687",
    "manual": "#FFF2CC",
    "dia": "#DDEBF7",
    "borda": "#B8C9D6",
    "texto": "#1F2937",
    "vermelho": "#D7191C",
}
# larguras em pt: soma 445 (< 451pt úteis em A4 com margens de 2,54 cm)
W = [72, 46, 52, 74, 40, 56, 105]
HEADERS = ["DOCUMENTO", "FOLIO", "VALOR", "TIPO", "HORA", "DIA", "MEIO DE PAGAMENTO"]
LINHAS_MIN = 17


def eur(v):
    s = f"{abs(v):,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return ("-" if v < 0 else "") + s + " &euro;"


def cel(txt, w, fundo=None, align="left", bold=False, cor=None):
    # table-layout:fixed => a largura só é necessária na 1.ª linha (w=None nas restantes)
    st = ([f"width:{w}pt"] if w else []) + ["padding:2pt 3pt"]
    if align != "left":
        st.append(f"text-align:{align}")
    if fundo:
        st.append(f"background-color:{fundo}")
    p = ["margin:0", "font:8pt Arial,sans-serif", "line-height:1.05"]
    if bold:
        p.append("font-weight:bold")
    if cor:
        p.append(f"color:{cor}")
    return (f'<td style="{";".join(st)}">'
            f'<p style="{";".join(p)}">{txt}</p></td>')


def build(date_br, movs, prov=False):
    tp = sum(m[1] for m in movs if m[1] > 0)
    td = sum(m[1] for m in movs if m[1] < 0)
    out = []
    a = out.append
    a(f'<p style="margin:0;padding:5pt;background-color:{C["azul"]};text-align:center">'
      f'<span style="font-family:Arial,sans-serif;font-size:16pt;font-weight:bold;color:#FFFFFF">'
      f'FOLHA DE APOIO &Agrave; CAIXA</span></p>')
    dt = date_br + (" &middot; PROVIS&Oacute;RIA - DIA EM CURSO" if prov else "")
    a(f'<p style="margin:0;padding:3pt;background-color:{C["manual"]};text-align:center">'
      f'<span style="font-family:Arial,sans-serif;font-size:11pt;font-weight:bold;color:{C["azul"]}">'
      f'{dt}</span></p>')
    a(f'<p style="margin:4pt 0 3pt 0">'
      f'<span style="font-family:Arial,sans-serif;font-size:7.5pt;color:{C["cab"]}">'
      f'Preencher manualmente os campos assinalados.</span></p>')

    tbl = (f'<table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse;'
           f'border-color:{C["borda"]};table-layout:fixed;width:{sum(W)}pt">')
    a(tbl)
    a("<tr>" + "".join(
        cel(h, W[i], C["cab"], "center", True, "#FFFFFF") for i, h in enumerate(HEADERS)
    ) + "</tr>")
    for doc, val in movs:
        ret = val < 0
        fundo = C["manual"]
        cor = C["vermelho"] if ret else C["texto"]
        a("<tr>"
          + cel(doc, None, C["dia"] if ret else None, "left", False, cor)
          + cel("________", None, fundo)
          + cel(eur(val), None, None, "right", False, cor)
          + cel("InvoiceReturn" if ret else "InvoicePayment", None, None, "left", False, cor)
          + cel("__:__", None, fundo, "center")
          + cel(date_br, None, None, "center")
          + cel("______________", None, fundo)
          + "</tr>")
    for _ in range(max(0, LINHAS_MIN - len(movs))):
        a("<tr>"
          + cel("__________", None, C["manual"])
          + cel("________", None, C["manual"])
          + cel("______ &euro;", None, C["manual"], "right")
          + cel("__________", None, C["manual"])
          + cel("__:__", None, C["manual"], "center")
          + cel(date_br, None, C["dia"], "center")
          + cel("______________", None, C["manual"])
          + "</tr>")
    a("</table>")

    a('<p style="margin:5pt 0 0 0;font-size:2pt">&nbsp;</p>')
    a(f'<table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse;'
      f'border-color:{C["borda"]};table-layout:fixed;width:244pt">')
    for lbl, v, cor in (("TOTAL PAGAMENTOS", tp, None),
                        ("TOTAL DEVOLU&Ccedil;&Otilde;ES", td, C["vermelho"]),
                        ("TOTAL L&Iacute;QUIDO", tp + td, None)):
        a("<tr>" + cel(lbl, 152, C["dia"], "right", True)
          + cel(eur(v), None, C["dia"], "right", True, cor) + "</tr>")
    a("</table>")

    a('<p style="margin:5pt 0 0 0;font-size:2pt">&nbsp;</p>')
    a(f'<p style="margin:0;padding:3pt;background-color:{C["azul"]};text-align:center;width:{sum(W)}pt">'
      f'<span style="font-family:Arial,sans-serif;font-size:11pt;font-weight:bold;color:#FFFFFF">'
      f'RESUMO POR MEIO DE PAGAMENTO</span></p>')
    a(f'<table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse;'
      f'border-color:{C["borda"]};table-layout:fixed;width:{sum(W)}pt">')
    a("<tr>" + cel("MEIO DE PAGAMENTO", 265, C["cab"], "left", True, "#FFFFFF")
      + cel("TOTAL", 180, C["cab"], "right", True, "#FFFFFF") + "</tr>")
    for meio, tot, bold in (("Cart&atilde;o de Cr&eacute;dito", "______________ &euro;", False),
                            ("Dinheiro", "______________ &euro;", False),
                            ("Transfer&ecirc;ncia", "______________ &euro;", False),
                            ("Current Account", "Anexar Folha do Programa", True)):
        a("<tr>" + cel(meio, None) + cel(tot, None, C["manual"], "right", bold) + "</tr>")
    a("</table>")
    return "\n".join(out)


if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    day = data["days"][0]
    d = day["date"].split("-")
    movs = [(m["document"], m["amount"]) for m in day["movements"]]
    html = build(f"{d[2]}/{d[1]}/{d[0]}", movs, day.get("provisional", False))
    open(sys.argv[2], "w", encoding="utf-8").write(html)
    print(f"escrito {sys.argv[2]} ({len(html)} bytes)")
