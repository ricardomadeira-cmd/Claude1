---
name: gerar-folha-apoio-caixa
description: Cria folhas diárias de apoio à caixa do Hotel Oslo a partir de faturas e notas de crédito do InvoiceXpress, com seleção Stay/ConsumptionItem e saídas Excel/PDF validadas. Usar sempre que for pedida a "folha de apoio à caixa", "folha de caixa" ou equivalente para uma ou mais datas.
---

# Folha diária de apoio à caixa

## Objetivo

Consultar documentos emitidos no InvoiceXpress e produzir, para cada dia pedido, uma
folha de apoio à caixa em Excel e PDF. Tratar cada fatura elegível como um
`InvoicePayment` e cada nota de crédito elegível como um `InvoiceReturn`.

Usar exclusivamente operações de leitura. Nunca criar, editar, liquidar, enviar,
anular ou apagar documentos, pagamentos ou clientes no InvoiceXpress.

## Acesso ao InvoiceXpress a partir do Claude Code

Ao contrário do claude.ai, o Claude Code não tem um conector InvoiceXpress
pré-instalado. Antes de começar, verificar qual destes cenários se aplica:

1. **Servidor MCP configurado** (`claude mcp list`) — se existir um servidor MCP
   para o InvoiceXpress, usar as suas ferramentas normalmente. Descobrir primeiro
   os nomes e esquemas reais (variam por instalação).
2. **API REST direta** — se não existir MCP, usar a API pública do InvoiceXpress
   (`https://<subdominio>.app.invoicexpress.com/...`) com uma API key fornecida
   pelo utilizador (variável de ambiente, nunca escrita em código ou ficheiros
   de saída). Autenticação por `api_key` como parâmetro de query, conforme a
   documentação oficial do InvoiceXpress. Chamar com `curl`/`requests` a partir
   do bash, paginar com o parâmetro `page`, e filtrar por `date` no pedido
   quando o endpoint suportar.
3. Se nenhum dos dois estiver disponível ou a credencial não for fornecida,
   parar e pedir ao utilizador a API key/subdomínio ou o MCP a usar. Não
   inventar nem adivinhar o endpoint ou a conta.

Nunca imprimir a API key, tokens, cabeçalhos de autenticação ou respostas
integrais nos ficheiros de saída ou nos logs partilhados com o utilizador.

## Fluxo obrigatório

Manter esta lista de controlo durante a execução:

```text
Progresso
- [ ] Confirmar datas e se algum dia ainda está em curso
- [ ] Confirmar o método de acesso ao InvoiceXpress (MCP ou API REST) e a conta/subdomínio
- [ ] Obter todas as páginas de faturas e notas de crédito
- [ ] Obter os itens/linhas de CADA documento individualmente (a listagem não chega)
- [ ] Filtrar, relacionar e deduplicar documentos
- [ ] Reconciliar quantidades e totais com a origem
- [ ] Criar o JSON normalizado
- [ ] Gerar Excel e PDF
- [ ] Verificar conteúdo, fórmulas, paginação e apresentação
- [ ] Publicar a folha no Google Drive como Google Doc
- [ ] Entregar Excel e PDF por SendUserFile, com os links do Drive
```

### 1. Ler as regras completas

Ler integralmente antes de qualquer chamada:

- [references/invoicexpress-extraction.md](references/invoicexpress-extraction.md)
  para descoberta de acesso, extração, seleção e normalização;
- [references/output-and-validation.md](references/output-and-validation.md)
  para composição, formatação e controlos finais;
- [references/google-drive-output.md](references/google-drive-output.md)
  para a publicação da folha no Google Drive;
- [references/saft-cross-check.md](references/saft-cross-check.md)
  para a conferência cruzada com o SAF-T, feita depois de a folha estar entregue.

### 2. Confirmar o âmbito

Resolver as datas exatas pedidas. Usar `Europe/Lisbon` para determinar o dia
corrente.

- Marcar o dia atual como provisório: `PROVISÓRIA - DIA EM CURSO`.
- Não marcar dias passados como provisórios.
- Se o utilizador pedir um dia futuro, confirmar antes de produzir.
- Se houver dúvida sobre a conta/subdomínio InvoiceXpress de origem, confirmar
  que é a do Hotel Oslo antes de continuar.

### 3. Extrair

Consultar faturas e notas de crédito pela **data de emissão**. Paginar até ao
fim — nunca assumir que a primeira página contém todos os documentos; confirmar
sempre pelo campo de contagem/paginação total da resposta.

**Obter o detalhe de CADA documento individualmente**, mesmo que a listagem
pareça trazer os itens. Na prática, os nomes de item mais informativos só
aparecem no detalhe, e é aí que se decide se o documento qualifica.

### 4. Selecionar e normalizar

Aplicar exatamente as regras de
[references/invoicexpress-extraction.md](references/invoicexpress-extraction.md).
Em particular:

- incluir apenas documentos emitidos, nunca rascunhos, anulados ou apagados;
- exigir evidência de `Stay` ou `ConsumptionItem` **por nome normalizado do
  item**, nunca por semelhança — ver a armadilha comum abaixo;
- aplicar o tratamento específico das notas de crédito (item próprio →
  documento de origem → padrão de intervalo ISO, por esta ordem);
- criar um só movimento por documento;
- usar o total final do documento, com impostos;
- tornar os valores de `InvoiceReturn` negativos;
- não confundir data/hora de criação da fatura com data/hora do pagamento;
- deixar `FOLIO`, `HORA` e `MEIO DE PAGAMENTO` para preenchimento manual.

**Armadilha comum, confirmada em produção:** neste hotel, muitas faturas de
"Consumidor Final" e de agências como a HotelBeds usam nomes de item como
`Quartos`, `Bar`, `Suplemento`, `Cafetaria ou Agua` ou `- Taxa Turistica
Coimbra` — nenhum destes qualifica, mesmo sendo claramente relacionado com
estadias. Só `Stay` e `ConsumptionItem` (normalizados) contam. É normal e
esperado que, num dia com 40+ faturas, apenas um pequeno subconjunto (tipicamente
as de Expedia, Airbnb e algumas emissões B2B) qualifique.

**Notas de crédito que revertem faturas do próprio dia:** quando uma fatura
qualificada é revertida no mesmo dia por uma nota de crédito, registar as duas
como movimentos separados (`InvoicePayment` positivo e `InvoiceReturn`
negativo) — não cancelar nem omitir nenhuma das duas. O efeito líquido dessa
reserva específica fica visível na folha, e é isso que se pretende.

Guardar apenas os dados mínimos necessários no JSON normalizado. Não incluir
nomes, NIF, moradas, emails ou outros dados de clientes.

Formato:

```json
{
  "timezone": "Europe/Lisbon",
  "days": [
    {
      "date": "2026-07-24",
      "provisional": true,
      "movements": [
        {
          "document": "140549/OS2014",
          "amount": 94.73,
          "movement_type": "InvoicePayment",
          "source_type": "Invoice",
          "source_id": "identificador-estavel-opcional"
        }
      ]
    }
  ]
}
```

### 5. Gerar os ficheiros

Executar:

```bash
python3 scripts/generate_cash_support.py normalized.json \
  --output-dir outputs
```

Usar `--basename nome_sem_extensao` apenas quando o utilizador pedir um nome
específico.

O gerador necessita de `openpyxl` e `reportlab`:

```bash
pip install openpyxl reportlab
```

Não alterar o gerador para recriar a folha manualmente — ajustar o script
apenas se o utilizador pedir explicitamente uma mudança de formato.

O comando cria:

- um workbook `.xlsx`, com uma folha por dia;
- um `.pdf`, com a mesma informação em A4 vertical.

O comando imprime um resumo JSON com contagens e totais por dia — usar esse
resumo como primeira camada de reconciliação antes de abrir os ficheiros.

### 6. Publicar no Google Drive

Gerar o HTML da folha e publicá-lo como Google Doc nativo na pasta
**Folhas de Caixa**, com o título `DD-MM-AAAA Folha de Apoio Caixa`:

```bash
python3 scripts/build_doc_gdocs.py normalized.json folha.html
```

Ler [references/google-drive-output.md](references/google-drive-output.md)
antes de o fazer — tem o ID da pasta, as armadilhas confirmadas do importador
do Docs e a validação obrigatória de "uma página" antes de publicar.

### 7. Validar antes de entregar

Reconciliar novamente os ficheiros produzidos com o resumo apresentado pelo
gerador:

- quantidade de movimentos por dia;
- total de pagamentos;
- total de devoluções;
- total líquido;
- documentos presentes uma única vez;
- igualdade entre Excel, PDF e dados normalizados.

Renderizar todas as folhas/páginas (converter o PDF para imagem, por exemplo
com `pdftoppm`/`pdf2image`) e confirmar visualmente que nada está cortado,
sobreposto ou ilegível. Corrigir e repetir a validação antes de entregar.

## Regras não negociáveis

- Usar português de Portugal nos textos da folha.
- Escrever `FOLIO`, sem acento.
- Manter unicamente a frase `Preencher manualmente os campos assinalados.`;
  não acrescentar notas de rodapé.
- Não escrever na folha qualquer explicação sobre o sinal negativo de
  `InvoiceReturn`.
- Manter o quadro `RESUMO POR MEIO DE PAGAMENTO` sem linha de total geral.
- Usar apenas estes meios no quadro: `Cartão de Crédito`, `Dinheiro`,
  `Transferência`, `Current Account`.
- Escrever `Anexar Folha do Programa` no campo de total de `Current Account`.
- Não colocar valores de clientes nem informação pessoal nos ficheiros de
  trabalho ou nas folhas finais.
- Não escrever API keys, tokens ou cabeçalhos de autenticação em nenhum
  ficheiro do repositório de trabalho ou de saída.
- Nunca carregar o PDF nem o Excel para o Google Drive, nem anexá-los a
  emails, passando conteúdo em base64 inline: corrompe-se de forma fiável.
  Os binários vão por `SendUserFile`; para o Drive vai HTML como texto.
- Nunca usar o atalho CSS `font:` no HTML para o Google Docs — o importador
  ignora-o. Declarar `font-size` num `<span>` dentro da célula.
- Se um dado de origem essencial estiver ausente ou houver conflito, não
  inventar. Parar, explicar a discrepância na conversa e pedir orientação.

## Resposta ao utilizador

Entregar o `.xlsx` e o `.pdf` ao utilizador com `SendUserFile`, e incluir na
resposta o link do Google Doc criado e o link da pasta **Folhas de Caixa**.
Indicar de forma concisa:

- datas abrangidas;
- número de movimentos por dia;
- totais de pagamentos, devoluções e líquido;
- quais os dias provisórios;
- qualquer limitação, exclusão relevante ou discrepância, apenas na conversa e
  nunca dentro das folhas.
