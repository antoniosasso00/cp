#!/usr/bin/env python3
"""
Script per verificare il contenuto del database CarbonPilot
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.tool import Tool
from models.ciclo_cura import CicloCura

# Database connection
DATABASE_URL = "sqlite:///./carbonpilot.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    """Verifica il contenuto del database"""
    print("🔍 VERIFICA CONTENUTO DATABASE CARBONPILOT")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # 1. Verifica ODL
        print("\n📋 1. VERIFICA ODL")
        print("-" * 20)
        
        total_odl = db.query(ODL).count()
        print(f"ODL totali nel database: {total_odl}")
        
        if total_odl > 0:
            # ODL per stato
            stati_odl = db.execute(text("SELECT status, COUNT(*) FROM odl GROUP BY status")).fetchall()
            print("ODL per stato:")
            for stato, count in stati_odl:
                print(f"  - {stato}: {count}")
            
            # ODL in attesa cura
            odl_attesa_cura = db.query(ODL).filter(ODL.status == "Attesa Cura").count()
            print(f"\nODL in 'Attesa Cura': {odl_attesa_cura}")
            
            if odl_attesa_cura > 0:
                print("Dettagli ODL in attesa cura:")
                odl_list = db.query(ODL).filter(ODL.status == "Attesa Cura").limit(5).all()
                for odl in odl_list:
                    print(f"  - ODL #{odl.id}: Priorità {odl.priorita}")
                    if odl.parte:
                        print(f"    Parte: {odl.parte.descrizione_breve}")
                    if odl.tool:
                        print(f"    Tool: {odl.tool.part_number_tool}")
        else:
            print("❌ Nessun ODL trovato nel database!")
        
        # 2. Verifica Autoclavi
        print("\n🏭 2. VERIFICA AUTOCLAVI")
        print("-" * 25)
        
        total_autoclavi = db.query(Autoclave).count()
        print(f"Autoclavi totali nel database: {total_autoclavi}")
        
        if total_autoclavi > 0:
            # Autoclavi per stato
            stati_autoclavi = db.execute(text("SELECT stato, COUNT(*) FROM autoclavi GROUP BY stato")).fetchall()
            print("Autoclavi per stato:")
            for stato, count in stati_autoclavi:
                print(f"  - {stato}: {count}")
            
            # Autoclavi disponibili
            autoclavi_disponibili = db.query(Autoclave).filter(Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE).count()
            print(f"\nAutoclavi DISPONIBILI: {autoclavi_disponibili}")
            
            if autoclavi_disponibili > 0:
                print("Dettagli autoclavi disponibili:")
                autoclave_list = db.query(Autoclave).filter(Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE).all()
                for autoclave in autoclave_list:
                    print(f"  - {autoclave.nome} ({autoclave.codice}): {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
        else:
            print("❌ Nessuna autoclave trovata nel database!")
        
        # 3. Verifica Parti
        print("\n🔧 3. VERIFICA PARTI")
        print("-" * 18)
        
        total_parti = db.query(Parte).count()
        print(f"Parti totali nel database: {total_parti}")
        
        if total_parti > 0:
            parti_sample = db.query(Parte).limit(3).all()
            print("Esempi di parti:")
            for parte in parti_sample:
                print(f"  - {parte.part_number}: {parte.descrizione_breve}")
        
        # 4. Verifica Tools
        print("\n🛠️ 4. VERIFICA TOOLS")
        print("-" * 19)
        
        total_tools = db.query(Tool).count()
        print(f"Tools totali nel database: {total_tools}")
        
        if total_tools > 0:
            tools_sample = db.query(Tool).limit(3).all()
            print("Esempi di tools:")
            for tool in tools_sample:
                print(f"  - {tool.part_number_tool}: {tool.larghezza_piano}x{tool.lunghezza_piano}mm")
        
        # 5. Verifica Cicli Cura
        print("\n🔥 5. VERIFICA CICLI CURA")
        print("-" * 24)
        
        total_cicli = db.query(CicloCura).count()
        print(f"Cicli cura totali nel database: {total_cicli}")
        
        if total_cicli > 0:
            cicli_sample = db.query(CicloCura).limit(3).all()
            print("Esempi di cicli cura:")
            for ciclo in cicli_sample:
                print(f"  - {ciclo.nome}: {ciclo.temperatura_stasi1}°C, {ciclo.pressione_stasi1} bar")
        
        # 6. Test di integrità relazioni
        print("\n🔗 6. TEST INTEGRITÀ RELAZIONI")
        print("-" * 32)
        
        # ODL con parti e tools
        if total_odl > 0:
            odl_con_parte = db.query(ODL).filter(ODL.parte_id.isnot(None)).count()
            odl_con_tool = db.query(ODL).filter(ODL.tool_id.isnot(None)).count()
            print(f"ODL con parte associata: {odl_con_parte}/{total_odl}")
            print(f"ODL con tool associato: {odl_con_tool}/{total_odl}")
        
        # Parti con cicli cura
        if total_parti > 0:
            parti_con_ciclo = db.query(Parte).filter(Parte.ciclo_cura_id.isnot(None)).count()
            print(f"Parti con ciclo cura: {parti_con_ciclo}/{total_parti}")
        
        # 7. Diagnosi problemi
        print("\n🩺 7. DIAGNOSI PROBLEMI")
        print("-" * 22)
        
        problemi = []
        
        if total_odl == 0:
            problemi.append("❌ Database vuoto: nessun ODL presente")
        elif odl_attesa_cura == 0:
            problemi.append("⚠️ Nessun ODL in 'Attesa Cura' - il nesting non può funzionare")
        
        if total_autoclavi == 0:
            problemi.append("❌ Nessuna autoclave nel database")
        elif autoclavi_disponibili == 0:
            problemi.append("⚠️ Nessuna autoclave 'DISPONIBILE' - il nesting non può funzionare")
        
        if odl_con_parte < total_odl:
            problemi.append(f"⚠️ {total_odl - odl_con_parte} ODL senza parte associata")
        
        if odl_con_tool < total_odl:
            problemi.append(f"⚠️ {total_odl - odl_con_tool} ODL senza tool associato")
        
        if problemi:
            print("Problemi identificati:")
            for problema in problemi:
                print(f"  {problema}")
        else:
            print("✅ Database in buono stato per il nesting!")
        
        print(f"\n✅ Verifica database completata!")
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main() 