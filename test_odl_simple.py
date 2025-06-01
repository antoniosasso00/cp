#!/usr/bin/env python3
"""
Test semplice per verificare il modello ODL
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool

# Configurazione database
DATABASE_URL = "sqlite:///./carbonpilot.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_odl_query():
    """
    Testa la query ODL per identificare il problema
    """
    print("🔍 Test Query ODL Diretta")
    print("=" * 40)
    
    db = SessionLocal()
    
    try:
        # Test 1: Query semplice senza relazioni
        print("📊 Test 1: Query ODL senza relazioni")
        odl_simple = db.query(ODL).first()
        if odl_simple:
            print(f"   ✅ ODL trovato: ID={odl_simple.id}, Status={odl_simple.status}")
        else:
            print("   ❌ Nessun ODL trovato")
        print()
        
        # Test 2: Query con relazioni
        print("📊 Test 2: Query ODL con relazioni")
        try:
            odl_with_relations = db.query(ODL).options(
                joinedload(ODL.parte),
                joinedload(ODL.tool)
            ).first()
            
            if odl_with_relations:
                print(f"   ✅ ODL con relazioni: ID={odl_with_relations.id}")
                print(f"   📋 Parte: {odl_with_relations.parte.part_number if odl_with_relations.parte else 'None'}")
                print(f"   🔧 Tool: {odl_with_relations.tool.part_number_tool if odl_with_relations.tool else 'None'}")
            else:
                print("   ❌ Nessun ODL con relazioni trovato")
        except Exception as e:
            print(f"   ❌ Errore query con relazioni: {str(e)}")
        print()
        
        # Test 3: Verifica integrità relazioni
        print("📊 Test 3: Verifica integrità relazioni")
        odl_list = db.query(ODL).all()
        
        for odl in odl_list[:5]:  # Testa solo i primi 5
            print(f"   ODL {odl.id}:")
            
            # Verifica parte
            if odl.parte_id:
                parte = db.query(Parte).filter(Parte.id == odl.parte_id).first()
                if parte:
                    print(f"     ✅ Parte {odl.parte_id}: {parte.part_number}")
                else:
                    print(f"     ❌ Parte {odl.parte_id}: NON TROVATA")
            else:
                print(f"     ⚠️ Parte: ID nullo")
            
            # Verifica tool
            if odl.tool_id:
                tool = db.query(Tool).filter(Tool.id == odl.tool_id).first()
                if tool:
                    print(f"     ✅ Tool {odl.tool_id}: {tool.part_number_tool}")
                else:
                    print(f"     ❌ Tool {odl.tool_id}: NON TROVATO")
            else:
                print(f"     ⚠️ Tool: ID nullo")
        
        print()
        
        # Test 4: Verifica stati
        print("📊 Test 4: Verifica stati ODL")
        from sqlalchemy import text
        result = db.execute(text("SELECT DISTINCT status FROM odl"))
        stati = [row[0] for row in result.fetchall()]
        print(f"   Stati trovati: {stati}")
        
        # Verifica se ci sono stati non validi
        stati_validi = ["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"]
        stati_non_validi = [s for s in stati if s not in stati_validi]
        
        if stati_non_validi:
            print(f"   ❌ Stati non validi: {stati_non_validi}")
        else:
            print(f"   ✅ Tutti gli stati sono validi")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_odl_query() 