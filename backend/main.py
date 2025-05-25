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
    title="Manta Group API",
    description="API per la gestione dei processi di produzione di parti in carbonio",
    version="0.1.0",
)

# Configurazione CORS per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare l'origine esatta come ["http://mantagroup-frontend:3000"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Importa tutti i modelli per assicurarsi che siano registrati
import models

# Crea le tabelle se non esistono (fallback se Alembic non è configurato o fallisce)
def create_tables_if_not_exist():
    try:
        # Verifica se la tabella 'odl' esiste
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"📋 Tabelle esistenti nel database: {tables}")
        
        if 'odl' not in tables:
            logger.info("⚙️ Tabella 'odl' non trovata, creazione tabelle con SQLAlchemy...")
            # Crea tutte le tabelle non esistenti
            Base.metadata.create_all(engine)
            logger.info("✅ Tabelle create con successo!")
        else:
            logger.info("✅ Tutte le tabelle necessarie sono già presenti")
    except Exception as e:
        logger.error(f"❌ Errore durante la creazione delle tabelle: {str(e)}")
        raise

def log_registered_routes():
    """Logga tutte le rotte registrate nell'applicazione."""
    logger.info("📝 Rotte API registrate:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            logger.info(f"  {methods:<20} {route.path}")

# Inizializzazione del database
@app.on_event("startup")
async def startup_db_client():
    logger.info("🚀 Avvio Manta Group Backend...")
    create_tables_if_not_exist()
    log_registered_routes()
    logger.info("✅ Database inizializzato e server pronto!")

# Inclusione dei router
app.include_router(router, prefix="/api")

# Health check endpoint
@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "message": "Manta Group API è attiva",
        "version": "0.1.0"
    }

@app.get("/health")
async def detailed_health_check():
    # Testa la connessione al database
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        db_status = "connected"
        db_tables = len(tables)
    except Exception as e:
        db_status = f"error: {str(e)}"
        db_tables = 0
    
    return {
        "status": "healthy",
        "database": {
            "status": db_status,
            "tables_count": db_tables
        },
        "api": {
            "version": "0.1.0",
            "routes_count": len([r for r in app.routes if hasattr(r, 'path')])
        }
    }

# Handler globale per le eccezioni
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"💥 Errore non gestito su {request.method} {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Errore interno del server: {str(exc)}",
            "path": str(request.url),
            "method": request.method
        },
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("🎯 Avvio diretto del server su http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)