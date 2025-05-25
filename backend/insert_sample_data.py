#!/usr/bin/env python3
"""
Script per inserire dati di esempio per i tempi di produzione.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from models.db import get_database_url

def insert_sample_data():
    """Inserisce dati di esempio per i tempi di produzione."""
    
    engine = create_engine(get_database_url())
    
    print("📝 Inserimento dati di esempio per tempi_produzione...")
    
    try:
        with engine.connect() as conn:
            # Prima controlla se ci sono già dati
            result = conn.execute(text("SELECT COUNT(*) FROM tempi_produzione"))
            count = result.scalar()
            
            if count > 0:
                print(f"  ℹ️  Dati già presenti ({count} record), salto l'inserimento")
                return True
            
            sample_data = [
                {"part_number": "PART001", "categoria": "Aerospace", "sotto_categoria": "Wing Components", "tempo_medio": 240, "tempo_min": 200, "tempo_max": 300, "osservazioni": 5},
                {"part_number": "PART002", "categoria": "Automotive", "sotto_categoria": "Engine Parts", "tempo_medio": 180, "tempo_min": 150, "tempo_max": 220, "osservazioni": 8},
                {"part_number": None, "categoria": "Aerospace", "sotto_categoria": "Fuselage", "tempo_medio": 360, "tempo_min": 300, "tempo_max": 420, "osservazioni": 3},
                {"part_number": None, "categoria": "Medical", "sotto_categoria": "Implants", "tempo_medio": 120, "tempo_min": 90, "tempo_max": 150, "osservazioni": 12},
                {"part_number": None, "categoria": "Industrial", "sotto_categoria": "Machinery", "tempo_medio": 480, "tempo_min": 400, "tempo_max": 600, "osservazioni": 6}
            ]
            
            for data in sample_data:
                try:
                    conn.execute(text("""
                        INSERT INTO tempi_produzione 
                        (part_number, categoria, sotto_categoria, tempo_medio_minuti, 
                         tempo_minimo_minuti, tempo_massimo_minuti, numero_osservazioni, 
                         ultima_osservazione, note)
                        VALUES (:part_number, :categoria, :sotto_categoria, :tempo_medio, 
                                :tempo_min, :tempo_max, :osservazioni, datetime('now'), 'Dati di esempio inseriti')
                    """), data)
                    print(f"  ✅ Inserito tempo per {data['categoria']}/{data['sotto_categoria']}")
                except Exception as e:
                    print(f"  ⚠️  Errore nell'inserimento: {e}")
            
            conn.commit()
            print("✅ Dati di esempio inseriti con successo!")
            
    except Exception as e:
        print(f"❌ Errore durante l'inserimento: {e}")
        return False
    
    return True

if __name__ == "__main__":
    insert_sample_data() 