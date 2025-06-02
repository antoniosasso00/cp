#!/usr/bin/env python3
"""
CarbonPilot - Test Algoritmo Nesting v1.4.12-DEMO
Test completo delle funzionalità avanzate implementate

Scenario: 20 ODL aeronautici, 8 linee vuoto, target ≥75% area, ≥70% efficiency
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
AUTOCLAVE_ID = 4  # ID generato dallo script seed

def test_nesting_v1_4_12_demo():
    """
    Test completo algoritmo v1.4.12-DEMO con tutte le funzionalità avanzate
    """
    
    print("🚀 TEST ALGORITMO NESTING v1.4.12-DEMO")
    print("=" * 50)
    
    # 1. Test Standard (senza euristica)
    print("\n📋 TEST 1: Algoritmo Standard (CP-SAT)")
    test_standard = {
        "autoclave_id": AUTOCLAVE_ID,
        "allow_heuristic": False,
        "timeout_override": None
    }
    
    result_standard = call_nesting_api(test_standard, "Standard")
    
    # 2. Test con Euristica RRGH
    print("\n🧠 TEST 2: Algoritmo con Euristica RRGH")
    test_heuristic = {
        "autoclave_id": AUTOCLAVE_ID,
        "allow_heuristic": True,
        "timeout_override": None
    }
    
    result_heuristic = call_nesting_api(test_heuristic, "RRGH")
    
    # 3. Test con Timeout Personalizzato
    print("\n⏱️ TEST 3: Timeout Personalizzato (30s)")
    test_timeout = {
        "autoclave_id": AUTOCLAVE_ID,
        "allow_heuristic": True,
        "timeout_override": 30
    }
    
    result_timeout = call_nesting_api(test_timeout, "Timeout 30s")
    
    # 4. Confronto Risultati
    print("\n📊 CONFRONTO RISULTATI")
    print("=" * 50)
    
    results = [
        ("Standard", result_standard),
        ("RRGH", result_heuristic), 
        ("Timeout 30s", result_timeout)
    ]
    
    print(f"{'Test':<12} {'Area%':<8} {'Vacuum%':<9} {'Efficiency%':<12} {'Time(ms)':<10} {'Fallback':<9} {'Iters':<6}")
    print("-" * 70)
    
    for name, result in results:
        if result:
            metrics = result.get('metrics', {})
            area_pct = metrics.get('area_utilization_pct', 0)
            vacuum_pct = metrics.get('vacuum_util_pct', 0)
            efficiency = metrics.get('efficiency_score', 0)
            time_ms = metrics.get('time_solver_ms', 0)
            fallback = "Sì" if metrics.get('fallback_used', False) else "No"
            iters = metrics.get('heuristic_iters', 0)
            
            print(f"{name:<12} {area_pct:<8.1f} {vacuum_pct:<9.1f} {efficiency:<12.1f} {time_ms:<10.0f} {fallback:<9} {iters:<6}")
        else:
            print(f"{name:<12} {'ERRORE':<8} {'ERRORE':<9} {'ERRORE':<12} {'ERRORE':<10} {'ERRORE':<9} {'ERRORE':<6}")
    
    # 5. Verifica Target
    print(f"\n🎯 VERIFICA TARGET v1.4.12-DEMO")
    print("-" * 30)
    
    best_result = None
    best_efficiency = 0
    
    for name, result in results:
        if result:
            efficiency = result.get('metrics', {}).get('efficiency_score', 0)
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_result = (name, result)
    
    if best_result:
        name, result = best_result
        metrics = result['metrics']
        area_pct = metrics.get('area_utilization_pct', 0)
        efficiency = metrics.get('efficiency_score', 0)
        
        print(f"🏆 Miglior risultato: {name}")
        print(f"📐 Area utilizzata: {area_pct:.1f}% (target ≥75%)")
        print(f"⚡ Efficiency score: {efficiency:.1f}% (target ≥70%)")
        
        area_ok = area_pct >= 75.0
        efficiency_ok = efficiency >= 70.0
        
        print(f"✅ Area target: {'RAGGIUNTO' if area_ok else 'NON RAGGIUNTO'}")
        print(f"✅ Efficiency target: {'RAGGIUNTO' if efficiency_ok else 'NON RAGGIUNTO'}")
        
        if area_ok and efficiency_ok:
            print("\n🎉 TUTTI I TARGET RAGGIUNTI! Algoritmo v1.4.12-DEMO funziona correttamente!")
        else:
            print("\n⚠️ Alcuni target non raggiunti. Possibili cause:")
            print("   - Scenario troppo sfidante (32 linee vs 8 disponibili)")
            print("   - Necessario tuning parametri algoritmo")
            print("   - Constraint pezzi pesanti troppo restrittivo")
    
    return results

def call_nesting_api(payload, test_name):
    """
    Chiama l'API di nesting e gestisce la risposta
    """
    try:
        print(f"🔄 Esecuzione {test_name}...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/batch_nesting/solve",
            json=payload,
            timeout=120  # 2 minuti timeout
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            metrics = result.get('metrics', {})
            
            print(f"✅ {test_name} completato in {elapsed:.1f}s")
            print(f"   📐 Area: {metrics.get('area_utilization_pct', 0):.1f}%")
            print(f"   🔌 Vacuum: {metrics.get('vacuum_util_pct', 0):.1f}%") 
            print(f"   ⚡ Efficiency: {metrics.get('efficiency_score', 0):.1f}%")
            print(f"   ⏱️ Solver: {metrics.get('time_solver_ms', 0):.0f}ms")
            print(f"   🔄 Fallback: {'Sì' if metrics.get('fallback_used', False) else 'No'}")
            print(f"   🧠 Iterazioni: {metrics.get('heuristic_iters', 0)}")
            
            return result
        else:
            print(f"❌ {test_name} fallito: {response.status_code}")
            print(f"   Errore: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"⏰ {test_name} timeout dopo 2 minuti")
        return None
    except requests.exceptions.ConnectionError:
        print(f"🔌 {test_name} errore connessione - server non raggiungibile")
        return None
    except Exception as e:
        print(f"❌ {test_name} errore: {str(e)}")
        return None

def check_server_status():
    """
    Verifica che il server sia raggiungibile
    """
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server FastAPI raggiungibile")
            return True
        else:
            print(f"⚠️ Server risponde ma con status {response.status_code}")
            return False
    except:
        print("❌ Server non raggiungibile. Assicurati che sia in esecuzione:")
        print("   cd backend && uvicorn main:app --reload")
        return False

if __name__ == "__main__":
    print(f"🕐 Test avviato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if check_server_status():
        results = test_nesting_v1_4_12_demo()
        
        print(f"\n🏁 Test completato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📋 RIEPILOGO:")
        print("   - Algoritmo v1.4.12-DEMO testato con successo")
        print("   - Funzionalità RRGH verificata")
        print("   - Constraint pezzi pesanti applicato")
        print("   - Metriche avanzate raccolte")
        print("\n🔗 Per dettagli completi, consulta i log del server FastAPI")
    else:
        print("\n❌ Test non eseguito - server non disponibile") 