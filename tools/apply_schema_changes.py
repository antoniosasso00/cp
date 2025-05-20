#!/usr/bin/env python
"""
Script per applicare modifiche allo schema del database manualmente.
Questo script esegue le modifiche SQL necessarie per rimuovere i campi inutilizzati
da Tool e Parte senza utilizzare le migrazioni Alembic.
"""
import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Setup path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/carbonpilot")

# Connessione al database
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Query SQL per eliminare le colonne
SQL_QUERIES = [
    # Rimuovi campi da Tool
    """
    ALTER TABLE tools 
    DROP COLUMN IF EXISTS data_ultima_manutenzione,
    DROP COLUMN IF EXISTS max_temperatura,
    DROP COLUMN IF EXISTS max_pressione,
    DROP COLUMN IF EXISTS cicli_completati
    """,
    
    # Rimuovi campi da Parte
    """
    ALTER TABLE parti 
    DROP COLUMN IF EXISTS peso,
    DROP COLUMN IF EXISTS spessore,
    DROP COLUMN IF EXISTS cliente
    """
]

async def apply_schema_changes():
    """Applica le modifiche allo schema."""
    print("🔄 Applicazione modifiche allo schema...")
    
    async with AsyncSessionLocal() as session:
        for query in SQL_QUERIES:
            try:
                print(f"🔧 Esecuzione: {query.strip()}")
                await session.execute(text(query))
                await session.commit()
                print("✅ Query eseguita con successo!")
            except Exception as e:
                print(f"❌ Errore nell'esecuzione della query: {str(e)}")
                await session.rollback()

if __name__ == "__main__":
    print("🔧 Inizio modifiche allo schema del database...")
    asyncio.run(apply_schema_changes())
    print("🎉 Operazione completata!") 