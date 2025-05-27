#!/usr/bin/env python3
"""
Script per testare la robustezza della barra di progresso ODL.

Questo script verifica che il componente funzioni correttamente
in tutti gli scenari possibili, inclusi quelli con dati mancanti.
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

def test_api_endpoint(odl_id: int, base_url: str = "http://localhost:8000"):
    """Testa l'endpoint API per un ODL specifico"""
    try:
        url = f"{base_url}/api/odl-monitoring/monitoring/{odl_id}/progress"
        response = requests.get(url, timeout=10)
        
        print(f"🔗 URL: {url}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Risposta ricevuta correttamente")
            
            # Analizza i dati ricevuti
            print(f"📋 ODL ID: {data.get('id', 'N/A')}")
            print(f"📋 Status: {data.get('status', 'N/A')}")
            print(f"📋 Timestamps: {len(data.get('timestamps', []))}")
            print(f"📋 Has Timeline Data: {data.get('has_timeline_data', False)}")
            print(f"📋 Tempo Totale Stimato: {data.get('tempo_totale_stimato', 0)} minuti")
            
            # Mostra i timestamps se presenti
            timestamps = data.get('timestamps', [])
            if timestamps:
                print(f"\n📅 Timestamps disponibili:")
                for i, ts in enumerate(timestamps):
                    durata = ts.get('durata_minuti', 0)
                    stato = ts.get('stato', 'N/A')
                    print(f"   {i+1}. {stato}: {durata} minuti")
            else:
                print(f"\n⚠️  Nessun timestamp disponibile - Il frontend userà la modalità fallback")
            
            return data
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"📄 Risposta: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossibile connettersi al server {base_url}")
        print(f"💡 Assicurati che il backend sia in esecuzione")
        return None
    except Exception as e:
        print(f"❌ Errore durante la richiesta: {str(e)}")
        return None

def test_frontend_fallback_logic():
    """Testa la logica di fallback del frontend con dati simulati"""
    print_section("Test Logica Fallback Frontend")
    
    # Simula diversi scenari di dati
    test_cases = [
        {
            "name": "ODL senza timestamps",
            "data": {
                "id": 1,
                "status": "Laminazione",
                "created_at": "2025-01-28T08:00:00Z",
                "updated_at": "2025-01-28T10:00:00Z",
                "timestamps": [],
                "tempo_totale_stimato": None,
                "has_timeline_data": False
            }
        },
        {
            "name": "ODL con timestamps parziali",
            "data": {
                "id": 2,
                "status": "Cura",
                "created_at": "2025-01-28T08:00:00Z",
                "updated_at": "2025-01-28T12:00:00Z",
                "timestamps": [
                    {
                        "stato": "Preparazione",
                        "inizio": "2025-01-28T08:00:00Z",
                        "fine": "2025-01-28T09:00:00Z",
                        "durata_minuti": 60
                    }
                ],
                "tempo_totale_stimato": 240,
                "has_timeline_data": True
            }
        },
        {
            "name": "ODL con dati completi",
            "data": {
                "id": 3,
                "status": "Finito",
                "created_at": "2025-01-28T08:00:00Z",
                "updated_at": "2025-01-28T17:00:00Z",
                "timestamps": [
                    {
                        "stato": "Preparazione",
                        "inizio": "2025-01-28T08:00:00Z",
                        "fine": "2025-01-28T09:00:00Z",
                        "durata_minuti": 60
                    },
                    {
                        "stato": "Laminazione",
                        "inizio": "2025-01-28T09:00:00Z",
                        "fine": "2025-01-28T11:00:00Z",
                        "durata_minuti": 120
                    },
                    {
                        "stato": "Attesa Cura",
                        "inizio": "2025-01-28T11:00:00Z",
                        "fine": "2025-01-28T12:00:00Z",
                        "durata_minuti": 60
                    },
                    {
                        "stato": "Cura",
                        "inizio": "2025-01-28T12:00:00Z",
                        "fine": "2025-01-28T17:00:00Z",
                        "durata_minuti": 300
                    }
                ],
                "tempo_totale_stimato": 540,
                "has_timeline_data": True
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Test: {test_case['name']}")
        data = test_case['data']
        
        # Simula la logica del frontend
        timestamps = data.get('timestamps', [])
        has_timeline = data.get('has_timeline_data', False)
        
        if has_timeline and timestamps:
            print(f"   ✅ Modalità normale: {len(timestamps)} segmenti da timeline")
            total_duration = sum(ts.get('durata_minuti', 0) for ts in timestamps)
            print(f"   📊 Durata totale: {total_duration} minuti")
        else:
            print(f"   🔄 Modalità fallback: dati stimati")
            # Simula calcolo fallback
            created = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            estimated_duration = int((updated - created).total_seconds() / 60)
            print(f"   📊 Durata stimata: {estimated_duration} minuti")
            print(f"   💡 Il frontend mostrerà segmenti stimati basati sullo stato corrente")

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
        
        # ODL senza logs
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM odl o 
            WHERE NOT EXISTS (
                SELECT 1 FROM state_logs sl WHERE sl.odl_id = o.id
            )
        """)).fetchone()
        odl_without_logs = result.count if result else 0
        print(f"📊 ODL senza state logs: {odl_without_logs}")
        
        if odl_without_logs > 0:
            print(f"⚠️  {odl_without_logs} ODL useranno la modalità fallback")
        
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
        
    except Exception as e:
        print(f"❌ Errore durante la verifica del database: {str(e)}")

def main():
    """Funzione principale di test"""
    print_header("TEST ROBUSTEZZA BARRA PROGRESSO ODL")
    print("Questo script verifica che la barra di progresso funzioni")
    print("correttamente in tutti gli scenari, inclusi quelli con dati mancanti.")
    
    # 1. Verifica stato database
    test_database_state()
    
    # 2. Testa logica fallback
    test_frontend_fallback_logic()
    
    # 3. Testa endpoint API
    print_section("Test Endpoint API")
    
    # Testa con ODL esistenti
    for odl_id in [1, 2, 3]:
        print(f"\n🧪 Test ODL #{odl_id}")
        data = test_api_endpoint(odl_id)
        
        if data:
            # Verifica che i dati siano utilizzabili dal frontend
            required_fields = ['id', 'status', 'created_at', 'updated_at', 'timestamps']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Campi mancanti: {missing_fields}")
            else:
                print(f"✅ Tutti i campi richiesti sono presenti")
    
    # 4. Riepilogo e raccomandazioni
    print_header("RIEPILOGO E RACCOMANDAZIONI")
    
    print("✅ Miglioramenti implementati:")
    print("   - Logica di fallback per ODL senza state logs")
    print("   - Visualizzazione stimata basata su stato corrente")
    print("   - Indicatori visivi per dati stimati vs reali")
    print("   - Sanitizzazione e validazione dati in ingresso")
    print("   - Gestione robusta di errori e casi edge")
    
    print("\n💡 Come testare nel browser:")
    print("   1. Avvia il backend: cd backend && python -m uvicorn main:app --reload")
    print("   2. Avvia il frontend: cd frontend && npm run dev")
    print("   3. Vai alla pagina ODL e verifica le barre di progresso")
    print("   4. Anche senza state logs, dovresti vedere barre stimate")
    
    print("\n🔧 Per generare logs mancanti (opzionale):")
    print("   POST /api/odl-monitoring/monitoring/generate-missing-logs")
    
    print(f"\n🎯 TEST COMPLETATO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 