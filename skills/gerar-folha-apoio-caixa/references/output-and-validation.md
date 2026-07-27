# Especificação de saída e validação

## Conteúdo

- Ficheiros e agrupamento
- Estrutura da folha
- Formatação
- Campos manuais
- Totais
- Quadro de meios de pagamento
- Paginação
- Validação do Excel
- Validação do PDF
- Comunicação final

## Ficheiros e agrupamento

Produzir sempre:

- um ficheiro Excel `.xlsx`;
- um ficheiro PDF `.pdf`.

Quando forem pedidas várias datas, criar um workbook com uma worksheet por data e um PDF com as páginas de todas as datas. Quando for pedida uma data, criar uma única worksheet e as páginas dessa data.

Usar nomes de ficheiro descritivos e sem espaços desnecessários. Não substituir uma versão anterior com o mesmo nome quando existir risco de cache; usar um nome novo ou a revisão pedida pelo utilizador.

## Estrutura da folha

Usar A4 vertical.

Ordem das secções:

1. título `FOLHA DE APOIO À CAIXA`;
2. data;
3. frase `Preencher manualmente os campos assinalados.`;
4. tabela de movimentos;
5. totais de pagamentos, devoluções e líquido;
6. quadro `RESUMO POR MEIO DE PAGAMENTO`.

Cabeçalhos da tabela de movimentos, nesta ordem:

| DOCUMENTO | FOLIO | VALOR | TIPO | HORA | DIA | MEIO DE PAGAMENTO |
| --- | --- | --- | --- | --- | --- | --- |

Não escrever `FÓLIO`.

## Formatação

Reproduzir esta linguagem visual:

- título e título do resumo: azul escuro `#173F59`, texto branco;
- cabeçalhos: azul acinzentado `#5D7687`, texto branco;
- campos manuais: amarelo claro `#FFF2CC`;
- células de dia nas linhas livres e bloco de totais: azul claro `#DDEBF7`;
- realce de devolução: vermelho claro `#FCE4E4`;
- texto principal: `#1F2937`;
- texto de devolução: vermelho `#D7191C`;
- linhas/bordas: `#B8C9D6`;
- fonte: Arial no Excel; fonte sans-serif compatível no PDF.

Usar números e datas como valores tipados no Excel:

- valor: número com formato monetário de duas casas decimais;
- dia: data com formato `dd/mm/yyyy`;
- totais: fórmulas auditáveis.

Esconder as linhas de grelha. Ajustar largura e altura para impedir cortes de texto. Não usar gráficos, logótipos, notas ou elementos decorativos.

## Campos manuais

Em cada movimento preenchido:

- `DOCUMENTO`: automático;
- `FOLIO`: `____________`;
- `VALOR`: automático;
- `TIPO`: automático;
- `HORA`: `____:____`;
- `DIA`: automático;
- `MEIO DE PAGAMENTO`: `________________`.

Manter pelo menos 17 lugares para movimentos por dia. Nas linhas livres, usar marcadores horizontais visíveis para todos os campos de entrada; preencher o dia automaticamente.

Não preencher a hora com a hora de criação da fatura.

## Totais

Apresentar:

- `TOTAL PAGAMENTOS`;
- `TOTAL DEVOLUÇÕES`;
- `TOTAL LÍQUIDO`.

No Excel, usar fórmulas baseadas nas colunas `TIPO` e `VALOR` de todas as linhas reservadas:

```excel
=SUMIF(tipo_intervalo,"InvoicePayment",valor_intervalo)
=SUMIF(tipo_intervalo,"InvoiceReturn",valor_intervalo)
=total_pagamentos+total_devolucoes
```

Os valores de `InvoiceReturn` são negativos, mas não escrever essa explicação na folha.

## Quadro de meios de pagamento

Título: `RESUMO POR MEIO DE PAGAMENTO`.

Colunas:

- `MEIO DE PAGAMENTO`;
- `TOTAL`.

Linhas, exatamente nesta ordem:

| MEIO DE PAGAMENTO | TOTAL |
| --- | --- |
| Cartão de Crédito | `________________ €` |
| Dinheiro | `________________ €` |
| Transferência | `________________ €` |
| Current Account | `Anexar Folha do Programa` |

Não acrescentar uma linha de total geral neste quadro. Isto não elimina os três totais contabilísticos anteriores.

## Paginação

Com até 17 movimentos, manter cada dia numa única página A4 vertical.

Com mais de 17 movimentos:

- não cortar nem omitir movimentos;
- criar páginas de continuação para o mesmo dia;
- repetir título, data, instrução e cabeçalhos;
- apresentar os totais e o quadro de meios apenas na última página do dia;
- indicar `PÁGINA n/total` na linha da data;
- manter um único agrupamento diário no workbook, mesmo que a impressão ocupe várias páginas.

O dia corrente deve mostrar:

```text
DD/MM/AAAA · PROVISÓRIA - DIA EM CURSO
```

Um dia concluído mostra apenas a data.

## Validação do Excel

Antes de entregar:

1. abrir novamente o workbook;
2. confirmar o número e o nome das worksheets;
3. confirmar que cada documento aparece uma vez;
4. confirmar tipos, sinais e datas;
5. confirmar fórmulas dos três totais;
6. pesquisar erros como `#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`;
7. confirmar orientação vertical, A4, área de impressão e repetição de cabeçalhos;
8. renderizar todas as worksheets;
9. confirmar que `FOLIO` não tem acento;
10. confirmar que `Current Account` mostra `Anexar Folha do Programa`.

As fórmulas do Excel devem abranger também as linhas livres para permitir preenchimento manual posterior.

## Validação do PDF

Antes de entregar:

1. confirmar que o número de páginas é o esperado;
2. extrair texto para uma verificação estrutural;
3. confirmar documentos e totais;
4. renderizar todas as páginas para PNG;
5. inspecionar visualmente todas as páginas;
6. corrigir texto cortado, sobreposições, glifos inválidos ou páginas em branco;
7. confirmar que Excel e PDF têm o mesmo conteúdo.

Não usar apenas extração de texto como validação visual.

## Comunicação final

Na conversa, indicar por dia:

- movimentos;
- total de pagamentos;
- total de devoluções;
- total líquido;
- estado provisório, quando aplicável.

Colocar discrepâncias, exclusões relevantes ou limitações apenas na conversa. Nunca acrescentar notas de rodapé ou comentários explicativos às folhas.
