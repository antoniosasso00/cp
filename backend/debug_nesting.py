#!/usr/bin/env python3
"""Script per analizzare i dati del database relativi al nesting"""

import sys
sys.path.append('.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.odl import ODL
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.tool import Tool
from models.autoclave import Autoclave

def analyze_nesting_data():
    """Analizza i dati nel database per identificare problemi con il nesting"""
    
    engine = create_engine('sqlite:///./carbonpilot.db')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        print("🔍 ANALISI DATI NESTING - STATO ATTUALE")
        print("=" * 60)
        
        # 1. Conteggi generali
        odl_count = db.query(ODL).count()
        cicli_count = db.query(CicloCura).count()
        tool_count = db.query(Tool).count()
        autoclave_count = db.query(Autoclave).count()
        
        print(f"📊 CONTEGGI GENERALI:")
        print(f"   • ODL totali: {odl_count}")
        print(f"   • Cicli di cura: {cicli_count}")
        print(f"   • Tool disponibili: {tool_count}")
        print(f"   • Autoclavi: {autoclave_count}")
        print()
        
        # 2. Analisi ODL
        if odl_count > 0:
            print("📋 ANALISI ODL (primi 5):")
            odls = db.query(ODL).limit(5).all()
            for odl in odls:
                print(f"   • ODL {odl.id}:")
                print(f"     - Status: {odl.status}")
                print(f"     - Parte ID: {odl.parte_id}")
                print(f"     - Tool ID: {odl.tool_id}")
                
                if odl.parte:
                    print(f"     - Parte: '{odl.parte.descrizione_breve}'")
                    print(f"     - Ciclo cura ID: {odl.parte.ciclo_cura_id}")
                    if odl.parte.ciclo_cura:
                        print(f"     - Ciclo nome: '{odl.parte.ciclo_cura.nome}'")
                    else:
                        print(f"     - ❌ PROBLEMA: Ciclo di cura non associato!")
                else:
                    print(f"     - ❌ PROBLEMA: Parte non trovata!")
                    
                if odl.tool:
                    print(f"     - Tool: '{odl.tool.part_number_tool}'")
                    print(f"     - Dimensioni: {odl.tool.lunghezza_piano}x{odl.tool.larghezza_piano}mm")
                    print(f"     - Peso: {odl.tool.peso}kg")
                else:
                    print(f"     - ❌ PROBLEMA: Tool non trovato!")
                print()
        
        # 3. Problemi identificati
        print("🚨 PROBLEMI IDENTIFICATI:")
        
        # Parti senza ciclo di cura
        parti_senza_ciclo = db.query(Parte).filter(Parte.ciclo_cura_id.is_(None)).count()
        if parti_senza_ciclo > 0:
            print(f"   • {parti_senza_ciclo} parti senza ciclo di cura associato")
            
        # Tool senza dimensioni
        tool_senza_dimensioni = db.query(Tool).filter(
            (Tool.lunghezza_piano.is_(None)) | (Tool.larghezza_piano.is_(None))
        ).count()
        if tool_senza_dimensioni > 0:
            print(f"   • {tool_senza_dimensioni} tool senza dimensioni complete")
            
        # Tool senza peso
        tool_senza_peso = db.query(Tool).filter(Tool.peso.is_(None)).count()
        if tool_senza_peso > 0:
            print(f"   • {tool_senza_peso} tool senza peso specificato")
            
        # ODL senza parte o tool
        odl_orfani = db.query(ODL).filter(
            (ODL.parte_id.is_(None)) | (ODL.tool_id.is_(None))
        ).count()
        if odl_orfani > 0:
            print(f"   • {odl_orfani} ODL senza parte o tool associato")
        
        # 4. Test compatibilità cicli di cura
        print("\n🔧 TEST COMPATIBILITÀ CICLI DI CURA:")
        odl_con_ciclo_valido = 0
        odl_senza_ciclo = 0
        
        for odl in db.query(ODL).all():
            if odl.parte and odl.parte.ciclo_cura_id:
                odl_con_ciclo_valido += 1
            else:
                odl_senza_ciclo += 1
                
        print(f"   • ODL con ciclo valido: {odl_con_ciclo_valido}")
        print(f"   • ODL senza ciclo: {odl_senza_ciclo}")
        
        if odl_senza_ciclo > 0:
            print("   ❌ PROBLEMA CRITICO: ODL senza cicli di cura validi!")
            print("   🔧 SOLUZIONE: Associare cicli di cura alle parti corrispondenti")
        
        # 5. Suggerimenti per il fix
        print("\n💡 SUGGERIMENTI PER IL FIX:")
        if cicli_count == 0:
            print("   1. Creare almeno un ciclo di cura nel database")
        if parti_senza_ciclo > 0:
            print("   2. Associare cicli di cura alle parti esistenti")
        if tool_senza_dimensioni > 0 or tool_senza_peso > 0:
            print("   3. Completare i dati dimensionali e di peso dei tool")
        if odl_senza_ciclo > 0:
            print("   4. Verificare che ogni ODL abbia una parte con ciclo di cura valido")
            
        print("\n✅ ANALISI COMPLETATA")
        
    except Exception as e:
        print(f"❌ Errore nell'analisi: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analyze_nesting_data() 