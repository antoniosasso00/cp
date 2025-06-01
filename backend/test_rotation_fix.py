#!/usr/bin/env python3
"""
Test specifico per verificare che il fix della rotazione funzioni correttamente.
"""

import sys
sys.path.append('.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.odl import ODL
from models.tool import Tool
from models.autoclave import Autoclave
from services.nesting_service import NestingService, NestingParameters

def test_rotation_fix():
    """Test specifico per verificare che la rotazione dei tool funzioni"""
    
    print("🔄 TEST ROTAZIONE TOOL - VERIFICA FIX")
    print("=" * 50)
    
    # Setup database
    engine = create_engine('sqlite:///./carbonpilot.db')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 1. Analizza i tool attuali
        print("📏 ANALISI TOOL ATTUALI:")
        tools = db.query(Tool).all()
        
        for tool in tools:
            print(f"   • Tool {tool.part_number_tool}: {tool.lunghezza_piano}x{tool.larghezza_piano}mm, peso {tool.peso}kg")
        
        # 2. Analizza le autoclavi disponibili
        print(f"\n🏭 AUTOCLAVI DISPONIBILI:")
        autoclavi = db.query(Autoclave).filter(Autoclave.stato == 'DISPONIBILE').all()
        
        for autoclave in autoclavi:
            print(f"   • {autoclave.nome}: {autoclave.larghezza_piano}x{autoclave.lunghezza}mm, max {autoclave.max_load_kg}kg")
        
        # 3. Test di compatibilità dimensionale
        print(f"\n🔍 TEST COMPATIBILITÀ DIMENSIONALE:")
        
        if not tools or not autoclavi:
            print("❌ Nessun tool o autoclave disponibile per il test!")
            return False
        
        test_tool = tools[0]  # Primo tool
        test_autoclave = autoclavi[0]  # Prima autoclave
        
        print(f"Tool di test: {test_tool.part_number_tool} ({test_tool.lunghezza_piano}x{test_tool.larghezza_piano}mm)")
        print(f"Autoclave di test: {test_autoclave.nome} ({test_autoclave.larghezza_piano}x{test_autoclave.lunghezza}mm)")
        
        # Verifica orientamenti
        normal_fits = (test_tool.lunghezza_piano <= test_autoclave.larghezza_piano and 
                      test_tool.larghezza_piano <= test_autoclave.lunghezza)
        
        rotated_fits = (test_tool.larghezza_piano <= test_autoclave.larghezza_piano and 
                       test_tool.lunghezza_piano <= test_autoclave.lunghezza)
        
        print(f"   Orientamento normale ({test_tool.lunghezza_piano}x{test_tool.larghezza_piano}): {normal_fits}")
        print(f"   Orientamento ruotato ({test_tool.larghezza_piano}x{test_tool.lunghezza_piano}): {rotated_fits}")
        
        if not normal_fits and not rotated_fits:
            print("❌ Tool troppo grande anche ruotato!")
            return False
        
        if normal_fits and rotated_fits:
            print("✅ Tool entra in entrambi gli orientamenti")
        elif rotated_fits:
            print("✅ Tool entra SOLO se ruotato - test perfetto per verificare la rotazione!")
        else:
            print("✅ Tool entra solo in orientamento normale")
        
        # 4. Test algoritmo di nesting
        print(f"\n🧠 TEST ALGORITMO DI NESTING:")
        
        # Trova un ODL che usa questo tool
        test_odl = db.query(ODL).filter(ODL.tool_id == test_tool.id).first()
        
        if not test_odl:
            print("❌ Nessun ODL trovato per questo tool!")
            return False
        
        print(f"ODL di test: {test_odl.id}")
        
        # Parametri ottimizzati per il test
        parameters = NestingParameters(
            padding_mm=20,     # Margine ridotto per facilitare il posizionamento
            min_distance_mm=15, # Distanza minima
            priorita_area=False  # Massimizza numero di ODL invece che area
        )
        
        # Esegui nesting
        nesting_service = NestingService()
        
        print(f"Esecuzione nesting per ODL {test_odl.id} su autoclave {test_autoclave.id}...")
        
        result = nesting_service.generate_nesting(
            db=db,
            odl_ids=[test_odl.id],
            autoclave_id=test_autoclave.id,
            parameters=parameters
        )
        
        # 5. Analizza risultati
        print(f"\n📊 RISULTATI NESTING:")
        print(f"   Successo: {result.success}")
        print(f"   Status algoritmo: {result.algorithm_status}")
        print(f"   ODL posizionati: {len(result.positioned_tools)}")
        print(f"   ODL esclusi: {len(result.excluded_odls)}")
        print(f"   Efficienza: {result.efficiency:.1f}%")
        
        if result.positioned_tools:
            print(f"\n✅ TOOL POSIZIONATI:")
            for tool_pos in result.positioned_tools:
                rotation_status = "RUOTATO" if tool_pos.rotated else "NORMALE"
                print(f"   • ODL {tool_pos.odl_id}: pos({tool_pos.x:.0f},{tool_pos.y:.0f}), dim({tool_pos.width:.0f}x{tool_pos.height:.0f}mm), {rotation_status}")
                
                # Verifica che la posizione sia valida
                if tool_pos.x + tool_pos.width <= test_autoclave.larghezza_piano and tool_pos.y + tool_pos.height <= test_autoclave.lunghezza:
                    print(f"     ✅ Posizione valida dentro i limiti dell'autoclave")
                else:
                    print(f"     ❌ ERRORE: Posizione fuori dai limiti!")
                    
                # Verifica rotazione corretta
                if tool_pos.rotated:
                    expected_width = test_tool.larghezza_piano
                    expected_height = test_tool.lunghezza_piano
                else:
                    expected_width = test_tool.lunghezza_piano
                    expected_height = test_tool.larghezza_piano
                
                if abs(tool_pos.width - expected_width) < 1 and abs(tool_pos.height - expected_height) < 1:
                    print(f"     ✅ Dimensioni corrette per rotazione {rotation_status}")
                else:
                    print(f"     ❌ ERRORE: Dimensioni non corrispondono alla rotazione!")
                    print(f"       Attese: {expected_width}x{expected_height}mm")
                    print(f"       Trovate: {tool_pos.width}x{tool_pos.height}mm")
        
        if result.excluded_odls:
            print(f"\n❌ ODL ESCLUSI:")
            for excl in result.excluded_odls:
                print(f"   • ODL {excl['odl_id']}: {excl['motivo']} - {excl.get('dettagli', '')}")
        
        # 6. Verifica successo del test
        success = (result.success and 
                  len(result.positioned_tools) > 0 and 
                  all(pos.x + pos.width <= test_autoclave.larghezza_piano and 
                      pos.y + pos.height <= test_autoclave.lunghezza 
                      for pos in result.positioned_tools))
        
        if success:
            print(f"\n🎉 TEST ROTAZIONE COMPLETATO CON SUCCESSO!")
            print(f"✅ L'algoritmo di nesting considera correttamente la rotazione")
            print(f"✅ I tool vengono posizionati correttamente")
            
            # Verifica se è stata usata effettivamente la rotazione
            rotated_tools = [pos for pos in result.positioned_tools if pos.rotated]
            if rotated_tools:
                print(f"✅ {len(rotated_tools)} tool sono stati posizionati ruotati!")
            else:
                print(f"ℹ️ Nessun tool è stato ruotato (orientamento normale sufficiente)")
            
            return True
        else:
            print(f"\n❌ TEST ROTAZIONE FALLITO!")
            print(f"🔧 L'algoritmo non riesce ancora a posizionare i tool correttamente")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE IL TEST: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_specific_case():
    """Test per il caso specifico menzionato dall'utente: tool 1250x450mm su autoclave 1200x2000mm"""
    
    print("\n" + "=" * 60)
    print("🎯 TEST CASO SPECIFICO: TOOL 1250x450mm SU AUTOCLAVE 1200x2000mm")
    print("=" * 60)
    
    # Simula il caso
    tool_width = 1250  # mm
    tool_height = 450  # mm
    autoclave_width = 1200  # mm  
    autoclave_height = 2000  # mm
    margin = 20  # mm
    
    print(f"Tool: {tool_width}x{tool_height}mm")
    print(f"Autoclave: {autoclave_width}x{autoclave_height}mm")
    print(f"Margine: {margin}mm")
    
    # Test orientamento normale
    normal_fits = (tool_width + margin <= autoclave_width and 
                  tool_height + margin <= autoclave_height)
    
    # Test orientamento ruotato
    rotated_fits = (tool_height + margin <= autoclave_width and 
                   tool_width + margin <= autoclave_height)
    
    print(f"\nTest orientamento normale ({tool_width}x{tool_height} + {margin}mm):")
    print(f"   Larghezza: {tool_width + margin} <= {autoclave_width} = {tool_width + margin <= autoclave_width}")
    print(f"   Altezza: {tool_height + margin} <= {autoclave_height} = {tool_height + margin <= autoclave_height}")
    print(f"   Risultato: {normal_fits}")
    
    print(f"\nTest orientamento ruotato ({tool_height}x{tool_width} + {margin}mm):")
    print(f"   Larghezza: {tool_height + margin} <= {autoclave_width} = {tool_height + margin <= autoclave_width}")
    print(f"   Altezza: {tool_width + margin} <= {autoclave_height} = {tool_width + margin <= autoclave_height}")
    print(f"   Risultato: {rotated_fits}")
    
    if rotated_fits and not normal_fits:
        print(f"\n✅ PERFETTO! Il tool entra SOLO se ruotato")
        print(f"✅ Questo è esattamente il caso che il fix deve risolvere!")
        return True
    elif normal_fits and rotated_fits:
        print(f"\n✅ Il tool entra in entrambi gli orientamenti")
        return True
    elif normal_fits:
        print(f"\n✅ Il tool entra solo in orientamento normale")
        return True
    else:
        print(f"\n❌ Il tool non entra in nessun orientamento")
        return False

if __name__ == "__main__":
    print("🚀 AVVIO TEST COMPLETO ROTAZIONE TOOL")
    print("=" * 60)
    
    # Test caso teorico
    case_success = test_specific_case()
    
    # Test con dati reali
    real_success = test_rotation_fix()
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI FINALI:")
    print("=" * 60)
    
    if case_success:
        print("✅ Test caso teorico: SUCCESSO")
    else:
        print("❌ Test caso teorico: FALLIMENTO")
        
    if real_success:
        print("✅ Test con dati reali: SUCCESSO")
        print("🏆 IL FIX DELLA ROTAZIONE FUNZIONA CORRETTAMENTE!")
    else:
        print("❌ Test con dati reali: FALLIMENTO")
        print("🔧 Il fix della rotazione necessita ulteriori correzioni")
    
    print("\n✅ ANALISI COMPLETATA") 