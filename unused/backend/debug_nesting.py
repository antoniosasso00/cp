#!/usr/bin/env python3
"""
Script di debug per testare la validazione del nesting
"""

from sqlalchemy.orm import Session, joinedload
from models.db import SessionLocal
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.ciclo_cura import CicloCura

def debug_nesting_validation():
    """Debug della validazione nesting"""
    db = SessionLocal()
    
    try:
        print("🔍 DEBUG NESTING VALIDATION")
        print("=" * 50)
        
        # 1. Verifica ODL #1
        print("\n1. Verifica ODL #1:")
        odl = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo),
            joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
            joinedload(ODL.tool)
        ).filter(ODL.id == 1).first()
        
        if not odl:
            print("❌ ODL #1 non trovato")
            return
        
        print(f"✅ ODL #1 trovato - Status: {odl.status}")
        print(f"   Priorità: {odl.priorita}")
        
        # 2. Verifica parte
        print("\n2. Verifica parte:")
        if not odl.parte:
            print("❌ Parte non definita")
            return
        
        print(f"✅ Parte: {odl.parte.part_number}")
        print(f"   Descrizione: {odl.parte.descrizione_breve}")
        print(f"   Valvole richieste: {odl.parte.num_valvole_richieste}")
        
        # 3. Verifica ciclo di cura
        print("\n3. Verifica ciclo di cura:")
        if not odl.parte.ciclo_cura:
            print("❌ Ciclo di cura non assegnato")
            return
        
        print(f"✅ Ciclo di cura: {odl.parte.ciclo_cura.nome} (ID: {odl.parte.ciclo_cura.id})")
        print(f"   Temperatura max: {odl.parte.ciclo_cura.temperatura_max}°C")
        print(f"   Pressione max: {odl.parte.ciclo_cura.pressione_max} bar")
        
        # 4. Verifica tool
        print("\n4. Verifica tool:")
        if not odl.tool:
            print("❌ Tool non assegnato")
            return
        
        print(f"✅ Tool: {odl.tool.part_number_tool}")
        print(f"   Descrizione: {odl.tool.descrizione}")
        print(f"   Dimensioni: {odl.tool.lunghezza_piano}x{odl.tool.larghezza_piano}mm")
        print(f"   Area: {odl.tool.area:.1f} cm²")
        print(f"   Peso: {odl.tool.peso} kg")
        print(f"   Disponibile: {odl.tool.disponibile}")
        
        # 5. Verifica autoclavi
        print("\n5. Verifica autoclavi disponibili:")
        autoclavi = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).all()
        
        if not autoclavi:
            print("❌ Nessuna autoclave disponibile")
            return
        
        print(f"✅ Trovate {len(autoclavi)} autoclavi disponibili:")
        
        for autoclave in autoclavi:
            print(f"\n   Autoclave: {autoclave.nome}")
            print(f"   - Area piano: {autoclave.area_piano} cm²")
            print(f"   - Valvole: {autoclave.num_linee_vuoto}")
            print(f"   - Carico max: {autoclave.max_load_kg} kg")
            print(f"   - Temperatura max: {autoclave.temperatura_max}°C")
            print(f"   - Pressione max: {autoclave.pressione_max} bar")
            print(f"   - Piano secondario: {autoclave.use_secondary_plane}")
            
            # Verifica compatibilità
            ciclo = odl.parte.ciclo_cura
            compatibile_temp = ciclo.temperatura_max <= autoclave.temperatura_max
            compatibile_press = ciclo.pressione_max <= autoclave.pressione_max
            compatibile_area = odl.tool.area <= autoclave.area_piano
            compatibile_valvole = odl.parte.num_valvole_richieste <= autoclave.num_linee_vuoto
            compatibile_peso = (odl.tool.peso or 0.5) <= autoclave.max_load_kg
            
            print(f"   - Compatibilità temperatura: {compatibile_temp} ({ciclo.temperatura_max} <= {autoclave.temperatura_max})")
            print(f"   - Compatibilità pressione: {compatibile_press} ({ciclo.pressione_max} <= {autoclave.pressione_max})")
            print(f"   - Compatibilità area: {compatibile_area} ({odl.tool.area:.1f} <= {autoclave.area_piano})")
            print(f"   - Compatibilità valvole: {compatibile_valvole} ({odl.parte.num_valvole_richieste} <= {autoclave.num_linee_vuoto})")
            print(f"   - Compatibilità peso: {compatibile_peso} ({odl.tool.peso or 0.5} <= {autoclave.max_load_kg})")
            
            if all([compatibile_temp, compatibile_press, compatibile_area, compatibile_valvole, compatibile_peso]):
                print(f"   ✅ AUTOCLAVE COMPATIBILE!")
            else:
                print(f"   ❌ Autoclave non compatibile")
        
        print("\n" + "=" * 50)
        print("Debug completato!")
        
    except Exception as e:
        print(f"❌ Errore durante il debug: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    debug_nesting_validation() 