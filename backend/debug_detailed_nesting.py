#!/usr/bin/env python3
"""
Debug dettagliato dell'algoritmo di nesting per capire perché non funziona
"""

import sys
sys.path.append('.')

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.odl import ODL
from models.tool import Tool
from models.autoclave import Autoclave
from models.parte import Parte
from models.ciclo_cura import CicloCura
from services.nesting_service import NestingService, NestingParameters

# Configura logging dettagliato
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_nesting_step_by_step():
    """Debug dettagliato passo-passo dell'algoritmo di nesting"""
    
    print("🔍 DEBUG DETTAGLIATO ALGORITMO NESTING")
    print("=" * 60)
    
    # Setup database
    engine = create_engine('sqlite:///./carbonpilot.db')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 1. Carica dati ODL con tutte le relazioni
        print("📋 STEP 1: CARICAMENTO DATI ODL")
        print("=" * 40)
        
        odls = db.query(ODL).join(Tool).join(Parte).outerjoin(CicloCura).all()
        
        print(f"ODL trovati: {len(odls)}")
        for odl in odls:
            print(f"\n• ODL {odl.id}:")
            print(f"  - Status: {odl.status}")
            print(f"  - Tool: {odl.tool.part_number_tool}")
            print(f"  - Tool dimensioni: {odl.tool.lunghezza_piano}x{odl.tool.larghezza_piano}mm")
            print(f"  - Tool peso: {odl.tool.peso}kg")
            print(f"  - Parte: {odl.parte.descrizione_breve}")
            print(f"  - Ciclo cura: {odl.parte.ciclo_cura.nome if odl.parte.ciclo_cura else 'NESSUNO'}")
        
        if not odls:
            print("❌ Nessun ODL trovato!")
            return False
        
        # 2. Carica dati autoclave
        print(f"\n🏭 STEP 2: CARICAMENTO DATI AUTOCLAVE")
        print("=" * 45)
        
        autoclavi = db.query(Autoclave).filter(Autoclave.stato == 'DISPONIBILE').all()
        
        for autoclave in autoclavi:
            print(f"\n• Autoclave {autoclave.id}: {autoclave.nome}")
            print(f"  - Dimensioni: {autoclave.larghezza_piano}x{autoclave.lunghezza}mm")
            print(f"  - Peso max: {autoclave.max_load_kg}kg")
            print(f"  - Stato: {autoclave.stato}")
        
        if not autoclavi:
            print("❌ Nessuna autoclave disponibile!")
            return False
        
        # 3. Test compatibilità manuale
        print(f"\n🔍 STEP 3: TEST COMPATIBILITÀ MANUALE")
        print("=" * 47)
        
        test_odl = odls[0]
        test_autoclave = autoclavi[0]
        
        tool_width = test_odl.tool.lunghezza_piano
        tool_height = test_odl.tool.larghezza_piano
        autoclave_width = test_autoclave.larghezza_piano
        autoclave_height = test_autoclave.lunghezza
        margin = 20
        
        print(f"Test ODL {test_odl.id} su autoclave {test_autoclave.nome}:")
        print(f"Tool: {tool_width}x{tool_height}mm")
        print(f"Autoclave: {autoclave_width}x{autoclave_height}mm")
        print(f"Margine: {margin}mm")
        
        # Test orientamenti
        normal_fits = (tool_width + margin <= autoclave_width and 
                      tool_height + margin <= autoclave_height)
        
        rotated_fits = (tool_height + margin <= autoclave_width and 
                       tool_width + margin <= autoclave_height)
        
        print(f"\nOrientamento normale ({tool_width}x{tool_height} + {margin}mm):")
        print(f"  Larghezza: {tool_width + margin} <= {autoclave_width} = {tool_width + margin <= autoclave_width}")
        print(f"  Altezza: {tool_height + margin} <= {autoclave_height} = {tool_height + margin <= autoclave_height}")
        print(f"  Risultato: {normal_fits}")
        
        print(f"\nOrientamento ruotato ({tool_height}x{tool_width} + {margin}mm):")
        print(f"  Larghezza: {tool_height + margin} <= {autoclave_width} = {tool_height + margin <= autoclave_width}")
        print(f"  Altezza: {tool_width + margin} <= {autoclave_height} = {tool_width + margin <= autoclave_height}")
        print(f"  Risultato: {rotated_fits}")
        
        if normal_fits or rotated_fits:
            print(f"✅ Tool può essere posizionato!")
        else:
            print(f"❌ Tool NON può essere posizionato in nessun orientamento")
            return False
        
        # 4. Test NestingService con logging attivato
        print(f"\n🧠 STEP 4: TEST NESTING SERVICE CON LOGGING")
        print("=" * 52)
        
        # Crea servizio con logging attivato
        nesting_service = NestingService()
        
        # Parametri ottimizzati
        parameters = NestingParameters(
            padding_mm=20,      # Margine ridotto
            min_distance_mm=15, # Distanza minima ridotta
            priorita_area=False # Massimizza numero ODL
        )
        
        print(f"Parametri nesting:")
        print(f"  - padding_mm: {parameters.padding_mm}")
        print(f"  - min_distance_mm: {parameters.min_distance_mm}")
        print(f"  - priorita_area: {parameters.priorita_area}")
        
        # Esegui nesting
        print(f"\nEsecuzione nesting...")
        
        result = nesting_service.generate_nesting(
            db=db,
            odl_ids=[test_odl.id],
            autoclave_id=test_autoclave.id,
            parameters=parameters
        )
        
        # 5. Analizza risultati dettagliati
        print(f"\n📊 STEP 5: ANALISI RISULTATI DETTAGLIATI")
        print("=" * 50)
        
        print(f"Successo: {result.success}")
        print(f"Status algoritmo: {result.algorithm_status}")
        print(f"ODL posizionati: {len(result.positioned_tools)}")
        print(f"ODL esclusi: {len(result.excluded_odls)}")
        print(f"Peso totale: {result.total_weight}kg")
        print(f"Area utilizzata: {result.used_area}")
        print(f"Area totale: {result.total_area}")
        print(f"Efficienza: {result.efficiency:.1f}%")
        
        if result.positioned_tools:
            print(f"\n✅ TOOL POSIZIONATI:")
            for tool_pos in result.positioned_tools:
                print(f"  • ODL {tool_pos.odl_id}: pos({tool_pos.x:.0f},{tool_pos.y:.0f}), dim({tool_pos.width:.0f}x{tool_pos.height:.0f}mm), ruotato={tool_pos.rotated}")
                
                # Verifica posizione
                if (tool_pos.x + tool_pos.width <= autoclave_width and 
                    tool_pos.y + tool_pos.height <= autoclave_height):
                    print(f"    ✅ Posizione valida")
                else:
                    print(f"    ❌ Posizione non valida!")
        
        if result.excluded_odls:
            print(f"\n❌ ODL ESCLUSI:")
            for excl in result.excluded_odls:
                print(f"  • ODL {excl['odl_id']}: {excl['motivo']}")
                if 'dettagli' in excl:
                    print(f"    Dettagli: {excl['dettagli']}")
        
        # 6. Test con parametri ancora più rilassati se fallisce
        if not result.positioned_tools:
            print(f"\n🔧 STEP 6: TENTATIVO CON PARAMETRI ULTRA-RILASSATI")
            print("=" * 57)
            
            relaxed_parameters = NestingParameters(
                padding_mm=5,       # Margine minimo
                min_distance_mm=5,  # Distanza minima molto ridotta
                priorita_area=False # Massimizza numero ODL
            )
            
            print(f"Parametri ultra-rilassati:")
            print(f"  - padding_mm: {relaxed_parameters.padding_mm}")
            print(f"  - min_distance_mm: {relaxed_parameters.min_distance_mm}")
            
            relaxed_result = nesting_service.generate_nesting(
                db=db,
                odl_ids=[test_odl.id],
                autoclave_id=test_autoclave.id,
                parameters=relaxed_parameters
            )
            
            print(f"\nRisultati con parametri rilassati:")
            print(f"  Successo: {relaxed_result.success}")
            print(f"  ODL posizionati: {len(relaxed_result.positioned_tools)}")
            print(f"  ODL esclusi: {len(relaxed_result.excluded_odls)}")
            
            if relaxed_result.positioned_tools:
                print(f"  ✅ FUNZIONA con parametri rilassati!")
                for tool_pos in relaxed_result.positioned_tools:
                    print(f"    • ODL {tool_pos.odl_id}: pos({tool_pos.x:.0f},{tool_pos.y:.0f}), dim({tool_pos.width:.0f}x{tool_pos.height:.0f}mm), ruotato={tool_pos.rotated}")
                return True
            else:
                print(f"  ❌ Non funziona nemmeno con parametri rilassati")
                for excl in relaxed_result.excluded_odls:
                    print(f"    • ODL {excl['odl_id']}: {excl['motivo']} - {excl.get('dettagli', '')}")
        else:
            print(f"\n✅ SUCCESS: L'algoritmo funziona correttamente!")
            return True
        
        return len(result.positioned_tools) > 0
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE IL DEBUG: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = debug_nesting_step_by_step()
    
    print(f"\n" + "=" * 60)
    print("📋 RIASSUNTO DEBUG:")
    print("=" * 60)
    
    if success:
        print("✅ L'algoritmo di nesting funziona!")
        print("🎉 Il fix della rotazione è efficace!")
    else:
        print("❌ L'algoritmo di nesting NON funziona")
        print("🔧 Sono necessarie ulteriori correzioni")
    
    print("\n�� DEBUG COMPLETATO") 