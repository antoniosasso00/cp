#!/usr/bin/env python3
"""
Test diretto dell'algoritmo di nesting enhanced
"""

from models.db import get_db
from models.odl import ODL
from models.autoclave import Autoclave
from nesting_optimizer.enhanced_nesting import compute_enhanced_nesting, NestingConstraints

def test_enhanced_nesting():
    """Testa l'algoritmo di nesting enhanced direttamente"""
    print("🧪 Test Algoritmo Nesting Enhanced")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        # Recupera ODL con stato "Attesa Cura"
        odl_list = db.query(ODL).filter(ODL.status == "Attesa Cura").limit(3).all()
        print(f"📦 ODL trovati: {len(odl_list)}")
        
        for odl in odl_list:
            print(f"   ODL {odl.id}: {odl.parte.part_number if odl.parte else 'N/A'} con {odl.tool.part_number_tool if odl.tool else 'N/A'}")
        
        if not odl_list:
            print("❌ Nessun ODL trovato con stato 'Attesa Cura'")
            return False
        
        # Recupera autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == 1).first()
        if not autoclave:
            print("❌ Autoclave con ID 1 non trovata")
            return False
        
        print(f"🏭 Autoclave: {autoclave.nome}")
        print(f"   Dimensioni: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
        print(f"   Superficie piano 2 max: {autoclave.superficie_piano_2_max} cm²")
        
        # Crea vincoli di default come dict
        constraints = {
            'distanza_minima_tool_mm': 10.0,
            'padding_bordo_mm': 20.0,
            'margine_sicurezza_peso_percent': 10.0,
            'priorita_minima': 1,
            'efficienza_minima_percent': 30.0
        }
        
        # Estrai solo gli ID - usa ODL compatibili
        odl_ids = [6, 7, 9]  # ODL con ciclo PRECISION_AUTOMOTIVE_190C
        
        print(f"\n🔧 Eseguo nesting per ODL: {odl_ids}")
        print(f"🔧 Autoclave ID: {autoclave.id}")
        
        # Esegui l'algoritmo
        result = compute_enhanced_nesting(
            odl_ids=odl_ids,
            autoclave_id=autoclave.id,
            constraints=constraints,
            db=db
        )
        
        print("\n✅ Risultato:")
        print(f"   Tipo risultato: {type(result)}")
        print(f"   Risultato: {result}")
        
        # Gestisce sia dict che oggetto
        if isinstance(result, dict):
            success = result.get('success', False)
            message = result.get('message', 'N/A')
            print(f"   Successo: {success}")
            print(f"   Messaggio: {message}")
        else:
            print(f"   Successo: {result.success}")
            print(f"   Messaggio: {result.message}")
            print(f"   ODL inclusi: {len(result.odl_inclusi)}")
            print(f"   ODL esclusi: {len(result.odl_esclusi)}")
            print(f"   Efficienza: {result.statistiche.efficienza_percent:.1f}%")
            print(f"   Peso totale: {result.statistiche.peso_totale_kg:.1f} kg")
        
            if result.odl_esclusi:
                print("\n⚠️ ODL esclusi:")
                for odl_escluso in result.odl_esclusi:
                    print(f"   ODL {odl_escluso.id}: {odl_escluso.motivo_esclusione}")
        
            if result.tool_positions:
                print(f"\n📍 Posizioni tool: {len(result.tool_positions)}")
                for pos in result.tool_positions[:3]:  # Mostra solo i primi 3
                    print(f"   ODL {pos.odl_id}: ({pos.x:.1f}, {pos.y:.1f}) - {pos.width:.1f}x{pos.height:.1f}mm")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_enhanced_nesting()
    if success:
        print("\n🎯 Test completato con successo!")
    else:
        print("\n❌ Test fallito!") 