#!/usr/bin/env python3
"""
Test script per verificare l'implementazione dell'endpoint 2L
"""

import sys
import os

# Aggiungi il percorso del backend al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test importazione moduli necessari"""
    print("🔍 Test 1: Importazione moduli...")
    
    try:
        from schemas.batch_nesting import NestingSolveRequest2L, NestingSolveResponse2L
        print("✅ Schemi 2L importati correttamente")
    except ImportError as e:
        print(f"❌ Errore importazione schemi 2L: {e}")
        return False
    
    try:
        from services.nesting.solver_2l import NestingModel2L
        print("✅ Solver 2L importato correttamente")
    except ImportError as e:
        print(f"❌ Errore importazione solver 2L: {e}")
        return False
    
    try:
        from api.routers.batch_nesting_modules.generation import router
        print("✅ Router generation importato correttamente")
    except ImportError as e:
        print(f"❌ Errore importazione router: {e}")
        return False
    
    return True

def test_schema_creation():
    """Test creazione schemi request/response"""
    print("\n🔍 Test 2: Creazione schemi...")
    
    try:
        from schemas.batch_nesting import NestingSolveRequest2L
        
        # Test creazione request con parametri di default
        request = NestingSolveRequest2L(
            autoclave_id=1,
            odl_ids=[1, 2, 3],
            use_cavalletti=True
        )
        print(f"✅ Request 2L creata: autoclave_id={request.autoclave_id}, use_cavalletti={request.use_cavalletti}")
        return True
        
    except Exception as e:
        print(f"❌ Errore creazione schema: {e}")
        return False

def test_solver_instantiation():
    """Test istanziazione solver 2L"""
    print("\n🔍 Test 3: Istanziazione solver...")
    
    try:
        from services.nesting.solver_2l import NestingModel2L, NestingParameters2L
        
        parameters = NestingParameters2L(
            use_cavalletti=True,
            padding_mm=10.0,
            min_distance_mm=15.0
        )
        
        solver = NestingModel2L(parameters)
        print(f"✅ Solver 2L istanziato con parametri: cavalletti={parameters.use_cavalletti}")
        return True
        
    except Exception as e:
        print(f"❌ Errore istanziazione solver: {e}")
        return False

def test_router_registration():
    """Test registrazione endpoint nel router"""
    print("\n🔍 Test 4: Registrazione endpoint...")
    
    try:
        from api.routers.batch_nesting_modules.generation import router
        
        # Cerca l'endpoint 2L nelle routes
        found_2l_endpoint = False
        for route in router.routes:
            if hasattr(route, 'path') and '/2l' in route.path:
                found_2l_endpoint = True
                print(f"✅ Endpoint 2L trovato: {route.path} ({route.methods})")
                break
        
        if not found_2l_endpoint:
            print("❌ Endpoint /2l non trovato nelle routes")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Errore verifica router: {e}")
        return False

def test_endpoint_structure():
    """Test struttura endpoint"""
    print("\n🔍 Test 5: Struttura endpoint...")
    
    try:
        from api.routers.batch_nesting_modules.generation import solve_nesting_2l_batch
        import inspect
        
        # Verifica signature della funzione
        sig = inspect.signature(solve_nesting_2l_batch)
        params = list(sig.parameters.keys())
        
        expected_params = ['request', 'db']
        if all(param in params for param in expected_params):
            print(f"✅ Signature endpoint corretta: {params}")
            return True
        else:
            print(f"❌ Signature endpoint incorretta. Attesa: {expected_params}, Trovata: {params}")
            return False
            
    except Exception as e:
        print(f"❌ Errore verifica struttura: {e}")
        return False

def main():
    """Esegue tutti i test"""
    print("🚀 === TEST ENDPOINT 2L - INIZIO ===\n")
    
    tests = [
        test_imports,
        test_schema_creation,
        test_solver_instantiation,
        test_router_registration,
        test_endpoint_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 === RISULTATI TEST ===")
    print(f"✅ Test passati: {passed}/{total}")
    
    if passed == total:
        print("🎉 Tutti i test sono passati! Endpoint 2L pronto per l'uso.")
        return True
    else:
        print("❌ Alcuni test sono falliti. Verifica l'implementazione.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 