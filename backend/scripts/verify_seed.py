#!/usr/bin/env python3
"""
Script per verificare che i dati del seed aeronautico siano stati inseriti correttamente.
"""

import sys
import os

# Aggiungi il path del backend per import dei modelli
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.odl import ODL
from models.tool import Tool
from models.autoclave import Autoclave
from models.ciclo_cura import CicloCura
from models.parte import Parte

# Configurazione database
DATABASE_URL = "sqlite:///./carbonpilot.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_data():
    """Verifica che i dati siano stati inseriti correttamente"""
    session = SessionLocal()
    
    try:
        print("🔍 VERIFICA DATI SEED AERONAUTICO")
        print("="*50)
        
        # Conta i dati
        odl_count = session.query(ODL).count()
        tool_count = session.query(Tool).count()
        autoclave_count = session.query(Autoclave).count()
        ciclo_count = session.query(CicloCura).count()
        parte_count = session.query(Parte).count()
        
        print(f"📊 CONTEGGI:")
        print(f"   • ODL: {odl_count}")
        print(f"   • Tools: {tool_count}")
        print(f"   • Autoclavi: {autoclave_count}")
        print(f"   • Cicli di cura: {ciclo_count}")
        print(f"   • Parti: {parte_count}")
        
        # Verifica ODL in "Attesa Cura"
        odl_attesa_cura = session.query(ODL).filter(ODL.status == "Attesa Cura").count()
        print(f"\n📋 ODL STATUS:")
        print(f"   • ODL in 'Attesa Cura': {odl_attesa_cura}")
        
        # Mostra primi 5 ODL
        print(f"\n📋 PRIMI 5 ODL:")
        for odl in session.query(ODL).limit(5):
            print(f"   • {odl.numero_odl} - {odl.status} - Priorità {odl.priorita}")
        
        # Verifica dimensioni tools
        tools = session.query(Tool).all()
        if tools:
            sizes = [t.lunghezza_piano for t in tools]
            print(f"\n🔧 TOOLS (dimensioni):")
            print(f"   • Dimensione min: {min(sizes):.1f}mm")
            print(f"   • Dimensione max: {max(sizes):.1f}mm")
            print(f"   • Dimensione media: {sum(sizes)/len(sizes):.1f}mm")
            
            # Mostra primi 5 tools
            print(f"\n🔧 PRIMI 5 TOOLS:")
            for tool in session.query(Tool).limit(5):
                print(f"   • {tool.part_number_tool}: {tool.lunghezza_piano}x{tool.larghezza_piano}mm - Peso: {tool.peso}")
        
        # Verifica autoclavi
        print(f"\n🏭 AUTOCLAVI:")
        for autoclave in session.query(Autoclave).all():
            print(f"   • {autoclave.nome}: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
            print(f"     Linee vuoto: {autoclave.num_linee_vuoto}, Max load: {autoclave.max_load_kg}kg")
        
        # Verifica cicli di cura
        print(f"\n🔄 CICLI DI CURA:")
        for ciclo in session.query(CicloCura).all():
            stasi2_text = f" + {ciclo.temperatura_stasi2}°C x {ciclo.durata_stasi2}min" if ciclo.attiva_stasi2 else ""
            print(f"   • {ciclo.nome}: {ciclo.temperatura_stasi1}°C x {ciclo.durata_stasi1}min{stasi2_text}")
        
        # Verifica che tutti i requisiti siano soddisfatti
        print(f"\n✅ VERIFICA REQUISITI:")
        print(f"   • 45 ODL richiesti: {'✅' if odl_count == 45 else '❌'} ({odl_count}/45)")
        print(f"   • Tutti ODL in 'Attesa Cura': {'✅' if odl_attesa_cura == odl_count else '❌'} ({odl_attesa_cura}/{odl_count})")
        print(f"   • 45 Tools richiesti: {'✅' if tool_count == 45 else '❌'} ({tool_count}/45)")
        print(f"   • 3 Autoclavi richieste: {'✅' if autoclave_count == 3 else '❌'} ({autoclave_count}/3)")
        print(f"   • 4 Cicli cura richiesti: {'✅' if ciclo_count == 4 else '❌'} ({ciclo_count}/4)")
        
        # Verifica dimensioni massime tools
        if tools:
            max_size = max(max(t.lunghezza_piano, t.larghezza_piano) for t in tools)
            print(f"   • Dimensioni tools ≤ 450mm: {'✅' if max_size <= 450 else '❌'} (max: {max_size:.1f}mm)")
        
        # Verifica peso nullo
        tools_with_weight = [t for t in tools if t.peso is not None]
        print(f"   • Peso nullo per tutti i tools: {'✅' if len(tools_with_weight) == 0 else '❌'} ({len(tools_with_weight)} tools con peso)")
        
        # Verifica 2 valvole per tool
        parti_con_2_valvole = session.query(Parte).filter(Parte.num_valvole_richieste == 2).count()
        print(f"   • 2 valvole per ogni tool: {'✅' if parti_con_2_valvole == parte_count else '❌'} ({parti_con_2_valvole}/{parte_count})")
        
        if (odl_count == 45 and odl_attesa_cura == 45 and tool_count == 45 and 
            autoclave_count == 3 and ciclo_count == 4):
            print(f"\n🎉 SEED AERONAUTICO COMPLETATO CON SUCCESSO!")
            print(f"   Il database è pronto per testare il comportamento del nesting aeronautico!")
        else:
            print(f"\n⚠️ ALCUNE VERIFICHE NON SONO PASSATE")
            print(f"   Controlla i dati sopra e riesegui il seed se necessario.")
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    verify_data() 