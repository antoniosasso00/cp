from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from api.database import get_db, init_db
from api.routes import router

# Carica variabili d'ambiente
load_dotenv()

app = FastAPI(
    title="CarbonPilot API",
    description="Backend API per CarbonPilot",
    version="0.1.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare domini precisi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includi i router
app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Benvenuto nella CarbonPilot API", "version": "0.1.0"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Endpoint per verificare la salute dell'API e la connessione al database"""
    return {"status": "ok", "database_connected": True}

# Inizializza il database all'avvio
@app.on_event("startup")
async def startup_event():
    init_db() 