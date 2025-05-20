import os
import sys
import asyncio
import importlib
import inspect
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from dotenv import load_dotenv

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# Load .env and DB URL
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("❌ DATABASE_URL non definito nel file .env")
    sys.exit(1)

if not DATABASE_URL.startswith("postgresql+asyncpg"):
    logger.error("❌ DATABASE_URL deve iniziare con 'postgresql+asyncpg://' per usare SQLAlchemy async")
    sys.exit(1)

# DB engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Importa dinamicamente tutti i modelli da backend.models
MODELS_PATH = ROOT_DIR / "backend" / "models"
MODEL_MODULE = "backend.models"

async def inspect_all():
    loaded_modules = set()

    async with AsyncSessionLocal() as session:
        logger.info("\n📊 MODEL INSPECTION REPORT:\n")

        for file in MODELS_PATH.glob("*.py"):
            if file.name in {"__init__.py", "base.py"}:
                continue

            module_name = f"{MODEL_MODULE}.{file.stem}"
            if module_name in loaded_modules:
                continue

            try:
                module = importlib.import_module(module_name)
                loaded_modules.add(module_name)
                logger.info(f"✅ Modulo {module_name} importato correttamente")
            except ImportError as e:
                logger.error(f"❌ Errore import {module_name}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"❌ Errore imprevisto durante l'import di {module_name}: {str(e)}")
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
                    logger.info(f"\n📦 {model_class.__name__} ({len(items)} record):")

                    if not items:
                        logger.info(" - Nessun record trovato")
                        continue

                    for item in items:
                        data = {col: getattr(item, col, None) for col in item.__table__.columns.keys()}
                        logger.info(" - " + ", ".join([f"{k}: {v}" for k, v in data.items()]))

                except Exception as e:
                    logger.error(f"⚠️ Errore durante query su {model_class.__name__}: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(inspect_all())
    except Exception as e:
        logger.error(f"❌ Errore durante l'esecuzione: {str(e)}")
        sys.exit(1)
