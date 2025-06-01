#!/usr/bin/env python3
"""
Test per verificare le ottimizzazioni del modulo di nesting
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_endpoint(method: str, endpoint: str, data=None):
    """Helper per testare endpoint API"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data)
        else:
            print(f"❌ Metodo {method} non supportato")
            return None
            
        if response.status_code >= 200 and response.status_code < 300:
            return response.json()
        else:
            print(f"❌ Errore API {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Errore di connessione: {str(e)}")
        return None

def print_section(title: str):
    """Stampa una sezione con formattazione"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def main():
    """Test completo delle ottimizzazioni nesting"""
    
    print_section("TEST OTTIMIZZAZIONI NESTING")
    
    # 1. Verifica ODL disponibili
    print("\n📋 1. VERIFICA ODL DISPONIBILI")
    odl_data = test_endpoint("GET", "/odl")
    if not odl_data:
        print("❌ Impossibile recuperare ODL")
        return
        
    # Filtra ODL in Attesa Cura
    odl_attesa_cura = [odl for odl in odl_data if odl.get('status') == 'Attesa Cura']
    print(f"📊 ODL totali: {len(odl_data)}")
    print(f"📊 ODL in Attesa Cura: {len(odl_attesa_cura)}")
    
    if len(odl_attesa_cura) < 4:
        print("⚠️ Pochi ODL disponibili per il test ottimale")
    
    # 2. Verifica autoclavi disponibili  
    print("\n🏭 2. VERIFICA AUTOCLAVI DISPONIBILI")
    autoclave_data = test_endpoint("GET", "/autoclavi")
    if not autoclave_data:
        print("❌ Impossibile recuperare autoclavi")
        return
    
    autoclavi_disponibili = [ac for ac in autoclave_data if ac.get('stato') == 'DISPONIBILE']
    print(f"📊 Autoclavi totali: {len(autoclave_data)}")
    print(f"📊 Autoclavi disponibili: {len(autoclavi_disponibili)}")
    
    if len(autoclavi_disponibili) < 2:
        print("⚠️ Poche autoclavi disponibili per il test multi-batch")
    
    # Mostra dettagli autoclavi
    for autoclave in autoclavi_disponibili[:3]:  # Prime 3
        print(f"  🏭 {autoclave['nome']}: {autoclave['larghezza_piano']}x{autoclave['lunghezza']}mm")
    
    # 3. Test generazione nesting ottimizzato
    print_section("GENERAZIONE NESTING OTTIMIZZATO")
    
    # Usa tutti gli ODL disponibili e tutte le autoclavi
    test_odl_ids = [str(odl['id']) for odl in odl_attesa_cura[:4]]  # Primi 4 ODL
    test_autoclave_ids = [str(ac['id']) for ac in autoclavi_disponibili[:3]]  # Prime 3 autoclavi
    
    nesting_request = {
        "odl_ids": test_odl_ids,
        "autoclave_ids": test_autoclave_ids,
        "parametri": {
            "padding_mm": 8,     # ✅ OTTIMIZZATO: Valori bassi
            "min_distance_mm": 5,  # ✅ OTTIMIZZATO: Valori bassi
            "priorita_area": False  # ✅ OTTIMIZZATO: Massimizza ODL
        }
    }
    
    print(f"📤 Test con parametri ottimizzati:")
    print(f"   📋 ODL: {len(test_odl_ids)} ({test_odl_ids})")
    print(f"   🏭 Autoclavi: {len(test_autoclave_ids)} ({test_autoclave_ids})")
    print(f"   📐 Padding: {nesting_request['parametri']['padding_mm']}mm")
    print(f"   📏 Distanza: {nesting_request['parametri']['min_distance_mm']}mm")
    print(f"   🎯 Obiettivo: Massimizza ODL")
    
    print(f"\n🔄 Invio richiesta nesting...")
    start_time = time.time()
    
    nesting_result = test_endpoint("POST", "/nesting/genera", nesting_request)
    
    execution_time = time.time() - start_time
    
    if not nesting_result:
        print("❌ Generazione nesting fallita!")
        return
    
    # 4. Analisi risultati
    print_section("ANALISI RISULTATI")
    
    print(f"⏱️ Tempo esecuzione: {execution_time:.2f}s")
    print(f"✅ Successo: {nesting_result.get('success', False)}")
    print(f"📦 Batch ID principale: {nesting_result.get('batch_id', 'N/A')}")
    print(f"📊 ODL posizionati: {len(nesting_result.get('positioned_tools', []))}")
    print(f"📊 ODL esclusi: {len(nesting_result.get('excluded_odls', []))}")
    print(f"📊 Efficienza: {nesting_result.get('efficiency', 0):.1f}%")
    print(f"📊 Peso totale: {nesting_result.get('total_weight', 0):.1f}kg")
    print(f"🔧 Status algoritmo: {nesting_result.get('algorithm_status', 'N/A')}")
    
    # Mostra messaggio dettagliato
    if nesting_result.get('message'):
        print(f"💬 Messaggio: {nesting_result['message']}")
    
    # 5. Verifica batch creati
    print_section("VERIFICA BATCH MULTIPLI")
    
    # Recupera lista batch recenti
    batch_list = test_endpoint("GET", "/v1/batch_nesting?limit=10")
    if batch_list:
        print(f"📦 Batch totali nel sistema: {len(batch_list)}")
        
        # Filtra batch creati negli ultimi 5 minuti
        import datetime
        now = datetime.datetime.now()
        recent_batches = []
        
        for batch in batch_list:
            try:
                created_time = datetime.datetime.fromisoformat(batch['created_at'].replace('Z', '+00:00'))
                if (now - created_time.replace(tzinfo=None)).total_seconds() < 300:  # 5 minuti
                    recent_batches.append(batch)
            except:
                pass
                
        print(f"📦 Batch creati negli ultimi 5 minuti: {len(recent_batches)}")
        
        for i, batch in enumerate(recent_batches[:3]):  # Mostra primi 3
            print(f"   Batch #{i+1}: {batch['nome']}")
            print(f"     🏭 Autoclave: {batch['autoclave_id']}")
            print(f"     📋 ODL: {len(batch.get('odl_ids', []))}")
            print(f"     📊 Stato: {batch['stato']}")
    
    # 6. Test visualizzazione batch principale
    batch_id = nesting_result.get('batch_id')
    if batch_id:
        print_section("TEST VISUALIZZAZIONE BATCH")
        
        batch_detail = test_endpoint("GET", f"/v1/batch_nesting/{batch_id}/full")
        if batch_detail:
            print(f"✅ Batch recuperato con successo")
            print(f"📦 Nome: {batch_detail.get('nome', 'N/A')}")
            
            config = batch_detail.get('configurazione_json', {})
            tool_positions = config.get('tool_positions', [])
            
            print(f"🔧 Canvas: {config.get('canvas_width', 0)}x{config.get('canvas_height', 0)}mm")
            print(f"🎯 Tool posizionati: {len(tool_positions)}")
            
            # Verifica che ci siano posizioni valide
            if tool_positions:
                print("✅ Posizioni tool trovate:")
                for i, tool in enumerate(tool_positions[:2]):  # Primi 2
                    print(f"   Tool #{i+1}: ODL {tool.get('odl_id')} a ({tool.get('x')}, {tool.get('y')}) - {tool.get('width')}x{tool.get('height')}mm")
            else:
                print("⚠️ Nessuna posizione tool trovata nel batch")
    
    # 7. Confronto con parametri standard
    print_section("CONFRONTO CON PARAMETRI STANDARD")
    
    # Test con parametri standard (meno ottimizzati)
    nesting_request_standard = {
        "odl_ids": test_odl_ids,
        "autoclave_ids": [test_autoclave_ids[0]],  # Solo una autoclave
        "parametri": {
            "padding_mm": 20,    # Parametri standard
            "min_distance_mm": 15,
            "priorita_area": True
        }
    }
    
    print(f"🔄 Test con parametri standard...")
    nesting_standard = test_endpoint("POST", "/nesting/genera", nesting_request_standard)
    
    if nesting_standard:
        positioned_optimized = len(nesting_result.get('positioned_tools', []))
        positioned_standard = len(nesting_standard.get('positioned_tools', []))
        
        print(f"📊 CONFRONTO RISULTATI:")
        print(f"   🚀 Ottimizzato: {positioned_optimized} ODL posizionati")
        print(f"   📐 Standard: {positioned_standard} ODL posizionati")
        
        if positioned_optimized > positioned_standard:
            print(f"✅ Miglioramento: +{positioned_optimized - positioned_standard} ODL ({((positioned_optimized/positioned_standard - 1) * 100):.1f}%)")
        elif positioned_optimized == positioned_standard:
            print("➡️ Risultati equivalenti")
        else:
            print(f"⚠️ Peggioramento: -{positioned_standard - positioned_optimized} ODL")
    
    print_section("TEST COMPLETATO")
    print("🎉 Verifica delle ottimizzazioni completata!")
    print("\n📋 PROSSIMI PASSI:")
    print("   1. Testare il frontend su http://localhost:3000/dashboard/curing/nesting")
    print("   2. Verificare la visualizzazione dei batch multipli")
    print("   3. Controllare il canvas per errori di rendering")

if __name__ == "__main__":
    main() 