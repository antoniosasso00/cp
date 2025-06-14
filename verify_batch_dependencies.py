#!/usr/bin/env python3
"""
Script per verificare le dipendenze del batch che sta fallendo
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.database import get_db
from models.batch_nesting import BatchNesting
from models.autoclave import Autoclave
from models.odl import ODL

def check_batch_dependencies():
    """Verifica le dipendenze del batch problematico"""
    print("🔍 === VERIFICA DIPENDENZE BATCH ===")
    
    try:
        db = next(get_db())
        batch_id = 'e187ce8d-ed33-4609-a6ab-b03591ab7488'
        
        # 1. Carica il batch
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            print("❌ Batch non trovato!")
            return
            
        print(f"✅ Batch trovato: {batch.nome}")
        print(f"   ODL IDs: {batch.odl_ids}")
        print(f"   Autoclave ID: {batch.autoclave_id}")
        
        # 2. Verifica autoclave
        if batch.autoclave_id:
            autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
            if autoclave:
                print(f"✅ Autoclave trovata: {autoclave.nome}")
            else:
                print(f"❌ Autoclave ID {batch.autoclave_id} NON TROVATA!")
        
        # 3. Verifica ODL
        if batch.odl_ids:
            print(f"\n🔍 Verifica ODL...")
            for odl_id in batch.odl_ids:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                if odl:
                    print(f"   ✅ ODL {odl_id}: {odl.numero_odl}")
                    if odl.parte:
                        print(f"      Parte: {odl.parte.part_number}")
                    else:
                        print(f"      ⚠️ ODL senza parte associata!")
                    if odl.tool:
                        print(f"      Tool: {odl.tool.part_number_tool}")
                    else:
                        print(f"      ⚠️ ODL senza tool associato!")
                else:
                    print(f"   ❌ ODL {odl_id} NON TROVATO!")
        
        # 4. Verifica configurazione JSON
        print(f"\n🔍 Verifica configurazione JSON...")
        if batch.configurazione_json:
            config_keys = list(batch.configurazione_json.keys())
            print(f"   ✅ Configurazione presente con keys: {config_keys}")
            
            # Verifica tool_positions
            tool_pos = batch.configurazione_json.get('tool_positions', [])
            positioned_tools = batch.configurazione_json.get('positioned_tools', [])
            print(f"   Tool positions: {len(tool_pos)}")
            print(f"   Positioned tools: {len(positioned_tools)}")
        else:
            print(f"   ⚠️ Configurazione JSON mancante!")
            
        print(f"\n📊 === RISULTATO VERIFICA ===")
        print(f"Batch: ✅")
        print(f"Autoclave: {'✅' if batch.autoclave_id and db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first() else '❌'}")
        print(f"ODL: {'✅' if all(db.query(ODL).filter(ODL.id == odl_id).first() for odl_id in (batch.odl_ids or [])) else '❌'}")
        print(f"Configurazione: {'✅' if batch.configurazione_json else '❌'}")
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_batch_dependencies() 