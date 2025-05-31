#!/usr/bin/env python3
"""
🔧 SCRIPT PER AGGIORNARE TABELLA NESTING_RESULTS
================================================

Aggiunge tutti i campi mancanti alla tabella nesting_results.
"""

import sys
import os

# Aggiungi il path del backend per gli import
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import text, inspect
from backend.models.db import engine, SessionLocal

def fix_nesting_results_table():
    """Aggiunge tutti i campi mancanti alla tabella nesting_results"""
    try:
        print("🔧 Aggiornamento tabella nesting_results...")
        
        # Verifica quali colonne esistono
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('nesting_results')]
        
        print(f"📋 Colonne esistenti: {existing_columns}")
        
        # Campi da aggiungere
        fields_to_add = [
            ('batch_id', 'VARCHAR(36)'),
            ('peso_totale_kg', 'FLOAT DEFAULT 0.0'),
            ('area_piano_1', 'FLOAT DEFAULT 0.0'),
            ('area_piano_2', 'FLOAT DEFAULT 0.0'),
            ('superficie_piano_2_max', 'FLOAT')
        ]
        
        with engine.connect() as conn:
            for field_name, field_type in fields_to_add:
                if field_name not in existing_columns:
                    print(f"➕ Aggiunta colonna '{field_name}' alla tabella nesting_results")
                    conn.execute(text(f"ALTER TABLE nesting_results ADD COLUMN {field_name} {field_type}"))
                    conn.commit()
                else:
                    print(f"✅ Colonna '{field_name}' già presente")
            
            # Verifica le modifiche
            new_columns = [col['name'] for col in inspector.get_columns('nesting_results')]
            print(f"📋 Colonne dopo fix: {new_columns}")
            
        print("✅ Fix tabella nesting_results completato!")
        return True
        
    except Exception as e:
        print(f"❌ Errore nel fix: {e}")
        return False

if __name__ == "__main__":
    success = fix_nesting_results_table()
    sys.exit(0 if success else 1) 