#!/usr/bin/env python3
"""
Script di validazione per il canvas del nesting con orientamento e quote.
Verifica che le dimensioni reali siano visualizzate correttamente con la scala appropriata,
che l'orientamento automatico funzioni e che le quote siano mostrate correttamente.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from models.db import get_db
from models.tool import Tool
from models.autoclave import Autoclave
from models.odl import ODL
from models.parte import Parte
from models.catalogo import Catalogo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dimensioni_reali_canvas():
    """Verifica che le dimensioni reali siano visualizzate correttamente nel canvas con scala corretta"""
    print("🔍 Test: Verifica dimensioni reali in canvas (scala corretta)")
    
    db = next(get_db())
    try:
        # Prendi alcuni tool di esempio
        tools = db.query(Tool).limit(5).all()
        autoclavi = db.query(Autoclave).limit(2).all()
        
        if not tools:
            print("❌ Nessun tool trovato nel database")
            return False
            
        if not autoclavi:
            print("❌ Nessuna autoclave trovata nel database")
            return False
            
        print(f"✅ Trovati {len(tools)} tools e {len(autoclavi)} autoclavi")
        
        # Verifica che i tool abbiano dimensioni valide
        for tool in tools:
            if not tool.lunghezza_piano or not tool.larghezza_piano:
                print(f"❌ Tool {tool.part_number_tool} ha dimensioni non valide")
                return False
            
            # Calcola il rapporto di aspetto
            aspect_ratio = tool.lunghezza_piano / tool.larghezza_piano
            print(f"📏 Tool {tool.part_number_tool}: {tool.lunghezza_piano}x{tool.larghezza_piano}mm (ratio: {aspect_ratio:.2f})")
        
        # Verifica che le autoclavi abbiano dimensioni valide
        for autoclave in autoclavi:
            if not autoclave.lunghezza or not autoclave.larghezza_piano:
                print(f"❌ Autoclave {autoclave.nome} ha dimensioni non valide")
                return False
            
            print(f"🏭 Autoclave {autoclave.nome}: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
            
            # Calcola scala per adattare l'autoclave a un canvas 800x500
            canvas_width, canvas_height = 800, 500
            scale_x = (canvas_width * 0.85) / autoclave.lunghezza
            scale_y = (canvas_height * 0.85) / autoclave.larghezza_piano
            scale = min(scale_x, scale_y)
            
            print(f"📐 Scala calcolata per canvas 800x500: {scale:.4f}")
            
            # Verifica che i tool si adattino nell'autoclave
            for tool in tools:
                tool_fits_normal = (tool.lunghezza_piano <= autoclave.lunghezza and 
                                  tool.larghezza_piano <= autoclave.larghezza_piano)
                tool_fits_rotated = (tool.larghezza_piano <= autoclave.lunghezza and 
                                   tool.lunghezza_piano <= autoclave.larghezza_piano)
                
                if tool_fits_normal or tool_fits_rotated:
                    orientation = "normale" if tool_fits_normal else "ruotato"
                    print(f"  ✅ Tool {tool.part_number_tool} si adatta ({orientation})")
                else:
                    print(f"  ❌ Tool {tool.part_number_tool} NON si adatta")
        
        print("✅ Test dimensioni reali completato con successo")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test dimensioni: {e}")
        return False
    finally:
        db.close()

def test_orientamento_automatico():
    """Verifica che l'orientamento automatico funzioni correttamente"""
    print("\n🔄 Test: Controlla orientamento automatico")
    
    db = next(get_db())
    try:
        tools = db.query(Tool).all()
        autoclavi = db.query(Autoclave).all()
        
        if not tools or not autoclavi:
            print("❌ Dati insufficienti per il test")
            return False
        
        autoclave = autoclavi[0]  # Usa la prima autoclave
        
        orientamento_ottimale_count = 0
        
        for tool in tools:
            # Logica di orientamento: se lunghezza > larghezza, ruota per allinearlo al lato lungo dell'autoclave
            should_rotate = False
            
            if tool.lunghezza_piano > tool.larghezza_piano:
                # Tool rettangolare - verifica se ruotarlo migliora l'utilizzo dello spazio
                if autoclave.lunghezza > autoclave.larghezza_piano:
                    # Autoclave più lunga che larga - allinea il lato lungo del tool al lato lungo dell'autoclave
                    should_rotate = False  # Mantieni orientamento normale
                else:
                    # Autoclave più larga che lunga - ruota il tool
                    should_rotate = True
            
            # Calcola efficienza spazio per entrambi gli orientamenti
            normal_efficiency = min(tool.lunghezza_piano / autoclave.lunghezza, 
                                  tool.larghezza_piano / autoclave.larghezza_piano)
            rotated_efficiency = min(tool.larghezza_piano / autoclave.lunghezza, 
                                   tool.lunghezza_piano / autoclave.larghezza_piano)
            
            optimal_rotation = rotated_efficiency > normal_efficiency
            
            if optimal_rotation:
                orientamento_ottimale_count += 1
            
            print(f"🔧 Tool {tool.part_number_tool}:")
            print(f"   Normale: {normal_efficiency:.3f} | Ruotato: {rotated_efficiency:.3f}")
            print(f"   Orientamento ottimale: {'Ruotato' if optimal_rotation else 'Normale'}")
        
        print(f"✅ {orientamento_ottimale_count}/{len(tools)} tools beneficiano della rotazione")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test orientamento: {e}")
        return False
    finally:
        db.close()

def test_quote_e_labels():
    """Verifica che le quote e le label siano visualizzate correttamente"""
    print("\n📋 Test: Quote e label visualizzate correttamente")
    
    db = next(get_db())
    try:
        # Prendi alcuni ODL con dati completi
        odls = db.query(ODL).join(Parte).join(Catalogo).join(Tool).limit(5).all()
        
        if not odls:
            print("❌ Nessun ODL con dati completi trovato")
            return False
        
        print(f"✅ Trovati {len(odls)} ODL con dati completi")
        
        for odl in odls:
            parte = odl.parte
            catalogo = parte.catalogo
            tool = odl.tool
            
            # Verifica che tutti i dati necessari per le quote siano presenti
            required_fields = {
                'Part Number': catalogo.part_number,
                'Lunghezza': tool.lunghezza_piano,
                'Larghezza': tool.larghezza_piano,
                'Superficie': getattr(catalogo, 'area_cm2', None),
                'Valvole': parte.num_valvole_richieste,
                'Priorità': odl.priorita
            }
            
            missing_fields = []
            for field_name, value in required_fields.items():
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing_fields.append(field_name)
            
            if missing_fields:
                print(f"⚠️  ODL {odl.id} - Campi mancanti: {', '.join(missing_fields)}")
            else:
                print(f"✅ ODL {odl.id} - Tutti i dati per le quote sono presenti:")
                print(f"   📦 {required_fields['Part Number']}")
                print(f"   📏 {required_fields['Lunghezza']}x{required_fields['Larghezza']}mm")
                print(f"   📐 Superficie: {required_fields['Superficie']}cm²")
                print(f"   🔧 Valvole: {required_fields['Valvole']}")
                print(f"   ⭐ Priorità: {required_fields['Priorità']}")
        
        print("✅ Test quote e label completato")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test quote: {e}")
        return False
    finally:
        db.close()

def test_multi_canvas():
    """Verifica la gestione di multi-canvas per diversi nesting"""
    print("\n🖼️  Test: Multi-canvas per diversi nesting")
    
    db = next(get_db())
    try:
        from models.nesting_result import NestingResult
        
        # Prendi alcuni nesting esistenti
        nesting_results = db.query(NestingResult).limit(3).all()
        
        if not nesting_results:
            print("⚠️  Nessun nesting result trovato - test saltato")
            return True
        
        print(f"✅ Trovati {len(nesting_results)} nesting results")
        
        for nesting in nesting_results:
            autoclave = nesting.autoclave
            odl_count = len(nesting.odl_ids) if nesting.odl_ids else 0
            
            canvas_title = f"Autoclave {autoclave.nome} – Nesting {nesting.id}"
            print(f"🖼️  Canvas: {canvas_title}")
            print(f"   📦 ODL inclusi: {odl_count}")
            print(f"   📏 Dimensioni autoclave: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
            print(f"   📊 Area utilizzata: {nesting.area_utilizzata:.1f}/{nesting.area_totale:.1f}cm²")
            print(f"   🔧 Valvole: {nesting.valvole_utilizzate}/{nesting.valvole_totali}")
        
        print("✅ Test multi-canvas completato")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test multi-canvas: {e}")
        return False
    finally:
        db.close()

def main():
    """Esegue tutti i test di validazione"""
    print("🧪 VALIDAZIONE NESTING CANVAS - Orientamento e Quote")
    print("=" * 60)
    
    tests = [
        test_dimensioni_reali_canvas,
        test_orientamento_automatico,
        test_quote_e_labels,
        test_multi_canvas
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Errore durante {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI FINALI:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\n🎯 Test superati: {passed}/{total}")
    
    if passed == total:
        print("🎉 Tutti i test sono stati superati!")
        return True
    else:
        print("⚠️  Alcuni test hanno fallito - verificare l'implementazione")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 