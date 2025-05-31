import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, text
from datetime import datetime, timedelta

from api.database import get_db
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
from models.autoclave import Autoclave
from models.batch_nesting import BatchNesting
from schemas.produzione import (
    ProduzioneODLResponse, 
    StatisticheGeneraliResponse, 
    HealthCheckResponse,
    ODLProduzioneRead,
    StatisticheProduzione,
    AutoclaveStats,
    BatchNestingStats,
    ProduzioneGiornaliera
)

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/produzione",
    tags=["Produzione"],
    responses={404: {"description": "Risorsa non trovata"}}
)

@router.get("/odl", response_model=ProduzioneODLResponse, 
            summary="Ottiene ODL per la produzione separati per stato")
def get_odl_produzione(db: Session = Depends(get_db)):
    """
    Recupera gli ODL rilevanti per la produzione, separati per stato.
    
    Returns:
        ProduzioneODLResponse con:
        - attesa_cura: ODL in attesa di cura
        - in_cura: ODL attualmente in cura
        - statistiche: informazioni aggiuntive
    """
    try:
        logger.info("Recupero ODL per produzione curing...")
        
        # Carica tutti gli ODL con relazioni
        query = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo),
            joinedload(ODL.tool)
        )
        
        # ODL in attesa di cura
        odl_attesa_cura = query.filter(ODL.status == "Attesa Cura").order_by(desc(ODL.priorita)).all()
        
        # ODL in cura
        odl_in_cura = query.filter(ODL.status == "Cura").order_by(desc(ODL.priorita)).all()
        
        logger.info(f"Trovati {len(odl_attesa_cura)} ODL in attesa cura, {len(odl_in_cura)} in cura")
        
        # Crea la risposta usando i modelli Pydantic
        return ProduzioneODLResponse(
            attesa_cura=[ODLProduzioneRead.from_orm(odl) for odl in odl_attesa_cura],
            in_cura=[ODLProduzioneRead.from_orm(odl) for odl in odl_in_cura],
            statistiche=StatisticheProduzione(
                totale_attesa_cura=len(odl_attesa_cura),
                totale_in_cura=len(odl_in_cura),
                ultima_sincronizzazione=datetime.now()
            )
        )
        
    except Exception as e:
        logger.error(f"Errore durante il recupero ODL produzione: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero degli ODL di produzione: {str(e)}"
        )

@router.get("/statistiche", response_model=StatisticheGeneraliResponse, 
            summary="Ottiene statistiche di produzione")
def get_statistiche_produzione(db: Session = Depends(get_db)):
    """
    Recupera le statistiche di produzione generale.
    
    Returns:
        StatisticheGeneraliResponse con statistiche generali di produzione
    """
    try:
        logger.info("Recupero statistiche produzione...")
        
        # Conta ODL per stato
        odl_per_stato = {}
        stati_interesse = ["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"]
        
        for stato in stati_interesse:
            count = db.query(ODL).filter(ODL.status == stato).count()
            odl_per_stato[stato] = count
        
        # Autoclave disponibili/occupate
        autoclavi_disponibili = db.query(Autoclave).filter(Autoclave.stato == "DISPONIBILE").count()
        autoclavi_occupate = db.query(Autoclave).filter(Autoclave.stato == "IN_USO").count()
        
        # Batch nesting attivi
        batch_attivi = db.query(BatchNesting).filter(BatchNesting.stato == "confermato").count()
        
        # Produzione giornaliera (ODL completati oggi)
        oggi = datetime.now().date()
        domani = oggi + timedelta(days=1)
        odl_completati_oggi = db.query(ODL).filter(
            and_(
                ODL.status == "Finito",
                ODL.updated_at >= oggi,
                ODL.updated_at < domani
            )
        ).count()
        
        logger.info("Statistiche produzione recuperate con successo")
        
        return StatisticheGeneraliResponse(
            odl_per_stato=odl_per_stato,
            autoclavi=AutoclaveStats(
                disponibili=autoclavi_disponibili,
                occupate=autoclavi_occupate,
                totali=autoclavi_disponibili + autoclavi_occupate
            ),
            batch_nesting=BatchNestingStats(attivi=batch_attivi),
            produzione_giornaliera=ProduzioneGiornaliera(
                odl_completati_oggi=odl_completati_oggi,
                data=oggi.isoformat()
            ),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Errore durante il recupero statistiche produzione: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero delle statistiche di produzione: {str(e)}"
        )

@router.get("/health", response_model=HealthCheckResponse, 
            summary="Verifica stato del sistema di produzione")
def health_check_produzione(db: Session = Depends(get_db)):
    """
    Verifica lo stato del sistema di produzione.
    
    Returns:
        HealthCheckResponse con informazioni sullo stato del sistema
    """
    try:
        # Test connessione database
        db.execute(text("SELECT 1"))
        
        # Test modelli principali
        odl_count = db.query(ODL).count()
        autoclavi_count = db.query(Autoclave).count()
        
        return HealthCheckResponse(
            status="healthy",
            database="connected",
            odl_totali=str(odl_count),
            autoclavi_totali=str(autoclavi_count),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check produzione fallito: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sistema di produzione non disponibile: {str(e)}"
        ) 