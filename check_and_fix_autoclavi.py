#!/usr/bin/env python3
"""
SCRIPT VERIFICA E FIX AUTOCLAVI 2L
Controlla e aggiorna le autoclavi 2L con peso_max_per_cavalletto_kg = 250kg
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import sessionmaker
from backend.models.db import engine
from backend.models import Autoclave

def check_and_fix_autoclavi():
    """Verifica e sistema le autoclavi 2L"""
    
    print("🔍 VERIFICA E FIX AUTOCLAVI 2L")
    print("=" * 50)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Trova tutte le autoclavi 2L
        autoclavi_2l = session.query(Autoclave).filter(
            Autoclave.usa_cavalletti == True
        ).all()
        
        print(f"\n📋 AUTOCLAVI 2L TROVATE: {len(autoclavi_2l)}")
        print("-" * 40)
        
        # 2. Mostra stato attuale
        for autoclave in autoclavi_2l:
            print(f"\n🔧 {autoclave.nome} (ID: {autoclave.id}):")
            print(f"  🏗️  usa_cavalletti: {autoclave.usa_cavalletti}")
            print(f"  📏 max_cavalletti: {autoclave.max_cavalletti}")
            print(f"  ⚖️  peso_max_per_cavalletto_kg: {autoclave.peso_max_per_cavalletto_kg}")
            print(f"  🏋️  max_load_kg: {autoclave.max_load_kg}")
            
            # Calcola capacità totale livello 1
            if autoclave.peso_max_per_cavalletto_kg and autoclave.max_cavalletti:
                capacita_l1 = autoclave.peso_max_per_cavalletto_kg * autoclave.max_cavalletti
                print(f"  📊 Capacità livello 1: {capacita_l1}kg")
            else:
                print(f"  ❌ Capacità livello 1: Non calcolabile (dati mancanti)")
        
        # 3. Aggiorna le autoclavi con peso_max_per_cavalletto_kg = 250kg
        print(f"\n🔧 AGGIORNAMENTO PESO CAVALLETTI")
        print("-" * 40)
        
        updated_count = 0
        for autoclave in autoclavi_2l:
            # Aggiorna solo se necessario
            if autoclave.peso_max_per_cavalletto_kg != 250.0:
                old_value = autoclave.peso_max_per_cavalletto_kg
                autoclave.peso_max_per_cavalletto_kg = 250.0
                
                print(f"✅ {autoclave.nome}: {old_value}kg → 250kg")
                updated_count += 1
            else:
                print(f"ℹ️  {autoclave.nome}: già 250kg, nessun aggiornamento")
        
        # 4. Salva le modifiche
        if updated_count > 0:
            session.commit()
            print(f"\n💾 SALVATO: {updated_count} autoclavi aggiornate")
        else:
            print(f"\n💾 NESSUN AGGIORNAMENTO NECESSARIO")
        
        # 5. Verifica finale
        print(f"\n📊 VERIFICA FINALE")
        print("-" * 25)
        
        # Ricarica dal database
        
        for autoclave in autoclavi_2l:
            session.refresh(autoclave)
            capacita_l1 = (autoclave.peso_max_per_cavalletto_kg or 0) * (autoclave.max_cavalletti or 0)
            
            print(f"🔧 {autoclave.nome}:")
            print(f"  ✅ Peso/cavalletto: {autoclave.peso_max_per_cavalletto_kg}kg")
            print(f"  ✅ Capacità L1: {capacita_l1}kg")
        
        print(f"\n🎉 CONFIGURAZIONE AUTOCLAVI 2L COMPLETATA!")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = check_and_fix_autoclavi()
    if success:
        print("\n✅ Autoclavi 2L configurate correttamente")
    else:
        print("\n❌ Problemi nella configurazione autoclavi")
    
    exit(0 if success else 1) 