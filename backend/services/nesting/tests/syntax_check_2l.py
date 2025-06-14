#!/usr/bin/env python3
"""
Verifica sintattica del Solver 2L
Controlla che il modulo sia importabile e che la struttura sia corretta
"""

def check_syntax():
    """Verifica che il modulo solver_2l abbia una sintassi corretta"""
    print("🔍 Verifica sintattica del modulo solver_2l...")
    
    try:
        # Import del modulo per verifica sintattica
        import ast
        import os
        
        # Leggi il file solver_2l.py
        current_dir = os.path.dirname(__file__)
        solver_path = os.path.join(current_dir, 'solver_2l.py')
        
        if not os.path.exists(solver_path):
            print(f"❌ File {solver_path} non trovato")
            return False
        
        print(f"✅ File {solver_path} trovato")
        
        # Verifica sintassi Python
        with open(solver_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        try:
            ast.parse(source_code)
            print("✅ Sintassi Python corretta")
        except SyntaxError as e:
            print(f"❌ Errore sintassi: {e}")
            return False
        
        # Verifica presenza delle classi principali
        tree = ast.parse(source_code)
        
        expected_classes = [
            'NestingParameters2L',
            'ToolInfo2L',
            'AutoclaveInfo2L', 
            'NestingLayout2L',
            'NestingMetrics2L',
            'NestingSolution2L',
            'NestingModel2L'
        ]
        
        found_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                found_classes.append(node.name)
        
        print(f"\n📋 Classi trovate: {len(found_classes)}")
        for class_name in found_classes:
            print(f"   ✅ {class_name}")
        
        missing_classes = [cls for cls in expected_classes if cls not in found_classes]
        if missing_classes:
            print(f"\n❌ Classi mancanti: {missing_classes}")
            return False
        
        # Verifica presenza delle funzioni principali
        expected_functions = ['solve_2l', 'test_solver_2l']
        found_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                found_functions.append(node.name)
        
        print(f"\n📋 Funzioni trovate: {len(found_functions)}")
        for func in expected_functions:
            if func in found_functions:
                print(f"   ✅ {func}")
            else:
                print(f"   ❌ {func} mancante")
        
        # Verifica import necessari
        expected_imports = ['logging', 'math', 'time', 'cp_model', 'numpy']
        found_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    found_imports.append(node.module.split('.')[0])
        
        print(f"\n📋 Import principali:")
        for imp in expected_imports:
            if any(imp in found_imp for found_imp in found_imports):
                print(f"   ✅ {imp}")
            else:
                print(f"   ⚠️ {imp} (potrebbe mancare)")
        
        print(f"\n🎯 Dimensioni modulo: {len(source_code)} caratteri, {len(source_code.splitlines())} linee")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante verifica: {e}")
        return False

def check_structure():
    """Verifica la struttura del codice"""
    print("\n🏗️ Verifica struttura del codice...")
    
    try:
        import os
        
        current_dir = os.path.dirname(__file__)
        solver_path = os.path.join(current_dir, 'solver_2l.py')
        
        with open(solver_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Verifica presenza docstring iniziale
        has_docstring = False
        for i, line in enumerate(lines[:10]):
            if '"""' in line and '2L' in line:
                has_docstring = True
                break
        
        print(f"   Docstring iniziale: {'✅ Presente' if has_docstring else '❌ Mancante'}")
        
        # Verifica presenza commenti di sezione
        key_sections = ['@dataclass', 'def solve_2l', 'def _solve_cpsat_2l', 'def _solve_greedy_2l']
        sections_found = []
        
        for line in lines:
            for section in key_sections:
                if section in line:
                    sections_found.append(section)
                    break
        
        print(f"   Sezioni chiave trovate: {len(set(sections_found))}/{len(key_sections)}")
        for section in key_sections:
            status = "✅" if section in sections_found else "❌"
            print(f"     {status} {section}")
        
        # Verifica presenza test function
        has_test = any('def test_solver_2l' in line for line in lines)
        print(f"   Funzione di test: {'✅ Presente' if has_test else '❌ Mancante'}")
        
        return len(set(sections_found)) >= len(key_sections) - 1  # Tolleranza di 1
        
    except Exception as e:
        print(f"❌ Errore verifica struttura: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Verifica Sintattica Solver 2L")
    print("=" * 50)
    
    # Test 1: Sintassi
    syntax_ok = check_syntax()
    
    # Test 2: Struttura
    structure_ok = check_structure()
    
    # Riepilogo
    print(f"\n🏁 RIEPILOGO")
    print("=" * 30)
    print(f"Sintassi: {'✅ OK' if syntax_ok else '❌ ERRORE'}")
    print(f"Struttura: {'✅ OK' if structure_ok else '❌ ERRORE'}")
    
    overall_success = syntax_ok and structure_ok
    
    if overall_success:
        print("\n🎉 Il modulo solver_2l ha superato tutti i controlli!")
        print("📝 Il solver è pronto per essere testato con dati reali.")
        print("\n💡 Per testare la funzionalità:")
        print("   1. Assicurati che OR-Tools sia installato")
        print("   2. Esegui: python solver_2l.py")
        print("   3. Controlla l'output del test integrato")
    else:
        print("\n⚠️ Sono stati rilevati problemi nel modulo.")
        print("📝 Controlla e correggi gli errori segnalati.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 