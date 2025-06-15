#!/usr/bin/env python3
"""
🔧 TEST COMPLETO CAVALLETTI OPTIMIZER v2.0

Verifica sistematica di TUTTI i problemi critici identificati:
1. ❌ Numero massimo cavalletti NON rispettato
2. ❌ Logica fisica errata (cavalletti stessa metà)  
3. ❌ Mancanza ottimizzazione adiacenza
4. ❌ Risultati batch non visualizzati
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.nesting.solver_2l import (
    NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L,
    CavallettiConfiguration, NestingLayout2L
)
from backend.services.nesting.cavalletti_optimizer import (
    CavallettiOptimizerAdvanced, OptimizationStrategy
)
import logging

def test_problema_1_max_cavalletti():
    """
    🚨 TEST PROBLEMA 1: Numero massimo cavalletti NON rispettato
    
    VERIFICA:
    - Sistema rispetta max_cavalletti dal database
    - Attivazione ottimizzazione quando limite superato
    - Validazione finale corretta
    """
    print("\n🔧 TEST PROBLEMA 1: NUMERO MASSIMO CAVALLETTI")
    print("=" * 70)
    
    # Setup autoclave con limite cavalletti basso
    autoclave = AutoclaveInfo2L(
        id=1,
        width=2000.0,
        height=1000.0,
        max_weight=5000.0,
        max_lines=25,
        has_cavalletti=True,
        max_cavalletti=6,  # LIMITE BASSO per forzare ottimizzazione
        cavalletto_width=80.0,
        cavalletto_height_mm=60.0
    )
    
    # Tool multipli che genererebbero molti cavalletti
    layouts = [
        NestingLayout2L(odl_id=1, x=100, y=100, width=800, height=200, weight=150, level=1),
        NestingLayout2L(odl_id=2, x=100, y=350, width=600, height=250, weight=120, level=1),
        NestingLayout2L(odl_id=3, x=800, y=100, width=700, height=180, weight=180, level=1),
        NestingLayout2L(odl_id=4, x=800, y=350, width=500, height=220, weight=100, level=1),
    ]
    
    config = CavallettiConfiguration(
        cavalletto_width=80.0,
        cavalletto_height=60.0,
        max_span_without_support=400.0,
        force_minimum_two=True
    )
    
    # Test con ottimizzatore avanzato
    optimizer = CavallettiOptimizerAdvanced()
    
    try:
        result = optimizer.optimize_cavalletti_complete(
            layouts, autoclave, config, OptimizationStrategy.INDUSTRIAL
        )
        
        print(f"🏭 Autoclave limite: {autoclave.max_cavalletti} cavalletti")
        print(f"📊 Risultati ottimizzazione:")
        print(f"   Cavalletti originali: {result.cavalletti_originali}")
        print(f"   Cavalletti ottimizzati: {result.cavalletti_ottimizzati}")
        print(f"   Riduzione: {result.riduzione_percentuale:.1f}%")
        print(f"   Limite rispettato: {'✅' if result.limite_rispettato else '❌'}")
        
        if result.limite_rispettato:
            print("✅ PROBLEMA 1 RISOLTO: Numero massimo cavalletti rispettato!")
        else:
            print("❌ PROBLEMA 1 PERSISTENTE: Limite non rispettato")
            
        return result.limite_rispettato
        
    except Exception as e:
        print(f"❌ Errore test problema 1: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_problema_2_logica_fisica():
    """
    🚨 TEST PROBLEMA 2: Logica fisica errata
    
    VERIFICA:
    - Distribuzione bilanciata (no cavalletti stessa metà)
    - Minimo 2 supporti per stabilità
    - Span coverage appropriato
    """
    print("\n🔧 TEST PROBLEMA 2: LOGICA FISICA ERRATA")
    print("=" * 70)
    
    autoclave = AutoclaveInfo2L(
        id=2,
        width=2000.0,
        height=1000.0,
        max_weight=5000.0,
        max_lines=25,
        has_cavalletti=True,
        max_cavalletti=None,  # Nessun limite per test logica
        cavalletto_width=80.0,
        cavalletto_height_mm=60.0
    )
    
    # Tool di test specifici per logica fisica
    test_cases = [
        ("Tool molto lungo", NestingLayout2L(odl_id=10, x=100, y=100, width=1200, height=200, weight=200, level=1)),
        ("Tool medio", NestingLayout2L(odl_id=11, x=100, y=400, width=600, height=300, weight=150, level=1)),
        ("Tool piccolo", NestingLayout2L(odl_id=12, x=800, y=100, width=300, height=150, weight=80, level=1)),
        ("Tool quadrato", NestingLayout2L(odl_id=13, x=800, y=400, width=400, height=400, weight=120, level=1)),
    ]
    
    config = CavallettiConfiguration(
        cavalletto_width=80.0,
        cavalletto_height=60.0,
        max_span_without_support=400.0,
        force_minimum_two=True
    )
    
    optimizer = CavallettiOptimizerAdvanced()
    problemi_fisici = 0
    
    for case_name, layout in test_cases:
        print(f"\n📐 {case_name}: {layout.width:.0f}x{layout.height:.0f}mm, {layout.weight:.0f}kg")
        
        try:
            result = optimizer.optimize_cavalletti_complete(
                [layout], autoclave, config, OptimizationStrategy.BALANCED
            )
            
            if len(result.cavalletti_finali) == 0:
                print(f"   Tool troppo piccolo - nessun supporto necessario")
                continue
            
            # Analisi distribuzione fisica
            tool_center_x = layout.x + layout.width / 2
            left_half = sum(1 for c in result.cavalletti_finali if c.center_x < tool_center_x)
            right_half = len(result.cavalletti_finali) - left_half
            
            print(f"   Cavalletti generati: {len(result.cavalletti_finali)}")
            print(f"   Distribuzione: {left_half} sinistra, {right_half} destra")
            
            # Validazione fisica
            if len(result.cavalletti_finali) >= 2:
                if left_half == 0 or right_half == 0:
                    print(f"   ❌ PROBLEMA FISICO: Cavalletti tutti in una metà!")
                    problemi_fisici += 1
                elif abs(left_half - right_half) > 1:
                    print(f"   ⚠️ SQUILIBRIO: Distribuzione non ottimale")
                else:
                    print(f"   ✅ Distribuzione fisica corretta")
            
            # Verifica span coverage
            if len(result.cavalletti_finali) >= 2:
                cavalletti_sorted = sorted(result.cavalletti_finali, key=lambda c: c.center_x)
                max_span = 0
                for i in range(len(cavalletti_sorted) - 1):
                    span = cavalletti_sorted[i+1].center_x - cavalletti_sorted[i].center_x
                    max_span = max(max_span, span)
                
                print(f"   Span massimo: {max_span:.0f}mm (limite: {config.max_span_without_support:.0f}mm)")
                if max_span > config.max_span_without_support:
                    print(f"   ❌ SPAN ECCESSIVO: Supporto insufficiente!")
                    problemi_fisici += 1
                else:
                    print(f"   ✅ Span coverage appropriato")
            
        except Exception as e:
            print(f"   ❌ Errore calcolo: {e}")
            problemi_fisici += 1
    
    if problemi_fisici == 0:
        print("\n✅ PROBLEMA 2 RISOLTO: Logica fisica corretta per tutti i tool!")
        return True
    else:
        print(f"\n❌ PROBLEMA 2 PERSISTENTE: {problemi_fisici} violazioni fisiche rilevate")
        return False

def test_problema_3_ottimizzazione_adiacenza():
    """
    🚨 TEST PROBLEMA 3: Mancanza ottimizzazione adiacenza
    
    VERIFICA:
    - Condivisione supporti tra tool adiacenti
    - Riduzione cavalletti totali
    - Mantenimento stabilità
    """
    print("\n🔧 TEST PROBLEMA 3: OTTIMIZZAZIONE ADIACENZA")
    print("=" * 70)
    
    autoclave = AutoclaveInfo2L(
        id=3,
        width=2000.0,
        height=1000.0,
        max_weight=5000.0,
        max_lines=25,
        has_cavalletti=True,
        max_cavalletti=None,
        cavalletto_width=80.0,
        cavalletto_height_mm=60.0
    )
    
    # Tool adiacenti per test ottimizzazione
    layouts_adiacenti = [
        NestingLayout2L(odl_id=20, x=100, y=100, width=400, height=200, weight=100, level=1),
        NestingLayout2L(odl_id=21, x=520, y=100, width=400, height=200, weight=120, level=1),  # Adiacente a 20
        NestingLayout2L(odl_id=22, x=940, y=100, width=400, height=200, weight=110, level=1),  # Adiacente a 21
    ]
    
    config = CavallettiConfiguration(
        cavalletto_width=80.0,
        cavalletto_height=60.0,
        max_span_without_support=400.0,
        force_minimum_two=True
    )
    
    optimizer = CavallettiOptimizerAdvanced()
    
    try:
        # Test senza ottimizzazione adiacenza
        result_minimal = optimizer.optimize_cavalletti_complete(
            layouts_adiacenti, autoclave, config, OptimizationStrategy.MINIMAL
        )
        
        # Test con ottimizzazione industriale (include adiacenza)
        result_industrial = optimizer.optimize_cavalletti_complete(
            layouts_adiacenti, autoclave, config, OptimizationStrategy.INDUSTRIAL
        )
        
        print(f"📊 Confronto ottimizzazione adiacenza:")
        print(f"   Senza ottimizzazione: {result_minimal.cavalletti_ottimizzati} cavalletti")
        print(f"   Con ottimizzazione:   {result_industrial.cavalletti_ottimizzati} cavalletti")
        
        riduzione_adiacenza = result_minimal.cavalletti_ottimizzati - result_industrial.cavalletti_ottimizzati
        print(f"   Riduzione ottenuta:   {riduzione_adiacenza} cavalletti")
        
        if riduzione_adiacenza > 0:
            print("✅ PROBLEMA 3 RISOLTO: Ottimizzazione adiacenza funzionante!")
            return True
        else:
            print("⚠️ PROBLEMA 3 PARZIALE: Nessuna riduzione ottenuta (implementazione in corso)")
            return False  # Accettabile se implementazione è in corso
            
    except Exception as e:
        print(f"❌ Errore test problema 3: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_problema_4_risultati_batch():
    """
    🚨 TEST PROBLEMA 4: Risultati batch non visualizzati
    
    VERIFICA:
    - Generazione batch 2L corretta
    - Dati cavalletti nel risultato
    - Formato compatibile frontend
    """
    print("\n🔧 TEST PROBLEMA 4: RISULTATI BATCH NON VISUALIZZATI")
    print("=" * 70)
    
    # Test integrazione con solver 2L
    try:
        params = NestingParameters2L(
            padding_mm=5.0,
            min_distance_mm=10.0,
            use_cavalletti=True,
            base_timeout_seconds=5.0
        )
        
        solver = NestingModel2L(params)
        
        # Autoclave di test
        autoclave = AutoclaveInfo2L(
            id=4,
            width=2000.0,
            height=1000.0,
            max_weight=5000.0,
            max_lines=25,
            has_cavalletti=True,
            max_cavalletti=8,
            cavalletto_width=80.0,
            cavalletto_height_mm=60.0
        )
        
        # Tool di test
        tools = [
            ToolInfo2L(odl_id=30, width=600.0, height=300.0, weight=150.0),
            ToolInfo2L(odl_id=31, width=500.0, height=250.0, weight=120.0),
        ]
        
        # Configura cavalletti nel solver
        config = CavallettiConfiguration(
            cavalletto_width=80.0,
            cavalletto_height=60.0,
            max_span_without_support=400.0,
            force_minimum_two=True
        )
        solver._cavalletti_config = config
        
        print("🎯 Test integrazione solver 2L...")
        
        # Esegui solve
        solution = solver.solve_2l(tools, autoclave)
        
        print(f"📊 Risultati solve 2L:")
        print(f"   Success: {solution.success}")
        print(f"   Tool posizionati: {len(solution.layouts)}")
        print(f"   Algorithm: {solution.algorithm_status}")
        
        if solution.success and len(solution.layouts) > 0:
            # Verifica presenza tool su livello 1 (cavalletto)
            level_1_tools = [l for l in solution.layouts if l.level == 1]
            print(f"   Tool su cavalletto: {len(level_1_tools)}")
            
            if len(level_1_tools) > 0:
                # Test conversione a risposta Pydantic (formato frontend)
                print("🔄 Test conversione formato frontend...")
                
                try:
                    pydantic_response = solver.convert_to_pydantic_response(solution, autoclave)
                    
                    print(f"✅ Conversione Pydantic riuscita!")
                    print(f"   Positioned tools: {len(pydantic_response.positioned_tools)}")
                    print(f"   Cavalletti fissi: {len(pydantic_response.cavalletti_fissi) if pydantic_response.cavalletti_fissi else 0}")
                    
                    if pydantic_response.cavalletti_fissi and len(pydantic_response.cavalletti_fissi) > 0:
                        print("✅ PROBLEMA 4 RISOLTO: Dati cavalletti presenti nel risultato!")
                        return True
                    else:
                        print("⚠️ PROBLEMA 4 PARZIALE: Cavalletti non inclusi nella risposta")
                        return False
                        
                except Exception as e:
                    print(f"❌ Errore conversione Pydantic: {e}")
                    return False
            else:
                print("⚠️ Nessun tool posizionato su cavalletto - test non applicabile")
                return False
        else:
            print("❌ Solve 2L fallito - impossibile testare risultati")
            return False
            
    except Exception as e:
        print(f"❌ Errore test problema 4: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    🎯 ESECUZIONE TEST COMPLETI
    
    Verifica sistematica di tutti i problemi critici identificati
    """
    print("🔧 CAVALLETTI OPTIMIZER v2.0 - TEST COMPLETI")
    print("=" * 80)
    print("Verifica sistematica problemi critici identificati:")
    print("1. ❌ Numero massimo cavalletti NON rispettato")
    print("2. ❌ Logica fisica errata (cavalletti stessa metà)")
    print("3. ❌ Mancanza ottimizzazione adiacenza") 
    print("4. ❌ Risultati batch non visualizzati")
    
    # Configurazione logging
    logging.basicConfig(
        level=logging.WARNING,  # Riduci log per focus sui test
        format='%(levelname)s - %(message)s'
    )
    
    # Esecuzione test
    risultati = {}
    
    risultati['problema_1'] = test_problema_1_max_cavalletti()
    risultati['problema_2'] = test_problema_2_logica_fisica()
    risultati['problema_3'] = test_problema_3_ottimizzazione_adiacenza()
    risultati['problema_4'] = test_problema_4_risultati_batch()
    
    # Riepilogo finale
    print("\n" + "=" * 80)
    print("🎯 RIEPILOGO FINALE TEST")
    print("=" * 80)
    
    problemi_risolti = sum(risultati.values())
    totale_problemi = len(risultati)
    
    for problema, risolto in risultati.items():
        status = "✅ RISOLTO" if risolto else "❌ PERSISTENTE"
        print(f"{problema.replace('_', ' ').upper()}: {status}")
    
    print(f"\n📊 STATO COMPLESSIVO: {problemi_risolti}/{totale_problemi} problemi risolti")
    
    if problemi_risolti == totale_problemi:
        print("🎉 TUTTI I PROBLEMI CRITICI SONO STATI RISOLTI!")
        print("✅ Sistema cavalletti pronto per produzione")
    elif problemi_risolti >= totale_problemi * 0.75:
        print("🔧 MAGGIOR PARTE DEI PROBLEMI RISOLTI")
        print("⚠️ Implementazione ottimizzazioni avanzate in corso")
    else:
        print("❌ PROBLEMI CRITICI PERSISTENTI")
        print("🚨 Richiesto intervento immediato")
    
    return problemi_risolti == totale_problemi

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 