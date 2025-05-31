#!/usr/bin/env python3
"""
Script semplice per controllare i dati nel database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import get_db
from models.parte import Parte
from models.tool import Tool
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura
from models.odl import ODL
from models.autoclave import Autoclave

def main():
    db = next(get_db())
    
    print("🔍 Controllo Dati Database")
    print("=" * 50)
    
    # Conta entità
    parti_count = db.query(Parte).count()
    tool_count = db.query(Tool).count()
    cataloghi_count = db.query(Catalogo).count()
    cicli_count = db.query(CicloCura).count()
    odl_count = db.query(ODL).count()
    autoclavi_count = db.query(Autoclave).count()
    
    print(f"📦 Parti: {parti_count}")
    print(f"🔧 Tool: {tool_count}")
    print(f"📋 Cataloghi: {cataloghi_count}")
    print(f"🔄 Cicli cura: {cicli_count}")
    print(f"📝 ODL: {odl_count}")
    print(f"🏭 Autoclavi: {autoclavi_count}")
    
    # Mostra tutti gli ODL se esistono
    if odl_count > 0:
        print("\n📝 Tutti gli ODL:")
        odl_list = db.query(ODL).all()
        for odl in odl_list:
            print(f"   ID: {odl.id} | Status: {odl.status} | Priorità: {odl.priorita}")
        
        # Mostra i primi 5 ID per il test
        first_5_ids = [odl.id for odl in odl_list[:5]]
        print(f"\n🎯 Primi 5 ID per test: {first_5_ids}")
    
    # Mostra autoclavi
    if autoclavi_count > 0:
        print("\n🏭 Autoclavi:")
        autoclavi = db.query(Autoclave).all()
        for autoclave in autoclavi:
            print(f"   ID: {autoclave.id} | Nome: {autoclave.nome} | Stato: {autoclave.stato}")
    
    db.close()

if __name__ == "__main__":
    main() 