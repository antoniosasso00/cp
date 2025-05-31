#!/usr/bin/env python3
"""
Script per pulire completamente il database e correggere tutti gli stati.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import engine
from sqlalchemy import text

def fix_database_final():
    """Pulizia finale del database."""
    print("🧹 Pulizia finale database...")
    
    with engine.connect() as conn:
        print("1. 🗑️ Eliminazione batch di nesting esistenti...")
        
        # Verifica se le tabelle esistono prima di eliminarle
        try:
            result = conn.execute(text("DELETE FROM nesting_results"))
            print(f"   Eliminati {result.rowcount} nesting results")
        except Exception as e:
            print(f"   Tabella nesting_results non trovata o vuota")
        
        try:
            result = conn.execute(text("DELETE FROM nesting_batches"))
            print(f"   Eliminati {result.rowcount} batch di nesting")
        except Exception as e:
            print(f"   Tabella nesting_batches non trovata o vuota")
        
        print("2. 📋 Creazione tabelle mancanti...")
        # Crea le tabelle se non esistono
        try:
            from models.nesting_batch import NestingBatch
            from models.base import Base
            print("   Creazione tabella nesting_batches...")
            Base.metadata.create_all(bind=engine, tables=[NestingBatch.__table__])
            print("   ✅ Tabella nesting_batches creata!")
        except Exception as e:
            print(f"   ❌ Errore creazione tabelle: {e}")
        
        print("3. 🔧 Correzione stati ODL...")
        result = conn.execute(text("UPDATE odl SET status = 'Attesa Cura'"))
        print(f"   Aggiornati {result.rowcount} ODL allo stato 'Attesa Cura'")
        
        print("4. 🛠️ Correzione disponibilità tool...")
        result = conn.execute(text("UPDATE tools SET disponibile = 1"))
        print(f"   Aggiornati {result.rowcount} tool a disponibile=True")
        
        print("5. 🏭 Correzione stati autoclavi...")
        result = conn.execute(text("UPDATE autoclavi SET stato = 'DISPONIBILE'"))
        print(f"   Aggiornate {result.rowcount} autoclavi allo stato DISPONIBILE")
        
        # Commit delle modifiche
        conn.commit()
        
        print("6. ✅ Verifica finale...")
        # Verifica ODL
        result = conn.execute(text("SELECT COUNT(*) as total, status FROM odl GROUP BY status"))
        odl_stats = result.fetchall()
        print("   📋 Stati ODL:")
        for stat in odl_stats:
            print(f"     - {stat[1]}: {stat[0]} ODL")
        
        # Verifica tool
        result = conn.execute(text("SELECT COUNT(*) as total, disponibile FROM tools GROUP BY disponibile"))
        tool_stats = result.fetchall()
        print("   🔧 Disponibilità tool:")
        for stat in tool_stats:
            status = "Disponibile" if stat[1] else "Non disponibile"
            print(f"     - {status}: {stat[0]} tool")
        
        # Verifica autoclavi
        result = conn.execute(text("SELECT COUNT(*) as total, stato FROM autoclavi GROUP BY stato"))
        auto_stats = result.fetchall()
        print("   🏭 Stati autoclavi:")
        for stat in auto_stats:
            print(f"     - {stat[1]}: {stat[0]} autoclavi")

if __name__ == "__main__":
    fix_database_final()
    print("🎉 Pulizia database completata!") 