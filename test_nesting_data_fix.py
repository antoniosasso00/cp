#!/usr/bin/env python3
"""
🧪 Test dell'endpoint /api/v1/batch_nesting/data dopo il fix
"""

import requests
import json
import sys

def test_nesting_data_endpoint():
    """Test dell'endpoint dati nesting"""
    
    print("🧪 TEST ENDPOINT NESTING DATA - Dopo Fix")
    print("="*60)
    
    try:
        # URL dell'endpoint
        url = "http://localhost:8000/api/v1/batch_nesting/data"
        
        print(f"📡 Richiesta GET a: {url}")
        
        # Richiesta GET
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Analizza i dati ricevuti
            odl_count = len(data.get("odl_in_attesa_cura", []))
            autoclavi_count = len(data.get("autoclavi_disponibili", []))
            
            print(f"✅ SUCCESSO!")
            print(f"   📋 ODL in attesa cura trovati: {odl_count}")
            print(f"   🏭 Autoclavi disponibili trovate: {autoclavi_count}")
            
            # Mostra statistiche
            stats = data.get("statistiche", {})
            print(f"\n📊 STATISTICHE:")
            print(f"   - Total ODL sistema: {stats.get('total_odl_sistema', 0)}")
            print(f"   - Total autoclavi sistema: {stats.get('total_autoclavi_sistema', 0)}")
            print(f"   - Last update: {stats.get('last_update', 'N/A')}")
            
            # Mostra alcuni ODL
            if odl_count > 0:
                print(f"\n🔍 PRIMI 3 ODL TROVATI:")
                for i, odl in enumerate(data["odl_in_attesa_cura"][:3]):
                    print(f"   {i+1}. ID: {odl.get('id')} | Status: '{odl.get('status')}' | Priorità: {odl.get('priorita')}")
                    if odl.get('parte'):
                        print(f"      Parte: {odl['parte'].get('part_number')} - {odl['parte'].get('descrizione_breve')}")
                    if odl.get('tool'):
                        print(f"      Tool: {odl['tool'].get('part_number_tool')}")
            
            # Mostra alcune autoclavi
            if autoclavi_count > 0:
                print(f"\n🏭 AUTOCLAVI DISPONIBILI:")
                for i, autoclave in enumerate(data["autoclavi_disponibili"]):
                    print(f"   {i+1}. ID: {autoclave.get('id')} | Nome: {autoclave.get('nome')} | Stato: '{autoclave.get('stato')}'")
                    print(f"      Dimensioni: {autoclave.get('lunghezza')}x{autoclave.get('larghezza_piano')}mm")
            
            # Verifica if se ci sono dati per il nesting
            if odl_count > 0 and autoclavi_count > 0:
                print(f"\n🎯 NESTING POSSIBILE!")
                print(f"   ✅ {odl_count} ODL disponibili per nesting")
                print(f"   ✅ {autoclavi_count} autoclavi disponibili")
            else:
                print(f"\n⚠️  NESTING NON POSSIBILE:")
                if odl_count == 0:
                    print(f"   ❌ Nessun ODL in attesa cura")
                if autoclavi_count == 0:
                    print(f"   ❌ Nessuna autoclave disponibile")
            
            return True
            
        else:
            print(f"❌ ERRORE HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Dettagli: {error_data.get('detail', 'N/A')}")
            except:
                print(f"   Testo errore: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERRORE: Server non raggiungibile su localhost:8000")
        print(f"   💡 Assicurati che il server FastAPI sia avviato")
        return False
        
    except Exception as e:
        print(f"❌ ERRORE: {str(e)}")
        return False

def main():
    """Funzione principale"""
    success = test_nesting_data_endpoint()
    
    print(f"\n" + "="*60)
    if success:
        print(f"✅ TEST COMPLETATO CON SUCCESSO!")
        print(f"   Il fix per l'endpoint /data sembra funzionare correttamente")
    else:
        print(f"❌ TEST FALLITO!")
        print(f"   Ci sono ancora problemi con l'endpoint /data")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 