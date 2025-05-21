import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Importiamo Base da models
from models.base import Base

# Carica variabili d'ambiente
load_dotenv()

# Configurazione della connessione al database
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "carbonpilot-db")  # Usa il nome del servizio completo
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "carbonpilot")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dipendenza per ottenere una sessione del database"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_nesting_tables():
    """Crea le tabelle nesting se non esistono già"""
    conn = engine.connect()
    
    # Tabella nesting_params
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS nesting_params (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100) NOT NULL UNIQUE,
        peso_valvole FLOAT NOT NULL DEFAULT 1.0,
        peso_area FLOAT NOT NULL DEFAULT 1.0,
        peso_priorita FLOAT NOT NULL DEFAULT 1.0,
        spazio_minimo_mm FLOAT NOT NULL DEFAULT 50.0,
        attivo BOOLEAN NOT NULL DEFAULT FALSE,
        descrizione TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    )
    """))
    
    # Indice per nesting_params
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nesting_params_id ON nesting_params (id)"))
    
    # Tabella nesting_results
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS nesting_results (
        id SERIAL PRIMARY KEY,
        codice VARCHAR(50) NOT NULL UNIQUE,
        autoclave_id INTEGER NOT NULL REFERENCES autoclavi (id),
        confermato BOOLEAN NOT NULL DEFAULT FALSE,
        data_conferma TIMESTAMP WITH TIME ZONE,
        area_totale_mm2 FLOAT NOT NULL,
        area_utilizzata_mm2 FLOAT NOT NULL,
        efficienza_area FLOAT NOT NULL,
        valvole_totali INTEGER NOT NULL,
        valvole_utilizzate INTEGER NOT NULL,
        layout JSONB NOT NULL,
        odl_ids JSONB NOT NULL,
        generato_manualmente BOOLEAN NOT NULL DEFAULT FALSE,
        note TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        CONSTRAINT fk_autoclave FOREIGN KEY (autoclave_id) REFERENCES autoclavi (id)
    )
    """))
    
    # Indice per nesting_results
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nesting_results_id ON nesting_results (id)"))
    
    # Inserisci parametri di default
    conn.execute(text("""
    INSERT INTO nesting_params (nome, peso_valvole, peso_area, peso_priorita, spazio_minimo_mm, attivo, descrizione, created_at, updated_at)
    VALUES ('Configurazione Default', 2.0, 3.0, 5.0, 30.0, TRUE, 'Configurazione predefinita del sistema', now(), now())
    ON CONFLICT (nome) DO NOTHING
    """))
    
    conn.commit()
    conn.close()

def init_db():
    """Inizializza il database creando tutte le tabelle definite"""
    # Importa qui i modelli per assicurarsi che siano registrati con Base
    # Il modello User è già importato tramite Base
    
    # Non crea le tabelle in produzione - usare Alembic per le migrazioni
    if os.getenv("ENVIRONMENT") == "development":
        Base.metadata.create_all(bind=engine)
    
    # Crea sempre le tabelle nesting
    create_nesting_tables() 