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

## Armadilha do importador do Google Docs

O importador **ignora o atalho CSS `font:`** e aplica o tamanho por omissão do
Docs (11pt) às células. Isso parte `DOCUMENTO`/`InvoicePayment`/`26/07/2026` em
duas linhas, duplica a altura de cada linha e empurra a folha para 2 páginas.

Só é respeitado `font-size` (e `font-family`) declarado num `<span>` dentro da
célula — que é o que este script gera. **Não voltar a usar o atalho.**

## Restrições de desenho

O layout está calibrado para caber numa única página A4 no Google Docs
(margens por omissão de 2,54 cm, ou seja ~451 pt úteis):

- fonte 8 pt Arial em `<span>`, `padding: 1pt 3pt`, `line-height: 1.05`;
- data na mesma linha do título, para poupar altura;
- `@page { margin: 1,2 cm }` para estreitar as margens da página;
- `table-layout: fixed` com larguras explícitas só na primeira linha
  (soma 445 pt), o que evita quebras de linha em `InvoicePayment` e
  `140716/OS2014` e mantém o HTML pequeno. A soma fica deliberadamente dentro
  dos 451 pt úteis das margens POR OMISSÃO do Docs, para a tabela não
  transbordar se o `@page` acima for ignorado no import;
- 17 linhas de movimento no total (preenchidas + livres).

Ao alterar o desenho, revalidar a contagem de páginas antes de publicar:

```bash
python3 scripts/build_doc_gdocs.py normalized.json folha.html
# embrulhar em <html> e imprimir para PDF com o Chromium headless
chromium --headless --no-pdf-header-footer --print-to-pdf=out.pdf preview.html
python3 -c "import fitz; print(fitz.open('out.pdf').page_count)"   # tem de ser 1
```

Validar em três cenários, porque não é possível renderizar o Doc a partir daqui:

1. `@page{margin:1.2cm}` — o pedido;
2. `@page{margin:2.54cm}` — se o import ignorar as margens;
3. o mesmo, com `td span{font-size:11pt !important}` — se o import voltar a
   ignorar o tamanho da letra.

Nos três tem de dar 1 página.

## Regras da folha que este script respeita

`FOLIO` sem acento; apenas a frase `Preencher manualmente os campos
assinalados.`; sem notas de rodapé; `RESUMO POR MEIO DE PAGAMENTO` sem total
geral; `Current Account` com `Anexar Folha do Programa`.
