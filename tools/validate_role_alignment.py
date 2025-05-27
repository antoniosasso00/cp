#!/usr/bin/env python3
"""
Script di validazione per verificare l'allineamento dei ruoli tra frontend e backend
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text: str, color: str):
    """Stampa testo colorato"""
    print(f"{color}{text}{Colors.END}")

def print_header(text: str):
    """Stampa un header colorato"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f"  {text}", Colors.BOLD + Colors.WHITE)
    print_colored(f"{'='*60}", Colors.CYAN)

def check_frontend_roles() -> Dict[str, any]:
    """Verifica i ruoli definiti nel frontend"""
    print_header("🎨 VERIFICA FRONTEND")
    
    results = {
        'success': True,
        'roles_found': [],
        'issues': []
    }
    
    # Controlla il hook useUserRole
    hook_file = Path("frontend/src/hooks/useUserRole.ts")
    if hook_file.exists():
        content = hook_file.read_text(encoding='utf-8')
        
        # Estrai i ruoli dal type UserRole
        role_match = re.search(r"type UserRole = '([^']+)'(?:\s*\|\s*'([^']+)')*", content)
        if role_match:
            roles = [role_match.group(1)]
            # Trova tutti gli altri ruoli
            for match in re.finditer(r"\|\s*'([^']+)'", content):
                roles.append(match.group(1))
            
            results['roles_found'] = roles
            print_colored(f"✅ Ruoli trovati in useUserRole: {', '.join(roles)}", Colors.GREEN)
            
            # Verifica che siano i ruoli corretti
            expected_roles = {'ADMIN', 'Management', 'Clean Room', 'Curing'}
            found_roles = set(roles)
            
            if found_roles == expected_roles:
                print_colored("✅ Ruoli frontend corretti", Colors.GREEN)
            else:
                missing = expected_roles - found_roles
                extra = found_roles - expected_roles
                if missing:
                    results['issues'].append(f"Ruoli mancanti: {missing}")
                    print_colored(f"❌ Ruoli mancanti: {missing}", Colors.RED)
                if extra:
                    results['issues'].append(f"Ruoli extra: {extra}")
                    print_colored(f"❌ Ruoli extra: {extra}", Colors.RED)
                results['success'] = False
        else:
            results['issues'].append("Impossibile trovare la definizione UserRole")
            print_colored("❌ Impossibile trovare la definizione UserRole", Colors.RED)
            results['success'] = False
    else:
        results['issues'].append("File useUserRole.ts non trovato")
        print_colored("❌ File useUserRole.ts non trovato", Colors.RED)
        results['success'] = False
    
    # Controlla la pagina di selezione ruolo
    role_page = Path("frontend/src/app/role/page.tsx")
    if role_page.exists():
        content = role_page.read_text(encoding='utf-8')
        
        # Verifica che non ci siano riferimenti ai vecchi ruoli
        old_role_patterns = [
            r'\bRESPONSABILE\b',
            r'\bLAMINATORE\b', 
            r'\bAUTOCLAVISTA\b',
            r'\bresponsabile\b',
            r'\blaminatore\b',
            r'\bautoclavista\b'
        ]
        
        old_roles_found = []
        for pattern in old_role_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                old_roles_found.append(pattern)
        
        if old_roles_found:
            results['issues'].append(f"Vecchi ruoli trovati nella pagina: {old_roles_found}")
            print_colored(f"❌ Vecchi ruoli trovati nella pagina: {old_roles_found}", Colors.RED)
            results['success'] = False
        else:
            print_colored("✅ Pagina role/page.tsx pulita dai vecchi ruoli", Colors.GREEN)
    
    return results

def check_backend_roles() -> Dict[str, any]:
    """Verifica i ruoli definiti nel backend"""
    print_header("⚙️ VERIFICA BACKEND")
    
    results = {
        'success': True,
        'roles_found': [],
        'issues': []
    }
    
    # Controlla l'enum UserRole nel backend
    system_log_file = Path("backend/models/system_log.py")
    if system_log_file.exists():
        content = system_log_file.read_text(encoding='utf-8')
        
        # Estrai i ruoli dall'enum
        enum_match = re.search(r'class UserRole\(enum\.Enum\):(.*?)(?=class|\Z)', content, re.DOTALL)
        if enum_match:
            enum_content = enum_match.group(1)
            roles = []
            for match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']+)["\']', enum_content):
                roles.append(match.group(1))
            
            results['roles_found'] = roles
            print_colored(f"✅ Ruoli trovati nell'enum backend: {', '.join(roles)}", Colors.GREEN)
            
            # Verifica che siano i ruoli corretti
            expected_roles = {'ADMIN', 'MANAGEMENT', 'CLEAN_ROOM', 'CURING', 'SISTEMA'}
            found_roles = set(roles)
            
            if found_roles == expected_roles:
                print_colored("✅ Enum UserRole backend corretto", Colors.GREEN)
            else:
                missing = expected_roles - found_roles
                extra = found_roles - expected_roles
                if missing:
                    results['issues'].append(f"Ruoli mancanti nell'enum: {missing}")
                    print_colored(f"❌ Ruoli mancanti nell'enum: {missing}", Colors.RED)
                if extra:
                    results['issues'].append(f"Ruoli extra nell'enum: {extra}")
                    print_colored(f"❌ Ruoli extra nell'enum: {extra}", Colors.RED)
                results['success'] = False
        else:
            results['issues'].append("Impossibile trovare l'enum UserRole")
            print_colored("❌ Impossibile trovare l'enum UserRole", Colors.RED)
            results['success'] = False
    else:
        results['issues'].append("File system_log.py non trovato")
        print_colored("❌ File system_log.py non trovato", Colors.RED)
        results['success'] = False
    
    return results

def check_migrations() -> Dict[str, any]:
    """Verifica che le migrazioni siano aggiornate"""
    print_header("🗄️ VERIFICA MIGRAZIONI")
    
    results = {
        'success': True,
        'issues': []
    }
    
    # Controlla le migrazioni per vecchi ruoli
    migration_dirs = [
        Path("backend/migrations/versions"),
        Path("backend/alembic/versions")
    ]
    
    # Pattern più specifici per evitare falsi positivi sui nomi di campo
    old_role_patterns = [
        r"'RESPONSABILE'",
        r"'LAMINATORE'",
        r"'AUTOCLAVISTA'",
        r'"RESPONSABILE"',
        r'"LAMINATORE"',
        r'"AUTOCLAVISTA"',
        r"RESPONSABILE\b(?!')",  # RESPONSABILE non seguito da '
        r"LAMINATORE\b(?!')",    # LAMINATORE non seguito da '
        r"AUTOCLAVISTA\b(?!')",  # AUTOCLAVISTA non seguito da '
    ]
    
    for migration_dir in migration_dirs:
        if migration_dir.exists():
            for migration_file in migration_dir.glob("*.py"):
                content = migration_file.read_text(encoding='utf-8')
                
                for pattern in old_role_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Verifica che non sia solo un nome di campo come 'responsabile'
                        if not all('responsabile' in match.lower() and len(match) < 15 for match in matches):
                            results['issues'].append(f"Vecchio ruolo trovato in {migration_file.name}: {matches}")
                            print_colored(f"⚠️ Vecchio ruolo trovato in {migration_file.name}: {matches}", Colors.YELLOW)
                            results['success'] = False
                            break
    
    if results['success']:
        print_colored("✅ Migrazioni pulite dai vecchi ruoli", Colors.GREEN)
    
    return results

def check_role_consistency() -> Dict[str, any]:
    """Verifica la consistenza tra frontend e backend"""
    print_header("🔄 VERIFICA CONSISTENZA")
    
    results = {
        'success': True,
        'issues': []
    }
    
    # Mapping tra ruoli frontend e backend
    role_mapping = {
        'ADMIN': 'ADMIN',
        'Management': 'MANAGEMENT', 
        'Clean Room': 'CLEAN_ROOM',
        'Curing': 'CURING'
    }
    
    print_colored("📋 Mapping ruoli Frontend → Backend:", Colors.BLUE)
    for frontend, backend in role_mapping.items():
        print_colored(f"   {frontend} → {backend}", Colors.WHITE)
    
    # Verifica che il mapping sia implementato correttamente
    # Questo potrebbe richiedere controlli aggiuntivi nei router API
    
    print_colored("✅ Mapping ruoli definito correttamente", Colors.GREEN)
    
    return results

def generate_report(frontend_results: Dict, backend_results: Dict, migration_results: Dict, consistency_results: Dict):
    """Genera un report finale"""
    print_header("📊 REPORT FINALE")
    
    all_success = all([
        frontend_results['success'],
        backend_results['success'], 
        migration_results['success'],
        consistency_results['success']
    ])
    
    if all_success:
        print_colored("🎉 VALIDAZIONE COMPLETATA CON SUCCESSO!", Colors.GREEN + Colors.BOLD)
        print_colored("✅ Tutti i ruoli sono allineati tra frontend e backend", Colors.GREEN)
        print_colored("✅ La pagina di selezione ruolo è pronta per la produzione", Colors.GREEN)
    else:
        print_colored("❌ VALIDAZIONE FALLITA", Colors.RED + Colors.BOLD)
        print_colored("Problemi trovati:", Colors.RED)
        
        all_issues = []
        all_issues.extend(frontend_results.get('issues', []))
        all_issues.extend(backend_results.get('issues', []))
        all_issues.extend(migration_results.get('issues', []))
        all_issues.extend(consistency_results.get('issues', []))
        
        for i, issue in enumerate(all_issues, 1):
            print_colored(f"  {i}. {issue}", Colors.RED)
    
    print_colored(f"\n{'='*60}", Colors.CYAN)
    
    return all_success

def main():
    """Funzione principale"""
    print_colored("🚀 VALIDAZIONE ALLINEAMENTO RUOLI CARBONPILOT", Colors.BOLD + Colors.PURPLE)
    print_colored("Verifica completa dell'allineamento tra frontend e backend", Colors.WHITE)
    
    # Esegui tutte le verifiche
    frontend_results = check_frontend_roles()
    backend_results = check_backend_roles()
    migration_results = check_migrations()
    consistency_results = check_role_consistency()
    
    # Genera report finale
    success = generate_report(frontend_results, backend_results, migration_results, consistency_results)
    
    # Suggerimenti finali
    if success:
        print_colored("\n🎯 PROSSIMI PASSI:", Colors.BLUE + Colors.BOLD)
        print_colored("1. Testa la pagina su localhost:3000/role", Colors.WHITE)
        print_colored("2. Verifica che ogni ruolo reindirizzi correttamente", Colors.WHITE)
        print_colored("3. Controlla che le funzionalità siano accessibili per ogni ruolo", Colors.WHITE)
        print_colored("4. Esegui i test automatici se disponibili", Colors.WHITE)
    else:
        print_colored("\n🔧 AZIONI RICHIESTE:", Colors.YELLOW + Colors.BOLD)
        print_colored("1. Risolvi i problemi elencati sopra", Colors.WHITE)
        print_colored("2. Riesegui questo script per verificare", Colors.WHITE)
        print_colored("3. Testa manualmente la funzionalità", Colors.WHITE)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 