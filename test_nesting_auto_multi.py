#!/usr/bin/env python3
"""
Script di test per il modulo Nesting Multi-Autoclave Automatico.
Verifica che tutte le API e i servizi funzionino correttamente.
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000/api/v1"
NESTING_AUTO_MULTI_URL = f"{BASE_URL}/nesting/auto-multi"

def test_health_check():
    """Testa se il server è in esecuzione."""
    try:
        response = requests.get(f"http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Server backend attivo")
            return True
        else:
            print(f"❌ Server non risponde correttamente: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossibile connettersi al server backend")
        return False

def test_odl_disponibili():
    """Testa l'API per recuperare gli ODL disponibili."""
    try:
        response = requests.get(f"{NESTING_AUTO_MULTI_URL}/odl-disponibili")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ODL disponibili recuperati: {data.get('total', 0)} ODL")
            return data.get('data', [])
        else:
            print(f"❌ Errore nel recupero ODL: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Errore nella richiesta ODL: {str(e)}")
        return []

def test_autoclavi_disponibili():
    """Testa l'API per recuperare le autoclavi disponibili."""
    try:
        response = requests.get(f"{NESTING_AUTO_MULTI_URL}/autoclavi-disponibili")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Autoclavi disponibili recuperate: {data.get('total', 0)} autoclavi")
            return data.get('data', [])
        else:
            print(f"❌ Errore nel recupero autoclavi: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Errore nella richiesta autoclavi: {str(e)}")
        return []

def test_genera_nesting(odl_ids, autoclave_ids):
    """Testa la generazione del nesting automatico."""
    if not odl_ids or not autoclave_ids:
        print("⚠️  Saltando test generazione nesting: dati insufficienti")
        return None
    
    try:
        payload = {
            "odl_ids": odl_ids[:3],  # Prendi solo i primi 3 ODL per il test
            "autoclave_ids": autoclave_ids[:2],  # Prendi solo le prime 2 autoclavi
            "parametri": {
                "efficienza_minima_percent": 50.0,  # Soglia più bassa per il test
                "peso_massimo_percent": 90.0,
                "margine_sicurezza_mm": 10.0,
                "priorita_efficienza": True,
                "separa_cicli_cura": True
            }
        }
        
        print(f"🔄 Generando nesting per {len(payload['odl_ids'])} ODL su {len(payload['autoclave_ids'])} autoclavi...")
        
        response = requests.post(
            f"{NESTING_AUTO_MULTI_URL}/genera",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                batch_id = data.get('batch_id')
                print(f"✅ Nesting generato con successo! Batch ID: {batch_id}")
                print(f"   Autoclavi utilizzate: {len(data.get('nesting_results', []))}")
                return batch_id
            else:
                print(f"❌ Errore nella generazione: {data.get('error', 'Errore sconosciuto')}")
                return None
        else:
            print(f"❌ Errore HTTP nella generazione: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Errore nella generazione nesting: {str(e)}")
        return None

def test_preview_nesting(batch_id):
    """Testa l'API per il preview del nesting."""
    if not batch_id:
        print("⚠️  Saltando test preview: nessun batch ID")
        return False
    
    try:
        response = requests.get(f"{NESTING_AUTO_MULTI_URL}/preview/{batch_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                preview_data = data.get('data', {})
                batch_info = preview_data.get('batch', {})
                layouts = preview_data.get('nesting_layouts', [])
                
                print(f"✅ Preview recuperato con successo!")
                print(f"   Batch: {batch_info.get('nome', 'N/A')}")
                print(f"   Autoclavi: {len(layouts)}")
                print(f"   ODL totali: {batch_info.get('numero_odl_totali', 0)}")
                print(f"   Efficienza media: {batch_info.get('efficienza_media', 0):.1f}%")
                return True
            else:
                print(f"❌ Errore nel preview: {data.get('error', 'Errore sconosciuto')}")
                return False
        else:
            print(f"❌ Errore HTTP nel preview: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore nel preview: {str(e)}")
        return False

def test_batch_attivi():
    """Testa l'API per recuperare i batch attivi."""
    try:
        response = requests.get(f"{NESTING_AUTO_MULTI_URL}/batch-attivi")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                batches = data.get('data', [])
                print(f"✅ Batch attivi recuperati: {len(batches)} batch")
                for batch in batches:
                    print(f"   - {batch.get('nome', 'N/A')} ({batch.get('stato', 'N/A')})")
                return True
            else:
                print(f"❌ Errore nel recupero batch: {data.get('error', 'Errore sconosciuto')}")
                return False
        else:
            print(f"❌ Errore HTTP nel recupero batch: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore nel recupero batch: {str(e)}")
        return False

def test_elimina_nesting(batch_id):
    """Testa l'eliminazione di un nesting."""
    if not batch_id:
        print("⚠️  Saltando test eliminazione: nessun batch ID")
        return False
    
    try:
        response = requests.delete(f"{NESTING_AUTO_MULTI_URL}/elimina/{batch_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Nesting eliminato con successo!")
                return True
            else:
                print(f"❌ Errore nell'eliminazione: {data.get('error', 'Errore sconosciuto')}")
                return False
        else:
            print(f"❌ Errore HTTP nell'eliminazione: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore nell'eliminazione: {str(e)}")
        return False

def main():
    """Esegue tutti i test."""
    print("🚀 Avvio test del modulo Nesting Multi-Autoclave Automatico")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Test fallito: server non disponibile")
        return
    
    print()
    
    # Test 2: ODL disponibili
    odl_list = test_odl_disponibili()
    odl_ids = [odl['id'] for odl in odl_list] if odl_list else []
    
    # Test 3: Autoclavi disponibili
    autoclavi_list = test_autoclavi_disponibili()
    autoclave_ids = [autoclave['id'] for autoclave in autoclavi_list] if autoclavi_list else []
    
    print()
    
    # Test 4: Generazione nesting
    batch_id = test_genera_nesting(odl_ids, autoclave_ids)
    
    print()
    
    # Test 5: Preview nesting
    if batch_id:
        test_preview_nesting(batch_id)
        print()
    
    # Test 6: Batch attivi
    test_batch_attivi()
    
    print()
    
    # Test 7: Eliminazione nesting (cleanup)
    if batch_id:
        print("🧹 Pulizia: eliminazione del nesting di test...")
        test_elimina_nesting(batch_id)
    
    print("\n" + "=" * 60)
    print("✅ Test completati!")

if __name__ == "__main__":
    main() 