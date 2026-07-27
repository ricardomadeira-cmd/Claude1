# Extração e normalização do InvoiceXpress

## Conteúdo

- Princípios de segurança
- Descoberta do método de acesso
- Consulta completa
- Seleção dos documentos
- Correspondência documento-movimento
- Deduplicação e ordenação
- Contrato do JSON normalizado
- Reconciliação antes da geração
- Situações de erro

## Princípios de segurança

Usar exclusivamente operações de leitura. Não chamar ferramentas ou endpoints
que criem, atualizem, liquidem, enviem, anulem ou apaguem faturas, notas de
crédito, pagamentos ou clientes.

Não expor credenciais, API keys, identificadores de autenticação ou respostas
integrais nos ficheiros de saída ou nos logs partilhados com o utilizador. Não
guardar dados pessoais dos clientes. O relatório necessita apenas de data,
tipo, número, total, estado e nomes/tipos dos itens.

## Descoberta do método de acesso

Dois caminhos possíveis, a confirmar no início da tarefa:

**MCP** — se existir um servidor MCP para o InvoiceXpress disponível no
ambiente, inspecionar as ferramentas e os respetivos esquemas antes da
primeira consulta. Os nomes variam conforme o servidor instalado.

**API REST direta** — na ausência de MCP, usar a API do InvoiceXpress
diretamente (autenticação por API key da conta, HTTPS, respostas em JSON).
Confirmar com o utilizador o subdomínio da conta (`https://<conta>.app.invoicexpress.com`)
e a variável de ambiente ou local seguro onde a API key está disponível. Nunca
pedir para a colar em texto simples no chat se houver alternativa mais segura
disponível no ambiente.

Em qualquer dos casos, procurar capacidades equivalentes a:

1. listar ou pesquisar faturas;
2. listar ou pesquisar notas de crédito;
3. obter o detalhe de um documento (itens, totais, estado, cliente);
4. filtrar por data de emissão e estado;
5. paginar resultados.

Fazer primeiro uma consulta pequena e apenas de leitura para compreender:

- formato da data;
- nomes dos campos de tipo e estado;
- identificador estável;
- número/série do documento;
- total com impostos;
- estrutura dos itens;
- paginação (campo de contagem total, número de páginas, ou cursor).

Não assumir nomes de campos que a origem não devolveu. Mapear semanticamente
os campos reais para o contrato normalizado abaixo.

## Consulta completa

Para cada data pedida:

1. consultar documentos cuja **data de emissão** pertence ao dia;
2. incluir faturas e notas de crédito;
3. pedir um limite de página elevado quando permitido;
4. seguir a paginação (`page`, `next_cursor`, `has_more` ou equivalente) até ao
   fim — confirmar sempre pelo total de resultados devolvido, nunca assumir
   que uma única página chega;
5. guardar os identificadores estáveis encontrados;
6. **obter o detalhe de cada documento elegível por data e estado**, mesmo que
   a listagem pareça trazer os itens — na prática os itens completos e os
   nomes normalizáveis só aparecem fiavelmente no detalhe do documento.

Usar os limites inclusivos corretos para a conta. Se a origem trabalhar com
timestamps, consultar o intervalo de `00:00:00` inclusive a `00:00:00` do dia
seguinte exclusivo, em `Europe/Lisbon`.

Não usar `due_date`, data de pagamento, data de atualização ou data de criação
como substituto da data de emissão.

## Seleção dos documentos

### Estado

Incluir apenas documentos emitidos. Nos dados já observados neste hotel, os
estados emitidos são `sent`, `final` e `settled`.

Incluir um estado diferente apenas se o esquema da origem provar que significa
documento fiscal definitivamente emitido. Excluir sempre:

- `draft` e equivalentes;
- anulados/void/cancelled;
- apagados;
- proformas, orçamentos, guias e outros tipos que não sejam `Invoice` ou
  `CreditNote`.

### Normalização dos nomes dos itens

Para comparar o nome/tipo de um item:

1. remover espaços nas extremidades;
2. converter para minúsculas;
3. remover espaços, `_` e `-`.

Tratar como equivalentes:

- `Stay`, `stay`;
- `ConsumptionItem`, `Consumption Item`, `consumption_item`.

**Não fazer correspondência vaga por palavras parecidas.** Confirmado em
execuções reais: nomes como `Quartos`, `Bar`, `Suplemento`, `Room`,
`Cafetaria ou Agua`, `Comidas` ou `- Taxa Turistica Coimbra` **não qualificam**
uma fatura por si só, mesmo quando a descrição do item menciona claramente uma
data de estadia (ex.: `"24/07/2026-203"`). É comum que a maioria das faturas de
um dia (faturação direta a "Consumidor Final", HotelBeds, etc.) use estes
nomes e fique de fora, enquanto só uma minoria — tipicamente Expedia, Airbnb
Ireland UC e algumas emissões B2B — use `Stay`/`ConsumptionItem` e qualifique.
Não presumir que isto é um erro de dados; é o comportamento normal desta
conta. Verificar sempre item a item, documento a documento — nunca por
amostragem.

### Faturas

Incluir uma `Invoice` apenas quando pelo menos um dos seus itens normaliza
para:

- `stay`;
- `consumptionitem`.

O movimento usa o total integral da fatura, não apenas a soma dos itens
qualificadores.

### Notas de crédito

Aplicar por esta ordem:

1. incluir se um item da própria `CreditNote` normalizar para `stay` ou
   `consumptionitem`;
2. caso contrário, obter o documento de origem relacionado (campo tipo
   `owner_invoice_id` ou equivalente), se a relação estiver disponível, e
   incluir se esse documento cumprir a regra das faturas acima — mesmo que os
   itens da própria nota de crédito usem nomes não qualificantes;
3. se a relação não estiver disponível, aceitar como evidência de estadia um
   nome de item composto exatamente por um intervalo ISO, por exemplo
   `2026-06-02 - 2026-06-03`.

Padrão de recurso:

```regex
^\d{4}-\d{2}-\d{2}\s+-\s+\d{4}-\d{2}-\d{2}$
```

Não alargar esta exceção a descrições vagas.

Uma nota de crédito que reverte, no mesmo dia, uma fatura já incluída como
`InvoicePayment` continua a gerar o seu próprio `InvoiceReturn` — não anular
nem fundir os dois movimentos.

## Correspondência documento-movimento

Criar exatamente um movimento por documento elegível:

| Documento de origem | Movimento | Valor |
| --- | --- | --- |
| `Invoice` | `InvoicePayment` | total final positivo |
| `CreditNote` | `InvoiceReturn` | total final multiplicado por `-1` |

Usar o campo equivalente a `total`, incluindo IVA/impostos e depois de
descontos. Não usar:

- `total_before_taxes`;
- `subtotal`;
- `total_paid`;
- soma parcial de itens;
- valor em dívida.

Preservar cêntimos e arredondar apenas a duas casas com regra decimal normal.

Usar o número de sequência completo, incluindo a série, por exemplo
`140549/OS2014`. Se a origem devolver número e série separados, compor
`número/série`.

Não consultar nem criar pagamentos reais para substituir esta correspondência.
A regra operacional é assumir um `InvoicePayment` por fatura emitida e um
`InvoiceReturn` por nota de crédito emitida.

`FOLIO`, `HORA` e `MEIO DE PAGAMENTO` permanecem manuais:

- não usar o número do documento como folio;
- não usar `created_at` ou `updated_at` como hora do pagamento;
- não preencher o meio de pagamento com dados do cliente ou condições
  comerciais.

## Deduplicação e ordenação

Deduplicar antes de gerar movimentos.

Preferir como chave:

1. identificador estável do documento fornecido pelo InvoiceXpress;
2. na ausência desse identificador: `data|tipo|número completo|total`.

Se duas respostas com a mesma chave tiverem valores, estados ou itens
incompatíveis, não escolher silenciosamente. Obter novamente o detalhe e, se o
conflito persistir, parar e comunicá-lo.

Ordenar por timestamp de emissão quando este existir e for semanticamente
confirmado. Na ausência de hora de emissão, preservar a ordem devolvida pela
origem; não inventar uma hora.

## Contrato do JSON normalizado

Guardar o ficheiro em UTF-8:

```json
{
  "timezone": "Europe/Lisbon",
  "days": [
    {
      "date": "2026-07-22",
      "provisional": false,
      "movements": [
        {
          "document": "140500/OS2014",
          "amount": 125.5,
          "movement_type": "InvoicePayment",
          "source_type": "Invoice",
          "source_id": "opcional"
        },
        {
          "document": "3969/OS2014",
          "amount": -20.0,
          "movement_type": "InvoiceReturn",
          "source_type": "CreditNote",
          "source_id": "opcional"
        }
      ]
    }
  ]
}
```

Regras:

- `date`: ISO `YYYY-MM-DD`;
- `provisional`: booleano;
- `document`: texto não vazio;
- `amount`: número, nunca texto formatado e nunca nulo;
- `movement_type`: apenas `InvoicePayment` ou `InvoiceReturn`;
- `source_type`: deve corresponder ao movimento;
- `source_id`: opcional, apenas para auditoria técnica;
- não incluir objetos de cliente nem itens completos no ficheiro final.

O gerador preserva a ordem dos movimentos.

## Reconciliação antes da geração

Para cada dia, calcular a partir dos documentos deduplicados:

- número de faturas elegíveis;
- número de notas de crédito elegíveis;
- soma dos totais das faturas;
- soma negativa dos totais das notas de crédito;
- total líquido.

Confirmar:

```text
movimentos = faturas elegíveis + notas de crédito elegíveis
total pagamentos = soma dos InvoicePayment
total devoluções = soma dos InvoiceReturn
total líquido = total pagamentos + total devoluções
```

O número e os totais no JSON normalizado têm de coincidir exatamente com esta
reconciliação. O resumo JSON impresso pelo gerador (`scripts/generate_cash_support.py`)
serve como segunda confirmação independente — comparar os dois antes de
prosseguir para a validação visual.

## Situações de erro

Parar e pedir orientação quando:

- a conta/subdomínio de origem for ambígua;
- não houver MCP nem API key disponível para aceder ao InvoiceXpress;
- a paginação não puder ser concluída;
- faltarem itens e não existir forma de obter o detalhe do documento;
- faltar o total final ou o número completo;
- houver moedas diferentes de EUR;
- o estado do documento for ambíguo;
- o mesmo documento surgir com versões incompatíveis;
- uma nota de crédito não tiver evidência suficiente de
  `Stay`/`ConsumptionItem`, mesmo depois de verificar o documento de origem;
- os totais calculados não reconciliem com os documentos selecionados.

Deixar campos manuais em branco é esperado. Faltar um campo essencial de
origem não é motivo para inventar um valor.
