#!/usr/bin/env python3
"""
Migrazione per aggiornare gli enum del nesting e aggiungere parametri personalizzabili

Questo script:
1. Aggiunge i campi per parametri personalizzabili:
   - padding_mm (Float, default 10.0)
   - borda_mm (Float, default 20.0) 
   - max_valvole_per_autoclave (Integer, nullable)
   - rotazione_abilitata (Boolean, default True)
2. Migra i dati esistenti al nuovo formato
3. Compatibile con SQLite (non usa enum PostgreSQL)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from models.db import get_database_url
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_nesting_enum_and_parameters():
    """Esegue la migrazione degli enum e parametri del nesting"""
    
    # Connessione al database
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    # Determina il tipo di database
    is_sqlite = "sqlite" in database_url.lower()
    is_postgresql = "postgresql" in database_url.lower()
    
    try:
        with engine.connect() as conn:
            # Inizia una transazione
            trans = conn.begin()
            
            try:
                logger.info("🔄 Inizio migrazione nesting parametri...")
                logger.info(f"📊 Database rilevato: {'SQLite' if is_sqlite else 'PostgreSQL' if is_postgresql else 'Altro'}")
                
                # 1. Crea enum solo per PostgreSQL
                if is_postgresql:
                    logger.info("📝 Creazione enum StatoNesting (PostgreSQL)...")
                    try:
                        conn.execute(text("""
                            CREATE TYPE statonesting AS ENUM (
                                'bozza', 
                                'in_sospeso', 
                                'confermato', 
                                'annullato', 
                                'completato'
                            )
                        """))
                        logger.info("✅ Enum StatoNesting creato")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info("ℹ️ Enum StatoNesting già esistente")
                        else:
                            logger.warning(f"⚠️ Possibile errore nella creazione enum: {e}")
                else:
                    logger.info("ℹ️ SQLite rilevato - enum non supportati, uso CHECK constraint")
                
                # 2. Aggiungi i nuovi campi per parametri personalizzabili
                logger.info("📝 Aggiunta campi parametri personalizzabili...")
                
                new_columns = [
                    ("padding_mm", "REAL DEFAULT 10.0", "Spaziatura tra tool in mm"),
                    ("borda_mm", "REAL DEFAULT 20.0", "Bordo minimo dall'autoclave in mm"),
                    ("max_valvole_per_autoclave", "INTEGER", "Limite massimo valvole per autoclave"),
                    ("rotazione_abilitata", "BOOLEAN DEFAULT 1", "Abilita rotazione automatica dei tool")
                ]
                
                for column_name, column_type, description in new_columns:
                    try:
                        conn.execute(text(f"""
                            ALTER TABLE nesting_results 
                            ADD COLUMN {column_name} {column_type}
                        """))
                        logger.info(f"✅ Colonna {column_name} aggiunta")
                    except Exception as e:
                        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                            logger.info(f"ℹ️ Colonna {column_name} già esistente")
                        else:
                            logger.warning(f"⚠️ Errore aggiunta colonna {column_name}: {e}")
                
                # 3. Aggiorna i valori di default per i record esistenti
                logger.info("🔄 Aggiornamento valori di default per record esistenti...")
                
                # Imposta valori di default per i record che hanno NULL
                default_updates = [
                    ("padding_mm", "10.0"),
                    ("borda_mm", "20.0"),
                    ("rotazione_abilitata", "1" if is_sqlite else "TRUE")
                ]
                
                for column_name, default_value in default_updates:
                    try:
                        result = conn.execute(text(f"""
                            UPDATE nesting_results 
                            SET {column_name} = {default_value}
                            WHERE {column_name} IS NULL
                        """))
                        if result.rowcount > 0:
                            logger.info(f"✅ Aggiornati {result.rowcount} record per {column_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Errore aggiornamento {column_name}: {e}")
                
                # 4. Migrazione stati esistenti (solo aggiornamento valori)
                logger.info("🔄 Migrazione stati al nuovo formato...")
                
                state_mapping = {
                    "Bozza": "bozza",
                    "In sospeso": "in_sospeso", 
                    "In attesa schedulazione": "in_sospeso",
                    "Schedulato": "confermato",
                    "Confermato": "confermato",
                    "Completato": "completato",
                    "Annullato": "annullato"
                }
                
                for old_state, new_state in state_mapping.items():
                    try:
                        result = conn.execute(text("""
                            UPDATE nesting_results 
                            SET stato = :new_state 
                            WHERE stato = :old_state
                        """), {"old_state": old_state, "new_state": new_state})
                        
                        if result.rowcount > 0:
                            logger.info(f"✅ Migrati {result.rowcount} record da '{old_state}' a '{new_state}'")
                    except Exception as e:
                        logger.warning(f"⚠️ Errore migrazione stato {old_state}: {e}")
                
                # 5. Gestisci stati non mappati (imposta default a 'in_sospeso')
                try:
                    result = conn.execute(text("""
                        UPDATE nesting_results 
                        SET stato = 'in_sospeso'
                        WHERE stato NOT IN ('bozza', 'in_sospeso', 'confermato', 'annullato', 'completato')
                    """))
                    if result.rowcount > 0:
                        logger.info(f"✅ Impostati {result.rowcount} record non mappati a 'in_sospeso'")
                except Exception as e:
                    logger.warning(f"⚠️ Errore normalizzazione stati: {e}")
                
                # 6. Aggiungi CHECK constraint per SQLite (simula enum)
                if is_sqlite:
                    try:
                        # SQLite non supporta ADD CONSTRAINT, quindi creiamo una nuova tabella
                        logger.info("📝 Aggiunta CHECK constraint per stati (SQLite)...")
                        # Per ora saltiamo questo step, sarà gestito dal modello SQLAlchemy
                        logger.info("ℹ️ CHECK constraint sarà gestito dal modello SQLAlchemy")
                    except Exception as e:
                        logger.warning(f"⚠️ Errore CHECK constraint: {e}")
                
                # 7. Verifica i risultati finali
                logger.info("📊 Verifica risultati migrazione...")
                
                # Conta stati attuali
                try:
                    result = conn.execute(text("SELECT stato, COUNT(*) as count FROM nesting_results GROUP BY stato"))
                    logger.info("📊 Stati attuali nel database:")
                    for row in result:
                        logger.info(f"   - {row.stato}: {row.count} record")
                except Exception as e:
                    logger.warning(f"⚠️ Errore conteggio stati: {e}")
                
                # Verifica parametri
                try:
                    result = conn.execute(text("""
                        SELECT 
                            COUNT(*) as total,
                            AVG(padding_mm) as avg_padding,
                            AVG(borda_mm) as avg_borda,
                            COUNT(max_valvole_per_autoclave) as with_max_valvole,
                            SUM(CASE WHEN rotazione_abilitata THEN 1 ELSE 0 END) as with_rotation
                        FROM nesting_results
                    """))
                    
                    for row in result:
                        logger.info(f"📊 Parametri: {row.total} record totali")
                        if row.avg_padding is not None:
                            logger.info(f"   - Padding medio: {row.avg_padding:.1f}mm")
                        if row.avg_borda is not None:
                            logger.info(f"   - Borda media: {row.avg_borda:.1f}mm")
                        logger.info(f"   - Con limite valvole: {row.with_max_valvole or 0}")
                        logger.info(f"   - Con rotazione abilitata: {row.with_rotation or 0}")
                except Exception as e:
                    logger.warning(f"⚠️ Errore verifica parametri: {e}")
                
                # Commit della transazione
                trans.commit()
                logger.info("✅ Migrazione parametri completata con successo!")
                
            except Exception as e:
                # Rollback in caso di errore
                trans.rollback()
                logger.error(f"❌ Errore durante la migrazione: {e}")
                raise e
                
    except Exception as e:
        logger.error(f"❌ Errore di connessione al database: {e}")
        raise e

if __name__ == "__main__":
    migrate_nesting_enum_and_parameters() 