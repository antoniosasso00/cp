#!/usr/bin/env python3
"""
Script di debug per verificare e risolvere i problemi di scheduling.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from models.db import get_database_url
from models import Base
from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus, ScheduleEntryType
from models.tempo_produzione import TempoProduzione

def debug_database():
    """Debug completo del database."""
    
    print("🔍 DEBUG SISTEMA SCHEDULING")
    print("=" * 50)
    
    # Crea il motore del database
    database_url = get_database_url()
    print(f"📊 Database URL: {database_url}")
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # 1. Verifica tabelle esistenti
            print("\n📋 TABELLE ESISTENTI:")
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            for table in sorted(tables):
                print(f"  ✅ {table}")
            
            # 2. Verifica tabella schedule_entries
            print("\n🗓️ TABELLA SCHEDULE_ENTRIES:")
            if 'schedule_entries' in tables:
                result = conn.execute(text("PRAGMA table_info(schedule_entries)"))
                columns = list(result)
                print(f"  📊 Colonne ({len(columns)}):")
                for col in columns:
                    print(f"    - {col[1]}: {col[2]} (nullable: {not col[3]})")
                
                # Conta i record
                result = conn.execute(text("SELECT COUNT(*) FROM schedule_entries"))
                count = result.scalar()
                print(f"  📈 Record: {count}")
            else:
                print("  ❌ Tabella schedule_entries NON ESISTE")
                return False
            
            # 3. Verifica tabella tempi_produzione
            print("\n⏱️ TABELLA TEMPI_PRODUZIONE:")
            if 'tempi_produzione' in tables:
                result = conn.execute(text("PRAGMA table_info(tempi_produzione)"))
                columns = list(result)
                print(f"  📊 Colonne ({len(columns)}):")
                for col in columns:
                    print(f"    - {col[1]}: {col[2]} (nullable: {not col[3]})")
                
                # Conta i record
                result = conn.execute(text("SELECT COUNT(*) FROM tempi_produzione"))
                count = result.scalar()
                print(f"  📈 Record: {count}")
                
                if count > 0:
                    # Mostra alcuni esempi
                    result = conn.execute(text("SELECT part_number, categoria, sotto_categoria, tempo_medio_minuti FROM tempi_produzione LIMIT 3"))
                    print("  📝 Esempi:")
                    for row in result:
                        print(f"    - {row[0] or 'N/A'} | {row[1] or 'N/A'} | {row[2] or 'N/A'} | {row[3]}min")
            else:
                print("  ❌ Tabella tempi_produzione NON ESISTE")
                return False
            
            # 4. Test API endpoint simulation
            print("\n🔌 TEST ENDPOINT SIMULATION:")
            try:
                # Simula la query dell'endpoint schedules
                result = conn.execute(text("""
                    SELECT s.*, a.nome as autoclave_nome, o.id as odl_id
                    FROM schedule_entries s
                    LEFT JOIN autoclavi a ON s.autoclave_id = a.id
                    LEFT JOIN odl o ON s.odl_id = o.id
                    LIMIT 5
                """))
                schedules = list(result)
                print(f"  📊 Schedulazioni trovate: {len(schedules)}")
                
                if schedules:
                    for schedule in schedules:
                        print(f"    - ID: {schedule[0]}, Tipo: {schedule[1]}, Autoclave: {schedule[2] if len(schedule) > 2 else 'N/A'}")
                else:
                    print("  ℹ️  Nessuna schedulazione presente (normale per nuovo sistema)")
                
            except Exception as e:
                print(f"  ❌ Errore query: {e}")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Errore connessione database: {e}")
        return False

def create_missing_tables():
    """Crea le tabelle mancanti."""
    
    print("\n🔧 CREAZIONE TABELLE MANCANTI")
    print("=" * 50)
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        # Crea tutte le tabelle
        Base.metadata.create_all(engine)
        print("✅ Tutte le tabelle create/verificate con successo!")
        return True
    except Exception as e:
        print(f"❌ Errore creazione tabelle: {e}")
        return False

def insert_sample_data():
    """Inserisce dati di esempio."""
    
    print("\n📝 INSERIMENTO DATI DI ESEMPIO")
    print("=" * 50)
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Verifica se ci sono già dati
            result = conn.execute(text("SELECT COUNT(*) FROM tempi_produzione"))
            count = result.scalar()
            
            if count > 0:
                print(f"ℹ️  Dati già presenti ({count} record), salto l'inserimento")
                return True
            
            # Inserisce dati di esempio
            sample_data = [
                ("PART001", "Aerospace", "Wing Components", 240, 200, 300, 5),
                ("PART002", "Automotive", "Engine Parts", 180, 150, 220, 8),
                (None, "Aerospace", "Fuselage", 360, 300, 420, 3),
                (None, "Medical", "Implants", 120, 90, 150, 12),
                (None, "Industrial", "Machinery", 480, 400, 600, 6)
            ]
            
            for part_number, categoria, sotto_categoria, tempo_medio, tempo_min, tempo_max, osservazioni in sample_data:
                try:
                    conn.execute(text("""
                        INSERT INTO tempi_produzione 
                        (part_number, categoria, sotto_categoria, tempo_medio_minuti, 
                         tempo_minimo_minuti, tempo_massimo_minuti, numero_osservazioni, 
                         ultima_osservazione, note)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 'Dati di esempio per debug')
                    """), (part_number, categoria, sotto_categoria, tempo_medio, tempo_min, tempo_max, osservazioni))
                    print(f"  ✅ Inserito: {categoria}/{sotto_categoria} - {tempo_medio}min")
                except Exception as e:
                    print(f"  ❌ Errore inserimento: {e}")
            
            conn.commit()
            print("✅ Dati di esempio inseriti con successo!")
            return True
            
    except Exception as e:
        print(f"❌ Errore inserimento dati: {e}")
        return False

def test_api_endpoints():
    """Testa gli endpoint API."""
    
    print("\n🌐 TEST ENDPOINT API")
    print("=" * 50)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test health check
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Health check OK")
                data = response.json()
                print(f"  📊 Database: {data.get('database', {}).get('status', 'unknown')}")
                print(f"  📊 Tabelle: {data.get('database', {}).get('tables_count', 0)}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Backend non raggiungibile! Assicurati che sia avviato con 'python main.py'")
            return False
        
        # Test endpoint schedules
        try:
            response = requests.get(f"{base_url}/api/v1/schedules", timeout=5)
            print(f"📅 Endpoint /schedules: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  📊 Schedulazioni: {len(data)}")
            elif response.status_code == 422:
                print("  ℹ️  Errore validazione (normale se non ci sono dati)")
            else:
                print(f"  ⚠️  Risposta: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Errore endpoint schedules: {e}")
        
        # Test endpoint production times
        try:
            response = requests.get(f"{base_url}/api/v1/schedules/production-times", timeout=5)
            print(f"⏱️ Endpoint /production-times: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  📊 Tempi produzione: {len(data)}")
            else:
                print(f"  ⚠️  Risposta: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Errore endpoint production-times: {e}")
        
        return True
        
    except ImportError:
        print("⚠️  Modulo requests non disponibile")
        return True

def main():
    """Esegue il debug completo."""
    
    print("🚀 AVVIO DEBUG SISTEMA SCHEDULING")
    print("=" * 60)
    
    # 1. Debug database
    if not debug_database():
        print("\n🔧 Tentativo riparazione...")
        if not create_missing_tables():
            print("❌ Impossibile creare le tabelle")
            return False
        
        # Riprova il debug
        if not debug_database():
            print("❌ Problemi persistenti con il database")
            return False
    
    # 2. Inserisci dati di esempio se necessario
    insert_sample_data()
    
    # 3. Test API
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("🎉 DEBUG COMPLETATO!")
    print("\n📋 PROSSIMI PASSI:")
    print("1. Assicurati che il backend sia avviato: python main.py")
    print("2. Avvia il frontend: cd ../frontend && npm run dev")
    print("3. Vai su http://localhost:3000/dashboard/schedule")
    print("4. Se ci sono ancora errori, controlla la console del browser")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 