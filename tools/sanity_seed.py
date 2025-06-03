#!/usr/bin/env python3
"""
Sanity Seed Tool per CarbonPilot v1.4.17-DEMO
Script per creare dati di test specifici per la rotazione 90°

Scenario Test: 3 pezzi 150×300mm in autoclave 200×300mm
Aspettativa: placed=3, rotation_used=true, efficiency ≥ 80%
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from models.database import SessionLocal, engine
from models.models import Autoclave, ODL, Parte, Tool, Catalogo, CicloCura
from sqlalchemy.orm import Session

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_existing_test_data(db: Session):
    """Pulisce dati di test esistenti per evitare conflitti"""
    logger.info("🧹 Pulizia dati test esistenti...")
    
    # Rimuovi ODL di test
    db.query(ODL).filter(ODL.id.in_([9001, 9002, 9003])).delete(synchronize_session=False)
    
    # Rimuovi parti di test  
    db.query(Parte).filter(Parte.id.in_([9001, 9002, 9003])).delete(synchronize_session=False)
    
    # Rimuovi tool di test
    db.query(Tool).filter(Tool.id.in_([9001, 9002, 9003])).delete(synchronize_session=False)
    
    # Rimuovi catalogo di test
    db.query(Catalogo).filter(Catalogo.part_number.like('TEST-ROT-%')).delete(synchronize_session=False)
    
    # Rimuovi autoclave di test
    db.query(Autoclave).filter(Autoclave.id == 9001).delete(synchronize_session=False)
    
    # Rimuovi ciclo cura di test
    db.query(CicloCura).filter(CicloCura.id == 9001).delete(synchronize_session=False)
    
    db.commit()
    logger.info("✅ Pulizia completata")

def create_test_autoclave(db: Session) -> Autoclave:
    """Crea autoclave di test 200×300mm"""
    logger.info("🏭 Creazione autoclave test 200×300mm...")
    
    autoclave = Autoclave(
        id=9001,
        nome="Test-Autoclave-Rotazione",
        codice="TEST-ROT-001",
        larghezza_piano=200.0,  # mm
        lunghezza=300.0,        # mm
        max_load_kg=1000.0,
        num_linee_vuoto=10,
        temperatura_max=200.0,
        pressione_max=8.0,
        produttore="Test-Manufacturer",
        anno_produzione=2024,
        stato="DISPONIBILE",
        use_secondary_plane=False,
        note="Autoclave per test rotazione v1.4.17-DEMO"
    )
    
    db.add(autoclave)
    db.commit()
    db.refresh(autoclave)
    
    logger.info(f"✅ Autoclave creata: {autoclave.nome} ({autoclave.larghezza_piano}×{autoclave.lunghezza}mm)")
    return autoclave

def create_test_ciclo_cura(db: Session) -> CicloCura:
    """Crea ciclo di cura di test"""
    logger.info("🔄 Creazione ciclo cura test...")
    
    ciclo = CicloCura(
        id=9001,
        nome="Test-Ciclo-Rotazione",
        temperatura_stasi1=180.0,
        pressione_stasi1=6.0,
        durata_stasi1=30,
        attiva_stasi2=False,
        descrizione="Ciclo di test per rotazione v1.4.17-DEMO"
    )
    
    db.add(ciclo)
    db.commit()
    db.refresh(ciclo)
    
    logger.info(f"✅ Ciclo cura creato: {ciclo.nome}")
    return ciclo

def create_test_data(db: Session):
    """
    Crea 3 pezzi 150×300mm che richiedono rotazione per entrare in autoclave 200×300mm
    
    Logica: 
    - Autoclave: 200×300mm
    - Pezzi: 150×300mm
    - Orientamento normale: 150mm ≤ 200mm ✅, 300mm ≤ 300mm ✅ → Possibile
    - Orientamento ruotato: 300mm ≤ 200mm ❌, 150mm ≤ 300mm ✅ → Impossibile
    
    Quindi i pezzi dovrebbero essere posizionati normalmente.
    Per forzare la rotazione, creo pezzi 250×150mm:
    - Normale: 250mm ≤ 200mm ❌
    - Ruotato: 150mm ≤ 200mm ✅, 250mm ≤ 300mm ✅ → Rotazione necessaria!
    """
    logger.info("📦 Creazione 3 pezzi test 250×150mm (richiedono rotazione)...")
    
    # Crea ciclo cura
    ciclo_cura = create_test_ciclo_cura(db)
    
    # Crea 3 pezzi identici che richiedono rotazione
    for i in range(1, 4):
        # Catalogo
        part_number = f"TEST-ROT-{i:03d}"
        catalogo = Catalogo(
            part_number=part_number,
            descrizione=f"Test Piece {i} per rotazione 90° - v1.4.17-DEMO",
            categoria="Test-Rotazione",
            sotto_categoria="v1.4.17-DEMO",
            attivo=True,
            note="Pezzo di test per validare rotazione automatica"
        )
        db.add(catalogo)
        
        # Tool - dimensioni che richiedono rotazione
        tool = Tool(
            id=9000 + i,
            part_number_tool=f"TOOL-ROT-{i:03d}",
            larghezza_piano=250.0,   # mm - troppo largo per autoclave (200mm)
            lunghezza_piano=150.0,   # mm - OK per autoclave (300mm)
            peso=20.0 + i,           # kg - diverso per ogni tool
            materiale="Alluminio",
            disponibile=True,
            descrizione=f"Tool test rotazione {i} - 250×150mm"
        )
        db.add(tool)
        
        # Parte
        parte = Parte(
            id=9000 + i,
            part_number=part_number,
            ciclo_cura_id=ciclo_cura.id,
            descrizione_breve=f"Test Piece {i} - Rotazione",
            num_valvole_richieste=1,
            note_produzione=f"Test rotazione v1.4.17-DEMO piece {i}"
        )
        db.add(parte)
        
        # ODL
        odl = ODL(
            id=9000 + i,
            parte_id=9000 + i,
            tool_id=9000 + i,
            status="Preparazione",
            priorita=i,  # Priorità crescente
            note=f"ODL test rotazione {i} - v1.4.17-DEMO"
        )
        db.add(odl)
        
        logger.info(f"  ✅ Creato pezzo {i}: {part_number} - 250×150mm, {20.0 + i}kg")
    
    db.commit()
    logger.info("📦 3 pezzi test creati con successo")

def create_sanity_test_scenario():
    """Crea lo scenario di test per la rotazione"""
    logger.info("🚀 AVVIO CREAZIONE SCENARIO TEST ROTAZIONE v1.4.17-DEMO")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Pulisci dati precedenti
        clear_existing_test_data(db)
        
        # Crea autoclave di test
        autoclave = create_test_autoclave(db)
        
        # Crea i 3 pezzi di test
        create_test_data(db)
        
        logger.info("=" * 60)
        logger.info("🎉 SCENARIO TEST CREATO CON SUCCESSO!")
        logger.info("")
        logger.info("📋 RIASSUNTO SCENARIO:")
        logger.info(f"   🏭 Autoclave: {autoclave.nome} - {autoclave.larghezza_piano}×{autoclave.lunghezza}mm")
        logger.info(f"   📦 Pezzi: 3 × 250×150mm (richiedono rotazione 90°)")
        logger.info(f"   🎯 ODL IDs: 9001, 9002, 9003")
        logger.info(f"   🔄 Rotazione attesa: SÌ (250mm > 200mm → ruota in 150×250mm)")
        logger.info("")
        logger.info("🧪 TEST ASPETTATO:")
        logger.info("   ✅ placed=3 (tutti i pezzi posizionati)")
        logger.info("   ✅ rotation_used=true")
        logger.info("   ✅ efficiency ≥ 80%")
        logger.info("   ✅ algorithm_status contenente 'CP-SAT' o 'BL_FFD'")
        logger.info("")
        logger.info("🚀 PRONTO PER IL TEST!")
        logger.info("   Esegui il nesting con autoclave_id=9001")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la creazione dello scenario: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main function"""
    try:
        success = create_sanity_test_scenario()
        
        if success:
            print("✅ Scenario test rotazione creato con successo!")
            print("🧪 Ora puoi testare il nesting con autoclave_id=9001")
            print("📊 Aspettativa: 3 pezzi posizionati con rotazione_used=true")
            sys.exit(0)
        else:
            print("❌ Creazione scenario fallita!")
            print("🔍 Controlla i log sopra per dettagli")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Creazione scenario interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Errore imprevisto: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 