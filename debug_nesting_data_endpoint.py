#!/usr/bin/env python3
"""
Debug specifico per l'endpoint /batch_nesting/data
"""
import sys
sys.path.append('./backend')

from backend.models.db import SessionLocal
from backend.models.odl import ODL
from backend.models.parte import Parte
from backend.models.ciclo_cura import CicloCura
from backend.models.tool import Tool
from sqlalchemy.orm import joinedload

def debug_nesting_data():
    """Debug specifico per l'endpoint /data"""
    
    print("🔍 DEBUG ENDPOINT /batch_nesting/data")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Test 1: Verifica se ci sono ODL
        print("\n📋 1. Verifica ODL nel database:")
        total_odl = db.query(ODL).count()
        print(f"   Totale ODL: {total_odl}")
        
        odl_attesa_cura = db.query(ODL).filter(ODL.status == "Attesa cura").count()
        print(f"   ODL 'Attesa cura': {odl_attesa_cura}")
        
        # Test 2: Verifica primo ODL con relazioni
        print("\n📋 2. Analisi primo ODL:")
        first_odl = db.query(ODL).first()
        if first_odl:
            print(f"   ID: {first_odl.id}")
            print(f"   Status: {first_odl.status}")
            print(f"   Parte ID: {first_odl.parte_id}")
            print(f"   Tool ID: {first_odl.tool_id}")
            
            # Test relazione parte
            print(f"   Parte caricata: {first_odl.parte is not None}")
            if first_odl.parte:
                print(f"   Parte - ID: {first_odl.parte.id}")
                print(f"   Parte - PN: {first_odl.parte.part_number}")
                print(f"   Ciclo cura ID: {first_odl.parte.ciclo_cura_id}")
                print(f"   Ciclo cura caricato: {first_odl.parte.ciclo_cura is not None}")
                
            # Test relazione tool
            print(f"   Tool caricato: {first_odl.tool is not None}")
            if first_odl.tool:
                print(f"   Tool - ID: {first_odl.tool.id}")
                print(f"   Tool - PN: {first_odl.tool.part_number_tool}")
        else:
            print("   ❌ Nessun ODL trovato!")
        
        # Test 3: Prova query con joinedload (simulando l'endpoint)
        print("\n📋 3. Test query con joinedload:")
        try:
            odl_with_relations = db.query(ODL).options(
                joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
                joinedload(ODL.tool)
            ).filter(ODL.status == "Attesa cura").first()
            
            if odl_with_relations:
                print(f"   ✅ Query joinedload riuscita")
                print(f"   ODL ID: {odl_with_relations.id}")
                if odl_with_relations.parte:
                    print(f"   Parte caricata: ✅")
                    if odl_with_relations.parte.ciclo_cura:
                        print(f"   Ciclo cura caricato: ✅")
                        print(f"   Ciclo cura nome: {odl_with_relations.parte.ciclo_cura.nome}")
                    else:
                        print(f"   Ciclo cura: ❌ None")
                else:
                    print(f"   Parte: ❌ None")
                    
                if odl_with_relations.tool:
                    print(f"   Tool caricato: ✅")
                else:
                    print(f"   Tool: ❌ None")
            else:
                print("   ❌ Nessun ODL 'Attesa cura' trovato")
                
        except Exception as e:
            print(f"   ❌ Errore query joinedload: {str(e)}")
            
        # Test 4: Simulazione logica endpoint
        print("\n📋 4. Simulazione logica endpoint:")
        try:
            odl_list = []
            odl_test = db.query(ODL).options(
                joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
                joinedload(ODL.tool)
            ).filter(ODL.status == "Attesa cura").all()
            
            for odl in odl_test:
                print(f"   Processando ODL {odl.id}...")
                
                # Test accesso parte
                parte_data = None
                if odl.parte:
                    print(f"     Parte OK: {odl.parte.id}")
                    
                    # Test accesso ciclo_cura
                    ciclo_cura_data = None
                    if odl.parte.ciclo_cura:
                        print(f"     Ciclo cura OK: {odl.parte.ciclo_cura.nome}")
                        ciclo_cura_data = {
                            "nome": odl.parte.ciclo_cura.nome,
                            "durata_stasi1": odl.parte.ciclo_cura.durata_stasi1,
                            "temperatura_stasi1": odl.parte.ciclo_cura.temperatura_stasi1,
                            "pressione_stasi1": odl.parte.ciclo_cura.pressione_stasi1
                        }
                    else:
                        print(f"     Ciclo cura: None")
                    
                    parte_data = {
                        "id": odl.parte.id,
                        "part_number": odl.parte.part_number,
                        "descrizione_breve": odl.parte.descrizione_breve,
                        "num_valvole_richieste": odl.parte.num_valvole_richieste,
                        "ciclo_cura": ciclo_cura_data
                    }
                else:
                    print(f"     Parte: None")
                
                # Test accesso tool
                tool_data = None
                if odl.tool:
                    print(f"     Tool OK: {odl.tool.id}")
                    tool_data = {
                        "id": odl.tool.id,
                        "part_number_tool": odl.tool.part_number_tool,
                        "descrizione": odl.tool.descrizione,
                        "larghezza_piano": odl.tool.larghezza_piano,
                        "lunghezza_piano": odl.tool.lunghezza_piano,
                        "peso": getattr(odl.tool, 'peso', 10.0),  # Default se peso non esiste
                        "disponibile": odl.tool.disponibile
                    }
                else:
                    print(f"     Tool: None")
                
                print(f"     ✅ ODL {odl.id} processato con successo")
            
            print(f"   ✅ Simulazione completata: {len(odl_test)} ODL processati")
            
        except Exception as e:
            print(f"   ❌ Errore simulazione: {str(e)}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Errore generale: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_nesting_data() 