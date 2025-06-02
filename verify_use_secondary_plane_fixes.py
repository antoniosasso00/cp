#!/usr/bin/env python3
"""
Script per verificare che tutte le modifiche per il fix use_secondary_plane siano state applicate
"""

import os
import re

def check_file_fix(file_path, line_number, expected_pattern, description):
    """Verifica che un file contenga il fix atteso"""
    if not os.path.exists(file_path):
        return f"❌ File non trovato: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if line_number > len(lines):
            return f"❌ Linea {line_number} non esiste in {file_path}"
        
        line_content = lines[line_number - 1].strip()
        
        if re.search(expected_pattern, line_content):
            return f"✅ {description}: OK"
        else:
            return f"❌ {description}: FALLITO\n   Trovato: {line_content}\n   Atteso: pattern '{expected_pattern}'"
    
    except Exception as e:
        return f"❌ Errore leggendo {file_path}: {str(e)}"

def main():
    """Verifica principale"""
    print("🔍 VERIFICA FIX use_secondary_plane")
    print("=" * 60)
    
    # Lista dei fix da verificare
    fixes_to_check = [
        {
            'file': 'backend/services/nesting_service.py',
            'line': 262,
            'pattern': r"getattr\(autoclave,\s*['\"]use_secondary_plane['\"],\s*False\)",
            'description': 'NestingService.get_autoclave_data'
        },
        {
            'file': 'backend/api/routers/batch_nesting.py',
            'line': 315,
            'pattern': r"getattr\(autoclave,\s*['\"]use_secondary_plane['\"],\s*False\)",
            'description': 'BatchNesting router'
        },
        {
            'file': 'backend/models/batch_nesting.py',
            'line': 116,
            'pattern': r"getattr\(self\.autoclave,\s*['\"]use_secondary_plane['\"],\s*False\)",
            'description': 'BatchNesting model'
        },
        {
            'file': 'unused/backend/nesting_service.py',
            'line': 949,
            'pattern': r"getattr\(autoclave,\s*['\"]use_secondary_plane['\"],\s*False\)",
            'description': 'Unused NestingService (linea 949)'
        },
        {
            'file': 'unused/backend/nesting_service.py',
            'line': 988,
            'pattern': r"getattr\(autoclave,\s*['\"]use_secondary_plane['\"],\s*False\)",
            'description': 'Unused NestingService (linea 988)'
        },
        {
            'file': 'unused/backend/nesting_service.py',
            'line': 1520,
            'pattern': r"getattr\(autoclave,\s*['\"]use_secondary_plane['\"],\s*False\)",
            'description': 'Unused NestingService (linea 1520)'
        },
        {
            'file': 'backend/check_nesting_data.py',
            'line': 72,
            'pattern': r"num_linee_vuoto$",  # La linea dovrebbe finire con num_linee_vuoto (senza use_secondary_plane)
            'description': 'check_nesting_data.py query SQL'
        }
    ]
    
    # Verifica ogni fix
    all_good = True
    for fix in fixes_to_check:
        result = check_file_fix(
            fix['file'], 
            fix['line'], 
            fix['pattern'], 
            fix['description']
        )
        print(result)
        if result.startswith('❌'):
            all_good = False
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 TUTTI I FIX SONO STATI APPLICATI CORRETTAMENTE!")
        print("\n📋 Prossimi passi:")
        print("1. Riavviare il server backend per caricare le modifiche")
        print("2. Eseguire: python test_fix_verification.py")
        print("3. Verificare che il nesting funzioni senza errori")
    else:
        print("❌ ALCUNI FIX NON SONO STATI APPLICATI CORRETTAMENTE")
        print("\n🔧 Azioni richieste:")
        print("1. Correggere i file indicati sopra")
        print("2. Riavviare il server backend")
        print("3. Testare nuovamente")

if __name__ == "__main__":
    main() 