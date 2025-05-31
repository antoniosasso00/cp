#!/usr/bin/env python3
"""
Script per creare dati di test completi per il sistema CarbonPilot
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import get_db
from models.parte import Parte
from models.tool import Tool
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura
from models.odl import ODL
from models.autoclave import Autoclave
from datetime import datetime

def create_tools(db):
    """Crea tool di test"""
    print("🔧 Creazione Tool...")
    
    tools_data = [
        {
            "part_number_tool": "TOOL-001",
            "descrizione": "Stampo per pannello carrozzeria automotive",
            "lunghezza_piano": 800.0,  # mm
            "larghezza_piano": 600.0,  # mm
            "peso": 15.0,  # kg
            "materiale": "Alluminio",
            "disponibile": True
        },
        {
            "part_number_tool": "TOOL-002", 
            "descrizione": "Stampo per staffa supporto motore",
            "lunghezza_piano": 400.0,
            "larghezza_piano": 300.0,
            "peso": 8.0,
            "materiale": "Acciaio",
            "disponibile": True
        },
        {
            "part_number_tool": "TOOL-003",
            "descrizione": "Stampo per prototipo componente test",
            "lunghezza_piano": 200.0,
            "larghezza_piano": 150.0,
            "peso": 3.0,
            "materiale": "Alluminio",
            "disponibile": True
        },
        {
            "part_number_tool": "TOOL-004",
            "descrizione": "Stampo per componente grande",
            "lunghezza_piano": 1000.0,
            "larghezza_piano": 800.0,
            "peso": 25.0,
            "materiale": "Acciaio",
            "disponibile": True
        },
        {
            "part_number_tool": "TOOL-005",
            "descrizione": "Stampo per componente medio",
            "lunghezza_piano": 600.0,
            "larghezza_piano": 400.0,
            "peso": 12.0,
            "materiale": "Alluminio",
            "disponibile": True
        }
    ]
    
    created_tools = []
    for tool_data in tools_data:
        # Controlla se esiste già
        existing = db.query(Tool).filter(Tool.part_number_tool == tool_data["part_number_tool"]).first()
        if not existing:
            tool = Tool(**tool_data)
            db.add(tool)
            db.commit()
            db.refresh(tool)
            created_tools.append(tool)
            print(f"   ✅ Creato tool: {tool.part_number_tool}")
        else:
            created_tools.append(existing)
            print(f"   ⚠️ Tool già esistente: {tool_data['part_number_tool']}")
    
    return created_tools

def associate_tools_to_parts(db, tools):
    """Associa i tool alle parti esistenti"""
    print("🔗 Associazione Tool alle Parti...")
    
    parti = db.query(Parte).all()
    
    # Associa tool alle parti in modo ciclico
    for i, parte in enumerate(parti):
        tool = tools[i % len(tools)]
        
        # Controlla se l'associazione esiste già
        if tool not in parte.tools:
            parte.tools.append(tool)
            db.commit()
            print(f"   ✅ Associato {tool.part_number_tool} a {parte.part_number}")

def create_odl(db):
    """Crea ODL di test"""
    print("📝 Creazione ODL...")
    
    parti = db.query(Parte).all()
    
    if not parti:
        print("   ❌ Nessuna parte trovata per creare ODL")
        return []
    
    created_odl = []
    for i, parte in enumerate(parti):
        if parte.tools:  # Solo se la parte ha tool associati
            tool = parte.tools[0]  # Prendi il primo tool
            
            odl = ODL(
                parte_id=parte.id,
                tool_id=tool.id,
                status="Attesa Cura",
                priorita=i + 1,
                note=f"ODL di test per {parte.descrizione_breve}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(odl)
            db.commit()
            db.refresh(odl)
            created_odl.append(odl)
            print(f"   ✅ Creato ODL {odl.id}: {parte.part_number} con {tool.part_number_tool}")
    
    return created_odl

def main():
    db = next(get_db())
    
    print("🚀 Creazione Dati di Test Completi")
    print("=" * 50)
    
    try:
        # 1. Crea tool
        tools = create_tools(db)
        
        # 2. Associa tool alle parti
        associate_tools_to_parts(db, tools)
        
        # 3. Crea ODL
        odl_list = create_odl(db)
        
        print("\n✅ Creazione completata!")
        print(f"   🔧 Tool creati: {len(tools)}")
        print(f"   📝 ODL creati: {len(odl_list)}")
        
        # Verifica finale
        print("\n🔍 Verifica finale:")
        print(f"   📦 Parti totali: {db.query(Parte).count()}")
        print(f"   🔧 Tool totali: {db.query(Tool).count()}")
        print(f"   📝 ODL totali: {db.query(ODL).count()}")
        print(f"   🏭 Autoclavi totali: {db.query(Autoclave).count()}")
        
    except Exception as e:
        print(f"❌ Errore durante la creazione: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 