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

# Configura la connessione al database tramite variabili d'ambiente
section = config.config_ini_section
config.set_section_option(section, "POSTGRES_USER", os.getenv("POSTGRES_USER", "postgres"))
config.set_section_option(section, "POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
config.set_section_option(section, "POSTGRES_SERVER", os.getenv("POSTGRES_SERVER", "db"))
config.set_section_option(section, "POSTGRES_PORT", os.getenv("POSTGRES_PORT", "5432"))
config.set_section_option(section, "POSTGRES_DB", os.getenv("POSTGRES_DB", "carbonpilot"))

url = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'postgres')}@{os.getenv('POSTGRES_SERVER', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'carbonpilot')}"
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