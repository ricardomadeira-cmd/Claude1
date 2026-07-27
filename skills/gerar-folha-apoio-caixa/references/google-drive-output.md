# Publicação no Google Drive

Além do Excel e do PDF, cada folha é publicada no Google Drive do Hotel Oslo
como **Google Doc nativo**, para a receção abrir e imprimir sem transferir nada.

## Destino e nome

- Pasta: **Folhas de Caixa**, ID `1rrucCA6hvqMQeZoo1pn2dXv4XIrjp98I`
  (`https://drive.google.com/drive/folders/1rrucCA6hvqMQeZoo1pn2dXv4XIrjp98I`).
- Título do ficheiro: `DD-MM-AAAA Folha de Apoio Caixa`
  (exemplo: `26-07-2026 Folha de Apoio Caixa`).

## Como publicar

O conector do Google Drive só aceita conteúdo **inline**. Gerar o HTML e
enviá-lo como texto; o Drive converte para Doc nativo:

```bash
python3 scripts/build_doc_gdocs.py normalized.json folha.html
```

Depois, `create_file` com `contentMimeType: "text/html"` e o HTML em
`textContent`, `parentId` na pasta acima. Confirmar com `read_file_content`.

**Nunca** carregar o PDF nem o Excel para o Drive, nem anexá-los a emails,
passando `base64Content`. Está confirmado em produção que o base64 se corrompe
(quatro tentativas, todas falhadas). Os binários vão para o utilizador por
`SendUserFile`, que é fiável.

O conector **não tem ferramenta para apagar nem para alterar permissões**. Só
cria, copia, lê e pesquisa. Publicar duas vezes o mesmo dia deixa duplicados
que só o utilizador pode remover — por isso, validar antes de publicar.

## Armadilhas confirmadas do importador do Docs

1. **Ignora o atalho CSS `font:`.** As células caem nos 11pt por omissão, o
   texto parte dentro das colunas, cada linha passa a ocupar duas e a folha vai
   para duas páginas. Declarar sempre `font-size` e `font-family` num `<span>`
   dentro da célula.
2. **Ignora `@page`.** As margens ficam nos 2,54 cm por omissão e não são
   controláveis a partir do HTML. A largura útil é **451 pt**; a tabela usa 448.
3. Respeita larguras de coluna, cores de fundo das células e `<span>` com
   `font-size`, `font-weight` e `color`.

## Desenho (uma página A4)

- corpo a 9 pt, cabeçalhos da tabela a 8 pt, tudo em `<span>`;
- `padding: 4pt` nas células, para dar espaço a escrever à mão;
- larguras fixas somando 448 pt, definidas só na primeira linha
  (`table-layout: fixed`);
- data na mesma linha do título;
- 18 linhas de movimento (`LINHAS_MIN`), que ocupam bem a página deixando
  folga; a skill exige um mínimo de 17;
- tabela de totais e quadro RESUMO à largura toda.

Mantêm-se todas as regras da folha: português de Portugal, `FOLIO` sem acento,
apenas a frase `Preencher manualmente os campos assinalados.`, sem notas de
rodapé, RESUMO sem total geral, e `Anexar Folha do Programa` no Current Account.

## Validação obrigatória antes de publicar

Não é possível renderizar um Google Doc a partir do Claude Code. Validar o HTML
de origem com o Chromium, em A4 e com margens de 2,54 cm:

```bash
chromium --headless --no-pdf-header-footer --print-to-pdf=out.pdf preview.html
python3 -c "import fitz; print(fitz.open('out.pdf').page_count)"   # tem de ser 1
```

Renderizar a página para PNG e inspecionar visualmente antes de publicar.

## Limite de uma página

Medido com este desenho: cabem **23 movimentos preenchidos** numa página A4.
A partir de 24 a tabela passa para uma segunda página. O gerador imprime um
aviso em `stderr` quando esse limite é ultrapassado — nesse caso, parar e
confirmar com o utilizador antes de publicar, em vez de publicar duas páginas
em silêncio.

As 18 linhas livres são só o mínimo: num dia com 6 movimentos a tabela tem
18 linhas no total, e num dia com 20 movimentos tem 20.
