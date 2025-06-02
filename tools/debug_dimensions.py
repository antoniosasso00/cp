#!/usr/bin/env python3
"""
Debug script per verificare dimensioni tool gigante vs autoclave
"""

import sys
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from api.database import get_db
from models.tool import Tool
from models.autoclave import Autoclave
from models.odl import ODL

def main():
    db = next(get_db())
    
    print("🔍 VERIFICA DIMENSIONI TOOL GIGANTE")
    print("=" * 50)
    
    # Trova tool gigante
    giant_tool = db.query(Tool).filter(
        Tool.part_number_tool.like('TOOL-GIANT-A%')
    ).first()
    
    if giant_tool:
        print(f"✅ Tool Gigante trovato:")
        print(f"   Part Number: {giant_tool.part_number_tool}")
        print(f"   Dimensioni: {giant_tool.lunghezza_piano}x{giant_tool.larghezza_piano}mm")
        print(f"   Peso: {giant_tool.peso}kg")
        
        # Trova ODL associato
        odl = db.query(ODL).filter(ODL.tool_id == giant_tool.id).first()
        if odl:
            print(f"   ODL ID: {odl.id}")
        
    else:
        print("❌ Tool gigante non trovato")
        return
    
    # Trova autoclave test
    autoclave = db.query(Autoclave).filter(
        Autoclave.codice == 'EDGE-001'
    ).first()
    
    if autoclave:
        print(f"\n🏭 Autoclave Test:")
        print(f"   Nome: {autoclave.nome}")
        print(f"   Dimensioni: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
        print(f"   Max weight: {autoclave.max_load_kg}kg")
        print(f"   Linee vuoto: {autoclave.num_linee_vuoto}")
    else:
        print("❌ Autoclave test non trovata")
        return
    
    # Verifica compatibilità
    print(f"\n🧮 ANALISI COMPATIBILITÀ:")
    print(f"   Tool: {giant_tool.lunghezza_piano}x{giant_tool.larghezza_piano}mm")
    print(f"   Autoclave: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
    
    fits_normal = (giant_tool.larghezza_piano <= autoclave.larghezza_piano and 
                   giant_tool.lunghezza_piano <= autoclave.lunghezza)
    fits_rotated = (giant_tool.lunghezza_piano <= autoclave.larghezza_piano and 
                    giant_tool.larghezza_piano <= autoclave.lunghezza)
    
    print(f"   Fit normale: {fits_normal}")
    print(f"   Fit ruotato: {fits_rotated}")
    
    if not fits_normal and not fits_rotated:
        print("   ✅ CORRETTO: Tool NON dovrebbe essere posizionato!")
    else:
        print("   ❌ PROBLEMA: Tool potrebbe essere posizionato!")
    
    db.close()

if __name__ == "__main__":
    main() 