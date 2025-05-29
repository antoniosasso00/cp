#!/usr/bin/env python3
"""
Migrazione per aggiungere le colonne peso e materiale alla tabella tools.
Queste colonne sono necessarie per il nesting con orientamento e quote.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_tool_peso_materiale_columns():
    """Aggiunge le colonne peso e materiale alla tabella tools"""
    
    # Percorso del database
    db_path = Path(__file__).parent.parent.parent / "carbonpilot.db"
    
    if not db_path.exists():
        logger.error(f"Database non trovato: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica struttura attuale
        cursor.execute('PRAGMA table_info(tools)')
        columns = cursor.fetchall()
        column_names = [row[1] for row in columns]
        
        logger.info(f"Colonne attuali in tools: {column_names}")
        
        # Aggiungi colonna peso se non esiste
        if 'peso' not in column_names:
            logger.info("Aggiunta colonna 'peso' alla tabella tools...")
            cursor.execute('ALTER TABLE tools ADD COLUMN peso FLOAT')
            logger.info("✅ Colonna 'peso' aggiunta con successo")
        else:
            logger.info("✅ Colonna 'peso' già presente")
        
        # Aggiungi colonna materiale se non esiste
        if 'materiale' not in column_names:
            logger.info("Aggiunta colonna 'materiale' alla tabella tools...")
            cursor.execute('ALTER TABLE tools ADD COLUMN materiale VARCHAR(100)')
            logger.info("✅ Colonna 'materiale' aggiunta con successo")
        else:
            logger.info("✅ Colonna 'materiale' già presente")
        
        # Aggiungi colonna orientamento se non esiste (per il nesting)
        if 'orientamento_preferito' not in column_names:
            logger.info("Aggiunta colonna 'orientamento_preferito' alla tabella tools...")
            cursor.execute('ALTER TABLE tools ADD COLUMN orientamento_preferito VARCHAR(20) DEFAULT "auto"')
            logger.info("✅ Colonna 'orientamento_preferito' aggiunta con successo")
        else:
            logger.info("✅ Colonna 'orientamento_preferito' già presente")
        
        # Commit delle modifiche
        conn.commit()
        
        # Verifica finale
        cursor.execute('PRAGMA table_info(tools)')
        new_columns = cursor.fetchall()
        new_column_names = [row[1] for row in new_columns]
        
        logger.info(f"Nuove colonne in tools: {new_column_names}")
        
        # Aggiorna alcuni tool di esempio con dati di peso e materiale
        logger.info("Aggiornamento dati di esempio...")
        
        # Verifica se ci sono tool nel database
        cursor.execute('SELECT COUNT(*) FROM tools')
        tool_count = cursor.fetchone()[0]
        
        if tool_count > 0:
            # Aggiorna i primi tool con dati di esempio
            cursor.execute('''
                UPDATE tools 
                SET peso = CASE 
                    WHEN peso IS NULL THEN 
                        CASE 
                            WHEN (lunghezza_piano * larghezza_piano) < 50000 THEN 5.0
                            WHEN (lunghezza_piano * larghezza_piano) < 100000 THEN 10.0
                            ELSE 15.0
                        END
                    ELSE peso
                END,
                materiale = CASE 
                    WHEN materiale IS NULL THEN 'Alluminio'
                    ELSE materiale
                END
                WHERE peso IS NULL OR materiale IS NULL
            ''')
            
            updated_rows = cursor.rowcount
            logger.info(f"✅ Aggiornati {updated_rows} tool con dati di esempio")
        
        conn.commit()
        conn.close()
        
        logger.info("🎉 Migrazione completata con successo!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la migrazione: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """Verifica che la migrazione sia stata applicata correttamente"""
    
    db_path = Path(__file__).parent.parent.parent / "carbonpilot.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica struttura
        cursor.execute('PRAGMA table_info(tools)')
        columns = cursor.fetchall()
        column_names = [row[1] for row in columns]
        
        required_columns = ['peso', 'materiale', 'orientamento_preferito']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            logger.error(f"❌ Colonne mancanti: {missing_columns}")
            return False
        
        # Verifica dati
        cursor.execute('SELECT COUNT(*) FROM tools WHERE peso IS NOT NULL')
        tools_with_peso = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tools WHERE materiale IS NOT NULL')
        tools_with_materiale = cursor.fetchone()[0]
        
        logger.info(f"✅ Verifica completata:")
        logger.info(f"  - Tutte le colonne richieste sono presenti")
        logger.info(f"  - Tool con peso: {tools_with_peso}")
        logger.info(f"  - Tool con materiale: {tools_with_materiale}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la verifica: {e}")
        return False

def main():
    """Esegue la migrazione e la verifica"""
    logger.info("🚀 Avvio migrazione per aggiungere colonne peso e materiale ai tools")
    
    if add_tool_peso_materiale_columns():
        if verify_migration():
            logger.info("🎉 Migrazione e verifica completate con successo!")
            return True
        else:
            logger.error("❌ Verifica fallita")
            return False
    else:
        logger.error("❌ Migrazione fallita")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1) 