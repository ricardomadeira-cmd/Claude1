# Extração via InvoiceXpress MCP

Não assumir nomes de ferramentas MCP. Descobrir as ferramentas InvoiceXpress disponíveis no ambiente e usar as que permitem listar/pesquisar documentos e obter detalhes.

## Âmbito da pesquisa

1. Intervalo = datas de emissão confirmadas pelo utilizador.
2. Entidade = Hotelbeds.
3. Percorrer toda a paginação.
4. Preferir documentos emitidos/finalizados/sent; ignorar drafts e anulados.
5. Guardar o ID imutável do InvoiceXpress quando disponível.

## Campos a recolher por fatura

- InvoiceXpress document ID.
- Série e número completos, por exemplo `OS2014/140387`.
- Tipo de documento.
- Data real de emissão.
- Estado.
- Moeda.
- Total sem IVA, IVA e total com IVA.
- Observações, referências e notas.
- Todas as linhas de documento, com descrição, quantidade, preço, imposto e totais.
- PDF/conteúdo integral se existir ferramenta para o obter.

## Booking Nº

Procurar primeiro nas observações/referências da fatura. O padrão historicamente visto é semelhante a `59-5952432`, mas não limitar a extração apenas a esse regex se o InvoiceXpress expuser um campo explícito.

Se houver mais de um número plausível, não escolher por adivinhação.

## Nome do hóspede

O campo Hotelbeds `Costumer Name` deve ser o hóspede/titular da reserva. Não usar o nome comercial Hotelbeds.

Extrair de campos estruturados, observações ou descrição da linha. Se o nome não puder ser associado com segurança à reserva, bloquear essa fatura para revisão.

## Linhas de serviço

O padrão conhecido das faturas Hotel Oslo é `Quartos - <data>-<quarto> ...`.

- Exportar as linhas de alojamento/quarto.
- Usar a data da linha como `Service Date`.
- Cada linha desse padrão representa normalmente 1 noite e quantidade 1.
- Não exportar taxas, extras ou outras linhas não Hotelbeds sem validação explícita.

## Normalização

Depois da recolha, criar um ficheiro JSON conforme `normalized_schema.md`. Não passar diretamente de respostas MCP dispersas para o CSV final.
