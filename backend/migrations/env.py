from logging.config import fileConfig
import os
import sys
from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

config = context.config

# 🔁 Usa DATABASE_URL_SYNC per Alembic se presente, altrimenti fallback su DATABASE_URL
url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/carbonpilot")
config.set_main_option('sqlalchemy.url', url)

fileConfig(config.config_file_name)

# Importa metadata dei modelli
from models.base import Base
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
