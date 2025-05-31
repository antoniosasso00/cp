#!/usr/bin/env python3
"""
Script per verificare lo stato dei tool e degli ODL.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import engine
from sqlalchemy import text

def check_tools_and_odl():
    """Verifica lo stato dei tool e degli ODL."""
    print("🔧 Verifica stato tool e ODL...")
    
    with engine.connect() as conn:
        # Verifica tool
        result = conn.execute(text("SELECT id, disponibile FROM tools LIMIT 10"))
        tools = result.fetchall()
        
        print(f"🔧 Tool disponibili:")
        for tool in tools:
            print(f"  - Tool {tool[0]}: disponibile={tool[1]}")
        
        # Aggiorna tutti i tool a disponibile
        result = conn.execute(text("UPDATE tools SET disponibile = 1"))
        print(f"✅ Aggiornati {result.rowcount} tool a disponibile=True")
        
        # Verifica ODL con tool
        result = conn.execute(text("""
            SELECT o.id, o.status, t.disponibile 
            FROM odl o 
            JOIN tools t ON o.tool_id = t.id 
            WHERE o.status = 'Attesa Cura' 
            LIMIT 10
        """))
        odl_tools = result.fetchall()
        
        print(f"📋 ODL in Attesa Cura con tool:")
        for odl in odl_tools:
            print(f"  - ODL {odl[0]}: status={odl[1]}, tool_disponibile={odl[2]}")
        
        # Commit delle modifiche
        conn.commit()

if __name__ == "__main__":
    check_tools_and_odl()
    print("🎉 Verifica completata!") 