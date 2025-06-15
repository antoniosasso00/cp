#!/usr/bin/env python3
"""
ANALISI PROBLEMI CRITICI SISTEMA POSIZIONAMENTO CAVALLETTI
Identifica discrepanze logiche e problemi fisici nel posizionamento
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import sessionmaker
from backend.models.db import engine
from backend.models import Autoclave, ODL, Tool, Parte
from backend.services.nesting.solver_2l import (
    NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L,
    CavallettiConfiguration, NestingLayout2L
)
from backend.api.routers.batch_nesting_modules.generation import _convert_db_to_autoclave_info_2l
import logging

def analyze_cavalletti_issues():
    """Analizza problemi critici nel sistema cavalletti"""
    
    print("🔍 ANALISI PROBLEMI CRITICI SISTEMA CAVALLETTI")
    print("=" * 70)
    
    logging.basicConfig(level=logging.WARNING)  # Riduci log per focus sui problemi
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. PROBLEMA: max_cavalletti non rispettato
        print("\n🚨 PROBLEMA 1: NUMERO MASSIMO CAVALLETTI NON RISPETTATO")
        print("-" * 60)
        
        autoclavi_2l = session.query(Autoclave).filter(
            Autoclave.usa_cavalletti == True
        ).all()
        
        for autoclave in autoclavi_2l:
            print(f"🏭 {autoclave.nome} (ID: {autoclave.id})")
            print(f"   ✅ max_cavalletti DB: {autoclave.max_cavalletti}")
            
            # Converte in AutoclaveInfo2L per testing
            autoclave_info = _convert_db_to_autoclave_info_2l(autoclave)
            
            # Test: Calcola cavalletti fissi
            solver = NestingModel2L(NestingParameters2L())
            cavalletti_fissi = solver.calcola_cavalletti_fissi_autoclave(autoclave_info)
            
            print(f"   🔧 Cavalletti fissi generati: {len(cavalletti_fissi)}")
            
            if len(cavalletti_fissi) > autoclave.max_cavalletti:
                print(f"   ❌ VIOLAZIONE: {len(cavalletti_fissi)} > {autoclave.max_cavalletti} (limite DB)")
            else:
                print(f"   ✅ Rispetta limite DB")
            print()
        
        # 2. PROBLEMA: Logica fisica errata - due cavalletti stessa metà
        print("\n🚨 PROBLEMA 2: LOGICA FISICA ERRATA - CAVALLETTI STESSA METÀ")
        print("-" * 60)
        
        # Simula tool di test per analisi posizionamento
        test_tools = [
            ToolInfo2L(odl_id=1, width=800.0, height=200.0, weight=100.0),  # Tool lungo
            ToolInfo2L(odl_id=2, width=600.0, height=300.0, weight=150.0),  # Tool medio
            ToolInfo2L(odl_id=3, width=1200.0, height=250.0, weight=200.0), # Tool molto lungo
        ]
        
        config = CavallettiConfiguration(
            cavalletto_width=80.0,
            cavalletto_height=60.0,
            min_distance_from_edge=30.0,
            max_span_without_support=400.0,
            force_minimum_two=True
        )
        
        for tool in test_tools:
            print(f"🔧 Tool ODL {tool.odl_id}: {tool.width}x{tool.height}mm")
            
            # Simula layout
            layout = NestingLayout2L(
                odl_id=tool.odl_id,
                x=100.0, y=100.0,
                width=tool.width, height=tool.height,
                weight=tool.weight, level=1, rotated=False, lines_used=1
            )
            
            # Calcola cavalletti
            cavalletti = solver.calcola_cavalletti_per_tool(layout, config)
            
            print(f"   Numero cavalletti: {len(cavalletti)}")
            
            # Analisi fisica: Verifica distribuzione cavalletti
            if len(cavalletti) >= 2:
                metà_tool = tool.width / 2 + layout.x
                cavalletti_prima_metà = sum(1 for c in cavalletti if c.center_x < metà_tool)
                cavalletti_seconda_metà = len(cavalletti) - cavalletti_prima_metà
                
                print(f"   Distribuzione: {cavalletti_prima_metà} prima metà, {cavalletti_seconda_metà} seconda metà")
                
                if cavalletti_prima_metà == 0 or cavalletti_seconda_metà == 0:
                    print(f"   ❌ PROBLEMA FISICO: Tutti cavalletti in una metà - instabilità!")
                elif abs(cavalletti_prima_metà - cavalletti_seconda_metà) > 1:
                    print(f"   ⚠️  SQUILIBRIO: Distribuzione non bilanciata")
                else:
                    print(f"   ✅ Distribuzione fisica accettabile")
                
                # Verifica spaziatura tra cavalletti
                cavalletti_sorted = sorted(cavalletti, key=lambda c: c.center_x)
                for i in range(len(cavalletti_sorted) - 1):
                    distanza = cavalletti_sorted[i+1].center_x - cavalletti_sorted[i].center_x
                    print(f"   Distanza cav {i}-{i+1}: {distanza:.1f}mm")
                    
                    if distanza > config.max_span_without_support:
                        print(f"     ❌ TROPPA DISTANZA: > {config.max_span_without_support}mm")
                    elif distanza < config.min_distance_between_cavalletti:
                        print(f"     ❌ TROPPO VICINI: < {config.min_distance_between_cavalletti}mm")
            print()
        
        # 3. PROBLEMA: Ottimizzazione adiacenza tool
        print("\n🚨 PROBLEMA 3: MANCANZA OTTIMIZZAZIONE ADIACENZA TOOL")
        print("-" * 60)
        
        # Simula due tool adiacenti
        tool_a = NestingLayout2L(
            odl_id=10, x=100.0, y=100.0, width=400.0, height=200.0,
            weight=100.0, level=1, rotated=False, lines_used=1
        )
        
        tool_b = NestingLayout2L(
            odl_id=11, x=500.0, y=100.0, width=400.0, height=200.0,  # Adiacente a tool_a
            weight=120.0, level=1, rotated=False, lines_used=1
        )
        
        print(f"Tool A: ({tool_a.x:.0f},{tool_a.y:.0f}) {tool_a.width:.0f}x{tool_a.height:.0f}mm")
        print(f"Tool B: ({tool_b.x:.0f},{tool_b.y:.0f}) {tool_b.width:.0f}x{tool_b.height:.0f}mm")
        
        # Calcola cavalletti per entrambi
        cavalletti_a = solver.calcola_cavalletti_per_tool(tool_a, config)
        cavalletti_b = solver.calcola_cavalletti_per_tool(tool_b, config)
        
        print(f"Cavalletti Tool A: {len(cavalletti_a)}")
        print(f"Cavalletti Tool B: {len(cavalletti_b)}")
        
        # Verifica sovrapposizione potenziale
        overlap_found = False
        for cav_a in cavalletti_a:
            for cav_b in cavalletti_b:
                # Check se cavalletti sono nella stessa zona Y e vicini in X
                if abs(cav_a.center_y - cav_b.center_y) < config.cavalletto_height:
                    distance_x = abs(cav_a.center_x - cav_b.center_x)
                    if distance_x < config.min_distance_between_cavalletti:
                        print(f"   ⚠️  POTENZIALE CONFLITTO:")
                        print(f"     Cav A: ({cav_a.center_x:.0f},{cav_a.center_y:.0f})")
                        print(f"     Cav B: ({cav_b.center_x:.0f},{cav_b.center_y:.0f})")
                        print(f"     Distanza: {distance_x:.0f}mm < {config.min_distance_between_cavalletti}mm")
                        overlap_found = True
        
        if not overlap_found:
            print("   ✅ Nessun conflitto cavalletti tra tool adiacenti")
        
        # 4. PROBLEMA: Mancanza principi ottimizzazione palletizing
        print("\n🚨 PROBLEMA 4: MANCANZA PRINCIPI OTTIMIZZAZIONE PALLETIZING")
        print("-" * 60)
        
        print("Principi mancanti nel sistema attuale:")
        print("❌ 1. Column Stacking: Cavalletti non allineati tra tool")
        print("❌ 2. Weight Distribution: Non considera peso per posizionamento cavalletti")
        print("❌ 3. Support Efficiency: Non ottimizza per ridurre numero cavalletti totali")
        print("❌ 4. Load Stability: Non verifica stabilità complessiva carico")
        print("❌ 5. Adjacency Optimization: Non condivide supporti tra tool adiacenti")
        
        # Raccomandazioni
        print("\n💡 RACCOMANDAZIONI IMPLEMENTAZIONE")
        print("-" * 60)
        print("1. ✅ Implementare validazione max_cavalletti dal DB")
        print("2. ✅ Aggiungere logica distribuzione fisica equilibrata")  
        print("3. ✅ Implementare ottimizzazione adiacenza tool")
        print("4. ✅ Aggiungere principi column stacking")
        print("5. ✅ Implementare weight-based support positioning")
        print("6. ✅ Aggiungere validazione stabilità complessiva")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore analisi: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    analyze_cavalletti_issues() 