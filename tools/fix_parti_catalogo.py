#!/usr/bin/env python
"""
Script per identificare e correggere le parti con catalogo None.
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
from sqlalchemy import text

def find_problematic_parts():
    """Trova tutte le parti con catalogo None."""
    logger.info("🔍 Ricerca parti con catalogo None...")
    
    try:
        db = next(get_db())
        
        # Query diretta per trovare parti senza catalogo valido
        query = text("""
            SELECT p.id, p.part_number, p.descrizione_breve, c.part_number as catalogo_pn
            FROM parti p
            LEFT JOIN cataloghi c ON p.part_number = c.part_number
            WHERE c.part_number IS NULL
        """)
        
        result = db.execute(query)
        problematic_parts = result.fetchall()
        
        logger.info(f"📊 Parti problematiche trovate: {len(problematic_parts)}")
        
        for row in problematic_parts:
            logger.warning(f"❌ Parte ID {row.id}: part_number='{row.part_number}', descrizione='{row.descrizione_breve}', catalogo=None")
        
        return problematic_parts
        
    except Exception as e:
        logger.error(f"❌ Errore durante la ricerca: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def list_available_catalogs():
    """Elenca tutti i cataloghi disponibili."""
    logger.info("\n📋 Cataloghi disponibili:")
    
    try:
        db = next(get_db())
        cataloghi = db.query(Catalogo).all()
        
        for catalogo in cataloghi:
            logger.info(f"  - {catalogo.part_number}: {catalogo.descrizione}")
        
        return cataloghi
        
    except Exception as e:
        logger.error(f"❌ Errore durante il recupero cataloghi: {str(e)}")
        return []

def fix_parts_option1_delete():
    """Opzione 1: Elimina le parti problematiche."""
    logger.info("\n🗑️ OPZIONE 1: Eliminazione parti problematiche")
    
    try:
        db = next(get_db())
        
        # Trova parti problematiche
        query = text("""
            SELECT p.id
            FROM parti p
            LEFT JOIN cataloghi c ON p.part_number = c.part_number
            WHERE c.part_number IS NULL
        """)
        
        result = db.execute(query)
        problematic_ids = [row.id for row in result.fetchall()]
        
        if not problematic_ids:
            logger.info("✅ Nessuna parte problematica da eliminare")
            return True
        
        # Conferma eliminazione
        response = input(f"\n⚠️ Eliminare {len(problematic_ids)} parti problematiche? (s/N): ")
        if response.lower() not in ['s', 'si', 'sì', 'y', 'yes']:
            logger.info("❌ Operazione annullata")
            return False
        
        # Elimina le parti
        for part_id in problematic_ids:
            parte = db.query(Parte).filter(Parte.id == part_id).first()
            if parte:
                db.delete(parte)
                logger.info(f"🗑️ Eliminata parte ID {part_id}")
        
        db.commit()
        logger.info(f"✅ Eliminate {len(problematic_ids)} parti problematiche")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante l'eliminazione: {str(e)}")
        return False

def fix_parts_option2_update():
    """Opzione 2: Aggiorna le parti per collegarle a cataloghi esistenti."""
    logger.info("\n🔧 OPZIONE 2: Aggiornamento parti problematiche")
    
    try:
        db = next(get_db())
        
        # Trova parti problematiche
        query = text("""
            SELECT p.id, p.part_number, p.descrizione_breve
            FROM parti p
            LEFT JOIN cataloghi c ON p.part_number = c.part_number
            WHERE c.part_number IS NULL
        """)
        
        result = db.execute(query)
        problematic_parts = result.fetchall()
        
        if not problematic_parts:
            logger.info("✅ Nessuna parte problematica da aggiornare")
            return True
        
        # Recupera cataloghi disponibili
        cataloghi = db.query(Catalogo).all()
        if not cataloghi:
            logger.error("❌ Nessun catalogo disponibile per l'aggiornamento")
            return False
        
        logger.info(f"\n📋 Cataloghi disponibili:")
        for i, catalogo in enumerate(cataloghi):
            logger.info(f"  {i+1}. {catalogo.part_number}: {catalogo.descrizione}")
        
        # Per ogni parte problematica, chiedi a quale catalogo collegarla
        for row in problematic_parts:
            logger.info(f"\n🔧 Parte ID {row.id}: '{row.descrizione_breve}' (part_number: {row.part_number})")
            
            while True:
                try:
                    choice = input(f"Scegli catalogo (1-{len(cataloghi)}) o 's' per saltare: ")
                    if choice.lower() == 's':
                        logger.info("⏭️ Saltata")
                        break
                    
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(cataloghi):
                        new_catalog = cataloghi[choice_idx]
                        
                        # Aggiorna la parte
                        parte = db.query(Parte).filter(Parte.id == row.id).first()
                        if parte:
                            parte.part_number = new_catalog.part_number
                            logger.info(f"✅ Aggiornata parte ID {row.id} con catalogo {new_catalog.part_number}")
                        break
                    else:
                        logger.warning("❌ Scelta non valida")
                        
                except ValueError:
                    logger.warning("❌ Inserisci un numero valido")
        
        db.commit()
        logger.info("✅ Aggiornamento completato")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante l'aggiornamento: {str(e)}")
        return False

def fix_parts_option3_schema():
    """Opzione 3: Modifica lo schema per rendere catalogo opzionale."""
    logger.info("\n📝 OPZIONE 3: Modifica schema ParteResponse")
    logger.info("Questa opzione richiede modifiche al codice:")
    logger.info("1. Modificare schemas/parte.py per rendere catalogo opzionale")
    logger.info("2. Aggiornare il frontend per gestire catalogo None")
    logger.info("3. Testare tutte le funzionalità che dipendono dal catalogo")
    logger.info("\n⚠️ Questa è la soluzione più complessa e richiede modifiche manuali al codice")
    return False

def test_endpoint_after_fix():
    """Testa l'endpoint parti dopo la correzione."""
    logger.info("\n🧪 Test endpoint parti...")
    
    import requests
    
    try:
        response = requests.get("http://localhost:8000/api/v1/parti/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Endpoint parti OK - {len(data)} parti recuperate")
            return True
        else:
            logger.error(f"❌ Endpoint parti ancora problematico: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Errore nel test endpoint: {str(e)}")
        return False

def main():
    """Funzione principale."""
    logger.info("🔧 CORREZIONE PROBLEMA PARTI CON CATALOGO NONE")
    logger.info("=" * 60)
    
    # Step 1: Identifica parti problematiche
    problematic_parts = find_problematic_parts()
    
    if not problematic_parts:
        logger.info("✅ Nessuna parte problematica trovata!")
        # Testa comunque l'endpoint
        test_endpoint_after_fix()
        return
    
    # Step 2: Mostra cataloghi disponibili
    cataloghi = list_available_catalogs()
    
    # Step 3: Proponi soluzioni
    logger.info("\n💡 SOLUZIONI DISPONIBILI:")
    logger.info("1. Eliminare le parti problematiche (RAPIDO)")
    logger.info("2. Aggiornare le parti collegandole a cataloghi esistenti (SICURO)")
    logger.info("3. Modificare lo schema per rendere catalogo opzionale (COMPLESSO)")
    
    while True:
        choice = input("\nScegli soluzione (1-3) o 'q' per uscire: ")
        
        if choice == 'q':
            logger.info("❌ Operazione annullata")
            return
        elif choice == '1':
            success = fix_parts_option1_delete()
            break
        elif choice == '2':
            success = fix_parts_option2_update()
            break
        elif choice == '3':
            success = fix_parts_option3_schema()
            break
        else:
            logger.warning("❌ Scelta non valida")
    
    # Step 4: Test finale
    if success and choice in ['1', '2']:
        logger.info("\n🧪 Test finale...")
        test_endpoint_after_fix()

if __name__ == "__main__":
    main() 