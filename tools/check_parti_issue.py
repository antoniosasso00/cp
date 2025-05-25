#!/usr/bin/env python
"""
Script per diagnosticare il problema con l'endpoint parti che restituisce errore 500.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup ambiente
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "backend"))
load_dotenv()

# Importa i modelli e la configurazione del database
from api.database import get_db
from models.parte import Parte
from models.catalogo import Catalogo
from sqlalchemy.orm import joinedload

def check_parti_data():
    """Controlla i dati delle parti nel database."""
    logger.info("🔍 Controllo dati parti nel database...")
    
    try:
        db = next(get_db())
        
        # Recupera tutte le parti con la relazione catalogo
        parti = db.query(Parte).options(joinedload(Parte.catalogo)).all()
        logger.info(f"📊 Parti totali trovate: {len(parti)}")
        
        # Controlla ogni parte
        problematic_parts = []
        for parte in parti:
            logger.info(f"Parte ID: {parte.id}")
            logger.info(f"  - part_number: {parte.part_number}")
            logger.info(f"  - descrizione_breve: {parte.descrizione_breve}")
            logger.info(f"  - catalogo: {parte.catalogo}")
            
            if parte.catalogo is None:
                logger.warning(f"  ⚠️ PROBLEMA: Parte {parte.id} ha catalogo = None!")
                problematic_parts.append(parte)
            else:
                logger.info(f"  - catalogo.part_number: {parte.catalogo.part_number}")
                logger.info(f"  - catalogo.descrizione: {parte.catalogo.descrizione}")
        
        # Riepilogo problemi
        if problematic_parts:
            logger.error(f"❌ Trovate {len(problematic_parts)} parti con catalogo = None")
            logger.error("Questo causa l'errore 500 nell'endpoint parti perché lo schema ParteResponse richiede il campo catalogo obbligatorio")
            
            # Suggerimenti per risolvere
            logger.info("\n💡 SOLUZIONI POSSIBILI:")
            logger.info("1. Eliminare le parti problematiche")
            logger.info("2. Aggiornare le parti per collegarle a un catalogo esistente")
            logger.info("3. Modificare lo schema ParteResponse per rendere catalogo opzionale")
            
            return False
        else:
            logger.info("✅ Tutte le parti hanno un catalogo valido")
            return True
            
    except Exception as e:
        logger.error(f"❌ Errore durante il controllo: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def check_catalogo_data():
    """Controlla i dati del catalogo."""
    logger.info("\n🔍 Controllo dati catalogo...")
    
    try:
        db = next(get_db())
        
        # Recupera tutti i cataloghi
        cataloghi = db.query(Catalogo).all()
        logger.info(f"📊 Cataloghi totali: {len(cataloghi)}")
        
        for catalogo in cataloghi:
            logger.info(f"Catalogo: {catalogo.part_number}")
            logger.info(f"  - descrizione: {catalogo.descrizione}")
            logger.info(f"  - categoria: {catalogo.categoria}")
            logger.info(f"  - attivo: {catalogo.attivo}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante il controllo catalogo: {str(e)}")
        return False

def test_parti_serialization():
    """Testa la serializzazione delle parti usando lo schema Pydantic."""
    logger.info("\n🔍 Test serializzazione parti...")
    
    try:
        from schemas.parte import ParteResponse
        
        db = next(get_db())
        parti = db.query(Parte).options(joinedload(Parte.catalogo)).all()
        
        for parte in parti:
            try:
                # Prova a serializzare la parte usando lo schema Pydantic
                parte_response = ParteResponse.model_validate(parte)
                logger.info(f"✅ Parte {parte.id} serializzata correttamente")
            except Exception as e:
                logger.error(f"❌ Errore serializzazione Parte {parte.id}: {str(e)}")
                logger.error(f"   Catalogo: {parte.catalogo}")
                return False
        
        logger.info("✅ Tutte le parti si serializzano correttamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante il test di serializzazione: {str(e)}")
        return False

def main():
    """Funzione principale."""
    logger.info("🔍 DIAGNOSI PROBLEMA ENDPOINT PARTI")
    logger.info("=" * 50)
    
    # Step 1: Controlla dati parti
    parti_ok = check_parti_data()
    
    # Step 2: Controlla dati catalogo
    catalogo_ok = check_catalogo_data()
    
    # Step 3: Test serializzazione
    if parti_ok and catalogo_ok:
        serialization_ok = test_parti_serialization()
    else:
        serialization_ok = False
    
    # Riepilogo finale
    logger.info("\n📋 RIEPILOGO DIAGNOSI")
    logger.info("=" * 30)
    logger.info(f"Dati parti: {'✅ OK' if parti_ok else '❌ PROBLEMI'}")
    logger.info(f"Dati catalogo: {'✅ OK' if catalogo_ok else '❌ PROBLEMI'}")
    logger.info(f"Serializzazione: {'✅ OK' if serialization_ok else '❌ PROBLEMI'}")
    
    if parti_ok and catalogo_ok and serialization_ok:
        logger.info("\n🎉 Nessun problema trovato nei dati!")
        logger.info("Il problema potrebbe essere nell'endpoint API stesso.")
    else:
        logger.info("\n🔧 Problemi identificati - vedi dettagli sopra")

if __name__ == "__main__":
    main() 