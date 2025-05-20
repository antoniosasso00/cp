from logging.config import fileConfig
import os
import sys
from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# Aggiungi il percorso principale al PATH per poter importare i moduli del progetto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# questo è l'oggetto Alembic Config
config = context.config

# Usa la variabile d'ambiente DATABASE_URL
url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/carbonpilot")
config.set_main_option('sqlalchemy.url', url)

# Interpreta la configurazione del file logging.ini, se esiste
fileConfig(config.config_file_name)

# Aggiungi modello MetaData qui
# per supporto 'autogenerate'
from models.base import Base
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 