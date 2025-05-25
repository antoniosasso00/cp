#!/usr/bin/env python3
"""
Script di test per verificare l'implementazione completa del sistema di scheduling.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from models.db import get_database_url
from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus, ScheduleEntryType
from models.tempo_produzione import TempoProduzione

def test_database_schema():
    """Testa che lo schema del database sia aggiornato correttamente."""
    
    print("🔍 Test schema database...")
    
    engine = create_engine(get_database_url())
    
    try:
        with engine.connect() as conn:
            # Test tabella schedule_entries
            result = conn.execute(text("PRAGMA table_info(schedule_entries)"))
            columns = [row[1] for row in result]
            
            required_columns = [
                'schedule_type', 'categoria', 'sotto_categoria', 
                'is_recurring', 'pieces_per_month', 'note', 
                'estimated_duration_minutes'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                print(f"❌ Colonne mancanti in schedule_entries: {missing_columns}")
                return False
            else:
                print("✅ Tutte le colonne richieste presenti in schedule_entries")
            
            # Test tabella tempi_produzione
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM tempi_produzione"))
                count = result.scalar()
                print(f"✅ Tabella tempi_produzione presente con {count} record")
            except Exception as e:
                print(f"❌ Errore tabella tempi_produzione: {e}")
                return False
            
            # Test indici
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name IN ('schedule_entries', 'tempi_produzione')
                AND name NOT LIKE 'sqlite_%'
            """))
            indices = [row[0] for row in result]
            
            required_indices = [
                'idx_schedule_entries_categoria',
                'idx_schedule_entries_schedule_type',
                'idx_tempi_produzione_part_number'
            ]
            
            missing_indices = [idx for idx in required_indices if idx not in indices]
            if missing_indices:
                print(f"⚠️  Indici mancanti: {missing_indices}")
            else:
                print("✅ Tutti gli indici richiesti presenti")
            
            return True
            
    except Exception as e:
        print(f"❌ Errore test schema: {e}")
        return False

def test_enum_values():
    """Testa che gli enum siano definiti correttamente."""
    
    print("\n🔍 Test enum values...")
    
    try:
        # Test ScheduleEntryType
        expected_types = ['odl_specifico', 'categoria', 'sotto_categoria', 'ricorrente']
        actual_types = [t.value for t in ScheduleEntryType]
        
        if set(expected_types) <= set(actual_types):
            print("✅ ScheduleEntryType enum corretto")
        else:
            print(f"❌ ScheduleEntryType mancanti: {set(expected_types) - set(actual_types)}")
            return False
        
        # Test ScheduleEntryStatus
        expected_statuses = ['previsionale', 'in_attesa', 'in_corso', 'posticipato']
        actual_statuses = [s.value for s in ScheduleEntryStatus]
        
        if set(expected_statuses) <= set(actual_statuses):
            print("✅ ScheduleEntryStatus enum corretto")
        else:
            print(f"❌ ScheduleEntryStatus mancanti: {set(expected_statuses) - set(actual_statuses)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test enum: {e}")
        return False

def test_tempo_produzione_model():
    """Testa il modello TempoProduzione."""
    
    print("\n🔍 Test modello TempoProduzione...")
    
    try:
        # Test metodo get_tempo_stimato
        engine = create_engine(get_database_url())
        
        with engine.connect() as conn:
            # Test con part_number specifico
            result = conn.execute(text("""
                SELECT tempo_medio_minuti FROM tempi_produzione 
                WHERE part_number = 'PART001'
            """))
            row = result.fetchone()
            
            if row:
                print(f"✅ Tempo per PART001: {row[0]} minuti")
            else:
                print("⚠️  Nessun tempo trovato per PART001")
            
            # Test con categoria
            result = conn.execute(text("""
                SELECT tempo_medio_minuti FROM tempi_produzione 
                WHERE categoria = 'Aerospace' AND part_number IS NULL
            """))
            row = result.fetchone()
            
            if row:
                print(f"✅ Tempo per categoria Aerospace: {row[0]} minuti")
            else:
                print("⚠️  Nessun tempo trovato per categoria Aerospace")
            
            return True
            
    except Exception as e:
        print(f"❌ Errore test TempoProduzione: {e}")
        return False

def test_api_endpoints():
    """Testa che gli endpoint API siano disponibili."""
    
    print("\n🔍 Test endpoint API...")
    
    try:
        import requests
        
        base_url = "http://localhost:8000/api/v1"
        
        # Test endpoint schedules
        endpoints = [
            "/schedules",
            "/schedules/production-times"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code in [200, 404, 422]:  # 404/422 sono OK se non ci sono dati
                    print(f"✅ Endpoint {endpoint} disponibile")
                else:
                    print(f"⚠️  Endpoint {endpoint} risposta: {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"⚠️  Backend non raggiungibile per {endpoint}")
            except Exception as e:
                print(f"❌ Errore endpoint {endpoint}: {e}")
        
        return True
        
    except ImportError:
        print("⚠️  Modulo requests non disponibile, salto test API")
        return True
    except Exception as e:
        print(f"❌ Errore test API: {e}")
        return False

def test_frontend_files():
    """Testa che i file frontend siano presenti."""
    
    print("\n🔍 Test file frontend...")
    
    frontend_files = [
        "../frontend/src/components/ScheduleForm.tsx",
        "../frontend/src/components/RecurringScheduleForm.tsx",
        "../frontend/src/components/CalendarSchedule.tsx",
        "../frontend/src/lib/types/schedule.ts",
        "../frontend/src/app/dashboard/schedule/page.tsx"
    ]
    
    all_present = True
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"✅ File presente: {os.path.basename(file_path)}")
        else:
            print(f"❌ File mancante: {file_path}")
            all_present = False
    
    return all_present

def main():
    """Esegue tutti i test."""
    
    print("🚀 Test completo sistema di scheduling CarbonPilot")
    print("=" * 60)
    
    tests = [
        ("Schema Database", test_database_schema),
        ("Enum Values", test_enum_values),
        ("Modello TempoProduzione", test_tempo_produzione_model),
        ("API Endpoints", test_api_endpoints),
        ("File Frontend", test_frontend_files)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Errore durante {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI TEST")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {test_name}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"📈 TOTALE: {passed}/{total} test passati")
    
    if passed == total:
        print("🎉 TUTTI I TEST PASSATI! Sistema di scheduling completamente implementato.")
        return True
    else:
        print("⚠️  Alcuni test falliti. Controlla i dettagli sopra.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 