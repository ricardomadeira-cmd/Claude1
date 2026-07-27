# Hotel Oslo — folha diária de apoio à caixa

Skill do Claude Code que produz a folha diária de apoio à caixa do Hotel Oslo
(Coimbra) a partir do InvoiceXpress, em três formatos:

| Formato | Onde vai parar |
| --- | --- |
| `.xlsx` | entregue ao utilizador por `SendUserFile` |
| `.pdf` | entregue ao utilizador por `SendUserFile` |
| Google Doc | pasta **Folhas de Caixa** no Google Drive |

## Instalação

O diretório `~/.claude/skills/` é efémero nas sessões remotas. Para reinstalar:

```bash
cp -r skills/gerar-folha-apoio-caixa ~/.claude/skills/
pip install openpyxl reportlab pymupdf
```

## Estrutura

```
skills/gerar-folha-apoio-caixa/
├── SKILL.md                              fluxo obrigatório
├── references/
│   ├── invoicexpress-extraction.md       extração, seleção, normalização
│   ├── output-and-validation.md          Excel e PDF
│   └── google-drive-output.md            Google Doc no Drive
└── scripts/
    ├── generate_cash_support.py          gera .xlsx e .pdf
    └── build_doc_gdocs.py                gera o HTML para o Google Doc
```

## Rotina diária

Uma Routine dispara todos os dias às 00:02 de Lisboa (`2 23 * * *` em UTC),
gera a folha do dia anterior, publica-a no Drive e entrega os ficheiros.
