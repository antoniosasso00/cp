#!/usr/bin/env python3
"""
🔍 DIAGNOSI CRITICA SISTEMA 2L - DATA LAYER
===========================================

Script per identificare e risolvere il problema critico:
"Il solver 2L riceve tool con dimensioni/peso nulli"

Analizza:
1. Presenza dati nel database (ODL, Tool, Parte)
2. Correttezza funzione conversione _convert_db_to_tool_info_2l
3. Integrità delle relazioni database
4. Propone fix per completare l'implementazione
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import sessionmaker, joinedload
from database import engine
from models.odl import ODL
from models.tool import Tool
from models.parte import Parte
from models.autoclave import Autoclave
from api.routers.batch_nesting_modules.generation import _convert_db_to_tool_info_2l, _convert_db_to_autoclave_info_2l

def diagnose_2l_data_layer():
    """Diagnosi completa del data layer per sistema 2L"""
    
    print("🔍 DIAGNOSI CRITICA SISTEMA 2L - DATA LAYER")
    print("=" * 60)
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # ========== 1. VERIFICA PRESENZA DATI DATABASE ==========
        print("\n📋 1. VERIFICA PRESENZA DATI DATABASE")
        print("-" * 40)
        
        # Trova ODL con relazioni complete
        odls = db.query(ODL).options(
            joinedload(ODL.tool),
            joinedload(ODL.parte)
        ).filter(
            ODL.status.in_(['Attesa Cura', 'in_attesa_cura'])
        ).limit(15).all()
        
        print(f"📦 ODL in 'Attesa Cura' trovati: {len(odls)}")
        
        # Conta ODL con dati completi
        complete_count = 0
        problematic_count = 0
        
        print(f"\n📊 DETTAGLI PRIMI 10 ODL:")
        print(f"{'ODL':<6} {'Tool':<12} {'Dimensioni':<15} {'Peso':<8} {'Parte':<12} {'Status'}")
        print("-" * 75)
        
        for i, odl in enumerate(odls[:10]):
            # Analisi dati tool
            tool_data = "❌ NULL"
            dimensions = "0x0mm"
            weight = "0kg"
            
            if odl.tool:
                tool_data = f"{odl.tool.part_number_tool[:10]}"
                
                lunghezza = odl.tool.lunghezza_piano or 0
                larghezza = odl.tool.larghezza_piano or 0
                peso = odl.tool.peso or 0
                
                dimensions = f"{lunghezza:.0f}x{larghezza:.0f}mm"
                weight = f"{peso:.1f}kg"
                
                if lunghezza > 0 and larghezza > 0:
                    complete_count += 1
                else:
                    problematic_count += 1
            else:
                problematic_count += 1
            
            # Analisi dati parte
            parte_data = "❌ NULL"
            if odl.parte:
                parte_data = f"{odl.parte.part_number[:10]}"
            
            print(f"{odl.id:<6} {tool_data:<12} {dimensions:<15} {weight:<8} {parte_data:<12} {odl.status}")
        
        # ========== 2. ANALISI FUNZIONE CONVERSIONE ==========
        print(f"\n🔧 2. TEST FUNZIONE CONVERSIONE")
        print("-" * 40)
        
        print(f"✅ ODL con dimensioni valide: {complete_count}")
        print(f"❌ ODL con problemi dati: {problematic_count}")
        
        if len(odls) > 0:
            # Test conversione con primo ODL completo
            test_odl = None
            for odl in odls:
                if odl.tool and odl.parte and (odl.tool.lunghezza_piano or 0) > 0:
                    test_odl = odl
                    break
            
            if test_odl:
                print(f"\n🧪 TEST CONVERSIONE con ODL {test_odl.id}:")
                
                # Prima: dati originali
                print(f"   📊 DATI ORIGINALI:")
                print(f"     Tool: {test_odl.tool.part_number_tool}")
                print(f"     Dimensioni DB: {test_odl.tool.lunghezza_piano}x{test_odl.tool.larghezza_piano}mm")
                print(f"     Peso DB: {test_odl.tool.peso}kg")
                
                # Dopo: conversione a ToolInfo2L
                tool_2l = _convert_db_to_tool_info_2l(test_odl, test_odl.tool, test_odl.parte)
                
                print(f"   🔄 DOPO CONVERSIONE:")
                print(f"     Width (solver): {tool_2l.width}mm")
                print(f"     Height (solver): {tool_2l.height}mm")
                print(f"     Weight (solver): {tool_2l.weight}kg")
                print(f"     Can use cavalletto: {tool_2l.can_use_cavalletto}")
                
                # Verifica mappatura dimensioni
                if (test_odl.tool.lunghezza_piano == tool_2l.width and 
                    test_odl.tool.larghezza_piano == tool_2l.height):
                    print(f"   ✅ MAPPATURA DIMENSIONI: Corretta")
                else:
                    print(f"   ⚠️  MAPPATURA DIMENSIONI: Possibile problema")
                    print(f"     DB: lunghezza={test_odl.tool.lunghezza_piano} → solver width={tool_2l.width}")
                    print(f"     DB: larghezza={test_odl.tool.larghezza_piano} → solver height={tool_2l.height}")
                
                # Stima area e eligibilità cavalletti
                area_mm2 = tool_2l.width * tool_2l.height
                area_m2 = area_mm2 / 1_000_000
                print(f"   📐 Area calcolata: {area_mm2:,.0f}mm² ({area_m2:.3f}m²)")
                
                # Test criteri eligibilità
                peso_ok = tool_2l.weight <= 100.0
                size_ok = tool_2l.width <= 1200.0 and tool_2l.height <= 800.0
                print(f"   🎯 Eligibilità cavalletti:")
                print(f"     Peso ≤100kg: {peso_ok} ({tool_2l.weight:.1f}kg)")
                print(f"     Dimensioni ≤1200x800mm: {size_ok} ({tool_2l.width:.0f}x{tool_2l.height:.0f}mm)")
                print(f"     RISULTATO: {tool_2l.can_use_cavalletto}")
                
            else:
                print("❌ NESSUN ODL CON DATI COMPLETI TROVATO!")
        
        # ========== 3. ANALISI AUTOCLAVI 2L ==========
        print(f"\n🏭 3. VERIFICA AUTOCLAVI 2L")
        print("-" * 40)
        
        autoclavi_2l = db.query(Autoclave).filter(
            Autoclave.usa_cavalletti == True
        ).all()
        
        print(f"🏭 Autoclavi 2L trovate: {len(autoclavi_2l)}")
        
        for autoclave in autoclavi_2l:
            print(f"\n🏭 {autoclave.nome} (ID: {autoclave.id})")
            print(f"   📏 Dimensioni: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
            print(f"   ⚖️  Carico max: {autoclave.max_load_kg}kg")
            print(f"   🔧 Cavalletti: {autoclave.usa_cavalletti}")
            print(f"   📊 Max cavalletti: {autoclave.max_cavalletti}")
            print(f"   🏋️  Peso per cavalletto: {autoclave.peso_max_per_cavalletto_kg}kg")
            
            # Test conversione autoclave
            autoclave_2l = _convert_db_to_autoclave_info_2l(autoclave)
            print(f"   ✅ Conversione 2L: {autoclave_2l.has_cavalletti}, max_cavalletti={autoclave_2l.max_cavalletti}")
        
        # ========== 4. DIAGNOSI PROBLEMI E SOLUZIONI ==========
        print(f"\n🔧 4. DIAGNOSI PROBLEMI E SOLUZIONI")
        print("-" * 40)
        
        total_odls = len(odls)
        success_rate = (complete_count / total_odls * 100) if total_odls > 0 else 0
        
        print(f"📊 RIEPILOGO DIAGNOSI:")
        print(f"   ODL totali analizzati: {total_odls}")
        print(f"   ODL con dati completi: {complete_count}")
        print(f"   ODL problematici: {problematic_count}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        if problematic_count > 0:
            print(f"\n⚠️  PROBLEMI IDENTIFICATI:")
            
            # Verifica tool senza dimensioni
            tools_no_dimensions = db.query(Tool).filter(
                (Tool.lunghezza_piano.is_(None)) | 
                (Tool.larghezza_piano.is_(None)) |
                (Tool.lunghezza_piano == 0) |
                (Tool.larghezza_piano == 0)
            ).count()
            
            print(f"   🔧 Tool senza dimensioni: {tools_no_dimensions}")
            
            # Verifica tool senza peso
            tools_no_weight = db.query(Tool).filter(
                (Tool.peso.is_(None)) | (Tool.peso == 0)
            ).count()
            
            print(f"   ⚖️  Tool senza peso: {tools_no_weight}")
            
            # Verifica ODL senza tool
            odls_no_tool = db.query(ODL).filter(
                ODL.tool_id.is_(None)
            ).count()
            
            print(f"   🔗 ODL senza tool: {odls_no_tool}")
            
            print(f"\n🛠️  SOLUZIONI SUGGERITE:")
            print(f"   1. Popolare dimensioni mancanti nei tool esistenti")
            print(f"   2. Aggiungere peso di default per tool senza peso")
            print(f"   3. Verificare integrità relazioni ODL → Tool")
            print(f"   4. Implementare validazione dati in fase di inserimento")
        
        else:
            print(f"\n✅ SISTEMA DATI: PERFETTO!")
            print(f"   Tutti gli ODL hanno dati completi per il solver 2L")
        
        # ========== 5. TEST SIMULAZIONE SOLVER 2L ==========
        if complete_count >= 3:
            print(f"\n🚀 5. SIMULAZIONE SOLVER 2L")
            print("-" * 40)
            
            # Prendi primi 3 ODL completi
            complete_odls = []
            for odl in odls:
                if (odl.tool and odl.parte and 
                    (odl.tool.lunghezza_piano or 0) > 0 and 
                    (odl.tool.larghezza_piano or 0) > 0):
                    complete_odls.append(odl)
                    if len(complete_odls) >= 3:
                        break
            
            if len(complete_odls) >= 3 and len(autoclavi_2l) > 0:
                print(f"🧪 Simulazione con {len(complete_odls)} ODL e autoclave {autoclavi_2l[0].nome}")
                
                # Converti in formato solver
                tools_2l = []
                for odl in complete_odls:
                    tool_2l = _convert_db_to_tool_info_2l(odl, odl.tool, odl.parte)
                    tools_2l.append(tool_2l)
                
                autoclave_2l = _convert_db_to_autoclave_info_2l(autoclavi_2l[0])
                
                print(f"   📦 Tool preparati: {len(tools_2l)}")
                print(f"   🏭 Autoclave: {autoclave_2l.width}x{autoclave_2l.height}mm")
                print(f"   🔧 Cavalletti abilitati: {autoclave_2l.has_cavalletti}")
                
                # Calcola eligibilità
                eligible_for_cavalletti = [t for t in tools_2l if t.can_use_cavalletto]
                print(f"   🎯 Tool eligible per cavalletti: {len(eligible_for_cavalletti)}")
                
                # Calcola capacità teorica
                total_area_tools = sum(t.width * t.height for t in tools_2l)
                autoclave_area = autoclave_2l.width * autoclave_2l.height
                coverage = (total_area_tools / autoclave_area * 100)
                
                print(f"   📊 Copertura teorica: {coverage:.1f}%")
                
                if coverage > 80:
                    print(f"   ✅ POTENZIALE USO CAVALLETTI: Livello 0 può saturare")
                else:
                    print(f"   ⚠️  NOTA: Copertura bassa, livello 1 potrebbe rimanere vuoto")
                
                print(f"   🎯 SISTEMA PRONTO PER TEST SOLVER 2L COMPLETO")
            else:
                print(f"❌ Dati insufficienti per simulazione solver")
        
        return {
            'total_odls': total_odls,
            'complete_odls': complete_count,
            'problematic_odls': problematic_count,
            'success_rate': success_rate,
            'autoclavi_2l': len(autoclavi_2l),
            'ready_for_solver': complete_count >= 3 and len(autoclavi_2l) > 0
        }
        
    except Exception as e:
        print(f"❌ Errore durante diagnosi: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    result = diagnose_2l_data_layer()
    
    print(f"\n🏆 CONCLUSIONE DIAGNOSI")
    print("=" * 30)
    
    if result and result['ready_for_solver']:
        print("✅ SISTEMA PRONTO: Dati sufficienti per completare implementazione 2L")
        print("🚀 PROSSIMI PASSI:")
        print("   1. Eseguire test completo solver 2L")
        print("   2. Validare uso cavalletti")
        print("   3. Ottimizzare parametri eligibilità")
    else:
        print("⚠️  SISTEMA NON PRONTO: Necessario fix dati database")
        print("🛠️  AZIONI RICHIESTE:")
        print("   1. Popolare dimensioni tool mancanti")
        print("   2. Aggiungere pesi di default")
        print("   3. Riparare relazioni ODL-Tool problematiche") 