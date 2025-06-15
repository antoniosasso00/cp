#!/usr/bin/env python3
"""
Test completo con dataset reale dal database
Identifica perché nessun tool viene posizionato sul livello 1
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import requests
import time
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.models.autoclave import Autoclave
from backend.models.odl import ODL
from backend.models.tool import Tool
from backend.models.parte import Parte
from backend.api.routers.batch_nesting_modules.generation import (
    _convert_db_to_tool_info_2l, _convert_db_to_autoclave_info_2l
)
from backend.services.nesting.solver_2l import (
    NestingModel2L, NestingParameters2L
)

def test_complete_2l_workflow():
    """Test completo del workflow 2L con dataset reale"""
    print("🔍 TEST COMPLETO WORKFLOW 2L CON DATASET REALE")
    print("=" * 70)
    
    # 1. Analisi dataset database
    print("\n📋 FASE 1: Analisi dataset database")
    analyze_database_dataset()
    
    # 2. Test solver diretto con dati reali
    print("\n📋 FASE 2: Test solver diretto")
    test_solver_with_real_data()
    
    # 3. Test endpoint HTTP
    print("\n📋 FASE 3: Test endpoint HTTP")
    test_http_endpoint()
    
    # 4. Analisi risultati e diagnosi
    print("\n📋 FASE 4: Diagnosi finale")
    provide_final_diagnosis()

def analyze_database_dataset():
    """Analizza il dataset presente nel database"""
    print("🗄️ Analisi dataset database...")
    
    try:
        db = next(get_db())
        
        # Trova autoclavi 2L
        autoclavi_2l = db.query(Autoclave).filter(
            Autoclave.usa_cavalletti == True
        ).all()
        
        print(f"🏭 Autoclavi con cavalletti: {len(autoclavi_2l)}")
        for autoclave in autoclavi_2l:
            print(f"   {autoclave.nome} (ID: {autoclave.id})")
            print(f"     Dimensioni: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
            print(f"     Peso max: {autoclave.max_load_kg}kg")
            print(f"     Peso max per cavalletto: {autoclave.peso_max_per_cavalletto_kg}kg")
        
        # Trova ODL in attesa cura
        odls = db.query(ODL).options(
            joinedload(ODL.tool),
            joinedload(ODL.parte)
        ).filter(
            ODL.stato == 'in_attesa_cura'
        ).all()
        
        print(f"\n📦 ODL in attesa cura: {len(odls)}")
        
        # Analizza eligibilità per cavalletti
        eligible_count = 0
        weight_issues = 0
        size_issues = 0
        
        for odl in odls:
            if odl.tool and odl.parte:
                tool_2l = _convert_db_to_tool_info_2l(odl, odl.tool, odl.parte)
                
                weight_ok = tool_2l.weight <= 50.0  # Criterio peso attuale
                size_ok = tool_2l.width <= 500.0 and tool_2l.height <= 800.0
                
                if weight_ok and size_ok:
                    eligible_count += 1
                else:
                    if not weight_ok:
                        weight_issues += 1
                    if not size_ok:
                        size_issues += 1
                
                if len(odls) <= 10:  # Mostra dettagli per primi 10
                    print(f"   ODL {odl.id}: {tool_2l.width:.0f}x{tool_2l.height:.0f}mm, {tool_2l.weight:.1f}kg")
                    print(f"     Eligible: {tool_2l.can_use_cavalletto} (peso: {weight_ok}, size: {size_ok})")
        
        print(f"\n📊 ANALISI ELIGIBILITÀ:")
        print(f"   Tool totali: {len(odls)}")
        print(f"   Tool eligible per cavalletti: {eligible_count}")
        print(f"   Problemi peso (>{50}kg): {weight_issues}")
        print(f"   Problemi dimensioni (>500x800mm): {size_issues}")
        
        if eligible_count == 0:
            print("⚠️ PROBLEMA IDENTIFICATO: Nessun tool eligible per cavalletti!")
            print("   Possibili cause:")
            print("   1. Criteri troppo restrittivi (peso ≤50kg, dimensioni ≤500x800mm)")
            print("   2. Dataset con tool troppo grandi/pesanti")
            
        return len(odls), eligible_count
        
    except Exception as e:
        print(f"❌ Errore analisi database: {e}")
        return 0, 0
    finally:
        db.close()

def test_solver_with_real_data():
    """Test del solver direttamente con dati reali"""
    print("🧪 Test solver con dati reali...")
    
    try:
        db = next(get_db())
        
        # Prendi prima autoclave 2L
        autoclave_db = db.query(Autoclave).filter(
            Autoclave.usa_cavalletti == True
        ).first()
        
        if not autoclave_db:
            print("❌ Nessuna autoclave 2L trovata")
            return
        
        # Prendi primi 10 ODL per test veloce
        odls = db.query(ODL).options(
            joinedload(ODL.tool),
            joinedload(ODL.parte)
        ).filter(
            ODL.stato == 'in_attesa_cura'
        ).limit(10).all()
        
        if not odls:
            print("❌ Nessun ODL trovato")
            return
        
        # Converti in formato solver
        autoclave_2l = _convert_db_to_autoclave_info_2l(autoclave_db)
        tools_2l = []
        
        for odl in odls:
            if odl.tool and odl.parte:
                tool_2l = _convert_db_to_tool_info_2l(odl, odl.tool, odl.parte)
                tools_2l.append(tool_2l)
        
        print(f"🏭 Autoclave: {autoclave_db.nome}")
        print(f"📦 Tool: {len(tools_2l)}")
        print(f"🔧 Cavalletti abilitati: {autoclave_2l.has_cavalletti}")
        
        # Test con parametri standard
        print("\n🔄 Test 1: Parametri standard")
        test_solver_scenario(tools_2l, autoclave_2l, "standard")
        
        # Test con parametri modificati per favorire livello 1
        print("\n🔄 Test 2: Parametri modificati (favorisce livello 1)")
        test_solver_scenario_modified(tools_2l, autoclave_2l)
        
        # Test con tool artificialmente piccoli
        print("\n🔄 Test 3: Tool artificialmente ridotti")
        test_with_reduced_tools(tools_2l, autoclave_2l)
        
    except Exception as e:
        print(f"❌ Errore test solver: {e}")
    finally:
        db.close()

def test_solver_scenario(tools_2l, autoclave_2l, scenario_name):
    """Test scenario specifico del solver"""
    parameters = NestingParameters2L(
        use_cavalletti=True,
        prefer_base_level=True,
        base_timeout_seconds=20.0
    )
    
    solver = NestingModel2L(parameters)
    solution = solver.solve_2l(tools_2l, autoclave_2l)
    
    level_0_count = len([l for l in solution.layouts if l.level == 0])
    level_1_count = len([l for l in solution.layouts if l.level == 1])
    
    print(f"   Scenario {scenario_name}:")
    print(f"     Success: {solution.success}")
    print(f"     Algorithm: {solution.algorithm_status}")
    print(f"     Livello 0: {level_0_count}")
    print(f"     Livello 1: {level_1_count}")
    print(f"     Tool esclusi: {len(solution.excluded_odls)}")

def test_solver_scenario_modified(tools_2l, autoclave_2l):
    """Test con parametri modificati per favorire livello 1"""
    
    # Modifica criteri eligibilità per essere più permissivi
    for tool in tools_2l:
        if tool.weight <= 100.0:  # Aumenta limite peso
            tool.can_use_cavalletto = True
    
    parameters = NestingParameters2L(
        use_cavalletti=True,
        prefer_base_level=False,  # NON preferire livello base
        level_preference_weight=0.01,  # Peso ridotto per preferenza
        base_timeout_seconds=30.0
    )
    
    solver = NestingModel2L(parameters)
    solution = solver.solve_2l(tools_2l, autoclave_2l)
    
    level_0_count = len([l for l in solution.layouts if l.level == 0])
    level_1_count = len([l for l in solution.layouts if l.level == 1])
    
    print(f"   Scenario modificato:")
    print(f"     Success: {solution.success}")
    print(f"     Livello 0: {level_0_count}")
    print(f"     Livello 1: {level_1_count}")
    print(f"     Eligible tools: {len([t for t in tools_2l if t.can_use_cavalletto])}")

def test_with_reduced_tools(tools_2l, autoclave_2l):
    """Test con tool artificialmente ridotti per forzare uso livello 1"""
    
    # Crea versioni ridotte dei tool
    reduced_tools = []
    for i, tool in enumerate(tools_2l[:6]):  # Prendi solo primi 6
        reduced_tool = type(tool)(
            odl_id=tool.odl_id,
            width=min(tool.width, 400),  # Riduci dimensioni
            height=min(tool.height, 300),
            weight=min(tool.weight, 40),  # Riduci peso
            can_use_cavalletto=True,  # Forza eligibilità
            lines_needed=tool.lines_needed,
            priority=tool.priority
        )
        reduced_tools.append(reduced_tool)
    
    parameters = NestingParameters2L(
        use_cavalletti=True,
        prefer_base_level=False,
        base_timeout_seconds=20.0
    )
    
    solver = NestingModel2L(parameters)
    solution = solver.solve_2l(reduced_tools, autoclave_2l)
    
    level_0_count = len([l for l in solution.layouts if l.level == 0])
    level_1_count = len([l for l in solution.layouts if l.level == 1])
    
    print(f"   Scenario tool ridotti:")
    print(f"     Tool count: {len(reduced_tools)}")
    print(f"     Success: {solution.success}")
    print(f"     Livello 0: {level_0_count}")
    print(f"     Livello 1: {level_1_count}")
    
    if level_1_count > 0:
        print("✅ SUCCESS: Con tool ridotti, il solver usa livello 1!")
    else:
        print("❌ PROBLEMA: Anche con tool ridotti, non usa livello 1")

def test_http_endpoint():
    """Test dell'endpoint HTTP 2L"""
    print("🌐 Test endpoint HTTP...")
    
    try:
        # Test connessione
        response = requests.get('http://localhost:8000/api/batch_nesting/data', timeout=5)
        if response.status_code != 200:
            print("❌ Server non raggiungibile")
            return
        
        data = response.json()
        autoclavi_2l = [a for a in data.get('autoclavi_disponibili', []) if a.get('usa_cavalletti')]
        odls = data.get('odl_in_attesa_cura', [])
        
        if not autoclavi_2l:
            print("❌ Nessuna autoclave 2L disponibile via API")
            return
        
        if len(odls) < 5:
            print("❌ Troppo pochi ODL disponibili via API")
            return
        
        print(f"✅ API OK: {len(autoclavi_2l)} autoclavi 2L, {len(odls)} ODL")
        
        # Test generazione 2L
        payload = {
            "autoclavi_2l": [a['id'] for a in autoclavi_2l[:1]],  # Prima autoclave
            "odl_ids": [odl['id'] for odl in odls[:10]],  # Primi 10 ODL
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 15
            },
            "use_cavalletti": True,
            "prefer_base_level": True
        }
        
        print("📤 Invio richiesta generazione 2L...")
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:8000/api/batch_nesting/2l-multi',
            json=payload,
            timeout=120
        )
        
        duration = time.time() - start_time
        print(f"⏱️ Tempo generazione: {duration:.1f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Generazione completata:")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            
            batch_results = result.get('batch_results', [])
            if batch_results:
                batch = batch_results[0]
                level_0_count = batch.get('level_0_count', 0)
                level_1_count = batch.get('level_1_count', 0)
                cavalletti_count = batch.get('cavalletti_used', 0)
                
                print(f"   Livello 0: {level_0_count}")
                print(f"   Livello 1: {level_1_count}")
                print(f"   Cavalletti: {cavalletti_count}")
                print(f"   Batch ID: {batch.get('batch_id')}")
                
                if level_1_count > 0:
                    print("✅ SUCCESS: Endpoint genera tool su livello 1!")
                    return batch.get('batch_id')
                else:
                    print("⚠️ PROBLEMA: Endpoint non genera tool su livello 1")
            else:
                print("❌ Nessun batch result nell'endpoint")
        else:
            print(f"❌ Errore endpoint: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Errore test HTTP: {e}")
    
    return None

def provide_final_diagnosis():
    """Fornisce diagnosi finale e soluzioni"""
    print("🎯 DIAGNOSI FINALE E SOLUZIONI")
    print("-" * 50)
    
    print("📋 PROBLEMI IDENTIFICATI:")
    print("1. Criteri eligibilità troppo restrittivi:")
    print("   - Peso massimo: 50kg (troppo basso per molti tool industriali)")
    print("   - Dimensioni massime: 500x800mm (troppo piccole)")
    
    print("\n2. Algoritmo sequenziale:")
    print("   - Prima riempie completamente livello 0")
    print("   - Solo dopo prova livello 1 con tool rimanenti")
    print("   - Se tutti i tool stanno su livello 0, non usa mai livello 1")
    
    print("\n3. Preferenza eccessiva per livello base:")
    print("   - prefer_base_level=True sempre attivo")
    print("   - Peso preferenza troppo alto")
    
    print("\n🔧 SOLUZIONI PROPOSTE:")
    print("1. Aumentare criteri eligibilità:")
    print("   - Peso massimo: 100kg (invece di 50kg)")
    print("   - Dimensioni: 800x1200mm (invece di 500x800mm)")
    
    print("\n2. Modificare algoritmo sequenziale:")
    print("   - Implementare algoritmo ibrido")
    print("   - Distribuire tool tra livelli in base a criteri ottimali")
    print("   - Non riempire completamente livello 0 prima di provare livello 1")
    
    print("\n3. Parametri più bilanciati:")
    print("   - prefer_base_level=False per alcuni scenari")
    print("   - level_preference_weight ridotto")
    print("   - Considerare efficienza globale invece che preferenza fissa")

if __name__ == "__main__":
    test_complete_2l_workflow() 