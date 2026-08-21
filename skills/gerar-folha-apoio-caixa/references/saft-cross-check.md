# Conferência cruzada com o SAF-T

Verificação independente, feita **depois** de a folha estar entregue. Serve para
confirmar que o apuramento pela API não perdeu documentos. Nunca republicar nada
por iniciativa própria a partir daqui: em caso de divergência, descrever e
aguardar orientação.

## Obter o ficheiro

`export_saft` com `year`, `month`, `day` e `period: "day"`. A primeira resposta é
sempre:

```json
{"message": "O seu ficheiro SAF-T começou a ser gerado. Por favor, continue a enviar o pedido até receber o url."}
```

Repetir a chamada até vir `{"url": ...}`. Observado entre 2 e 9 chamadas. Depois
descarregar o ZIP com `curl` e extrair o XML.

## Aplicar a regra de qualificação

**O "nome" do item da API está em `ProductCode`, não em `ProductDescription`.**
Aplicar a regra ao campo errado devolve zero qualificados e produz um falso
alarme. Confirmado em produção.

Excluir documentos com `DocumentStatus/InvoiceStatus == "A"` (anulados).

## Notas de crédito no SAF-T

O SAF-T não tem `owner_invoice_id`. O elo para o documento de origem está em
`Line/References/Reference`, com o número no formato `FT OS2014/142050`.

Aplicar a mesma ordem da regra geral: item próprio → documento de origem via
`References/Reference` → padrão de intervalo ISO. Um script que só olhe para os
nomes dos itens dá falsos alarmes em dias com notas de crédito qualificantes.

## Limitação conhecida do cruzamento diário

Se a fatura de origem de uma nota de crédito for de **um dia anterior**, não está
no SAF-T do dia e a procura por `References/Reference` falha. A nota aparece então
como "só na folha, não no SAF-T".

Isto **não é divergência** — é o cruzamento diário a não alcançar o elo. Confirmar
inspecionando as `References` da nota: se apontarem para um documento fora do dia,
a folha está correta (foi a API, via `owner_invoice_id`, que resolveu o caso).

Exemplo real: nota `NC OS2014/4009` de 19/08/2026, origem `FT OS2014/142032`,
de dia anterior.

## Emissões tardias

Documentos com data do dia D podem ser emitidos depois de a folha de D já ter
sido gerada, e passam a aparecer no SAF-T de D. Diferenças observadas entre a
contagem da API na altura da geração e o SAF-T no dia seguinte: 07/08 69→82,
14/08 50→58, 15/08 43→54, 16/08 56→67, 19/08 69→85.

Na esmagadora maioria dos casos os documentos tardios **não qualificam** e a
folha mantém-se correta. Reconferir pelo SAF-T do dia seguinte é a forma fiável
de o confirmar. Só reportar se algum documento tardio qualificar.

## Script de referência

```python
import xml.etree.ElementTree as ET, re, json

t = ET.parse('SAF-T_2026_8_20.xml'); r = t.getroot()
ns = {'n': r.tag.split('}')[0].strip('{')}

def norm(s):
    return re.sub(r'[\s_\-]', '', (s or '').strip().lower())

docs = [d for d in r.findall('.//n:SalesInvoices/n:Invoice', ns)
        if d.findtext('n:DocumentStatus/n:InvoiceStatus', default='', namespaces=ns) != 'A']

def codes(d):
    return [l.findtext('n:ProductCode', default='', namespaces=ns) for l in d.findall('n:Line', ns)]

def ok(d):
    return any(norm(c) in ('stay', 'consumptionitem') for c in codes(d))

byno = {d.findtext('n:InvoiceNo', default='', namespaces=ns): d for d in docs}

qual = {}
for d in docs:
    no = d.findtext('n:InvoiceNo', default='', namespaces=ns)
    typ = d.findtext('n:InvoiceType', default='', namespaces=ns)
    tot = float(d.findtext('n:DocumentTotals/n:GrossTotal', default='0', namespaces=ns))
    good = ok(d)
    if not good and typ == 'NC':
        refs = {ref.text for l in d.findall('n:Line', ns)
                for ref in l.findall('n:References/n:Reference', ns)}
        good = any(byno.get(rf) is not None and ok(byno[rf]) for rf in refs)
    if good:
        qual[no.split('/')[-1]] = round(tot if typ != 'NC' else -tot, 2)

mine = json.load(open('normalized.json'))['days'][0]['movements']
mineq = {m['document'].split('/')[0]: m['amount'] for m in mine}
print('só no SAF-T:', {k: v for k, v in sorted(qual.items()) if k not in mineq})
print('só na folha:', {k: v for k, v in mineq.items() if k not in qual})
print('totais:', round(sum(qual.values()), 2), round(sum(mineq.values()), 2))
```
