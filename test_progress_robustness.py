#!/usr/bin/env python3
"""
Test per verificare la robustezza del sistema di progresso ODL

Questo script testa tutti i scenari:
1. ODL con StateTrackingService attivo
2. ODL con solo ODLLogService 
3. ODL senza log (fallback)
4. Frontend che gestisce tutti i casi

Autore: Sistema CarbonPilot
Data: 2024
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configurazione
BACKEND_URL = "http://localhost:8000/api"
FRONTEND_URL = "http://localhost:3000"

def print_header(title: str):
    """Stampa un header formattato"""
    print(f"\n{'='*60}")
    print(f"🎯 {title.upper()}")
    print(f"{'='*60}")

def print_section(title: str):
    """Stampa una sezione"""
    print(f"\n{'─'*40}")
    print(f"📋 {title}")
    print(f"{'─'*40}")

def test_progress_endpoint(odl_id: int) -> Optional[Dict[str, Any]]:
    """
    Testa l'endpoint di progresso per un ODL specifico
    
    Args:
        odl_id: ID dell'ODL da testare
        
    Returns:
        Dati di progresso o None se errore
    """
    try:
        url = f"{BACKEND_URL}/odl-monitoring/monitoring/{odl_id}/progress"
        print(f"🔗 Testing: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Analizza i dati ricevuti
            print(f"✅ Dati ricevuti con successo!")
            print(f"   📋 ODL ID: {data.get('id', 'N/A')}")
            print(f"   📋 Status: {data.get('status', 'N/A')}")
            print(f"   📋 Timeline Data: {data.get('has_timeline_data', False)}")
            print(f"   📋 Data Source: {data.get('data_source', 'N/A')}")
            print(f"   📋 Timestamps: {len(data.get('timestamps', []))}")
            print(f"   📋 Tempo Stimato: {data.get('tempo_totale_stimato', 'N/A')} min")
            
            # Dettagli timestamps se presenti
            timestamps = data.get('timestamps', [])
            if timestamps:
                print(f"\n   📅 Dettagli Timeline:")
                for i, ts in enumerate(timestamps, 1):
                    stato = ts.get('stato', 'N/A')
                    durata = ts.get('durata_minuti', 0)
                    inizio = ts.get('inizio', 'N/A')
                    fine = ts.get('fine', 'In corso')
                    print(f"      {i}. {stato}: {durata}min ({inizio} → {fine})")
            else:
                print(f"   ⚠️  Nessun timestamp (modalità fallback)")
            
            return data
            
        elif response.status_code == 404:
            print(f"❌ ODL {odl_id} non trovato")
            return None
        else:
            print(f"❌ Errore HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Errore durante il test: {str(e)}")
        return None

def test_odl_list() -> List[int]:
    """
    Ottiene una lista di ODL per i test
    
    Returns:
        Lista di ID ODL disponibili
    """
    try:
        url = f"{BACKEND_URL}/odl/"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            odl_list = response.json()
            odl_ids = [odl['id'] for odl in odl_list[:5]]  # Primi 5 ODL
            print(f"✅ Trovati {len(odl_ids)} ODL per test: {odl_ids}")
            return odl_ids
        else:
            print(f"❌ Errore nel recupero ODL: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Errore nel recupero lista ODL: {str(e)}")
        return []

def test_state_tracking_init() -> bool:
    """
    Inizializza il state tracking se necessario
    
    Returns:
        True se inizializzazione riuscita
    """
    try:
        url = f"{BACKEND_URL}/odl-monitoring/monitoring/initialize-state-tracking"
        response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logs_creati = data.get('logs_creati', 0)
            print(f"✅ State tracking inizializzato: {logs_creati} log creati")
            return True
        else:
            print(f"⚠️ Inizializzazione non riuscita: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore inizializzazione: {str(e)}")
        return False

def analyze_data_sources(results: List[Dict[str, Any]]):
    """
    Analizza le fonti dei dati raccolti
    
    Args:
        results: Lista dei risultati dei test
    """
    print_section("ANALISI FONTI DATI")
    
    sources = {}
    total_tested = len(results)
    
    for result in results:
        source = result.get('data_source', 'unknown')
        if source not in sources:
            sources[source] = 0
        sources[source] += 1
    
    print(f"📊 Distribuzione fonti dati su {total_tested} ODL testati:")
    
    for source, count in sources.items():
        percentage = (count / total_tested) * 100
        emoji = {
            'state_tracking': '🎯',
            'odl_logs': '📋', 
            'odl_created_time': '⏰',
            'fallback': '🔄'
        }.get(source, '❓')
        
        print(f"   {emoji} {source}: {count} ODL ({percentage:.1f}%)")
    
    # Raccomandazioni
    state_tracking_count = sources.get('state_tracking', 0)
    if state_tracking_count < total_tested * 0.8:
        print(f"\n💡 RACCOMANDAZIONE:")
        print(f"   Solo {state_tracking_count}/{total_tested} ODL hanno state tracking completo.")
        print(f"   Considera di:")
        print(f"   1. Eseguire initialize-state-tracking")
        print(f"   2. Verificare che i cambi di stato siano registrati correttamente")

def test_frontend_integration():
    """
    Testa l'integrazione frontend se disponibile
    """
    print_section("TEST INTEGRAZIONE FRONTEND")
    
    try:
        # Verifica se il frontend è raggiungibile
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Frontend raggiungibile su {FRONTEND_URL}")
            print(f"💡 Suggerimenti per test manuale:")
            print(f"   1. Vai alla pagina ODL")
            print(f"   2. Controlla che le barre di progresso mostrino dati corretti")
            print(f"   3. Verifica che i badge 'Stimato' appaiano quando appropriato")
            print(f"   4. Testa il click sulla timeline per aprire il modal")
        else:
            print(f"⚠️ Frontend non raggiungibile: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Frontend non disponibile: {str(e)}")

def main():
    """Funzione principale di test"""
    print_header("TEST ROBUSTEZZA SISTEMA PROGRESSO ODL")
    print(f"🕐 Test avviato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Ottieni lista ODL da testare
    print_section("PREPARAZIONE TEST")
    odl_ids = test_odl_list()
    
    if not odl_ids:
        print("❌ Nessun ODL disponibile per i test")
        return
    
    # 2. Inizializza state tracking se necessario
    print_section("INIZIALIZZAZIONE STATE TRACKING")
    state_init_success = test_state_tracking_init()
    
    if state_init_success:
        print("⏱️ Attendo 2 secondi per il processing...")
        time.sleep(2)
    
    # 3. Testa ogni ODL
    print_section("TEST ENDPOINT PROGRESSO")
    results = []
    
    for i, odl_id in enumerate(odl_ids, 1):
        print(f"\n🧪 Test {i}/{len(odl_ids)} - ODL #{odl_id}")
        result = test_progress_endpoint(odl_id)
        if result:
            results.append(result)
    
    # 4. Analizza i risultati
    if results:
        analyze_data_sources(results)
    
    # 5. Test integrazione frontend
    test_frontend_integration()
    
    # 6. Riepilogo finale
    print_header("RIEPILOGO FINALE")
    
    successful_tests = len(results)
    total_tests = len(odl_ids)
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"📊 Risultati test:")
    print(f"   ✅ Test riusciti: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"   🎯 State tracking attivo: {sum(1 for r in results if r.get('data_source') == 'state_tracking')}")
    print(f"   📋 ODL con logs: {sum(1 for r in results if r.get('data_source') == 'odl_logs')}")
    print(f"   ⏰ Fallback temporale: {sum(1 for r in results if r.get('data_source') == 'odl_created_time')}")
    
    if success_rate >= 90:
        print(f"\n🎉 SISTEMA ROBUSTO - Tutti i test sono passati!")
    elif success_rate >= 70:
        print(f"\n✅ SISTEMA FUNZIONANTE - La maggior parte dei test è passata")
    else:
        print(f"\n⚠️ SISTEMA INSTABILE - Molti test falliti, verifica configurazione")
    
    print(f"\n💡 Prossimi passi:")
    print(f"   1. Verifica nel browser che le barre di progresso mostrino tempi reali")
    print(f"   2. Controlla che i badge 'Stimato' appaiano solo quando necessario")
    print(f"   3. Testa i cambi di stato per verificare l'aggiornamento in tempo reale")
    print(f"   4. Monitora i log del backend per eventuali errori")
    
    print(f"\n🎯 TEST COMPLETATO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 