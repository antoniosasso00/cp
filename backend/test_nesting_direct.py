#!/usr/bin/env python3
"""
Test diretto dell'algoritmo di nesting senza server HTTP
"""

import sys
import os
from datetime import datetime

# Aggiungi il percorso del backend al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.nesting_service import NestingService, NestingParameters
from api.database import get_db

def test_nesting_direct():
    """
    Testa l'algoritmo di nesting direttamente
    """
    print("🧠 Test Diretto Algoritmo di Nesting OR-Tools")
    print("=" * 50)
    
    try:
        # Crea il servizio di nesting
        nesting_service = NestingService()
        
        # Parametri di test
        parameters = NestingParameters(
            padding_mm=20,
            min_distance_mm=15,
            priorita_area=True,
            accorpamento_odl=False
        )
        
        # Ottieni una sessione del database
        db = next(get_db())
        
        # ODL di test (assumiamo che esistano nel database)
        odl_ids = [1, 2, 3]
        autoclave_id = 1
        
        print(f"📤 Test con parametri:")
        print(f"   ODL: {odl_ids}")
        print(f"   Autoclave: {autoclave_id}")
        print(f"   Parametri: padding={parameters.padding_mm}mm, distanza={parameters.min_distance_mm}mm")
        print(f"   Priorità area: {parameters.priorita_area}")
        print()
        
        # Esegui l'algoritmo di nesting
        print("🚀 Avvio algoritmo di nesting...")
        result = nesting_service.generate_nesting(
            db=db,
            odl_ids=odl_ids,
            autoclave_id=autoclave_id,
            parameters=parameters
        )
        
        print("✅ Algoritmo completato!")
        print()
        print("📊 Risultati:")
        print(f"   Successo: {result.success}")
        print(f"   Status algoritmo: {result.algorithm_status}")
        print(f"   ODL posizionati: {len(result.positioned_tools)}")
        print(f"   ODL esclusi: {len(result.excluded_odls)}")
        print(f"   Efficienza: {result.efficiency:.1f}%")
        print(f"   Peso totale: {result.total_weight:.1f} kg")
        print(f"   Area utilizzata: {result.used_area:.0f} mm²")
        print(f"   Area totale: {result.total_area:.0f} mm²")
        print()
        
        # Dettagli tool posizionati
        if result.positioned_tools:
            print("🔧 Tool posizionati:")
            for i, tool in enumerate(result.positioned_tools, 1):
                print(f"   {i}. ODL {tool.odl_id}: posizione ({tool.x:.1f}, {tool.y:.1f}), dimensioni {tool.width:.1f}x{tool.height:.1f}mm, peso {tool.peso:.1f}kg")
        
        # Dettagli esclusioni
        if result.excluded_odls:
            print()
            print("❌ ODL esclusi:")
            for i, excluded in enumerate(result.excluded_odls, 1):
                print(f"   {i}. ODL {excluded['odl_id']}: {excluded['motivo']} - {excluded['dettagli']}")
        
        print()
        if result.success:
            print("✅ Test completato con successo!")
            return True
        else:
            print("⚠️ Test completato ma senza successo nell'algoritmo")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante il test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    """
    Funzione principale
    """
    print(f"🕐 Avvio test alle {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    success = test_nesting_direct()
    
    print()
    if success:
        print("🎉 Test completato con successo!")
        sys.exit(0)
    else:
        print("💥 Test fallito!")
        sys.exit(1)

if __name__ == "__main__":
    main() 