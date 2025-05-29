#!/usr/bin/env python3
"""
Script per creare un nesting di test e verificare i dati reali.

Questo script:
1. Crea un nesting manualmente usando l'API
2. Verifica che i dati reali vengano popolati correttamente
3. Testa tutti i campi implementati nelle modifiche
"""

import requests
import json
import sys
from typing import Dict, Any

# Configurazione
API_BASE_URL = "http://localhost:8000/api"
NESTING_ENDPOINT = f"{API_BASE_URL}/v1/nesting/"
ODL_ENDPOINT = f"{API_BASE_URL}/v1/odl/"
AUTOCLAVE_ENDPOINT = f"{API_BASE_URL}/v1/autoclavi/"

def test_api_connection() -> bool:
    """Testa la connessione alle API principali."""
    try:
        response = requests.get(NESTING_ENDPOINT, timeout=5)
        print(f"✅ API Nesting: {response.status_code}")
        
        response = requests.get(ODL_ENDPOINT, timeout=5)
        print(f"✅ API ODL: {response.status_code}")
        
        response = requests.get(AUTOCLAVE_ENDPOINT, timeout=5)
        print(f"✅ API Autoclave: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Errore connessione API: {e}")
        return False

def get_available_odl() -> list:
    """Ottiene gli ODL disponibili per il nesting."""
    try:
        response = requests.get(ODL_ENDPOINT, timeout=10)
        if response.status_code == 200:
            odl_list = response.json()
            # Filtra gli ODL in "Attesa Cura"
            available_odl = [odl for odl in odl_list if odl.get('status') == 'Attesa Cura']
            print(f"📋 ODL disponibili per nesting: {len(available_odl)}")
            return available_odl
        else:
            print(f"❌ Errore recupero ODL: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Errore get ODL: {e}")
        return []

def get_available_autoclaves() -> list:
    """Ottiene le autoclavi disponibili."""
    try:
        response = requests.get(AUTOCLAVE_ENDPOINT, timeout=10)
        if response.status_code == 200:
            autoclave_list = response.json()
            # Filtra le autoclavi disponibili
            available = [ac for ac in autoclave_list if ac.get('stato') == 'DISPONIBILE']
            print(f"🏭 Autoclavi disponibili: {len(available)}")
            return available
        else:
            print(f"❌ Errore recupero autoclavi: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Errore get autoclavi: {e}")
        return []

def create_manual_nesting(autoclave_id: int, odl_ids: list) -> Dict[str, Any]:
    """Crea un nesting manualmente utilizzando l'API aggiornata."""
    
    try:
        # ✅ AGGIORNATO: Usa il nuovo schema con autoclave_id e odl_ids
        nesting_data = {
            "note": "🧪 Nesting di test per verificare dati reali",
            "autoclave_id": autoclave_id,
            "odl_ids": odl_ids
        }
        
        print(f"   📋 Payload: {nesting_data}")
        
        response = requests.post(NESTING_ENDPOINT, 
                               json=nesting_data, 
                               timeout=15)
        
        if response.status_code == 200:
            nesting = response.json()
            print(f"✅ Nesting creato: ID={nesting.get('id', 'N/A')}")
            return nesting
        else:
            print(f"❌ Errore creazione nesting: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ Errore create nesting: {e}")
        return {}

def analyze_nesting_data(nesting: Dict[str, Any]) -> None:
    """Analizza i dati del nesting per verificare i campi reali."""
    
    print("\n🔍 ANALISI DATI NESTING REALI")
    print("=" * 50)
    
    # Campi base
    print(f"📋 ID Nesting: {nesting.get('id', 'NON DISPONIBILE')}")
    print(f"📋 Stato: {nesting.get('stato', 'NON DISPONIBILE')}")
    print(f"📋 Note: {nesting.get('note', 'NON DISPONIBILE')}")
    print(f"📋 Data Creazione: {nesting.get('created_at', 'NON DISPONIBILE')}")
    
    # ✅ CAMPI IMPLEMENTATI NELLE MODIFICHE
    print(f"\n🎯 CAMPI DATI REALI IMPLEMENTATI:")
    
    # Autoclave
    autoclave_nome = nesting.get('autoclave_nome')
    if autoclave_nome:
        print(f"✅ Nome Autoclave: {autoclave_nome}")
    else:
        print(f"⚠️ Nome Autoclave: NON DISPONIBILE (era: '—')")
    
    # Ciclo Cura
    ciclo_cura = nesting.get('ciclo_cura')
    if ciclo_cura:
        print(f"✅ Ciclo Cura: {ciclo_cura}")
    else:
        print(f"⚠️ Ciclo Cura: NON DISPONIBILE (era: None)")
    
    # ODL
    odl_inclusi = nesting.get('odl_inclusi')
    odl_esclusi = nesting.get('odl_esclusi')
    print(f"✅ ODL Inclusi: {odl_inclusi if odl_inclusi is not None else 'NON DISPONIBILE'}")
    print(f"✅ ODL Esclusi: {odl_esclusi if odl_esclusi is not None else 'NON DISPONIBILE'}")
    
    # Efficienza e Area
    efficienza = nesting.get('efficienza')
    area_utilizzata = nesting.get('area_utilizzata')
    area_totale = nesting.get('area_totale')
    
    if efficienza is not None:
        print(f"✅ Efficienza: {efficienza:.1f}%")
    else:
        print(f"⚠️ Efficienza: NON DISPONIBILE")
        
    if area_utilizzata is not None and area_totale is not None:
        print(f"✅ Area: {area_utilizzata:.1f}/{area_totale:.1f} m²")
    else:
        print(f"⚠️ Area: NON DISPONIBILE")
    
    # Peso e Valvole
    peso_totale = nesting.get('peso_totale')
    valvole_utilizzate = nesting.get('valvole_utilizzate')
    valvole_totali = nesting.get('valvole_totali')
    
    if peso_totale is not None:
        print(f"✅ Peso Totale: {peso_totale:.1f} kg")
    else:
        print(f"⚠️ Peso Totale: NON DISPONIBILE (era: '—')")
        
    if valvole_utilizzate is not None and valvole_totali is not None:
        print(f"✅ Valvole: {valvole_utilizzate}/{valvole_totali}")
    else:
        print(f"⚠️ Valvole: NON DISPONIBILI")
    
    # Motivi Esclusione
    motivi_esclusione = nesting.get('motivi_esclusione', [])
    if motivi_esclusione:
        print(f"✅ Motivi Esclusione: {len(motivi_esclusione)} elementi")
        for i, motivo in enumerate(motivi_esclusione[:3]):
            print(f"   {i+1}. {motivo}")
    else:
        print(f"✅ Motivi Esclusione: Nessuno (array vuoto)")

def main():
    print("🧪 CREAZIONE NESTING DI TEST - VERIFICA DATI REALI")
    print("=" * 60)
    
    # 1. Test connessione API
    if not test_api_connection():
        print("❌ Test fallito: problemi di connessione API")
        sys.exit(1)
    
    # 2. Ottieni dati disponibili
    available_odl = get_available_odl()
    available_autoclaves = get_available_autoclaves()
    
    if not available_odl:
        print("⚠️ Nessun ODL disponibile per il test")
        print("   Suggerimento: Cambia alcuni ODL a stato 'Attesa Cura'")
        return
        
    if not available_autoclaves:
        print("⚠️ Nessuna autoclave disponibile per il test")
        return
    
    # 3. Seleziona dati per il test
    test_autoclave = available_autoclaves[0]
    test_odl_ids = [odl['id'] for odl in available_odl[:3]]  # Prime 3 ODL
    
    print(f"\n🎯 CONFIGURAZIONE TEST:")
    print(f"   Autoclave: {test_autoclave['nome']} (ID: {test_autoclave['id']})")
    print(f"   ODL da includere: {test_odl_ids}")
    
    # 4. Crea nesting di test
    print(f"\n🔨 Creazione nesting di test...")
    nesting = create_manual_nesting(test_autoclave['id'], test_odl_ids)
    
    if not nesting:
        print("❌ Impossibile creare nesting di test")
        return
    
    # 5. Verifica che il nesting sia stato creato
    print(f"\n🔍 Verifica nesting creato...")
    try:
        response = requests.get(NESTING_ENDPOINT, timeout=10)
        if response.status_code == 200:
            nesting_list = response.json()
            if nesting_list:
                latest_nesting = nesting_list[-1]  # Ultimo nesting creato
                print(f"✅ Nesting trovato nel database")
                analyze_nesting_data(latest_nesting)
            else:
                print("⚠️ Nessun nesting trovato nel database")
        else:
            print(f"❌ Errore verifica nesting: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore verifica: {e}")
    
    print(f"\n✅ Test completato!")
    print(f"💡 Ora puoi aprire il frontend e verificare che i dati reali")
    print(f"   vengano visualizzati correttamente nelle tabelle e nei tab")

if __name__ == "__main__":
    main() 