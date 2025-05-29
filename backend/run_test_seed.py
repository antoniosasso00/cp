#!/usr/bin/env python3
"""
🌱 SCRIPT PER ESEGUIRE IL SEED DI TEST NESTING

Questo script esegue solo la parte di creazione del seed di test
per il sistema nesting, senza eseguire i test completi.

Utile per:
- Preparare dati di test prima di test manuali
- Reset del database con dati puliti
- Debug del sistema di seed

Uso:
    python run_test_seed.py [--clean]
    
Opzioni:
    --clean    Pulisce il database prima di creare il seed
"""

import sys
import os
import argparse
from datetime import datetime

# Aggiungi la directory backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from models.db import SessionLocal, engine, Base
from models.odl import ODL
from models.parte import Parte
from models.catalogo import Catalogo
from models.tool import Tool
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.ciclo_cura import CicloCura
from models.nesting_result import NestingResult
from models.schedule_entry import ScheduleEntry
from seeds.test_nesting_seed import create_test_nesting_data

def cleanup_database():
    """Pulisce il database"""
    print("🧹 Pulizia database...")
    
    db = SessionLocal()
    try:
        # Elimina in ordine per rispettare le foreign key
        db.query(ScheduleEntry).delete()
        db.query(NestingResult).delete()
        db.query(ODL).delete()
        db.query(Tool).delete()
        db.query(Parte).delete()
        db.query(Catalogo).delete()
        db.query(Autoclave).delete()
        db.query(CicloCura).delete()
        
        db.commit()
        print("✅ Database pulito con successo")
        return True
        
    except Exception as e:
        print(f"❌ Errore nella pulizia database: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def check_existing_data():
    """Verifica se esistono già dati nel database"""
    db = SessionLocal()
    try:
        odl_count = db.query(ODL).count()
        autoclave_count = db.query(Autoclave).count()
        cicli_count = db.query(CicloCura).count()
        
        if odl_count > 0 or autoclave_count > 0 or cicli_count > 0:
            print(f"⚠️ Database contiene già dati:")
            print(f"   - {odl_count} ODL")
            print(f"   - {autoclave_count} Autoclavi")
            print(f"   - {cicli_count} Cicli di cura")
            return True
        else:
            print("✅ Database vuoto, pronto per il seed")
            return False
            
    except Exception as e:
        print(f"❌ Errore nella verifica dati: {e}")
        return False
        
    finally:
        db.close()

def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(description='Esegue il seed di test per il sistema nesting')
    parser.add_argument('--clean', action='store_true', help='Pulisce il database prima del seed')
    parser.add_argument('--force', action='store_true', help='Forza il seed anche se esistono dati')
    
    args = parser.parse_args()
    
    print("🌱 SEED DI TEST SISTEMA NESTING")
    print("=" * 50)
    print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verifica dati esistenti
    has_existing_data = check_existing_data()
    
    if has_existing_data and not args.clean and not args.force:
        print("\n❌ Il database contiene già dati.")
        print("💡 Usa --clean per pulire prima del seed o --force per sovrascrivere")
        return 1
    
    # Pulizia se richiesta
    if args.clean:
        if not cleanup_database():
            print("\n❌ Errore nella pulizia database")
            return 1
    
    # Creazione seed
    print("\n🌱 Creazione seed di test...")
    try:
        success = create_test_nesting_data()
        
        if success:
            print("\n✅ SEED COMPLETATO CON SUCCESSO!")
            print("\n📊 Dati creati:")
            
            # Verifica finale
            db = SessionLocal()
            try:
                odl_count = db.query(ODL).count()
                autoclave_count = db.query(Autoclave).count()
                cicli_count = db.query(CicloCura).count()
                parti_count = db.query(Parte).count()
                tool_count = db.query(Tool).count()
                
                print(f"   - {cicli_count} Cicli di cura")
                print(f"   - {autoclave_count} Autoclavi")
                print(f"   - {parti_count} Parti nel catalogo")
                print(f"   - {tool_count} Tool")
                print(f"   - {odl_count} ODL in Attesa Cura")
                
                # Statistiche ODL per priorità
                odl_alta = db.query(ODL).filter(ODL.priorita == 5).count()
                odl_media = db.query(ODL).filter(ODL.priorita.in_([3, 4])).count()
                odl_bassa = db.query(ODL).filter(ODL.priorita.in_([1, 2])).count()
                
                print(f"\n📈 Distribuzione priorità ODL:")
                print(f"   - Alta (5): {odl_alta}")
                print(f"   - Media (3-4): {odl_media}")
                print(f"   - Bassa (1-2): {odl_bassa}")
                
            finally:
                db.close()
            
            print("\n🔗 Prossimi passi:")
            print("   1. Avvia il backend: cd backend && python -m uvicorn main:app --reload")
            print("   2. Testa preview: GET /api/v1/nesting/preview")
            print("   3. Genera nesting: POST /api/v1/nesting/automatic")
            print("   4. Frontend: http://localhost:3000/dashboard/curing/nesting")
            
            return 0
        else:
            print("\n❌ ERRORE NELLA CREAZIONE DEL SEED")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 