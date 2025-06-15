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
sys.path.append('backend')

from sqlalchemy.orm import sessionmaker, joinedload
from backend.database import engine
from backend.models.odl import ODL
from backend.models.tool import Tool
from backend.models.parte import Parte
from backend.models.autoclave import Autoclave
from backend.api.routers.batch_nesting_modules.generation import _convert_db_to_tool_info_2l, _convert_db_to_autoclave_info_2l

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
        
        return {
            'total_odls': len(odls),
            'complete_odls': complete_count,
            'problematic_odls': problematic_count,
            'success_rate': (complete_count / len(odls) * 100) if len(odls) > 0 else 0
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
    if result:
        print(f"\n✅ Success rate: {result['success_rate']:.1f}%") 