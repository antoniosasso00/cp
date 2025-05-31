#!/usr/bin/env python3
"""
Script per aggiornare il database principale nella root del progetto
"""
import sys
import os

# Aggiungi il backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from models.autoclave import Autoclave

def fix_main_database():
    """Aggiorna lo schema del database principale"""
    
    # Database nella root del progetto
    db_path = "./carbonpilot.db"
    engine = create_engine(f"sqlite:///{db_path}")
    
    print(f"🔧 Aggiornamento database: {db_path}")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            # Verifica se il campo esiste già
            result = conn.execute(text("PRAGMA table_info(autoclavi)")).fetchall()
            columns = [col[1] for col in result]
            
            print("🔍 Colonne attuali:")
            for col in result:
                print(f"   {col[1]} ({col[2]})")
            
            if 'superficie_piano_2_max' not in columns:
                print("\n🔧 Aggiunta campo superficie_piano_2_max...")
                conn.execute(text("ALTER TABLE autoclavi ADD COLUMN superficie_piano_2_max FLOAT"))
                conn.commit()
                print("✅ Campo superficie_piano_2_max aggiunto!")
                
                # Aggiorna i valori di default
                print("🔧 Aggiornamento valori di default...")
                
                # Recupera autoclavi esistenti
                autoclavi_data = conn.execute(text("""
                    SELECT id, nome, lunghezza, larghezza_piano 
                    FROM autoclavi
                """)).fetchall()
                
                for autoclave in autoclavi_data:
                    autoclave_id, nome, lunghezza, larghezza_piano = autoclave
                    
                    # Calcola area piano principale in cm² (converte da mm)
                    if lunghezza and larghezza_piano:
                        area_piano_cm2 = (lunghezza * larghezza_piano) / 100  # mm² -> cm²
                        superficie_piano_2_max = area_piano_cm2 * 0.8  # 80% del piano principale
                    else:
                        superficie_piano_2_max = 10000.0  # Default
                    
                    # Aggiorna il record
                    conn.execute(text("""
                        UPDATE autoclavi 
                        SET superficie_piano_2_max = :superficie 
                        WHERE id = :id
                    """), {
                        'superficie': superficie_piano_2_max,
                        'id': autoclave_id
                    })
                    
                    print(f"   ✅ {nome}: superficie_piano_2_max = {superficie_piano_2_max:.1f} cm²")
                
                conn.commit()
                print("✅ Aggiornamento valori completato!")
            else:
                print("\nℹ️ Campo superficie_piano_2_max già presente")
            
            # Verifica finale
            result = conn.execute(text("PRAGMA table_info(autoclavi)")).fetchall()
            columns = [col[1] for col in result]
            if 'superficie_piano_2_max' in columns:
                print("🎯 Verifica: Campo superficie_piano_2_max presente!")
                return True
            else:
                print("❌ Verifica: Campo superficie_piano_2_max NON presente!")
                return False
            
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fix Database Principale - Aggiunta superficie_piano_2_max")
    print("=" * 70)
    
    success = fix_main_database()
    
    if success:
        print("\n🎯 Database aggiornato con successo!")
        print("💡 Riavvia il server per applicare le modifiche")
    else:
        print("\n❌ Aggiornamento fallito!") 