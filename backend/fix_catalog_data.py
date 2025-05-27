#!/usr/bin/env python3
"""
Script per aggiornare i dati del catalogo con le dimensioni mancanti
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from models.db import get_db, engine
from models.catalogo import Catalogo

def update_catalog_dimensions():
    """Aggiorna le dimensioni dei part number nel catalogo"""
    
    # Dati delle dimensioni per ogni part number (in mm)
    dimensioni_parts = {
        "CPX-101": {"lunghezza": 2000, "larghezza": 1200, "altezza": 50},  # Pannello laterale sinistro
        "CPX-102": {"lunghezza": 2000, "larghezza": 1200, "altezza": 50},  # Pannello laterale destro
        "CPX-201": {"lunghezza": 1200, "larghezza": 800, "altezza": 100},  # Supporto motore principale
        "CPX-202": {"lunghezza": 800, "larghezza": 600, "altezza": 80},    # Supporto motore secondario
        "CPX-301": {"lunghezza": 1000, "larghezza": 800, "altezza": 30},   # Coperchio vano batterie
        "CPX-302": {"lunghezza": 800, "larghezza": 600, "altezza": 30},    # Coperchio vano elettronica
        "CPX-401": {"lunghezza": 1800, "larghezza": 400, "altezza": 60},   # Fascia frontale superiore
        "CPX-402": {"lunghezza": 1200, "larghezza": 350, "altezza": 60},   # Fascia frontale inferiore
        "CPX-501": {"lunghezza": 1200, "larghezza": 300, "altezza": 80},   # Rinforzo strutturale A
        "CPX-502": {"lunghezza": 1000, "larghezza": 250, "altezza": 80},   # Rinforzo strutturale B
    }
    
    db = next(get_db())
    
    try:
        print("🔧 Aggiornamento dimensioni catalogo...")
        
        updated_count = 0
        
        for part_number, dimensioni in dimensioni_parts.items():
            # Trova il part number nel catalogo
            catalogo = db.query(Catalogo).filter(Catalogo.part_number == part_number).first()
            
            if catalogo:
                # Aggiorna le dimensioni
                catalogo.lunghezza = dimensioni["lunghezza"]
                catalogo.larghezza = dimensioni["larghezza"] 
                catalogo.altezza = dimensioni["altezza"]
                
                db.add(catalogo)
                updated_count += 1
                
                area_cm2 = catalogo.area_cm2
                print(f"✅ {part_number}: {dimensioni['lunghezza']}x{dimensioni['larghezza']}mm = {area_cm2:.1f}cm²")
            else:
                print(f"❌ Part number {part_number} non trovato nel catalogo")
        
        # Salva le modifiche
        db.commit()
        print(f"\n🎉 Aggiornati {updated_count} part number con successo!")
        
        # Verifica i risultati
        print("\n📊 Verifica finale:")
        cataloghi = db.query(Catalogo).all()
        for cat in cataloghi:
            area = cat.area_cm2
            print(f"  {cat.part_number}: {area:.1f}cm² ({'✅' if area > 0 else '❌'})")
            
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_catalog_dimensions() 