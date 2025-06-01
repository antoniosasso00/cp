#!/usr/bin/env python3
"""
Script per l'aggiornamento notturno automatico dei tempi standard.
Questo script può essere eseguito da un cron job per mantenere aggiornati i tempi standard.

Uso:
    python tools/nightly_std_update.py

Oppure con logging dettagliato:
    python tools/nightly_std_update.py --verbose

Per eseguire in modalità dry-run (solo simulazione):
    python tools/nightly_std_update.py --dry-run
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Aggiungi il path del backend al sys.path per poter importare i moduli
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models.db import SessionLocal
from services.standard_time_service import recalc_std_times

# Crea la directory logs se non esiste
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'nightly_std_update.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Funzione principale dello script di aggiornamento notturno."""
    
    parser = argparse.ArgumentParser(description='Aggiornamento notturno dei tempi standard')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Abilita logging dettagliato')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Esegue solo una simulazione senza modificare il database')
    
    args = parser.parse_args()
    
    # Imposta il livello di logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🔍 Modalità verbose abilitata")
    
    # Informazioni di avvio
    logger.info("🌙 === INIZIO AGGIORNAMENTO NOTTURNO TEMPI STANDARD ===")
    logger.info(f"📅 Data/ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.dry_run:
        logger.info("🔍 MODALITÀ DRY-RUN: Nessuna modifica verrà apportata al database")
        # In modalità dry-run, potresti voler implementare una logica diversa
        # Per ora stampiamo solo un messaggio
        logger.info("✅ Dry-run completato")
        return 0
    
    try:
        # Ottieni una sessione del database
        logger.debug("🔗 Apertura connessione al database...")
        db = SessionLocal()
        
        # Esegui il ricalcolo dei tempi standard
        logger.info("🔄 Avvio ricalcolo automatico dei tempi standard...")
        
        result = recalc_std_times(
            db=db, 
            user_id="nightly_job", 
            user_role="ADMIN"
        )
        
        # Stampa i risultati
        logger.info("📊 === RISULTATI AGGIORNAMENTO ===")
        logger.info(f"📈 Combinazioni part-fase analizzate: {result['total_combinations']}")
        logger.info(f"✅ Record aggiornati: {result['updated_records']}")
        logger.info(f"🆕 Record creati: {result['created_records']}")
        logger.info(f"❌ Errori: {result['errors']}")
        
        if args.verbose and result['details']:
            logger.debug("📋 Dettagli per combinazione:")
            for detail in result['details']:
                if detail.get('action') == 'error':
                    logger.debug(f"  ❌ {detail['part_number']}-{detail['fase']}: {detail['error']}")
                else:
                    logger.debug(f"  ✅ {detail['part_number']}-{detail['fase']}: "
                               f"{detail['action']} (analizzati: {detail['records_analyzed']}, "
                               f"avg: {detail['avg_minutes']}min)")
        
        # Chiudi la sessione
        db.close()
        
        # Messaggio di completamento
        total_operations = result['updated_records'] + result['created_records']
        if result['errors'] == 0:
            logger.info(f"🎉 Aggiornamento completato con successo! "
                       f"Eseguite {total_operations} operazioni.")
            return 0
        else:
            logger.warning(f"⚠️ Aggiornamento completato con {result['errors']} errori. "
                          f"Eseguite {total_operations} operazioni.")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Errore critico durante l'aggiornamento: {str(e)}")
        return 2
    
    finally:
        logger.info("🌙 === FINE AGGIORNAMENTO NOTTURNO TEMPI STANDARD ===")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 