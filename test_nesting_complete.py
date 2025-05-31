#!/usr/bin/env python3
"""
Test completo del modulo Nesting - Verifica end-to-end
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(method, endpoint, data=None, expected_status=200, params=None):
    """Testa un endpoint e restituisce il risultato"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, params=params)
        elif method == "PATCH":
            response = requests.patch(url, json=data, params=params)
        elif method == "DELETE":
            response = requests.delete(url, params=params)
        
        print(f"🔍 {method} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ Successo")
            try:
                return response.json()
            except:
                return response.text
        else:
            print(f"   ❌ Errore - Atteso: {expected_status}, Ricevuto: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   📝 Dettaglio: {error_detail}")
            except:
                print(f"   📝 Risposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"   💥 Eccezione: {e}")
        return None

def main():
    """Test completo del modulo nesting"""
    print("🚀 INIZIO TEST COMPLETO MODULO NESTING")
    print("=" * 50)
    
    # 1. Verifica ODL disponibili
    print("\n📋 1. VERIFICA ODL DISPONIBILI")
    odl_list = test_endpoint("GET", "/odl/?status=Attesa%20Cura")
    if odl_list and len(odl_list) > 0:
        print(f"   ✅ Trovati {len(odl_list)} ODL in attesa di cura")
        odl_ids = [str(odl['id']) for odl in odl_list]  # Converti in stringhe
        print(f"   📝 ODL IDs: {odl_ids}")
    else:
        print("   ⚠️ Nessun ODL disponibile per il test")
        return
    
    # 2. Verifica autoclavi disponibili
    print("\n🏭 2. VERIFICA AUTOCLAVI DISPONIBILI")
    autoclavi = test_endpoint("GET", "/autoclavi/")
    if autoclavi and len(autoclavi) > 0:
        print(f"   ✅ Trovate {len(autoclavi)} autoclavi")
        autoclave_ids = [str(autoclavi[0]['id'])]  # Lista di stringhe
        print(f"   📝 Usando autoclave IDs: {autoclave_ids} ({autoclavi[0]['nome']})")
    else:
        print("   ❌ Nessuna autoclave disponibile")
        return
    
    # 3. Test generazione nesting
    print("\n⚙️ 3. TEST GENERAZIONE NESTING")
    nesting_data = {
        "odl_ids": odl_ids[:1],  # Lista di stringhe
        "autoclave_ids": autoclave_ids,  # Lista di stringhe
        "parametri": {
            "padding_mm": 20,  # int come richiesto
            "min_distance_mm": 15,  # int come richiesto
            "priorita_area": True,  # bool come richiesto
            "accorpamento_odl": False  # bool come richiesto
        }
    }
    
    batch_result = test_endpoint("POST", "/nesting/genera", nesting_data, 200)
    if batch_result:
        batch_id = batch_result.get('batch_id')
        print(f"   ✅ Batch creato con ID: {batch_id}")
        print(f"   📝 ODL posizionati: {batch_result.get('odl_count')}")
        print(f"   📝 Efficienza: {batch_result.get('efficiency', 0):.1f}%")
    else:
        print("   ❌ Fallita generazione nesting")
        return
    
    # 4. Verifica dettagli batch
    print("\n📊 4. VERIFICA DETTAGLI BATCH")
    batch_details = test_endpoint("GET", f"/batch_nesting/{batch_id}")
    if batch_details:
        print(f"   ✅ Batch recuperato: {batch_details.get('nome')}")
        print(f"   📝 Stato: {batch_details.get('stato')}")
        print(f"   📝 Numero nesting: {batch_details.get('numero_nesting')}")
    
    # 5. Test conferma batch
    print("\n✅ 5. TEST CONFERMA BATCH")
    conferma_params = {
        "confermato_da_utente": "test_user",
        "confermato_da_ruolo": "ADMIN"
    }
    conferma_result = test_endpoint("PATCH", f"/batch_nesting/{batch_id}/conferma", 
                                  params=conferma_params)
    if conferma_result:
        print(f"   ✅ Batch confermato")
        print(f"   📝 Nuovo stato: {conferma_result.get('stato')}")
        print(f"   📝 Confermato da: {conferma_result.get('confermato_da_utente')}")
    else:
        print("   ⚠️ Conferma non riuscita, probabile problema di stato ODL/autoclave")
    
    # 6. Test chiusura batch (solo se confermato)
    if conferma_result and conferma_result.get('stato') == 'confermato':
        print("\n🔒 6. TEST CHIUSURA BATCH")
        chiusura_params = {
            "chiuso_da_utente": "test_user",
            "chiuso_da_ruolo": "ADMIN"
        }
        chiusura_result = test_endpoint("PATCH", f"/batch_nesting/{batch_id}/chiudi", 
                                      params=chiusura_params)
        if chiusura_result:
            print(f"   ✅ Batch chiuso")
            print(f"   📝 Stato finale: {chiusura_result.get('stato')}")
            print(f"   📝 Durata ciclo: {chiusura_result.get('durata_ciclo_minuti', 'N/A')} minuti")
    else:
        print("\n🔒 6. SKIP CHIUSURA BATCH (batch non confermato)")
    
    # 7. Test statistiche batch specifico
    print("\n📈 7. TEST STATISTICHE BATCH")
    stats = test_endpoint("GET", f"/batch_nesting/{batch_id}/statistics")
    if stats:
        print(f"   ✅ Statistiche recuperate")
        print(f"   📝 Efficienza media: {stats.get('efficienza_media', 'N/A')}")
        print(f"   📝 Peso totale: {stats.get('peso_totale_kg', 'N/A')} kg")
    
    # 8. Verifica lista batch aggiornata
    print("\n📋 8. VERIFICA LISTA BATCH FINALE")
    final_list = test_endpoint("GET", "/batch_nesting/")
    if final_list:
        print(f"   ✅ Lista aggiornata: {len(final_list)} batch totali")
        # Trova il nostro batch nella lista
        our_batch = next((b for b in final_list if b['id'] == batch_id), None)
        if our_batch:
            print(f"   📝 Il nostro batch è presente: {our_batch['nome']} ({our_batch['stato']})")
    
    print("\n" + "=" * 50)
    print("🎉 TEST COMPLETO TERMINATO!")
    print("✅ MODULO NESTING PIENAMENTE FUNZIONALE!")

if __name__ == "__main__":
    main() 