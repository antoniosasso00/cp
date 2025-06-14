#!/usr/bin/env python3
"""
Test semplificato per il Solver 2L
"""

def test_import_basic():
    """Test di importazione base senza percorsi complessi"""
    print("🔍 Test import del solver_2l...")
    
    try:
        # Import diretto del modulo
        import sys
        import os
        
        # Aggiungi il path del modulo
        current_dir = os.path.dirname(__file__)
        sys.path.insert(0, current_dir)
        
        # Import del modulo solver_2l
        import solver_2l
        
        print("✅ Modulo solver_2l importato con successo")
        
        # Test delle classi principali
        classes_to_test = [
            'NestingParameters2L',
            'ToolInfo2L', 
            'AutoclaveInfo2L',
            'NestingLayout2L',
            'NestingMetrics2L',
            'NestingSolution2L',
            'NestingModel2L'
        ]
        
        for class_name in classes_to_test:
            if hasattr(solver_2l, class_name):
                print(f"✅ Classe {class_name} disponibile")
            else:
                print(f"❌ Classe {class_name} mancante")
                return False
        
        # Test creazione oggetti base
        parameters = solver_2l.NestingParameters2L()
        print(f"✅ NestingParameters2L creato: padding={parameters.padding_mm}mm")
        
        autoclave = solver_2l.AutoclaveInfo2L(
            id=1, 
            width=1000, 
            height=800, 
            max_weight=200, 
            max_lines=20
        )
        print(f"✅ AutoclaveInfo2L creato: {autoclave.width}x{autoclave.height}mm")
        
        tool = solver_2l.ToolInfo2L(
            odl_id=1, 
            width=100, 
            height=80, 
            weight=10
        )
        print(f"✅ ToolInfo2L creato: {tool.width}x{tool.height}mm, area={tool.area:.1f}mm²")
        
        solver = solver_2l.NestingModel2L(parameters)
        print("✅ NestingModel2L creato")
        
        # Test della funzione principale solve_2l
        if hasattr(solver, 'solve_2l'):
            print("✅ Metodo solve_2l disponibile")
        else:
            print("❌ Metodo solve_2l mancante")
            return False
        
        print("\n🎉 Tutti i test base sono passati!")
        return True
        
    except ImportError as e:
        print(f"❌ Errore import: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        return False

def test_solve_minimal():
    """Test risoluzione minima"""
    print("\n🚀 Test risoluzione minima...")
    
    try:
        import solver_2l
        
        # Configurazione minimale
        parameters = solver_2l.NestingParameters2L(
            padding_mm=5.0,
            use_cavalletti=False,  # Test senza cavalletti per semplicità
            base_timeout_seconds=5.0
        )
        
        autoclave = solver_2l.AutoclaveInfo2L(
            id=1,
            width=500.0,
            height=400.0, 
            max_weight=100.0,
            max_lines=10,
            has_cavalletti=False
        )
        
        # Un singolo tool piccolo
        tools = [
            solver_2l.ToolInfo2L(
                odl_id=1, 
                width=100, 
                height=80, 
                weight=5
            )
        ]
        
        solver = solver_2l.NestingModel2L(parameters)
        
        print(f"   Configurazione: {autoclave.width}x{autoclave.height}mm, {len(tools)} tool")
        
        # Risoluzione
        solution = solver.solve_2l(tools, autoclave)
        
        print(f"   Risultato: success={solution.success}")
        print(f"   Algoritmo: {solution.algorithm_status}")
        print(f"   Tool posizionati: {solution.metrics.positioned_count}")
        
        if solution.layouts:
            layout = solution.layouts[0]
            print(f"   Posizione: ({layout.x:.1f}, {layout.y:.1f}) livello {layout.level}")
        
        return solution.success
        
    except Exception as e:
        print(f"❌ Errore test risoluzione: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test principale"""
    print("🧪 Test Semplificato Solver 2L")
    print("=" * 50)
    
    # Test 1: Import
    if not test_import_basic():
        print("❌ Test import fallito")
        return False
    
    # Test 2: Risoluzione
    if not test_solve_minimal():
        print("❌ Test risoluzione fallito") 
        return False
    
    print("\n✅ Tutti i test sono passati!")
    print("🎯 Il solver_2l è operativo e pronto per l'uso")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 