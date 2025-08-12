#!/usr/bin/env python3

"""
Script para corrigir a importação da biblioteca rembg no app.py

Este script modifica o arquivo app.py para corrigir a importação da biblioteca rembg,
permitindo que a funcionalidade de remoção de fundo de imagens funcione corretamente.
"""

import re

# Caminho para o arquivo app.py
APP_FILE = 'app.py'

# Padrão para encontrar o bloco de código que precisa ser substituído
PATTERN = r"print\(\"Skipping rembg import \(causes hanging\) - background removal disabled\", flush=True\)\nREMBG_AVAILABLE = False\nrembg_remove = None"

# Novo bloco de código para substituir
REPLACEMENT = """try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
    print("rembg: OK", flush=True)
except ImportError as e:
    print(f"rembg not available: {e}", flush=True)
    REMBG_AVAILABLE = False
    rembg_remove = None"""

def fix_rembg_import():
    """Corrige a importação da biblioteca rembg no app.py"""
    try:
        # Ler o conteúdo do arquivo
        with open(APP_FILE, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Substituir o padrão pelo novo bloco de código
        new_content = re.sub(PATTERN, REPLACEMENT, content)
        
        # Escrever o conteúdo modificado de volta para o arquivo
        with open(APP_FILE, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print("Importação da biblioteca rembg corrigida com sucesso!")
        print("A funcionalidade de remoção de fundo agora deve funcionar corretamente.")
        print("Reinicie o servidor Flask para aplicar as alterações.")
    
    except Exception as e:
        print(f"Erro ao corrigir a importação da biblioteca rembg: {e}")

if __name__ == '__main__':
    fix_rembg_import()