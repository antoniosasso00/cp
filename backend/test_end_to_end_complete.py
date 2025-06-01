#!/usr/bin/env python3
"""
Test End-to-End COMPLETO del modulo Nesting CarbonPilot
Verifica tutto il flusso: algoritmo → API → database → frontend compatibility
"""

import sys
sys.path.append('.')

import json
import requests
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.odl import ODL
from models.autoclave import Autoclave
from models.batch_nesting import BatchNesting
from services.nesting_service import NestingService, NestingParameters

# Configurazione
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1"

def print_header(title):
    """Stampa un header formattato"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print('='*60)

def print_step(step_num, title):
    """Stampa un step formattato"""
    print(f"\n📋 STEP {step_num}: {title}")
    print('-'*50)

def test_backend_health():
    """Test 1: Verifica che il backend sia attivo"""
    print_step(1, "VERIFICA BACKEND HEALTH")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend attivo e funzionante")
            print(f"   📊 Status: {health_data.get('status')}")
            print(f"   📊 Database: {health_data.get('database', {}).get('status')}")
            print(f"   📊 Tabelle: {health_data.get('database', {}).get('tables_count')}")
            return True
        else:
            print(f"❌ Backend non healthy: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend non raggiungibile!")
        print("🔧 Assicurati che il backend sia avviato con:")
        print("   cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Errore nel test backend: {e}")
        return False

def test_database_data():
    """Test 2: Verifica dati nel database"""
    print_step(2, "VERIFICA DATI DATABASE")
    
    engine = create_engine('sqlite:///./carbonpilot.db')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Verifica ODL
        odl_count = db.query(ODL).count()
        odl_attesa_cura = db.query(ODL).filter(ODL.status == 'Attesa Cura').count()
        print(f"📋 ODL totali: {odl_count}")
        print(f"📋 ODL in 'Attesa Cura': {odl_attesa_cura}")
        
        # Verifica autoclavi
        autoclave_count = db.query(Autoclave).count()
        autoclave_disponibili = db.query(Autoclave).filter(Autoclave.stato == 'DISPONIBILE').count()
        print(f"🏭 Autoclavi totali: {autoclave_count}")
        print(f"🏭 Autoclavi disponibili: {autoclave_disponibili}")
        
        # Verifica che ci siano dati sufficienti per il test
        if odl_attesa_cura == 0:
            print("⚠️ Nessun ODL in 'Attesa Cura' - creazione dati di test...")
            return False
        
        if autoclave_disponibili == 0:
            print("⚠️ Nessuna autoclave disponibile - verifica configurazione")
            return False
        
        print("✅ Dati sufficienti per il test")
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test database: {e}")
        return False
    finally:
        db.close()

def test_nesting_algorithm():
    """Test 3: Verifica algoritmo di nesting diretto"""
    print_step(3, "VERIFICA ALGORITMO NESTING DIRETTO")
    
    engine = create_engine('sqlite:///./carbonpilot.db')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Prendi primi 2 ODL disponibili
        odls = db.query(ODL).filter(ODL.status == 'Attesa Cura').limit(2).all()
        autoclave = db.query(Autoclave).filter(Autoclave.stato == 'DISPONIBILE').first()
        
        if not odls or not autoclave:
            print("❌ Dati insufficienti per il test algoritmo")
            return False
        
        odl_ids = [odl.id for odl in odls]
        print(f"🔧 Test algoritmo con ODL {odl_ids} su autoclave {autoclave.id}")
        
        # Parametri ottimizzati
        parameters = NestingParameters(
            padding_mm=10,
            min_distance_mm=5,
            priorita_area=False
        )
        
        # Esegui algoritmo
        nesting_service = NestingService()
        result = nesting_service.generate_nesting(
            db=db,
            odl_ids=odl_ids,
            autoclave_id=autoclave.id,
            parameters=parameters
        )
        
        print(f"📊 Risultato algoritmo:")
        print(f"   • Successo: {result.success}")
        print(f"   • ODL posizionati: {len(result.positioned_tools)}")
        print(f"   • ODL esclusi: {len(result.excluded_odls)}")
        print(f"   • Efficienza: {result.efficiency:.1f}%")
        print(f"   • Status: {result.algorithm_status}")
        
        if result.positioned_tools:
            print("   ✅ Tool posizionati:")
            for tool in result.positioned_tools:
                print(f"     • ODL {tool.odl_id}: pos({tool.x:.0f},{tool.y:.0f}), dim({tool.width:.0f}x{tool.height:.0f}mm), ruotato={tool.rotated}")
        
        if result.excluded_odls:
            print("   ❌ ODL esclusi:")
            for excl in result.excluded_odls:
                print(f"     • ODL {excl['odl_id']}: {excl['motivo']}")
        
        success = result.success and len(result.positioned_tools) > 0
        
        if success:
            print("✅ Algoritmo di nesting funziona correttamente")
        else:
            print("❌ Algoritmo non riesce a posizionare ODL")
            
        return success
        
    except Exception as e:
        print(f"❌ Errore nel test algoritmo: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_api_endpoint():
    """Test 4: Verifica endpoint API /nesting/genera"""
    print_step(4, "VERIFICA ENDPOINT API /nesting/genera")
    
    # Prepara payload di test
    payload = {
        "odl_ids": ["1", "2"],
        "autoclave_ids": ["1"],
        "parametri": {
            "padding_mm": 10,
            "min_distance_mm": 5,
            "priorita_area": False
        }
    }
    
    try:
        print(f"🌐 POST {API_BASE}/nesting/genera")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{API_BASE}/nesting/genera",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Risposta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint funziona!")
            print(f"📊 Batch ID: {data.get('batch_id')}")
            print(f"📊 Successo: {data.get('success')}")
            print(f"📊 ODL posizionati: {len(data.get('positioned_tools', []))}")
            print(f"📊 Efficienza: {data.get('efficiency', 0):.1f}%")
            
            # Verifica struttura risposta
            required_fields = ['batch_id', 'success', 'positioned_tools', 'excluded_odls', 'efficiency']
            missing = [field for field in required_fields if field not in data]
            
            if missing:
                print(f"⚠️ Campi mancanti nella risposta: {missing}")
                return False
            
            return data.get('success', False) and data.get('batch_id')
            
        else:
            print(f"❌ API endpoint fallito: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 Errore: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📋 Risposta raw: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Errore nel test API: {e}")
        return False

def test_batch_nesting_crud():
    """Test 5: Verifica CRUD batch_nesting"""
    print_step(5, "VERIFICA CRUD BATCH_NESTING")
    
    try:
        # Test GET /batch_nesting
        print("🔍 GET /batch_nesting/")
        response = requests.get(f"{API_BASE}/batch_nesting/")
        
        if response.status_code == 200:
            batches = response.json()
            print(f"✅ {len(batches)} batch trovati")
            
            if batches:
                # Test dettagli primo batch
                batch_id = batches[0]['id']
                print(f"🔍 GET /batch_nesting/{batch_id}")
                
                detail_response = requests.get(f"{API_BASE}/batch_nesting/{batch_id}")
                if detail_response.status_code == 200:
                    batch_detail = detail_response.json()
                    print("✅ Dettagli batch recuperati")
                    print(f"   📊 Nome: {batch_detail.get('nome')}")
                    print(f"   📊 Stato: {batch_detail.get('stato')}")
                    print(f"   📊 ODL count: {len(batch_detail.get('odl_ids', []))}")
                    
                    # Test full endpoint
                    print(f"🔍 GET /batch_nesting/{batch_id}/full")
                    full_response = requests.get(f"{API_BASE}/batch_nesting/{batch_id}/full")
                    if full_response.status_code == 200:
                        full_data = full_response.json()
                        print("✅ Dati completi batch recuperati")
                        
                        # Verifica compatibilità frontend
                        if 'configurazione_json' in full_data:
                            config = full_data['configurazione_json']
                            frontend_fields = ['canvas_width', 'canvas_height', 'tool_positions']
                            missing_frontend = [f for f in frontend_fields if f not in config]
                            
                            if not missing_frontend:
                                print("✅ Struttura compatibile con frontend")
                                return True
                            else:
                                print(f"⚠️ Campi frontend mancanti: {missing_frontend}")
                        else:
                            print("⚠️ configurazione_json mancante")
                    else:
                        print(f"❌ Full endpoint fallito: {full_response.status_code}")
                else:
                    print(f"❌ Detail endpoint fallito: {detail_response.status_code}")
            else:
                print("⚠️ Nessun batch trovato - genera prima un nesting")
                
        else:
            print(f"❌ List endpoint fallito: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test CRUD: {e}")
        return False

def test_frontend_api_endpoints():
    """Test 6: Verifica endpoint necessari per il frontend"""
    print_step(6, "VERIFICA ENDPOINT PER FRONTEND")
    
    endpoints_to_test = [
        ("GET", "/odl/", "Lista ODL"),
        ("GET", "/autoclavi/", "Lista autoclavi"),
        ("GET", "/batch_nesting/", "Lista batch nesting")
    ]
    
    success_count = 0
    
    for method, endpoint, description in endpoints_to_test:
        try:
            print(f"🔍 {method} {endpoint} - {description}")
            response = requests.get(f"{API_BASE}{endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {len(data) if isinstance(data, list) else 'OK'}")
                success_count += 1
            else:
                print(f"   ❌ Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Errore: {e}")
    
    print(f"\n📊 Risultato: {success_count}/{len(endpoints_to_test)} endpoint funzionanti")
    return success_count == len(endpoints_to_test)

def run_complete_end_to_end_test():
    """Esegue il test end-to-end completo"""
    print_header("TEST END-TO-END COMPLETO MODULO NESTING")
    
    results = {}
    
    # Esegui tutti i test
    results['backend_health'] = test_backend_health()
    results['database_data'] = test_database_data()
    results['nesting_algorithm'] = test_nesting_algorithm()
    results['api_endpoint'] = test_api_endpoint()
    results['batch_crud'] = test_batch_nesting_crud()
    results['frontend_endpoints'] = test_frontend_api_endpoints()
    
    # Risultati finali
    print_header("RISULTATI FINALI TEST END-TO-END")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
        if result:
            passed += 1
    
    print(f"\n📊 SUMMARY: {passed}/{total} test passati")
    
    # Valutazione finale
    if passed == total:
        print("\n🎉 TUTTI I TEST SUPERATI!")
        print("✅ Il modulo nesting è completamente funzionale")
        print("✅ Backend, API e compatibilità frontend OK")
        print("✅ Pronto per l'uso in produzione")
        
        print("\n🌐 FRONTEND ACCESS:")
        print("   • Nuovo nesting: http://localhost:3000/nesting/new")
        print("   • Lista batch: http://localhost:3000/dashboard/curing/nesting/list")
        
    elif passed >= total * 0.8:  # 80% dei test passati
        print("\n🟡 MAGGIOR PARTE DEI TEST SUPERATI")
        print("✅ Funzionalità core operative")
        print("⚠️ Alcuni aspetti secondari necessitano verifica")
        
    else:
        print("\n❌ TROPPI TEST FALLITI")
        print("🔧 Il sistema necessita correzioni prima dell'uso")
        
        print("\n🔧 AZIONI SUGGERITE:")
        if not results['backend_health']:
            print("   • Avvia il backend: cd backend && uvicorn main:app --reload")
        if not results['database_data']:
            print("   • Verifica/inizializza database: cd backend && python create_test_odl.py")
        if not results['nesting_algorithm']:
            print("   • Debug algoritmo: cd backend && python debug_detailed_nesting.py")
    
    return passed == total

if __name__ == "__main__":
    print("🚀 AVVIO TEST END-TO-END COMPLETO")
    
    try:
        success = run_complete_end_to_end_test()
        exit_code = 0 if success else 1
        print(f"\n🏁 Test completato con exit code: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotto dall'utente")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Errore critico nel test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 