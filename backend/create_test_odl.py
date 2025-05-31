#!/usr/bin/env python3
"""
🧪 SCRIPT PER CREARE ODL DI TEST
===============================

Crea alcuni ODL di test per verificare il funzionamento delle API.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from models.db import SessionLocal
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura

def create_test_data():
    """Crea dati di test se non esistono"""
    try:
        print("🧪 Creazione dati di test...")
        
        db = SessionLocal()
        
        # Verifica se esistono già dati
        existing_odl = db.query(ODL).count()
        print(f"📋 ODL esistenti: {existing_odl}")
        
        # Crea catalogo di test se non esiste
        catalogo = db.query(Catalogo).first()
        if not catalogo:
            catalogo = Catalogo(
                part_number="TEST001",
                descrizione="Parte di test per curing",
                categoria="Test",
                attivo=True
            )
            db.add(catalogo)
            db.commit()
            print("✅ Creato catalogo di test")
        
        # Crea ciclo di cura di test se non esiste
        ciclo = db.query(CicloCura).first()
        if not ciclo:
            ciclo = CicloCura(
                nome="Ciclo Test",
                temperatura_stasi1=180.0,
                pressione_stasi1=6.0,
                durata_stasi1=120,
                attiva_stasi2=False
            )
            db.add(ciclo)
            db.commit()
            print("✅ Creato ciclo di cura di test")
        
        # Crea parte di test se non esiste
        parte = db.query(Parte).first()
        if not parte:
            parte = Parte(
                part_number=catalogo.part_number,
                descrizione_breve="Parte di test",
                num_valvole_richieste=2,
                ciclo_cura_id=ciclo.id
            )
            db.add(parte)
            db.commit()
            print("✅ Creata parte di test")
        
        # Crea tool di test se non esiste
        tool = db.query(Tool).first()
        if not tool:
            tool = Tool(
                part_number_tool="TOOL001",
                descrizione="Tool di test",
                lunghezza_piano=300.0,
                larghezza_piano=200.0,
                disponibile=True
            )
            db.add(tool)
            db.commit()
            print("✅ Creato tool di test")
        
        # Crea ODL di test
        test_odl_data = [
            {"status": "Attesa Cura", "priorita": 5, "note": "ODL test in attesa cura"},
            {"status": "Attesa Cura", "priorita": 3, "note": "ODL test in attesa cura 2"},
            {"status": "Cura", "priorita": 4, "note": "ODL test in cura"},
            {"status": "Preparazione", "priorita": 2, "note": "ODL test in preparazione"},
            {"status": "Finito", "priorita": 1, "note": "ODL test finito"},
        ]
        
        created_count = 0
        for odl_data in test_odl_data:
            # Verifica se esiste già un ODL con questo stato
            existing = db.query(ODL).filter(
                ODL.status == odl_data["status"],
                ODL.note == odl_data["note"]
            ).first()
            
            if not existing:
                odl = ODL(
                    parte_id=parte.id,
                    tool_id=tool.id,
                    status=odl_data["status"],
                    priorita=odl_data["priorita"],
                    note=odl_data["note"]
                )
                db.add(odl)
                created_count += 1
        
        db.commit()
        
        if created_count > 0:
            print(f"✅ Creati {created_count} ODL di test")
        else:
            print("ℹ️ ODL di test già esistenti")
        
        # Verifica finale
        print("\n📊 Riepilogo ODL per stato:")
        stati = ["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"]
        for stato in stati:
            count = db.query(ODL).filter(ODL.status == stato).count()
            print(f"   • {stato}: {count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la creazione dati di test: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

if __name__ == "__main__":
    success = create_test_data()
    if success:
        print("\n🎉 Dati di test creati con successo!")
    else:
        print("\n💥 Creazione dati di test fallita!") 