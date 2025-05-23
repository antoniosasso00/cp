#!/usr/bin/env python3
"""
Script per inserire dati di test nel catalogo con sotto-categorie
"""

import asyncio
import sys
import os

# Aggiungi il percorso del backend al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from api.database import get_db
from models.catalogo import Catalogo

def create_test_data():
    """Crea dati di test per il catalogo con sotto-categorie"""
    
    # Ottieni una sessione del database
    db = next(get_db())
    
    test_data = [
        {
            "part_number": "VALVE001",
            "descrizione": "Valvola di controllo principale",
            "categoria": "Valvole",
            "sotto_categoria": "Controllo",
            "attivo": True,
            "note": "Valvola per controllo flusso principale"
        },
        {
            "part_number": "VALVE002", 
            "descrizione": "Valvola di sicurezza",
            "categoria": "Valvole",
            "sotto_categoria": "Sicurezza",
            "attivo": True,
            "note": "Valvola di emergenza per sicurezza"
        },
        {
            "part_number": "SENSOR001",
            "descrizione": "Sensore di temperatura",
            "categoria": "Sensori",
            "sotto_categoria": "Temperatura",
            "attivo": True,
            "note": "Sensore per monitoraggio temperatura"
        },
        {
            "part_number": "SENSOR002",
            "descrizione": "Sensore di pressione",
            "categoria": "Sensori", 
            "sotto_categoria": "Pressione",
            "attivo": True,
            "note": "Sensore per monitoraggio pressione"
        },
        {
            "part_number": "PUMP001",
            "descrizione": "Pompa centrifuga",
            "categoria": "Pompe",
            "sotto_categoria": "Centrifughe",
            "attivo": True,
            "note": "Pompa per circolazione fluidi"
        },
        {
            "part_number": "PUMP002",
            "descrizione": "Pompa a vuoto",
            "categoria": "Pompe",
            "sotto_categoria": "Vuoto",
            "attivo": False,
            "note": "Pompa per creazione vuoto - Dismessa"
        },
        {
            "part_number": "FILTER001",
            "descrizione": "Filtro aria",
            "categoria": "Filtri",
            "sotto_categoria": "Aria",
            "attivo": True,
            "note": "Filtro per purificazione aria"
        },
        {
            "part_number": "FILTER002",
            "descrizione": "Filtro olio",
            "categoria": "Filtri",
            "sotto_categoria": "Olio",
            "attivo": True,
            "note": "Filtro per purificazione olio"
        }
    ]
    
    try:
        for item_data in test_data:
            # Controlla se il part number esiste già
            existing = db.query(Catalogo).filter(Catalogo.part_number == item_data["part_number"]).first()
            
            if not existing:
                catalogo_item = Catalogo(**item_data)
                db.add(catalogo_item)
                print(f"✅ Aggiunto: {item_data['part_number']} - {item_data['descrizione']}")
            else:
                print(f"⚠️  Già esistente: {item_data['part_number']}")
        
        db.commit()
        print(f"\n🎉 Dati di test inseriti con successo!")
        print(f"📊 Totale elementi nel catalogo: {db.query(Catalogo).count()}")
        
        # Mostra statistiche per categoria
        print("\n📈 Statistiche per categoria:")
        categories = db.query(Catalogo.categoria, Catalogo.sotto_categoria).distinct().all()
        for cat, sotto_cat in categories:
            if cat:
                count = db.query(Catalogo).filter(Catalogo.categoria == cat, Catalogo.sotto_categoria == sotto_cat).count()
                print(f"   {cat} > {sotto_cat}: {count} elementi")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante l'inserimento: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Inserimento dati di test per il catalogo...")
    create_test_data() 