#!/usr/bin/env python3
"""
Script per testare il sistema di tracking degli stati ODL.

Questo script verifica che il monitoraggio automatico funzioni correttamente
e che i cambi di stato vengano registrati con timestamp precisi.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Aggiungi il path del backend per importare i moduli
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_header(title: str):
    """Stampa un header formattato"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title: str):
    """Stampa una sezione formattata"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def test_initialize_state_tracking(base_url: str = "http://localhost:8000"):
    """Inizializza il tracking degli stati per ODL esistenti"""
    try:
        url = f"{base_url}/api/odl-monitoring/monitoring/initialize-state-tracking"
        response = requests.post(url, timeout=10)
        
        print(f"🔗 URL: {url}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Inizializzazione completata")
            print(f"📋 Log creati: {data.get('logs_creati', 0)}")
            print(f"📋 ODL processati: {data.get('odl_processati', [])}")
            return data
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"📄 Risposta: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossibile connettersi al server {base_url}")
        return None
    except Exception as e:
        print(f"❌ Errore durante l'inizializzazione: {str(e)}")
        return None

def test_change_odl_status(odl_id: int, new_status: str, base_url: str = "http://localhost:8000"):
    """Testa il cambio di stato di un ODL"""
    try:
        url = f"{base_url}/api/odl/{odl_id}/status"
        payload = {"new_status": new_status}
        response = requests.patch(url, json=payload, timeout=10)
        
        print(f"🔗 URL: {url}")
        print(f"📊 Payload: {payload}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stato cambiato con successo")
            print(f"📋 Nuovo stato: {data.get('status', 'N/A')}")
            return data
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"📄 Risposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Errore durante il cambio stato: {str(e)}")
        return None

def test_get_progress_data(odl_id: int, base_url: str = "http://localhost:8000"):
    """Testa il recupero dei dati di progresso"""
    try:
        url = f"{base_url}/api/odl-monitoring/monitoring/{odl_id}/progress"
        response = requests.get(url, timeout=10)
        
        print(f"🔗 URL: {url}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dati di progresso recuperati")
            print(f"📋 ODL ID: {data.get('id', 'N/A')}")
            print(f"📋 Status: {data.get('status', 'N/A')}")
            print(f"📋 Timestamps: {len(data.get('timestamps', []))}")
            print(f"📋 Has Timeline Data: {data.get('has_timeline_data', False)}")
            
            # Mostra i timestamps se presenti
            timestamps = data.get('timestamps', [])
            if timestamps:
                print(f"\n📅 Timeline disponibile:")
                for i, ts in enumerate(timestamps):
                    durata = ts.get('durata_minuti', 0)
                    stato = ts.get('stato', 'N/A')
                    inizio = ts.get('inizio', 'N/A')
                    print(f"   {i+1}. {stato}: {durata} minuti (inizio: {inizio})")
            else:
                print(f"\n⚠️  Nessun timestamp disponibile")
            
            return data
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"📄 Risposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Errore durante il recupero dati: {str(e)}")
        return None

def test_get_timeline(odl_id: int, base_url: str = "http://localhost:8000"):
    """Testa il recupero della timeline completa"""
    try:
        url = f"{base_url}/api/odl-monitoring/monitoring/{odl_id}/timeline"
        response = requests.get(url, timeout=10)
        
        print(f"🔗 URL: {url}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Timeline recuperata")
            print(f"📋 ODL ID: {data.get('odl_id', 'N/A')}")
            print(f"📋 Status corrente: {data.get('status_corrente', 'N/A')}")
            print(f"📋 Eventi: {len(data.get('logs', []))}")
            
            # Mostra gli eventi
            logs = data.get('logs', [])
            if logs:
                print(f"\n📅 Eventi registrati:")
                for i, log in enumerate(logs):
                    evento = log.get('evento', 'N/A')
                    timestamp = log.get('timestamp', 'N/A')
                    responsabile = log.get('responsabile', 'N/A')
                    print(f"   {i+1}. {evento} ({responsabile}) - {timestamp}")
            
            # Mostra statistiche
            stats = data.get('statistiche', {})
            if stats:
                print(f"\n📊 Statistiche:")
                print(f"   Durata totale: {stats.get('durata_totale_minuti', 0)} minuti")
                print(f"   Transizioni: {stats.get('numero_transizioni', 0)}")
                print(f"   Efficienza stimata: {stats.get('efficienza_stimata', 'N/A')}%")
            
            return data
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"📄 Risposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Errore durante il recupero timeline: {str(e)}")
        return None

def test_database_state():
    """Verifica lo stato del database"""
    print_section("Verifica Stato Database")
    
    try:
        from api.database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        
        # Conta ODL totali
        result = db.execute(text("SELECT COUNT(*) as count FROM odl")).fetchone()
        odl_count = result.count if result else 0
        print(f"📊 ODL totali nel database: {odl_count}")
        
        # Conta state logs
        result = db.execute(text("SELECT COUNT(*) as count FROM state_logs")).fetchone()
        logs_count = result.count if result else 0
        print(f"📊 State logs totali: {logs_count}")
        
        # ODL senza state logs
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM odl o 
            WHERE NOT EXISTS (
                SELECT 1 FROM state_logs sl WHERE sl.odl_id = o.id
            )
        """)).fetchone()
        odl_without_logs = result.count if result else 0
        print(f"📊 ODL senza state logs: {odl_without_logs}")
        
        # Mostra alcuni esempi di ODL
        result = db.execute(text("""
            SELECT id, status, created_at, updated_at 
            FROM odl 
            ORDER BY id 
            LIMIT 5
        """)).fetchall()
        
        print(f"\n📋 Esempi di ODL:")
        for row in result:
            print(f"   ODL #{row.id}: {row.status} (creato: {row.created_at})")
        
        db.close()
        return odl_count, logs_count, odl_without_logs
        
    except Exception as e:
        print(f"❌ Errore durante la verifica del database: {str(e)}")
        return 0, 0, 0

def main():
    """Funzione principale di test"""
    print_header("TEST SISTEMA TRACKING STATI ODL")
    print("Questo script verifica che il monitoraggio automatico")
    print("dei cambi di stato funzioni correttamente.")
    
    # 1. Verifica stato database
    odl_count, logs_count, odl_without_logs = test_database_state()
    
    # 2. Inizializza tracking se necessario
    if odl_without_logs > 0:
        print_section("Inizializzazione Tracking Stati")
        print(f"🔧 Trovati {odl_without_logs} ODL senza tracking. Inizializzo...")
        init_result = test_initialize_state_tracking()
        
        if init_result:
            print(f"✅ Tracking inizializzato per {init_result.get('logs_creati', 0)} ODL")
        else:
            print(f"❌ Errore durante l'inizializzazione")
            return
    else:
        print(f"✅ Tutti gli ODL hanno già il tracking attivo")
    
    # 3. Test cambio stato e monitoraggio
    if odl_count > 0:
        print_section("Test Cambio Stato e Monitoraggio")
        
        # Usa il primo ODL per il test
        test_odl_id = 1
        
        print(f"🧪 Test con ODL #{test_odl_id}")
        
        # Recupera stato iniziale
        print(f"\n📊 Stato iniziale:")
        initial_data = test_get_progress_data(test_odl_id)
        
        if initial_data:
            current_status = initial_data.get('status', 'Preparazione')
            
            # Determina il prossimo stato per il test
            status_sequence = ['Preparazione', 'Laminazione', 'Attesa Cura', 'Cura', 'Finito']
            try:
                current_index = status_sequence.index(current_status)
                if current_index < len(status_sequence) - 1:
                    next_status = status_sequence[current_index + 1]
                else:
                    # Se è già finito, torna a Preparazione per il test
                    next_status = 'Laminazione'
            except ValueError:
                next_status = 'Laminazione'
            
            print(f"\n🔄 Cambio stato da '{current_status}' a '{next_status}'")
            change_result = test_change_odl_status(test_odl_id, next_status)
            
            if change_result:
                print(f"✅ Stato cambiato con successo")
                
                # Attendi un momento per il processing
                import time
                time.sleep(1)
                
                # Verifica che il tracking abbia registrato il cambio
                print(f"\n📊 Verifica tracking dopo cambio stato:")
                updated_data = test_get_progress_data(test_odl_id)
                
                if updated_data and updated_data.get('has_timeline_data'):
                    print(f"✅ Tracking funzionante! Timeline aggiornata.")
                    
                    # Mostra timeline completa
                    print(f"\n📅 Timeline completa:")
                    test_get_timeline(test_odl_id)
                else:
                    print(f"⚠️  Tracking non ancora attivo o dati non aggiornati")
            else:
                print(f"❌ Errore durante il cambio stato")
    
    # 4. Riepilogo
    print_header("RIEPILOGO TEST")
    
    print("✅ Test completati:")
    print("   - Verifica stato database")
    print("   - Inizializzazione tracking (se necessario)")
    print("   - Test cambio stato")
    print("   - Verifica monitoraggio automatico")
    
    print("\n💡 Come verificare nel browser:")
    print("   1. Vai alla pagina ODL nel frontend")
    print("   2. Cambia lo stato di un ODL")
    print("   3. Verifica che la barra di progresso mostri dati reali")
    print("   4. I dati dovrebbero essere marcati come 'reali' (non stimati)")
    
    print(f"\n🎯 TEST COMPLETATO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 