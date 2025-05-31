#!/usr/bin/env python3
"""
Script per verificare i cicli di cura degli ODL
"""

from models.db import get_db
from models.odl import ODL

def check_odl_cycles():
    """Verifica i cicli di cura degli ODL"""
    db = next(get_db())
    
    try:
        # Recupera ODL con stato "Attesa Cura"
        odl_list = db.query(ODL).filter(ODL.status == "Attesa Cura").all()
        print(f"📦 ODL con stato 'Attesa Cura': {len(odl_list)}")
        print("=" * 60)
        
        cycles_map = {}
        
        for odl in odl_list:
            cycle_name = "N/A"
            if odl.parte and odl.parte.ciclo_cura:
                cycle_name = odl.parte.ciclo_cura.nome
            
            if cycle_name not in cycles_map:
                cycles_map[cycle_name] = []
            cycles_map[cycle_name].append(odl)
            
            print(f"ODL {odl.id:2d}: {odl.parte.part_number if odl.parte else 'N/A':20s} -> {cycle_name}")
        
        print("\n🔄 Raggruppamento per ciclo di cura:")
        print("=" * 60)
        
        for cycle, odl_group in cycles_map.items():
            print(f"\n📋 Ciclo: {cycle}")
            print(f"   ODL compatibili: {[odl.id for odl in odl_group]}")
            if len(odl_group) >= 2:
                print(f"   ✅ Gruppo valido per nesting ({len(odl_group)} ODL)")
            else:
                print(f"   ⚠️ Gruppo troppo piccolo per nesting ({len(odl_group)} ODL)")
        
        # Trova il gruppo più grande
        largest_group = max(cycles_map.values(), key=len) if cycles_map else []
        if len(largest_group) >= 2:
            print(f"\n🎯 Gruppo consigliato per test nesting:")
            print(f"   Ciclo: {largest_group[0].parte.ciclo_cura.nome if largest_group[0].parte and largest_group[0].parte.ciclo_cura else 'N/A'}")
            print(f"   ODL IDs: {[odl.id for odl in largest_group[:3]]}")  # Prendi i primi 3
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_odl_cycles() 