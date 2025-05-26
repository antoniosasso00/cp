#!/usr/bin/env python3
"""
Script di test per il nesting su due piani
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import get_db
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.tool import Tool
from models.odl import ODL
from models.parte import Parte
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura
from nesting_optimizer.two_level_nesting import compute_two_level_nesting
from sqlalchemy.orm import joinedload

def create_test_data(db):
    """Crea dati di test per il nesting su due piani"""
    
    # Crea un ciclo di cura di test
    ciclo_cura = CicloCura(
        nome="Test Ciclo",
        temperatura_stasi1=120.0,
        pressione_stasi1=2.0,
        durata_stasi1=180,
        attiva_stasi2=False,
        descrizione="Ciclo di test per nesting"
    )
    db.add(ciclo_cura)
    db.flush()
    
    # Crea un'autoclave di test con carico massimo
    autoclave = Autoclave(
        nome="Autoclave Test",
        codice="AC-TEST-01",
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
        {"part_number": "TOOL-HEAVY-01", "peso": 15.0, "lunghezza": 400, "larghezza": 300, "materiale": "Acciaio"},
        {"part_number": "TOOL-HEAVY-02", "peso": 12.0, "lunghezza": 350, "larghezza": 250, "materiale": "Acciaio"},
        {"part_number": "TOOL-MEDIUM-01", "peso": 8.0, "lunghezza": 300, "larghezza": 200, "materiale": "Alluminio"},
        {"part_number": "TOOL-MEDIUM-02", "peso": 6.0, "lunghezza": 250, "larghezza": 180, "materiale": "Alluminio"},
        {"part_number": "TOOL-LIGHT-01", "peso": 3.0, "lunghezza": 200, "larghezza": 150, "materiale": "Alluminio"},
        {"part_number": "TOOL-LIGHT-02", "peso": 2.5, "lunghezza": 180, "larghezza": 120, "materiale": "Alluminio"},
    ]
    
    tools = []
    for tool_data in tools_data:
        tool = Tool(
            part_number_tool=tool_data["part_number"],
            descrizione=f"Tool di test {tool_data['part_number']}",
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
            part_number=f"PART-{i+1:03d}",
            descrizione=f"Parte di test {i+1}",
            lunghezza=tool.lunghezza_piano,  # Lunghezza in mm
            larghezza=tool.larghezza_piano,  # Larghezza in mm
            categoria="Test",
            sotto_categoria="Nesting"
        )
        db.add(catalogo)
        db.flush()
        
        # Crea parte
        parte = Parte(
            part_number=catalogo.part_number,  # Usa part_number come chiave
            descrizione_breve=f"Parte test {i+1}",
            ciclo_cura_id=ciclo_cura.id,
            num_valvole_richieste=2
        )
        db.add(parte)
        db.flush()
        
        # Crea ODL
        odl = ODL(
            parte_id=parte.id,
            tool_id=tool.id,
            priorita=i+1,
            status="Attesa Cura",
            note=f"ODL di test per tool {tool.part_number_tool}"
        )
        db.add(odl)
        odl_list.append(odl)
    
    db.commit()
    return autoclave, odl_list

def main():
    db = next(get_db())
    
    try:
        print("🧪 Test del nesting su due piani")
        print("=" * 50)
        
        # Crea dati di test
        print("📝 Creazione dati di test...")
        autoclave, odl_list = create_test_data(db)
        
        print(f"✅ Autoclave creata: {autoclave.nome} (max_load: {autoclave.max_load_kg}kg)")
        print(f"✅ {len(odl_list)} ODL creati con tool di pesi diversi")
        
        # Mostra i tool e i loro pesi
        print("\n🔧 Tool creati:")
        for odl in odl_list:
            tool = odl.tool
            print(f"  - {tool.part_number_tool}: {tool.peso}kg, {tool.lunghezza_piano}x{tool.larghezza_piano}mm, {tool.materiale}")
        
        # Esegui il nesting su due piani
        print(f"\n🎯 Esecuzione nesting su due piani...")
        print(f"   Autoclave: {autoclave.nome}")
        print(f"   Area piano: {autoclave.area_piano:.2f} cm²")
        print(f"   Carico massimo: {autoclave.max_load_kg} kg")
        
        # Test con superficie piano 2 limitata (60% del piano 1)
        superficie_piano_2_max = autoclave.area_piano * 0.6
        print(f"   Superficie piano 2 max: {superficie_piano_2_max:.2f} cm²")
        
        result = compute_two_level_nesting(
            db=db,
            odl_list=odl_list,
            autoclave=autoclave,
            superficie_piano_2_max_cm2=superficie_piano_2_max
        )
        
        # Mostra i risultati
        print(f"\n📊 Risultati del nesting:")
        print(f"   Carico valido: {'✅ Sì' if result.carico_valido else '❌ No'}")
        if not result.carico_valido:
            print(f"   Motivo: {result.motivo_invalidita}")
        
        print(f"   Peso totale: {result.peso_totale:.2f} kg")
        print(f"   Piano 1: {len(result.piano_1)} ODL, {result.peso_piano_1:.2f} kg, {result.area_piano_1:.2f} cm²")
        print(f"   Piano 2: {len(result.piano_2)} ODL, {result.peso_piano_2:.2f} kg, {result.area_piano_2:.2f} cm²")
        print(f"   Non pianificabili: {len(result.odl_non_pianificabili)} ODL")
        
        # Dettagli per piano
        if result.piano_1:
            print(f"\n🔽 Piano 1 (inferiore) - ODL pesanti/grandi:")
            for odl_id in result.piano_1:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                tool = odl.tool
                print(f"   - ODL {odl_id}: {tool.part_number_tool} ({tool.peso}kg)")
        
        if result.piano_2:
            print(f"\n🔼 Piano 2 (superiore) - ODL leggeri/piccoli:")
            for odl_id in result.piano_2:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                tool = odl.tool
                print(f"   - ODL {odl_id}: {tool.part_number_tool} ({tool.peso}kg)")
        
        if result.odl_non_pianificabili:
            print(f"\n❌ ODL non pianificabili:")
            for item in result.odl_non_pianificabili:
                print(f"   - ODL {item['odl_id']}: {item['motivo']}")
        
        # Test posizionamento 2D
        print(f"\n📐 Posizionamento 2D:")
        print(f"   Piano 1: {len(result.posizioni_piano_1)} tool posizionati")
        print(f"   Piano 2: {len(result.posizioni_piano_2)} tool posizionati")
        
        # Test con carico eccessivo
        print(f"\n🧪 Test con carico eccessivo...")
        # Modifica temporaneamente il carico massimo
        autoclave.max_load_kg = 20.0  # Molto basso per forzare errore
        
        result_overload = compute_two_level_nesting(
            db=db,
            odl_list=odl_list,
            autoclave=autoclave
        )
        
        print(f"   Carico valido: {'✅ Sì' if result_overload.carico_valido else '❌ No'}")
        if not result_overload.carico_valido:
            print(f"   Motivo: {result_overload.motivo_invalidita}")
        
        print(f"\n✅ Test completato con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 