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

- corpo a 9 pt e cabeçalhos a 8 pt, sempre em `<span>`, `padding: 4pt`,
  `line-height: 1.05` — as linhas ficam altas o suficiente para escrever à mão;
- data na mesma linha do título, para poupar altura;
- 22 linhas de movimento (a skill exige >= 17), para ocupar a altura da página;
- `table-layout: fixed` com larguras explícitas só na primeira linha
  (soma 448 pt), o que evita quebras de linha em `InvoicePayment` e
  `140716/OS2014` e mantém o HTML pequeno;
- 17 linhas de movimento no total (preenchidas + livres).

Ao alterar o desenho, revalidar a contagem de páginas antes de publicar:

```bash
python3 scripts/build_doc_gdocs.py normalized.json folha.html
# embrulhar em <html> e imprimir para PDF com o Chromium headless
chromium --headless --no-pdf-header-footer --print-to-pdf=out.pdf preview.html
python3 -c "import fitz; print(fitz.open('out.pdf').page_count)"   # tem de ser 1
```

Validar sempre com margens de **2,54 cm** — confirmado em produção que o
importador do Docs **ignora `@page`**, por isso as margens da página não são
controláveis a partir do HTML e a largura útil é 451 pt. Tem de dar 1 página.

## Regras da folha que este script respeita

`FOLIO` sem acento; apenas a frase `Preencher manualmente os campos
assinalados.`; sem notas de rodapé; `RESUMO POR MEIO DE PAGAMENTO` sem total
geral; `Current Account` com `Anexar Folha do Programa`.
