#!/usr/bin/env python3
"""
Test completo per il nesting su due piani - algoritmo e API
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import get_db
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.tool import Tool
from models.odl import ODL
from models.parte import Parte
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura
from nesting_optimizer.two_level_nesting import compute_two_level_nesting
from services.nesting_service import run_two_level_nesting
from sqlalchemy.orm import joinedload

async def create_test_data(db):
    """Crea dati di test per il nesting su due piani"""
    
    # Crea un ciclo di cura di test con nome unico
    import time
    timestamp = int(time.time())
    ciclo_cura = CicloCura(
        nome=f"Test Ciclo API {timestamp}",
        temperatura_stasi1=120.0,
        pressione_stasi1=2.0,
        durata_stasi1=180,
        attiva_stasi2=False,
        descrizione="Ciclo di test per nesting API"
    )
    db.add(ciclo_cura)
    db.flush()
    
    # Crea un'autoclave di test con carico massimo
    autoclave = Autoclave(
        nome=f"Autoclave API Test {timestamp}",
        codice=f"AC-API-{timestamp}",
        lunghezza=2000.0,  # 2000mm
        larghezza_piano=1500.0,  # 1500mm
        num_linee_vuoto=10,
        temperatura_max=200.0,
        pressione_max=5.0,
        max_load_kg=500.0,  # 500kg di carico massimo
        stato=StatoAutoclaveEnum.DISPONIBILE
    )
    db.add(autoclave)
    db.flush()
    
    # Crea tool di test con pesi diversi
    tools_data = [
        {"part_number": f"TOOL-HEAVY-API-01-{timestamp}", "peso": 15.0, "lunghezza": 400, "larghezza": 300, "materiale": "Acciaio"},
        {"part_number": f"TOOL-HEAVY-API-02-{timestamp}", "peso": 12.0, "lunghezza": 350, "larghezza": 250, "materiale": "Acciaio"},
        {"part_number": f"TOOL-MEDIUM-API-01-{timestamp}", "peso": 8.0, "lunghezza": 300, "larghezza": 200, "materiale": "Alluminio"},
        {"part_number": f"TOOL-MEDIUM-API-02-{timestamp}", "peso": 6.0, "lunghezza": 250, "larghezza": 180, "materiale": "Alluminio"},
        {"part_number": f"TOOL-LIGHT-API-01-{timestamp}", "peso": 3.0, "lunghezza": 200, "larghezza": 150, "materiale": "Alluminio"},
        {"part_number": f"TOOL-LIGHT-API-02-{timestamp}", "peso": 2.5, "lunghezza": 180, "larghezza": 120, "materiale": "Alluminio"},
    ]
    
    tools = []
    for tool_data in tools_data:
        tool = Tool(
            part_number_tool=tool_data["part_number"],
            descrizione=f"Tool di test API {tool_data['part_number']}",
            lunghezza_piano=tool_data["lunghezza"],
            larghezza_piano=tool_data["larghezza"],
            peso=tool_data["peso"],
            materiale=tool_data["materiale"],
            disponibile=True
        )
        db.add(tool)
        tools.append(tool)
    
    db.flush()
    
    # Crea cataloghi e parti di test
    odl_list = []
    for i, tool in enumerate(tools):
        # Crea catalogo
        catalogo = Catalogo(
            part_number=f"PART-API-{i+1:03d}-{timestamp}",
            descrizione=f"Parte di test API {i+1}",
            lunghezza=tool.lunghezza_piano,  # Lunghezza in mm
            larghezza=tool.larghezza_piano,  # Larghezza in mm
            categoria="Test",
            sotto_categoria="Nesting API"
        )
        db.add(catalogo)
        db.flush()
        
        # Crea parte
        parte = Parte(
            part_number=catalogo.part_number,  # Usa part_number come chiave
            descrizione_breve=f"Parte test API {i+1}",
            ciclo_cura_id=ciclo_cura.id,
            num_valvole_richieste=2
        )
        db.add(parte)
        db.flush()
        
        # Crea ODL in stato "Attesa Cura"
        odl = ODL(
            parte_id=parte.id,
            tool_id=tool.id,
            priorita=i+1,
            status="Attesa Cura",
            note=f"ODL di test API per tool {tool.part_number_tool}"
        )
        db.add(odl)
        odl_list.append(odl)
    
    db.commit()
    return autoclave, odl_list

async def test_algorithm_directly(db, autoclave, odl_list):
    """Test diretto dell'algoritmo di nesting"""
    print("\n🔬 Test diretto dell'algoritmo")
    print("-" * 40)
    
    # Test con superficie piano 2 limitata (60% del piano 1)
    superficie_piano_2_max = autoclave.area_piano * 0.6
    print(f"   Superficie piano 2 max: {superficie_piano_2_max:.2f} cm²")
    
    result = compute_two_level_nesting(
        db=db,
        odl_list=odl_list,
        autoclave=autoclave,
        superficie_piano_2_max_cm2=superficie_piano_2_max
    )
    
    print(f"   ✅ Algoritmo completato")
    print(f"   Carico valido: {'✅ Sì' if result.carico_valido else '❌ No'}")
    print(f"   Peso totale: {result.peso_totale:.2f} kg")
    print(f"   Piano 1: {len(result.piano_1)} ODL, {result.peso_piano_1:.2f} kg")
    print(f"   Piano 2: {len(result.piano_2)} ODL, {result.peso_piano_2:.2f} kg")
    
    return result

async def test_service_layer(db, autoclave, odl_list):
    """Test del servizio di nesting"""
    print("\n🔧 Test del servizio di nesting")
    print("-" * 40)
    
    # Estrai gli ID degli ODL
    odl_ids = [odl.id for odl in odl_list]
    superficie_piano_2_max = autoclave.area_piano * 0.6
    
    try:
        result = await run_two_level_nesting(
            db=db,
            autoclave_id=autoclave.id,
            odl_ids=odl_ids,
            superficie_piano_2_max_cm2=superficie_piano_2_max,
            note="Test del servizio di nesting su due piani"
        )
        
        print(f"   ✅ Servizio completato")
        print(f"   Nesting ID: {result['nesting_id']}")
        print(f"   Success: {result['success']}")
        print(f"   Message: {result['message']}")
        print(f"   Peso totale: {result['statistiche']['peso_totale_kg']:.2f} kg")
        print(f"   Piano 1: {result['piano_1']['odl_count']} ODL, {result['piano_1']['peso_kg']:.2f} kg")
        print(f"   Piano 2: {result['piano_2']['odl_count']} ODL, {result['piano_2']['peso_kg']:.2f} kg")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Errore nel servizio: {e}")
        return None

async def test_api_simulation(db, autoclave, odl_list):
    """Simula una chiamata API"""
    print("\n🌐 Simulazione chiamata API")
    print("-" * 40)
    
    # Prepara i dati della richiesta come se arrivassero dall'API
    request_data = {
        "autoclave_id": autoclave.id,
        "odl_ids": [odl.id for odl in odl_list],
        "superficie_piano_2_max_cm2": autoclave.area_piano * 0.6,
        "note": "Test simulazione API per nesting su due piani"
    }
    
    print(f"   📤 Request data:")
    print(f"      autoclave_id: {request_data['autoclave_id']}")
    print(f"      odl_ids: {request_data['odl_ids']}")
    print(f"      superficie_piano_2_max_cm2: {request_data['superficie_piano_2_max_cm2']:.2f}")
    
    try:
        # Simula la chiamata al servizio (come farebbe l'endpoint API)
        result = await run_two_level_nesting(
            db=db,
            autoclave_id=request_data["autoclave_id"],
            odl_ids=request_data["odl_ids"],
            superficie_piano_2_max_cm2=request_data["superficie_piano_2_max_cm2"],
            note=request_data["note"]
        )
        
        print(f"   📥 Response:")
        print(f"      success: {result['success']}")
        print(f"      nesting_id: {result['nesting_id']}")
        print(f"      message: {result['message']}")
        
        # Mostra statistiche dettagliate
        stats = result['statistiche']
        print(f"   📊 Statistiche:")
        print(f"      peso_totale_kg: {stats['peso_totale_kg']:.2f}")
        print(f"      efficienza_piano_1: {stats['efficienza_piano_1']:.1f}%")
        print(f"      efficienza_piano_2: {stats['efficienza_piano_2']:.1f}%")
        print(f"      efficienza_totale: {stats['efficienza_totale']:.1f}%")
        print(f"      carico_valido: {stats['carico_valido']}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Errore nella simulazione API: {e}")
        return None

async def main():
    db = next(get_db())
    
    try:
        print("🧪 Test completo del nesting su due piani")
        print("=" * 60)
        
        # Crea dati di test
        print("📝 Creazione dati di test...")
        autoclave, odl_list = await create_test_data(db)
        
        print(f"✅ Autoclave creata: {autoclave.nome} (max_load: {autoclave.max_load_kg}kg)")
        print(f"✅ {len(odl_list)} ODL creati con tool di pesi diversi")
        
        # Mostra i tool e i loro pesi
        print("\n🔧 Tool creati:")
        for odl in odl_list:
            tool = odl.tool
            print(f"  - {tool.part_number_tool}: {tool.peso}kg, {tool.lunghezza_piano}x{tool.larghezza_piano}mm, {tool.materiale}")
        
        # Test 1: Algoritmo diretto
        algorithm_result = await test_algorithm_directly(db, autoclave, odl_list)
        
        # Test 2: Servizio di nesting
        service_result = await test_service_layer(db, autoclave, odl_list)
        
        # Test 3: Simulazione API
        api_result = await test_api_simulation(db, autoclave, odl_list)
        
        # Riepilogo finale
        print(f"\n📋 Riepilogo test:")
        print(f"   Algoritmo diretto: {'✅ OK' if algorithm_result else '❌ FAIL'}")
        print(f"   Servizio nesting: {'✅ OK' if service_result else '❌ FAIL'}")
        print(f"   Simulazione API: {'✅ OK' if api_result else '❌ FAIL'}")
        
        if all([algorithm_result, service_result, api_result]):
            print(f"\n🎉 Tutti i test sono passati con successo!")
            print(f"   Il nesting su due piani è completamente funzionale!")
        else:
            print(f"\n⚠️ Alcuni test sono falliti. Controllare i log sopra.")
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 