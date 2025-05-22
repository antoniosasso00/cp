import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from api.routes import router
from sqlalchemy import inspect

# Importa gli oggetti necessari dal modulo database corretto
from models.db import engine, Base

# Inizializzazione logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CarbonPilot API",
    description="API per la gestione dei processi di produzione di parti in carbonio",
    version="0.1.0",
)

# Configurazione CORS per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare l'origine esatta come ["http://carbonpilot-frontend:3000"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Importa tutti i modelli per assicurarsi che siano registrati
import models

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
    uvicorn.run(app, host="0.0.0.0", port=8000) 