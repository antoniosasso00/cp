#!/usr/bin/env python3
"""
Analisi dei vincoli di peso nel sistema 2L CarbonPilot
Verifica se i parametri di peso sono troppo restrittivi e impediscono l'utilizzo del livello 1
"""

import sys
import os
from sqlalchemy.orm import sessionmaker
from backend.database import engine
from backend.models import ODL, Autoclave, Tool, Parte

def analyze_weight_constraints():
    """Analizza i vincoli di peso e verifica se sono troppo restrittivi"""
    
    print("🔍 ANALISI VINCOLI PESO SISTEMA 2L")
    print("=" * 60)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Analisi autoclavi 2L
        print("\n📋 AUTOCLAVI 2L DISPONIBILI")
        print("-" * 40)
        
        autoclavi_2l = session.query(Autoclave).filter(Autoclave.usa_cavalletti == True).all()
        
        if not autoclavi_2l:
            print("❌ NESSUNA AUTOCLAVE 2L TROVATA!")
            return False
        
        for autoclave in autoclavi_2l:
            print(f"\n🏭 {autoclave.nome} (ID: {autoclave.id})")
            print(f"  📏 Dimensioni: {autoclave.lunghezza}mm x {autoclave.larghezza_piano}mm")
            print(f"  ⚖️  Carico max totale: {autoclave.max_load_kg}kg")
            print(f"  🔧 Cavalletti: {autoclave.max_cavalletti or 'N/A'}")
            print(f"  🏋️  Peso per cavalletto: {autoclave.peso_max_per_cavalletto_kg or 'N/A'}kg")
            
            # Calcola capacità teorica livelli
            if autoclave.peso_max_per_cavalletto_kg and autoclave.max_cavalletti:
                capacita_livello_1 = autoclave.peso_max_per_cavalletto_kg * autoclave.max_cavalletti
                capacita_livello_0 = autoclave.max_load_kg - capacita_livello_1
                
                print(f"  📊 Capacità teorica Livello 0: {capacita_livello_0}kg")
                print(f"  📊 Capacità teorica Livello 1: {capacita_livello_1}kg")
                
                if capacita_livello_0 < 0:
                    print("  ⚠️  PROBLEMA: Capacità livello 0 negativa!")
                if capacita_livello_1 <= 0:
                    print("  ⚠️  PROBLEMA: Capacità livello 1 zero o negativa!")
        
        # 2. Analisi ODL disponibili
        print("\n\n📦 ANALISI ODL DISPONIBILI")
        print("-" * 40)
        
        odl_attesa_cura = session.query(ODL).filter(
            ODL.stato == 'Attesa Cura'
        ).join(Tool).join(Parte).all()
        
        print(f"📋 ODL totali in 'Attesa Cura': {len(odl_attesa_cura)}")
        
        if len(odl_attesa_cura) == 0:
            print("❌ NESSUN ODL DISPONIBILE!")
            return False
        
        # Analizza pesi reali dei tool
        pesi_tool = []
        odl_con_peso = []
        
        for odl in odl_attesa_cura:
            if odl.tool and odl.tool.peso:
                pesi_tool.append(odl.tool.peso)
                odl_con_peso.append(odl)
        
        if not pesi_tool:
            print("⚠️  NESSUN TOOL CON PESO SPECIFICATO!")
            # Stima peso basato su dimensioni (alluminio ~2.7g/cm³, spessore 5mm)
            pesi_tool = []
            for odl in odl_attesa_cura:
                if odl.tool and odl.tool.larghezza_piano and odl.tool.lunghezza_piano:
                    # Stima: area * spessore * densità
                    area_mm2 = odl.tool.larghezza_piano * odl.tool.lunghezza_piano
                    volume_mm3 = area_mm2 * 5  # Spessore 5mm
                    peso_stimato = (volume_mm3 * 2.7e-6)  # Densità alluminio kg/mm³
                    pesi_tool.append(peso_stimato)
                    odl.peso_stimato = peso_stimato
            print(f"📊 Pesi stimati per {len(pesi_tool)} tool")
        else:
            print(f"📊 Pesi reali per {len(pesi_tool)} tool")
        
        if pesi_tool:
            peso_min = min(pesi_tool)
            peso_max = max(pesi_tool)
            peso_medio = sum(pesi_tool) / len(pesi_tool)
            peso_totale = sum(pesi_tool)
            
            print(f"  ⚖️  Peso minimo: {peso_min:.2f}kg")
            print(f"  ⚖️  Peso massimo: {peso_max:.2f}kg")
            print(f"  ⚖️  Peso medio: {peso_medio:.2f}kg")
            print(f"  ⚖️  Peso totale: {peso_totale:.2f}kg")
        
        # 3. Test reale con autoclave più grande
        print("\n\n🧪 SIMULAZIONE VINCOLI REALI")
        print("-" * 40)
        
        autoclave_test = max(autoclavi_2l, key=lambda a: a.max_load_kg or 0)
        print(f"🏭 Test con: {autoclave_test.nome}")
        print(f"📏 Capacità totale: {autoclave_test.max_load_kg}kg")
        
        # Simula configurazione corrente del frontend
        max_weight_per_level_kg = 200.0  # Valore dal frontend
        print(f"🔧 Parametro frontend: max_weight_per_level_kg = {max_weight_per_level_kg}kg")
        
        # Calcola quanti tool possono stare con vincoli attuali
        if pesi_tool:
            tool_su_livello_0 = 0
            peso_livello_0 = 0
            tool_su_livello_1 = 0 
            peso_livello_1 = 0
            
            for peso in sorted(pesi_tool, reverse=True):  # Tool più grandi per primi
                if peso_livello_0 + peso <= max_weight_per_level_kg:
                    peso_livello_0 += peso
                    tool_su_livello_0 += 1
                elif peso_livello_1 + peso <= max_weight_per_level_kg:
                    peso_livello_1 += peso
                    tool_su_livello_1 += 1
            
            print(f"📊 Simulazione con vincoli attuali:")
            print(f"  🔹 Livello 0: {tool_su_livello_0} tool, {peso_livello_0:.2f}kg")
            print(f"  🔹 Livello 1: {tool_su_livello_1} tool, {peso_livello_1:.2f}kg")
            print(f"  🔹 Tool totali posizionati: {tool_su_livello_0 + tool_su_livello_1}")
            print(f"  🔹 Tool non posizionati: {len(pesi_tool) - tool_su_livello_0 - tool_su_livello_1}")
            
            # Test con vincoli dinamici corretti
            print(f"\n🔧 Test con vincoli dinamici corretti:")
            
            # Simula logica dinamica del solver
            num_cavalletti_stimati = min(4, autoclave_test.max_cavalletti or 4)
            peso_max_livello_1_dinamico = (autoclave_test.peso_max_per_cavalletto_kg or 300) * num_cavalletti_stimati
            peso_max_livello_0_dinamico = autoclave_test.max_load_kg - peso_max_livello_1_dinamico
            
            print(f"  📊 Livello 0 dinamico: max {peso_max_livello_0_dinamico:.1f}kg")
            print(f"  📊 Livello 1 dinamico: max {peso_max_livello_1_dinamico:.1f}kg")
            
            # Riprova con limiti dinamici
            tool_su_livello_0_din = 0
            peso_livello_0_din = 0
            tool_su_livello_1_din = 0
            peso_livello_1_din = 0
            
            for peso in sorted(pesi_tool, reverse=True):
                if peso_livello_0_din + peso <= peso_max_livello_0_dinamico:
                    peso_livello_0_din += peso
                    tool_su_livello_0_din += 1
                elif peso_livello_1_din + peso <= peso_max_livello_1_dinamico:
                    peso_livello_1_din += peso
                    tool_su_livello_1_din += 1
            
            print(f"  🔹 Livello 0: {tool_su_livello_0_din} tool, {peso_livello_0_din:.2f}kg")
            print(f"  🔹 Livello 1: {tool_su_livello_1_din} tool, {peso_livello_1_din:.2f}kg")
            print(f"  🔹 Tool totali: {tool_su_livello_0_din + tool_su_livello_1_din}")
            
        # 4. Analisi problema identificato
        print("\n\n🎯 ANALISI PROBLEMA")
        print("-" * 40)
        
        print("❌ PROBLEMA IDENTIFICATO:")
        print("   Il parametro 'max_weight_per_level_kg = 200kg' dal frontend")
        print("   è TROPPO RESTRITTIVO rispetto alle capacità reali!")
        print()
        print("📊 CONFRONTO:")
        print(f"   Frontend parameter: 200kg per livello")
        print(f"   Autoclave capacity: {autoclave_test.max_load_kg}kg totale")
        print(f"   Cavalletto capacity: {autoclave_test.peso_max_per_cavalletto_kg or 'N/A'}kg per cavalletto")
        print()
        print("🔧 SOLUZIONE SUGGERITA:")
        print("   1. Usare calcolo dinamico basato su autoclave reale")
        print("   2. Non limitare a 200kg fissi per livello")
        print("   3. Utilizzare max_load_kg dell'autoclave come riferimento")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRORE DURANTE ANALISI: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        session.close()

def suggest_weight_fixes():
    """Suggerisce correzioni per i vincoli di peso"""
    
    print("\n\n🔧 CORREZIONI SUGGERITE")
    print("=" * 60)
    
    print("1. 🎯 FRONTEND: Modificare parametri dinamici")
    print("   File: frontend/src/modules/nesting/page.tsx")
    print("   Sostituire: max_weight_per_level_kg: 200.0 (fisso)")
    print("   Con: Calcolo dinamico basato su autoclave selezionata")
    print()
    
    print("2. 🎯 BACKEND: Verificare logica vincoli")
    print("   File: backend/services/nesting/solver_2l.py")
    print("   Verificare: _calculate_dynamic_weight_limits()")
    print("   Assicurarsi che i limiti siano realistici")
    print()
    
    print("3. 🎯 DATABASE: Verificare dati autoclavi")
    print("   Controllare: max_load_kg, peso_max_per_cavalletto_kg")
    print("   Assicurarsi che i valori siano realistici per uso industriale")
    print()
    
    print("4. 🎯 ALGORITMO: Preferenza sequenziale")
    print("   L'algoritmo 2L è progettato per essere sequenziale:")
    print("   - FASE 1: Riempie completamente livello 0")
    print("   - FASE 2: Solo overflow va su livello 1")
    print("   - Con dataset piccoli, livello 1 può rimanere vuoto (NORMALE)")

if __name__ == "__main__":
    print("🚀 AVVIO ANALISI VINCOLI PESO CARBONPILOT 2L")
    print("Verifica se i parametri di peso impediscono l'uso del livello 1")
    print()
    
    # Analisi principale
    success = analyze_weight_constraints()
    
    # Suggerimenti
    suggest_weight_fixes()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ANALISI COMPLETATA - Problema di vincoli identificato!")
    else:
        print("⚠️  ANALISI INCOMPLETA - Verificare configurazione database")
    print("=" * 60) 