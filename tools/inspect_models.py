# tools/inspect_all_models.py

import os
import sys
import asyncio
import importlib
import inspect
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from dotenv import load_dotenv

# Setup path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# Load .env and DB URL
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL non definito nel file .env")
    sys.exit(1)

if not DATABASE_URL.startswith("postgresql+asyncpg"):
    print("❌ DATABASE_URL deve iniziare con 'postgresql+asyncpg://' per usare SQLAlchemy async")
    sys.exit(1)

# DB engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Importa dinamicamente tutti i modelli da backend.models
MODELS_PATH = ROOT_DIR / "backend" / "models"
MODEL_MODULE = "backend.models"

async def inspect_all():
    async with AsyncSessionLocal() as session:
        print("\n📊 MODEL INSPECTION REPORT:\n")

        for file in MODELS_PATH.glob("*.py"):
            if file.name in {"__init__.py", "base.py"}:
                continue

            module_name = f"{MODEL_MODULE}.{file.stem}"
            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                print(f"❌ Errore import {module_name}: {e}")
                continue

            # Cerca le classi SQLAlchemy
            classes = [obj for name, obj in inspect.getmembers(module)
                       if inspect.isclass(obj)
                       and hasattr(obj, '__tablename__')
                       and hasattr(obj, '__table__')]

            for model_class in classes:
                try:
                    result = await session.execute(select(model_class))
                    items = result.scalars().all()
                    print(f"\n📦 {model_class.__name__} ({len(items)} record):")
                    for item in items:
                        data = {col: getattr(item, col, None) for col in item.__table__.columns.keys()}
                        print(" - " + ", ".join([f"{k}: {v}" for k, v in data.items()]))
                except Exception as e:
                    print(f"⚠️ Errore durante query su {model_class.__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_all())