#!/usr/bin/env python3
"""
Script per testare il sistema di efficienza dei batch nesting.
Crea un batch con area 55% per testare badge rosso + popup.

Uso: python seed_efficiency_test.py
"""

import sys
import os
import uuid

# Aggiungi il path root del progetto per gli import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from backend.models.autoclave import Autoclave, StatoAutoclaveEnum
from backend.models.odl import ODL, StatusEnum
from backend.models.parte import Parte
from backend.models.tool import Tool
from backend.models.catalogo import Catalogo
from backend.models.ciclo_cura import CicloCura
import json

def create_test_efficiency_batch():
    """Crea un batch con efficienza del 55% per testare il sistema di valutazione"""
    
    # Ottieni database session
    db = next(get_db())
    
    try:
        print("🧪 Creazione batch di test per efficienza...")
        
        # Trova o crea un'autoclave disponibile
        autoclave = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).first()
        
        if not autoclave:
            print("📦 Creazione autoclave di test...")
            autoclave = Autoclave(
                nome="Autoclave Test Efficienza",
                codice="AUTO-TEST-EFF",
                lunghezza=1000.0,  # 1000mm
                larghezza_piano=800.0,  # 800mm  
                produttore="Test Manufacturing",
                num_linee_vuoto=10,
                max_load_kg=500.0,
                stato=StatoAutoclaveEnum.DISPONIBILE
            )
            db.add(autoclave)
            db.commit()
            db.refresh(autoclave)
        
        # Area totale autoclave: 1000 * 800 = 800,000 mm²
        area_totale_autoclave = autoclave.lunghezza * autoclave.larghezza_piano
        
        # Per ottenere 55% di efficienza:
        # - area_pct = 55% = 0.55
        # - vacuum_util_pct = 50% = 0.50 (assumiamo)
        # - efficiency = 0.7 * 55 + 0.3 * 50 = 38.5 + 15 = 53.5%
        
        # Per ottenere area_pct = 55%, serve area utilizzata = 0.55 * 800,000 = 440,000 mm²
        area_target_mm2 = area_totale_autoclave * 0.55  # 440,000 mm²
        area_target_cm2 = area_target_mm2 / 100  # 4,400 cm²
        
        # Valvole utilizzate per 50% utilizzo
        valvole_target = int(autoclave.num_linee_vuoto * 0.5)  # 5 valvole
        
        print(f"🎯 Target: Area {area_target_cm2:.0f} cm², Valvole {valvole_target}")
        
        # Crea il batch nesting
        batch_id = str(uuid.uuid4())
        batch = BatchNesting(
            id=batch_id,
            nome="Batch Test Efficienza 55%",
            stato=StatoBatchNestingEnum.SOSPESO,
            autoclave_id=autoclave.id,
            odl_ids=[1, 2, 3],  # ID fittizi per il test
            area_totale_utilizzata=area_target_cm2,
            valvole_totali_utilizzate=valvole_target,
            peso_totale_kg=150,
            numero_nesting=1,
            note="Batch di test per verificare sistema di efficienza con 55% di area utilizzata",
            creato_da_utente="test_system",
            creato_da_ruolo="ADMIN"
        )
        
        # Aggiorna l'efficienza
        batch.update_efficiency()
        
        db.add(batch)
        db.commit()
        db.refresh(batch)
        
        print(f"✅ Batch creato con successo!")
        print(f"   ID: {batch.id}")
        print(f"   Area %: {batch.area_pct:.1f}%")
        print(f"   Vacuum %: {batch.vacuum_util_pct:.1f}%") 
        print(f"   Efficienza: {batch.efficiency_score:.1f}%")
        print(f"   Livello: {batch.efficiency_level}")
        print(f"   Classe CSS: {batch.efficiency_color_class}")
        
        # Verifica che sia effettivamente nel range "red"
        if batch.efficiency_level == "red":
            print("🔴 Badge ROSSO confermato - il popup di warning dovrebbe apparire!")
        else:
            print(f"⚠️ Attenzione: efficienza {batch.efficiency_score:.1f}% non nel range rosso")
        
        return batch
        
    except Exception as e:
        print(f"❌ Errore nella creazione del batch: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 SEED SCRIPT - Test Efficienza Batch Nesting")
    print("=" * 50)
    
    batch = create_test_efficiency_batch()
    
    print("\n📋 ISTRUZIONI PER IL TEST:")
    print("1. Vai alla pagina nesting preview")
    print("2. Usa i dati del batch creato per vedere il badge rosso")
    print("3. Verifica che appaia il warning toast")
    print(f"4. ID Batch: {batch.id}")
    print("=" * 50) 
 