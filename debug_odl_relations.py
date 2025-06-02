#!/usr/bin/env python3
"""
🔍 Script per verificare le relazioni degli ODL in Attesa Cura
"""

import sys
import os
# Cambia directory di lavoro al backend per usare il database corretto
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append('.')

from models.db import SessionLocal
from models.odl import ODL
from sqlalchemy import text

def main():
    """Verifica le relazioni degli ODL in Attesa Cura"""
    
    print("🔍 ANALISI RELAZIONI ODL IN ATTESA CURA")
    print("="*60)
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Crea sessione database
    db = SessionLocal()
    
    try:
        # 1. Query diretta per ODL in Attesa Cura
        print("\n📋 ODL IN ATTESA CURA (query diretta):")
        print("-"*50)
        
        result = db.execute(text("""
            SELECT o.id, o.status, o.priorita, o.parte_id, o.tool_id, o.note,
                   p.part_number, p.descrizione_breve,
                   t.part_number_tool, t.descrizione as tool_desc
            FROM odl o
            LEFT JOIN parti p ON o.parte_id = p.id
            LEFT JOIN tools t ON o.tool_id = t.id
            WHERE o.status = 'Attesa Cura'
            ORDER BY o.id
        """))
        
        odl_data = result.fetchall()
        
        print(f"   Trovati {len(odl_data)} ODL in 'Attesa Cura'")
        print()
        
        for i, odl in enumerate(odl_data, 1):
            print(f"   {i}. ODL ID: {odl[0]}")
            print(f"      Status: '{odl[1]}' | Priorità: {odl[2]}")
            print(f"      Parte ID: {odl[3]} | Tool ID: {odl[4]}")
            print(f"      Note: {odl[5]}")
            
            # Verifica relazioni
            if odl[3] is None:
                print(f"      ❌ PROBLEMA: Parte ID è NULL")
            else:
                if odl[6] is None:
                    print(f"      ⚠️  PROBLEMA: Parte non trovata (ID {odl[3]})")
                else:
                    print(f"      ✅ Parte: {odl[6]} - {odl[7]}")
            
            if odl[4] is None:
                print(f"      ❌ PROBLEMA: Tool ID è NULL")
            else:
                if odl[8] is None:
                    print(f"      ⚠️  PROBLEMA: Tool non trovato (ID {odl[4]})")
                else:
                    print(f"      ✅ Tool: {odl[8]} - {odl[9]}")
            
            print()
        
        # 2. Verifica con SQLAlchemy ORM
        print("\n🔍 VERIFICA CON SQLALCHEMY ORM:")
        print("-"*50)
        
        odl_orm = db.query(ODL).filter(ODL.status == "Attesa Cura").all()
        print(f"   SQLAlchemy trova {len(odl_orm)} ODL")
        
        for i, odl in enumerate(odl_orm, 1):
            print(f"   {i}. ODL ID: {odl.id}")
            try:
                # Test accesso parte
                if hasattr(odl, 'parte') and odl.parte is not None:
                    print(f"      ✅ Parte: {odl.parte.part_number}")
                else:
                    print(f"      ❌ Parte: Non accessibile")
                
                # Test accesso tool
                if hasattr(odl, 'tool') and odl.tool is not None:
                    print(f"      ✅ Tool: {odl.tool.part_number_tool}")
                else:
                    print(f"      ❌ Tool: Non accessibile")
                    
            except Exception as e:
                print(f"      ❌ Errore accesso relazioni: {str(e)}")
        
        # 3. Test con joinedload (come nell'API)
        print("\n🔍 TEST CON JOINEDLOAD (come nell'API):")
        print("-"*50)
        
        from sqlalchemy.orm import joinedload
        from models.parte import Parte
        
        try:
            odl_joined = db.query(ODL).options(
                joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
                joinedload(ODL.tool)
            ).filter(
                ODL.status == "Attesa Cura"
            ).all()
            
            print(f"   Joinedload trova {len(odl_joined)} ODL")
            
            for i, odl in enumerate(odl_joined, 1):
                print(f"   {i}. ODL ID: {odl.id}")
                try:
                    if odl.parte:
                        print(f"      ✅ Parte: {odl.parte.part_number}")
                        if odl.parte.ciclo_cura:
                            print(f"      ✅ Ciclo cura: {odl.parte.ciclo_cura.nome}")
                        else:
                            print(f"      ⚠️  Ciclo cura: Non trovato")
                    else:
                        print(f"      ❌ Parte: Non trovata")
                    
                    if odl.tool:
                        print(f"      ✅ Tool: {odl.tool.part_number_tool}")
                    else:
                        print(f"      ❌ Tool: Non trovato")
                        
                except Exception as e:
                    print(f"      ❌ Errore joinedload: {str(e)}")
                    
        except Exception as e:
            print(f"   ❌ Errore query joinedload: {str(e)}")
        
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    main() 