#!/usr/bin/env python3
"""
Reset Database Tool per CarbonPilot
Strumento per resettare completamente il database e ricrearlo da zero.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command: str, cwd: str = None) -> bool:
    """
    Esegue un comando shell e ritorna True se il comando ha successo.
    
    Args:
        command: Comando da eseguire
        cwd: Directory di lavoro (default: backend)
    
    Returns:
        bool: True se il comando ha successo, False altrimenti
    """
    if cwd is None:
        cwd = str(backend_path)
    
    logger.info(f"🔧 Esecuzione comando: {command}")
    logger.info(f"📁 Directory: {cwd}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120  # Timeout di 2 minuti
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Comando completato con successo")
            if result.stdout.strip():
                logger.info(f"📤 Output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ Comando fallito con codice {result.returncode}")
            if result.stderr.strip():
                logger.error(f"📤 Errore: {result.stderr.strip()}")
            if result.stdout.strip():
                logger.error(f"📤 Output: {result.stdout.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ Timeout del comando dopo 2 minuti")
        return False
    except Exception as e:
        logger.error(f"💥 Errore durante l'esecuzione del comando: {str(e)}")
        return False

def reset_database():
    """
    Resetta completamente il database usando Alembic.
    
    Steps:
    1. Alembic downgrade base (rimuove tutto)
    2. Alembic upgrade head (ricrea schema)
    """
    logger.info("🚀 AVVIO RESET DATABASE")
    logger.info("=" * 50)
    
    # Verifica che la directory backend esista
    if not backend_path.exists():
        logger.error(f"❌ Directory backend non trovata: {backend_path}")
        return False
    
    # Verifica che alembic.ini esista
    alembic_ini = backend_path / "alembic.ini"
    if not alembic_ini.exists():
        logger.error(f"❌ File alembic.ini non trovato: {alembic_ini}")
        return False
    
    # Step 1: Downgrade a base (elimina tutto)
    logger.info("📥 Step 1: Downgrade database a base")
    success = run_command("alembic downgrade base")
    if not success:
        logger.error("❌ Fallito downgrade database")
        return False
    
    # Step 2: Upgrade a head (ricrea schema)
    logger.info("📤 Step 2: Upgrade database a head")
    success = run_command("alembic upgrade head")
    if not success:
        logger.error("❌ Fallito upgrade database")
        return False
    
    # Verifica che il database sia stato ricreato
    db_file = backend_path / "carbonpilot.db"
    if db_file.exists():
        file_size = db_file.stat().st_size
        logger.info(f"✅ Database ricreato: {db_file} ({file_size} bytes)")
    else:
        logger.warning("⚠️  File database non trovato dopo il reset")
    
    logger.info("=" * 50)
    logger.info("🎉 RESET DATABASE COMPLETATO CON SUCCESSO")
    return True

def main():
    """Main function"""
    try:
        success = reset_database()
        
        if success:
            print("✅ Reset database completato con successo!")
            print("💡 Puoi ora eseguire seed_edge_data.py per caricare i dati di test")
            sys.exit(0)
        else:
            print("❌ Reset database fallito!")
            print("🔍 Controlla i log sopra per dettagli")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Reset interrotto dall'utente")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Errore imprevisto: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 