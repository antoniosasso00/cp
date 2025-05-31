"""
Test diretto del NestingLayoutService per debug
"""
import sys
import os
sys.path.append('./backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from backend.models.nesting_result import NestingResult
from backend.models.odl import ODL
from backend.services.nesting_layout_service import NestingLayoutService

# Setup database connection
DATABASE_URL = "sqlite:///./carbonpilot.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def test_nesting_service():
    print("🧪 TEST: NestingLayoutService")
    print("=" * 50)
    
    session = Session()
    
    try:
        # Recupera il nesting con tutte le relazioni
        print("1️⃣ Caricamento nesting con relazioni...")
        nesting = session.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list).joinedload(ODL.tool),
            joinedload(NestingResult.odl_list).joinedload(ODL.parte)
        ).filter(NestingResult.id == 1).first()
        
        if not nesting:
            print("❌ Nesting 1 non trovato!")
            return
        
        print(f"✅ Nesting trovato: ID {nesting.id}")
        print(f"   - Autoclave: {nesting.autoclave.nome}")
        print(f"   - ODL list length: {len(nesting.odl_list)}")
        
        # Verifica ogni ODL
        print("\n2️⃣ Verifica ODL individuali:")
        for i, odl in enumerate(nesting.odl_list):
            print(f"   ODL {i+1}: ID={odl.id}")
            print(f"     - Tool: {odl.tool.part_number_tool if odl.tool else 'None'}")
            print(f"     - Parte: {odl.parte.part_number if odl.parte else 'None'}")
            print(f"     - Tool is not None: {odl.tool is not None}")
            print(f"     - Parte is not None: {odl.parte is not None}")
        
        # Test del service
        print("\n3️⃣ Test NestingLayoutService.convert_nesting_to_layout_data:")
        layout_data = NestingLayoutService.convert_nesting_to_layout_data(nesting)
        
        print(f"✅ Layout data generato:")
        print(f"   - ID: {layout_data.id}")
        print(f"   - Autoclave: {layout_data.autoclave.nome}")
        print(f"   - ODL list length: {len(layout_data.odl_list)}")
        print(f"   - Posizioni tool length: {len(layout_data.posizioni_tool)}")
        
        if layout_data.odl_list:
            print("   - ODL nel layout:")
            for odl in layout_data.odl_list:
                print(f"     * ODL {odl.id}: {odl.tool.part_number_tool} - {odl.parte.part_number}")
        else:
            print("   ❌ Nessun ODL nel layout!")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_nesting_service() 