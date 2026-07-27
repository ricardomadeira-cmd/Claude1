# scripts/build_doc_gdocs.py

Gera o HTML da folha diária de apoio à caixa do Hotel Oslo para importar no
Google Drive como Google Doc nativo (`contentMimeType: text/html`).

Complementa a skill `gerar-folha-apoio-caixa`, que continua a ser a fonte do
Excel e do PDF. Este script produz apenas a versão para o Drive.

## Uso

```bash
python3 scripts/build_doc_gdocs.py normalized.json folha.html
```

`normalized.json` é o mesmo JSON normalizado que alimenta
`scripts/generate_cash_support.py` da skill.

## Restrições de desenho

O layout está calibrado para caber numa única página A4 no Google Docs
(margens por omissão de 2,54 cm, ou seja ~451 pt úteis):

- fonte 8 pt Arial, `padding: 2pt 3pt`, `line-height: 1.05`;
- `table-layout: fixed` com larguras explícitas só na primeira linha
  (soma 445 pt), o que evita quebras de linha em `InvoicePayment` e
  `140716/OS2014` e mantém o HTML pequeno;
- 17 linhas de movimento no total (preenchidas + livres).

Ao alterar o desenho, revalidar a contagem de páginas antes de publicar:

```bash
python3 scripts/build_doc_gdocs.py normalized.json folha.html
# embrulhar em <html> com @page{size:A4;margin:2.54cm} e imprimir para PDF
chromium --headless --no-pdf-header-footer --print-to-pdf=out.pdf preview.html
python3 -c "import fitz; print(fitz.open('out.pdf').page_count)"   # tem de ser 1
```

## Regras da folha que este script respeita

`FOLIO` sem acento; apenas a frase `Preencher manualmente os campos
assinalados.`; sem notas de rodapé; `RESUMO POR MEIO DE PAGAMENTO` sem total
geral; `Current Account` com `Anexar Folha do Programa`.
