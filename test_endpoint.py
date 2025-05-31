#!/usr/bin/env python3
"""
Script per testare l'endpoint ODL disponibili.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import SessionLocal
from models import ODL, Tool
from sqlalchemy.orm import Session

def test_odl_endpoint():
    """Testa la logica dell'endpoint ODL disponibili."""
    print("🔧 Test endpoint ODL disponibili...")
    
    db = SessionLocal()
    try:
        # Query per ODL in attesa di cura
        query = db.query(ODL).filter(
            ODL.status == "Attesa Cura"
        ).join(Tool).filter(
            Tool.disponibile == True
        )
        
        odl_list = query.all()
        print(f"📋 ODL trovati: {len(odl_list)}")
        
        # Preparazione dati per il frontend
        odl_data = []
        for odl in odl_list[:5]:  # Solo i primi 5 per test
            tool = odl.tool
            if tool:
                print(f"  - ODL {odl.id}: tool {tool.part_number_tool}")
                print(f"    Dimensioni: {tool.lunghezza_piano}x{tool.larghezza_piano} mm")
                print(f"    Peso: {tool.peso} kg")
                print(f"    Parte: {odl.parte.descrizione_breve if odl.parte else 'N/A'}")
                
                odl_data.append({
                    "id": odl.id,
                    "numero_odl": f"ODL-{odl.id:06d}",
                    "parte_nome": odl.parte.descrizione_breve if odl.parte else "N/A",
                    "tool_nome": tool.part_number_tool,
                    "tool_dimensioni": {
                        "lunghezza": tool.lunghezza_piano,
                        "larghezza": tool.larghezza_piano,
                        "altezza": 50.0
                    },
                    "peso_kg": tool.peso or 0.0,
                    "area_stimata": (tool.lunghezza_piano * tool.larghezza_piano) / 100 if tool.lunghezza_piano and tool.larghezza_piano else 0,
                    "ciclo_cura": {
                        "id": 1,
                        "nome": "Standard"
                    },
                    "priorita": "Media",
                    "data_creazione": odl.created_at.isoformat() if odl.created_at else None
                })
        
        print(f"✅ Dati preparati per {len(odl_data)} ODL")
        return {
            "success": True,
            "data": odl_data,
            "total": len(odl_data)
        }
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    result = test_odl_endpoint()
    print(f"🎉 Risultato: {result['success']}")
    if result['success']:
        print(f"📊 Totale ODL: {result['total']}")
    else:
        print(f"❌ Errore: {result['error']}") 