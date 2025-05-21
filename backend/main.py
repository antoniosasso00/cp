import logging
import os
import importlib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse
from api.routes import router
from sqlalchemy import inspect
from config.performance import (
    CustomORJSONResponse,
    MIDDLEWARE_CONFIG,
    DB_CONFIG,
    CACHE_CONFIG
)

# Importa gli oggetti necessari dal modulo database
from api.database import engine, Base, create_nesting_tables

# Inizializzazione logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CarbonPilot API",
    description="API per la gestione dei processi di produzione di parti in carbonio",
    version="0.1.0",
    default_response_class=CustomORJSONResponse,
)

# Configurazione CORS per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare l'origine esatta
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Aggiungi middleware GZip
app.add_middleware(
    GZipMiddleware,
    minimum_size=MIDDLEWARE_CONFIG["gzip"]["minimum_size"]
)

# Importa tutti i modelli per assicurarsi che siano registrati
from models import *

# Crea le tabelle se non esistono (fallback se Alembic non è configurato o fallisce)
def create_tables_if_not_exist():
    # Verifica se la tabella 'odl' esiste
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if 'odl' not in tables:
        logger.info("Tabella 'odl' non trovata, creazione tabelle con SQLAlchemy...")
        # Crea tutte le tabelle non esistenti
        Base.metadata.create_all(engine)
        logger.info("Tabelle create con successo!")

# Inizializzazione del database
@app.on_event("startup")
async def startup_db_client():
    create_tables_if_not_exist()
    # Assicurati che le tabelle nesting siano create
    create_nesting_tables()
    logger.info("Database inizializzato!")

# Inclusione dei router
app.include_router(router, prefix="/api")

# Handler globale per le eccezioni
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Errore non gestito: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Si è verificato un errore interno."},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4,  # Numero di worker per gestire le richieste in parallelo
        loop="uvloop",  # Usa uvloop per migliori performance
        http="httptools",  # Usa httptools per parsing HTTP più veloce
    ) 