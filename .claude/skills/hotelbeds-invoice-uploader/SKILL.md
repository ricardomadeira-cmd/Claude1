---
name: hotelbeds-invoice-uploader
description: Recolhe faturas Hotelbeds no InvoiceXpress via MCP, evita duplicados e gera CSV/Excel para o portal Hotelbeds por intervalo de datas.
---

# Hotelbeds Invoice Uploader

## Regra de arranque obrigatória

Antes de consultar o InvoiceXpress, obter sempre confirmação explícita do intervalo de **datas de emissão** a tratar.

Perguntar: **"Qual o intervalo de datas de emissão das faturas Hotelbeds que queres tratar?"**

Se o utilizador já indicar datas, repetir o intervalo e pedir confirmação antes da consulta MCP. Não pesquisar faturas antes dessa confirmação.

## Fonte de dados

Usar a ligação MCP do InvoiceXpress como fonte principal. Descobrir as ferramentas MCP disponíveis em vez de assumir nomes fixos.

1. Localizar o cliente/entidade Hotelbeds no InvoiceXpress.
2. Listar documentos emitidos/finalizados no intervalo confirmado, com paginação completa.
3. Obter o detalhe integral de cada fatura e, quando disponível, PDF/conteúdo associado.
4. Excluir rascunhos, anulados e documentos que não sejam Hotelbeds.
5. Nunca alterar dados no InvoiceXpress sem pedido explícito do utilizador.

Ler `references/invoicexpress_mcp.md` para regras de extração e normalização.

## Registo anti-duplicados obrigatório

Manter sempre um registo paralelo chamado `hotelbeds_upload_registry.csv` no diretório/projeto de trabalho.

- Procurar este ficheiro antes de construir qualquer lote.
- Se não existir, perguntar se é a primeira utilização do registo.
  - Se sim, criar a partir de `assets/hotelbeds_upload_registry_template.csv`.
  - Se não, pedir ao utilizador o último registo antes de continuar; não afirmar que há proteção contra duplicados sem esse ficheiro.
- Usar `invoicexpress_id` como chave principal quando disponível e `invoice_number` como chave secundária.
- Estado `uploaded`: excluir sempre do novo CSV.
- Estado `prepared`: não voltar a incluir silenciosamente. Perguntar se o lote anterior chegou a ser carregado. Só reprocessar após confirmação de que não foi carregado.
- Estado `rejected`: pode ser reprocessado depois de aplicar a correção necessária.
- Ao gerar um novo lote, registar as faturas como `prepared`.
- Só mudar para `uploaded` depois de confirmação do utilizador ou resposta do portal Hotelbeds que demonstre processamento aceite.
- Se o portal rejeitar, registar `rejected` e a causa conhecida.

O registo é append-only: preservar histórico de eventos em vez de apagar estados anteriores.

## Normalização antes da exportação

Criar um JSON normalizado conforme `references/normalized_schema.md` e validar todos os campos antes da exportação.

Regras específicas:

- `Invoice type`: `F` para fatura; `FR` para nota de crédito.
- `Nº to rectify`: vazio em faturas; preencher apenas quando a nota de crédito retificar documento conhecido.
- `Booking Nº`: extrair das observações/referências Hotelbeds. Não inventar.
- `Costumer Name`: usar nome do hóspede/titular da reserva, não "Hotelbeds". Se não for identificável com segurança, parar e pedir revisão.
- Exportar apenas linhas de alojamento/quartos associadas à reserva Hotelbeds. Linhas `Quartos - ...` são o padrão conhecido.
- `Services Description`: `Accommodation`.
- Cada linha noturna normal usa `Nº Days/Nights = 1` e `Quantity = 1`.
- `Service Date`: data da noite/check-in representada pela linha.
- `Currency`: `EUR`.
- `Tax`: `6`.
- `Tax Type`: `VAT`.
- Usar **valores com IVA incluído** em `Unit price`, `Line total` e `Invoice total`.

## Regra de datas Hotelbeds

O portal calcula check-out como:

`Service Date + Nº Days/Nights`

O valor exportado em `Invoice date` deve ser igual ou posterior ao check-out mais tardio da fatura.

- Preservar sempre a data real InvoiceXpress no ficheiro de revisão e no registo.
- Se necessário para cumprir a Hotelbeds, usar no CSV `upload_invoice_date = max(invoice_date_original, latest_checkout)`.
- Assinalar a correção no Excel e no TXT de validação.
- Esta regra evita o erro Hotelbeds `110004`.

## Arredondamentos

Usar valores gross/IVA incluído do InvoiceXpress quando disponíveis.

Se a soma das linhas gross diferir do total gross da fatura apenas por arredondamento de cêntimos, ajustar a última linha exportada para que:

`sum(Line total da fatura) == Invoice total`

Registar qualquer ajuste no Excel de revisão e no relatório TXT.

## Construção determinística

Depois de recolher e normalizar os dados, usar o script incluído:

```bash
python scripts/hotelbeds_pipeline.py build \
  --input hotelbeds_normalized_YYYY-MM-DD_YYYY-MM-DD.json \
  --registry hotelbeds_upload_registry.csv \
  --output-dir .
```

Se existirem faturas com estado `prepared`, o script deve bloquear. Depois de confirmar com o utilizador que o lote anterior não foi carregado, repetir com `--reinclude-prepared`.

Depois de o utilizador confirmar que um lote foi aceite:

```bash
python scripts/hotelbeds_pipeline.py mark \
  --registry hotelbeds_upload_registry.csv \
  --status uploaded \
  --batch NOME_DO_CSV.csv
```

Se o lote for rejeitado:

```bash
python scripts/hotelbeds_pipeline.py mark \
  --registry hotelbeds_upload_registry.csv \
  --status rejected \
  --batch NOME_DO_CSV.csv \
  --notes "descrição do erro Hotelbeds"
```

## CSV para o portal Hotelbeds

Seguir exatamente `references/hotelbeds_format.md`.

Formato obrigatório conhecido como funcional:

- sem cabeçalho;
- 16 colunas;
- separador `;`;
- decimal `,`;
- datas `dd-mm-yyyy`;
- UTF-8 **sem BOM**;
- uma linha por noite/quarto;
- valores com IVA incluído.

Não alterar esta estrutura sem evidência concreta do portal Hotelbeds.

## Ficheiros a entregar em cada execução

Gerar sempre:

1. `hotelbeds_<FROM>_<TO>_COM_IVA.csv` — ficheiro principal de upload.
2. `hotelbeds_<FROM>_<TO>_revisao.xlsx` — tabela legível para conferência.
3. `hotelbeds_<FROM>_<TO>_VALIDACAO.txt` — resumo de validações, exclusões, correções e arredondamentos.
4. `hotelbeds_upload_registry.csv` — registo atualizado de controlo de duplicados.

No final, indicar de forma curta:

- intervalo tratado;
- número de faturas encontradas;
- número de faturas exportadas;
- faturas excluídas por já estarem `uploaded`;
- faturas bloqueadas por estado `prepared`, se existirem;
- total gross/IVA incluído exportado;
- correções de data aplicadas;
- qual CSV deve ser carregado.

## Tratamento de erros Hotelbeds

- `110004`: aplicar/regenerar segundo a regra de check-out acima.
- `52000`: não adivinhar. Pedir o detalhe da lupa/descrição da regra personalizada antes de alterar valores ou estrutura.
- Outros erros: preservar o CSV original, registar o lote como `rejected`, interpretar a mensagem concreta e gerar nova versão apenas com correção fundamentada.

Nunca marcar uma fatura como `uploaded` apenas porque o ficheiro foi criado ou enviado a alguém.
