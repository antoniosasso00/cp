#!/usr/bin/env python3
"""
Script di validazione per verificare che tutti i ruoli siano stati aggiornati correttamente
da RESPONSABILE/LAMINATORE/AUTOCLAVISTA a Management/Clean Room/Curing
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Configurazione colori per output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text: str, color: str):
    """Stampa testo colorato"""
    print(f"{color}{text}{Colors.END}")

def find_old_role_references(directory: str, extensions: List[str]) -> Dict[str, List[Tuple[int, str]]]:
    """
    Cerca riferimenti ai vecchi ruoli nei file
    
    Returns:
        Dict con file_path -> [(line_number, line_content)]
    """
    old_patterns = [
        r'\bRESPONSABILE\b',
        r'\bLAMINATORE\b', 
        r'\bAUTOCLAVISTA\b',
        r'\bresponsabile\b',
        r'\blaminatore\b',
        r'\bautoclavista\b',
        r'/dashboard/responsabile',
        r'/dashboard/laminatore', 
        r'/dashboard/autoclavista',
        r'updateStatusLaminatore',
        r'updateStatusAutoclavista',
        r'laminatore-status',
        r'autoclavista-status'
    ]
    
    results = {}
    
    for root, dirs, files in os.walk(directory):
        # Escludi directory non rilevanti
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'dist', 'build']]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    matches = []
                    for line_num, line in enumerate(lines, 1):
                        for pattern in old_patterns:
                            if re.search(pattern, line):
                                matches.append((line_num, line.strip()))
                                break  # Evita duplicati per la stessa riga
                    
                    if matches:
                        results[relative_path] = matches
                        
                except (UnicodeDecodeError, PermissionError):
                    continue
    
    return results

def validate_backend_enum():
    """Valida che l'enum UserRole nel backend sia aggiornato"""
    enum_file = "backend/models/system_log.py"
    
    if not os.path.exists(enum_file):
        print_colored(f"❌ File {enum_file} non trovato", Colors.RED)
        return False
    
    try:
        with open(enum_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica che contenga i nuovi ruoli
        required_roles = [
            'ADMIN = "admin"',
            'MANAGEMENT = "management"',
            'CLEAN_ROOM = "clean_room"', 
            'CURING = "curing"',
            'SISTEMA = "sistema"'
        ]
        
        missing_roles = []
        for role in required_roles:
            if role not in content:
                missing_roles.append(role)
        
        if missing_roles:
            print_colored(f"❌ Enum UserRole mancante di: {missing_roles}", Colors.RED)
            return False
        
        # Verifica che non contenga i vecchi ruoli
        old_roles = ['RESPONSABILE', 'LAMINATORE', 'AUTOCLAVISTA']
        found_old = []
        for old_role in old_roles:
            if f'{old_role} =' in content:
                found_old.append(old_role)
        
        if found_old:
            print_colored(f"❌ Enum UserRole contiene ancora vecchi ruoli: {found_old}", Colors.RED)
            return False
        
        print_colored("✅ Enum UserRole aggiornato correttamente", Colors.GREEN)
        return True
        
    except Exception as e:
        print_colored(f"❌ Errore nella validazione enum: {e}", Colors.RED)
        return False

def validate_frontend_types():
    """Valida che i tipi TypeScript siano aggiornati"""
    hook_file = "frontend/src/hooks/useUserRole.ts"
    
    if not os.path.exists(hook_file):
        print_colored(f"❌ File {hook_file} non trovato", Colors.RED)
        return False
    
    try:
        with open(hook_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica che contenga i nuovi ruoli
        expected_type = "'ADMIN' | 'Management' | 'Clean Room' | 'Curing'"
        
        if expected_type not in content:
            print_colored(f"❌ Tipo UserRole non aggiornato in {hook_file}", Colors.RED)
            return False
        
        print_colored("✅ Tipi TypeScript aggiornati correttamente", Colors.GREEN)
        return True
        
    except Exception as e:
        print_colored(f"❌ Errore nella validazione tipi: {e}", Colors.RED)
        return False

def validate_api_endpoints():
    """Valida che gli endpoint API siano aggiornati"""
    api_file = "frontend/src/lib/api.ts"
    
    if not os.path.exists(api_file):
        print_colored(f"❌ File {api_file} non trovato", Colors.RED)
        return False
    
    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica che contenga i nuovi endpoint
        required_endpoints = [
            'updateStatusCleanRoom',
            'updateStatusCuring',
            'clean-room-status',
            'curing-status'
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print_colored(f"❌ Endpoint API mancanti: {missing_endpoints}", Colors.RED)
            return False
        
        print_colored("✅ Endpoint API aggiornati correttamente", Colors.GREEN)
        return True
        
    except Exception as e:
        print_colored(f"❌ Errore nella validazione API: {e}", Colors.RED)
        return False

def main():
    """Funzione principale di validazione"""
    print_colored("🔍 VALIDAZIONE AGGIORNAMENTO RUOLI", Colors.BOLD)
    print_colored("=" * 50, Colors.BLUE)
    
    # Cambia alla directory del progetto
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    os.chdir(project_dir)
    
    all_valid = True
    
    # 1. Valida enum backend
    print_colored("\n1. Validazione Enum Backend", Colors.BLUE)
    if not validate_backend_enum():
        all_valid = False
    
    # 2. Valida tipi frontend
    print_colored("\n2. Validazione Tipi Frontend", Colors.BLUE)
    if not validate_frontend_types():
        all_valid = False
    
    # 3. Valida endpoint API
    print_colored("\n3. Validazione Endpoint API", Colors.BLUE)
    if not validate_api_endpoints():
        all_valid = False
    
    # 4. Cerca riferimenti ai vecchi ruoli nel backend
    print_colored("\n4. Ricerca Riferimenti Vecchi Ruoli - Backend", Colors.BLUE)
    backend_refs = find_old_role_references("backend", [".py"])
    
    if backend_refs:
        print_colored(f"⚠️  Trovati {len(backend_refs)} file con riferimenti ai vecchi ruoli:", Colors.YELLOW)
        for file_path, matches in backend_refs.items():
            print_colored(f"  📁 {file_path}:", Colors.YELLOW)
            for line_num, line in matches[:3]:  # Mostra solo le prime 3 occorrenze
                print(f"    Riga {line_num}: {line}")
            if len(matches) > 3:
                print(f"    ... e altre {len(matches) - 3} occorrenze")
        all_valid = False
    else:
        print_colored("✅ Nessun riferimento ai vecchi ruoli nel backend", Colors.GREEN)
    
    # 5. Cerca riferimenti ai vecchi ruoli nel frontend
    print_colored("\n5. Ricerca Riferimenti Vecchi Ruoli - Frontend", Colors.BLUE)
    frontend_refs = find_old_role_references("frontend", [".ts", ".tsx", ".js", ".jsx"])
    
    if frontend_refs:
        print_colored(f"⚠️  Trovati {len(frontend_refs)} file con riferimenti ai vecchi ruoli:", Colors.YELLOW)
        for file_path, matches in frontend_refs.items():
            print_colored(f"  📁 {file_path}:", Colors.YELLOW)
            for line_num, line in matches[:3]:  # Mostra solo le prime 3 occorrenze
                print(f"    Riga {line_num}: {line}")
            if len(matches) > 3:
                print(f"    ... e altre {len(matches) - 3} occorrenze")
        all_valid = False
    else:
        print_colored("✅ Nessun riferimento ai vecchi ruoli nel frontend", Colors.GREEN)
    
    # 6. Verifica struttura directory
    print_colored("\n6. Validazione Struttura Directory", Colors.BLUE)
    required_dirs = [
        "frontend/src/app/dashboard/management",
        "frontend/src/app/dashboard/clean-room", 
        "frontend/src/app/dashboard/curing"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print_colored(f"❌ Directory mancanti: {missing_dirs}", Colors.RED)
        all_valid = False
    else:
        print_colored("✅ Struttura directory corretta", Colors.GREEN)
    
    # Risultato finale
    print_colored("\n" + "=" * 50, Colors.BLUE)
    if all_valid:
        print_colored("🎉 VALIDAZIONE COMPLETATA CON SUCCESSO!", Colors.GREEN)
        print_colored("Tutti i ruoli sono stati aggiornati correttamente.", Colors.GREEN)
        return 0
    else:
        print_colored("❌ VALIDAZIONE FALLITA", Colors.RED)
        print_colored("Alcuni riferimenti ai vecchi ruoli devono ancora essere aggiornati.", Colors.RED)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 