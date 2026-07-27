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
PT = 9            # corpo da tabela
PT_CAB = 8        # cabeçalhos (menores, senão "MEIO DE PAGAMENTO" parte)
PAD = "4pt 4pt"   # espaço para escrever à mão nas linhas livres
# Confirmado em produção: o import do Docs IGNORA o @page, logo as margens
# ficam nos 2,54 cm por omissão e a largura útil é 451pt. As colunas somam 448.
W = [78, 50, 56, 76, 36, 56, 96]
HEADERS = ["DOCUMENTO", "FOLIO", "VALOR", "TIPO", "HORA", "DIA", "MEIO DE PAGAMENTO"]
LINHAS_MIN = 18   # deixa folga de página; a skill exige >= 17
MAX_1_PAGINA = 23 # acima disto a tabela transborda para uma 2.ª página


def eur(v):
    s = f"{abs(v):,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return ("-" if v < 0 else "") + s + " &euro;"


def cel(txt, w, fundo=None, align="left", bold=False, cor=None, pt=None):
    # table-layout:fixed => a largura só é necessária na 1.ª linha (w=None nas restantes)
    st = ([f"width:{w}pt"] if w else []) + [f"padding:{PAD}"]
    if align != "left":
        st.append(f"text-align:{align}")
    if fundo:
        st.append(f"background-color:{fundo}")
    # O importador do Google Docs ignora o atalho `font:` e cai nos 11pt por
    # omissão; só respeita font-size/font-family declarados num <span>.
    sp = [f"font-size:{pt or PT}pt", "font-family:Arial,sans-serif"]
    if bold:
        sp.append("font-weight:bold")
    if cor:
        sp.append(f"color:{cor}")
    return (f'<td style="{";".join(st)}">'
            f'<p style="margin:0;line-height:1.05">'
            f'<span style="{";".join(sp)}">{txt}</span></p></td>')


def build(date_br, movs, prov=False):
    tp = sum(m[1] for m in movs if m[1] > 0)
    td = sum(m[1] for m in movs if m[1] < 0)
    out = []
    a = out.append
        # data na mesma linha do título, para poupar uma linha de altura
    dt = date_br + (" &middot; PROVIS&Oacute;RIA - DIA EM CURSO" if prov else "")
    a(f'<p style="margin:0;padding:6pt;background-color:{C["azul"]};text-align:center">'
      f'<span style="font-family:Arial,sans-serif;font-size:15pt;font-weight:bold;color:#FFFFFF">'
      f'FOLHA DE APOIO &Agrave; CAIXA &nbsp;&middot;&nbsp; {dt}</span></p>')
    a(f'<p style="margin:3pt 0 2pt 0">'
      f'<span style="font-family:Arial,sans-serif;font-size:8pt;color:{C["cab"]}">'
      f'Preencher manualmente os campos assinalados.</span></p>')

    tbl = (f'<table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse;'
           f'border-color:{C["borda"]};table-layout:fixed;width:{sum(W)}pt">')
    a(tbl)
    a("<tr>" + "".join(
        cel(h, W[i], C["cab"], "center", True, "#FFFFFF", PT_CAB)
        for i, h in enumerate(HEADERS)
    ) + "</tr>")
    for doc, val in movs:
        ret = val < 0
        fundo = C["manual"]
        cor = C["vermelho"] if ret else C["texto"]
        a("<tr>"
          + cel(doc, None, C["dia"] if ret else None, "left", False, cor)
          + cel("_" * 8, None, fundo)
          + cel(eur(val), None, None, "right", False, cor)
          + cel("InvoiceReturn" if ret else "InvoicePayment", None, None, "left", False, cor)
          + cel("__:__", None, fundo, "center")
          + cel(date_br, None, None, "center")
          + cel("_" * 17, None, fundo)
          + "</tr>")
    for _ in range(max(0, LINHAS_MIN - len(movs))):
        a("<tr>"
          + cel("_" * 14, None, C["manual"])
          + cel("_" * 8, None, C["manual"])
          + cel("_" * 7 + " &euro;", None, C["manual"], "right")
          + cel("_" * 13, None, C["manual"])
          + cel("__:__", None, C["manual"], "center")
          + cel(date_br, None, C["dia"], "center")
          + cel("_" * 17, None, C["manual"])
          + "</tr>")
    a("</table>")

    a('<p style="margin:6pt 0 0 0;font-size:2pt">&nbsp;</p>')
    a(f'<table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse;'
      f'border-color:{C["borda"]};table-layout:fixed;width:{sum(W)}pt">')
    for lbl, v, cor in (("TOTAL PAGAMENTOS", tp, None),
                        ("TOTAL DEVOLU&Ccedil;&Otilde;ES", td, C["vermelho"]),
                        ("TOTAL L&Iacute;QUIDO", tp + td, None)):
        a("<tr>" + cel(lbl, 352, C["dia"], "right", True)
          + cel(eur(v), None, C["dia"], "right", True, cor) + "</tr>")
    a("</table>")

    a('<p style="margin:6pt 0 0 0;font-size:2pt">&nbsp;</p>')
    a(f'<p style="margin:0;padding:3pt;background-color:{C["azul"]};text-align:center;width:{sum(W)}pt">'
      f'<span style="font-family:Arial,sans-serif;font-size:11pt;font-weight:bold;color:#FFFFFF">'
      f'RESUMO POR MEIO DE PAGAMENTO</span></p>')
    a(f'<table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse;'
      f'border-color:{C["borda"]};table-layout:fixed;width:{sum(W)}pt">')
    a("<tr>" + cel("MEIO DE PAGAMENTO", 300, C["cab"], "left", True, "#FFFFFF")
      + cel("TOTAL", 148, C["cab"], "right", True, "#FFFFFF") + "</tr>")
    for meio, tot, bold in (("Cart&atilde;o de Cr&eacute;dito", "_" * 22 + " &euro;", False),
                            ("Dinheiro", "_" * 22 + " &euro;", False),
                            ("Transfer&ecirc;ncia", "_" * 22 + " &euro;", False),
                            ("Current Account", "Anexar Folha do Programa", True)):
        a("<tr>" + cel(meio, None) + cel(tot, None, C["manual"], "right", bold) + "</tr>")
    a("</table>")
    return "\n".join(out)


if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    day = data["days"][0]
    if len(day["movements"]) > MAX_1_PAGINA:
        print(f"AVISO: {len(day['movements'])} movimentos excedem os "
              f"{MAX_1_PAGINA} que cabem numa página A4. A folha vai ocupar "
              f"duas páginas — confirmar com o utilizador antes de publicar.",
              file=sys.stderr)
    d = day["date"].split("-")
    movs = [(m["document"], m["amount"]) for m in day["movements"]]
    html = build(f"{d[2]}/{d[1]}/{d[0]}", movs, day.get("provisional", False))
    open(sys.argv[2], "w", encoding="utf-8").write(html)
    print(f"escrito {sys.argv[2]} ({len(html)} bytes)")
