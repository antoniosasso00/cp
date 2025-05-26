# tools/setup_db.py

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

# Carica il .env
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL non definito nel file .env")
    sys.exit(1)

if not DATABASE_URL.startswith("postgresql+asyncpg"):
    print("❌ DATABASE_URL deve iniziare con 'postgresql+asyncpg://' per usare SQLAlchemy async")
    sys.exit(1)

# Importa Base da backend.models.base
from backend.models.base import Base

# Crea l'engine
engine = create_async_engine(DATABASE_URL, echo=True)

async def setup_database():
    async with engine.begin() as conn:
        print("\n⚙️ Creazione tabelle nel database...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tutte le tabelle sono state create con successo.")

if __name__ == "__main__":
    asyncio.run(setup_database())