#!/usr/bin/env python3
"""
Script per verificare la relazione ODL -> Parte -> Ciclo di Cura
"""

from models.db import SessionLocal
from models.odl import ODL
from models.parte import Parte
from models.ciclo_cura import CicloCura
from sqlalchemy.orm import joinedload

def check_ciclo_cura_relation():
    """Verifica la relazione ODL -> Parte -> Ciclo di Cura"""
    db = SessionLocal()
    
    try:
        print("🔍 VERIFICA RELAZIONE ODL -> PARTE -> CICLO DI CURA")
        print("=" * 60)
        
        # Verifica ODL #1 con tutte le relazioni
        odl = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
            joinedload(ODL.tool)
        ).filter(ODL.id == 1).first()
        
        if not odl:
            print("❌ ODL #1 non trovato")
            return
        
        print(f"✅ ODL #1:")
        print(f"   - Status: {odl.status}")
        print(f"   - Parte ID: {odl.parte_id}")
        print(f"   - Tool ID: {odl.tool_id}")
        
        if odl.parte:
            print(f"\n✅ Parte:")
            print(f"   - Part Number: {odl.parte.part_number}")
            print(f"   - Descrizione: {odl.parte.descrizione_breve}")
            print(f"   - Ciclo cura ID: {odl.parte.ciclo_cura_id}")
            print(f"   - Valvole richieste: {odl.parte.num_valvole_richieste}")
            
            if odl.parte.ciclo_cura:
                print(f"\n✅ Ciclo di Cura:")
                print(f"   - ID: {odl.parte.ciclo_cura.id}")
                print(f"   - Nome: {odl.parte.ciclo_cura.nome}")
                print(f"   - Temperatura max: {odl.parte.ciclo_cura.temperatura_max}°C")
                print(f"   - Pressione max: {odl.parte.ciclo_cura.pressione_max} bar")
                print(f"   - Durata stasi 1: {odl.parte.ciclo_cura.durata_stasi1} min")
                if odl.parte.ciclo_cura.attiva_stasi2:
                    print(f"   - Durata stasi 2: {odl.parte.ciclo_cura.durata_stasi2} min")
            else:
                print(f"\n❌ CICLO DI CURA NON TROVATO!")
                print(f"   - Ciclo cura ID nella parte: {odl.parte.ciclo_cura_id}")
                
                # Verifica se esiste un ciclo con quell'ID
                if odl.parte.ciclo_cura_id:
                    ciclo = db.query(CicloCura).filter(CicloCura.id == odl.parte.ciclo_cura_id).first()
                    if ciclo:
                        print(f"   - ✅ Ciclo ID {odl.parte.ciclo_cura_id} esiste: {ciclo.nome}")
                        print(f"   - ❌ Ma la relazione non funziona!")
                    else:
                        print(f"   - ❌ Ciclo ID {odl.parte.ciclo_cura_id} NON ESISTE nel database!")
                else:
                    print(f"   - ❌ Ciclo cura ID è NULL nella parte!")
        else:
            print(f"\n❌ PARTE NON TROVATA!")
        
        # Verifica tutti i cicli di cura disponibili
        print(f"\n📋 CICLI DI CURA DISPONIBILI:")
        cicli = db.query(CicloCura).all()
        if cicli:
            for ciclo in cicli:
                print(f"   - ID {ciclo.id}: {ciclo.nome} ({ciclo.temperatura_max}°C, {ciclo.pressione_max}bar)")
        else:
            print("   - ❌ Nessun ciclo di cura trovato nel database!")
        
        print("\n" + "=" * 60)
        print("Verifica completata!")
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    check_ciclo_cura_relation() 