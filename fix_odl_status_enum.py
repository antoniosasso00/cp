#!/usr/bin/env python3
"""
Script per correggere i valori di stato ODL non validi nel database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Configurazione database
DATABASE_URL = "sqlite:///./carbonpilot.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_odl_status():
    """
    Corregge i valori di stato ODL non validi nel database
    """
    print("🔧 Correzione Stati ODL Non Validi")
    print("=" * 50)
    print(f"⏰ Data/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db = SessionLocal()
    
    try:
        # Verifica gli stati attuali
        print("📊 Verifica stati ODL attuali...")
        result = db.execute(text("SELECT DISTINCT status FROM odl ORDER BY status"))
        stati_attuali = [row[0] for row in result.fetchall()]
        print(f"   Stati trovati: {stati_attuali}")
        print()
        
        # Stati validi secondo l'enum
        stati_validi = ["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"]
        print(f"📋 Stati validi: {stati_validi}")
        print()
        
        # Trova stati non validi
        stati_non_validi = [stato for stato in stati_attuali if stato not in stati_validi]
        
        if not stati_non_validi:
            print("✅ Tutti gli stati ODL sono validi!")
            return True
        
        print(f"❌ Stati non validi trovati: {stati_non_validi}")
        print()
        
        # Mappatura correzioni
        correzioni = {
            "Terminato": "Finito",
            "Completato": "Finito",
            "Chiuso": "Finito",
            "In Produzione": "Laminazione",
            "In Lavorazione": "Laminazione",
            "Attesa": "Attesa Cura",
            "In Attesa": "Attesa Cura"
        }
        
        # Applica correzioni
        for stato_errato in stati_non_validi:
            stato_corretto = correzioni.get(stato_errato, "Preparazione")  # Default fallback
            
            print(f"🔄 Correzione: '{stato_errato}' → '{stato_corretto}'")
            
            # Conta quanti record verranno modificati
            count_result = db.execute(text("SELECT COUNT(*) FROM odl WHERE status = :old_status"), 
                                    {"old_status": stato_errato})
            count = count_result.fetchone()[0]
            print(f"   📊 Record da aggiornare: {count}")
            
            if count > 0:
                # Applica la correzione
                db.execute(text("UPDATE odl SET status = :new_status WHERE status = :old_status"), 
                          {"new_status": stato_corretto, "old_status": stato_errato})
                print(f"   ✅ Aggiornati {count} record")
            
            print()
        
        # Commit delle modifiche
        db.commit()
        print("💾 Modifiche salvate nel database")
        print()
        
        # Verifica finale
        print("🔍 Verifica finale...")
        result = db.execute(text("SELECT DISTINCT status FROM odl ORDER BY status"))
        stati_finali = [row[0] for row in result.fetchall()]
        print(f"   Stati finali: {stati_finali}")
        
        # Controlla se tutti gli stati sono ora validi
        stati_ancora_non_validi = [stato for stato in stati_finali if stato not in stati_validi]
        
        if not stati_ancora_non_validi:
            print("✅ Tutti gli stati ODL sono ora validi!")
            return True
        else:
            print(f"❌ Stati ancora non validi: {stati_ancora_non_validi}")
            return False
            
    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante la correzione: {str(e)}")
        return False
    finally:
        db.close()

def show_odl_summary():
    """
    Mostra un riassunto degli ODL per stato
    """
    print("📊 Riassunto ODL per Stato")
    print("-" * 30)
    
    db = SessionLocal()
    
    try:
        result = db.execute(text("SELECT status, COUNT(*) as count FROM odl GROUP BY status ORDER BY count DESC"))
        
        for row in result.fetchall():
            stato, count = row
            print(f"   {stato}: {count} ODL")
            
    except Exception as e:
        print(f"❌ Errore nel recupero riassunto: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Avvio correzione stati ODL...")
    print()
    
    # Mostra situazione iniziale
    show_odl_summary()
    print()
    
    # Applica correzioni
    success = fix_odl_status()
    
    if success:
        print()
        print("🎉 Correzione completata con successo!")
        print()
        
        # Mostra situazione finale
        show_odl_summary()
        print()
        print("💡 Ora puoi riavviare il backend senza errori")
    else:
        print()
        print("💥 Correzione fallita. Controlla i log per dettagli.")
        
    print()
    print("🏁 Script completato!") 