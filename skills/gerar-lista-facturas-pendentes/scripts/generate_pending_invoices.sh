#!/bin/bash
# Script para gerar PDF com lista de facturas pendentes
# Utiliza MCP InvoiceXpress para obter dados e gera PDF com reportlab

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não está instalado"
    exit 1
fi

# Verificar se reportlab está instalado
if ! python3 -c "import reportlab" 2>/dev/null; then
    echo "Instalando reportlab..."
    pip install reportlab
fi

# A lógica principal será implementada em Python
# Executar o script Python que integra com MCP e gera o PDF
python3 "$SCRIPT_DIR/generate_pending_invoices_list.py"

echo "✓ Processo concluído"
