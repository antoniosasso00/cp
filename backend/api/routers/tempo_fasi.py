from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime

from models import TempoFase, ODL, Parte, Catalogo
from schemas import TempoFaseCreate, TempoFaseUpdate, TempoFaseInDB, PrevisioneTempo, TipoFase
from api.database import get_db

router = APIRouter()

@router.post("/", response_model=TempoFaseInDB)
def create_tempo_fase(tempo_fase: TempoFaseCreate, db: Session = Depends(get_db)):
    """Crea una nuova registrazione per il tempo di una fase di produzione."""
    
    # Verifica che l'ODL esista
    odl = db.query(ODL).filter(ODL.id == tempo_fase.odl_id).first()
    if not odl:
        raise HTTPException(status_code=404, detail=f"ODL con ID {tempo_fase.odl_id} non trovato")
    
    # Verifica eventuali sovrapposizioni di fasi
    sovrapposizione = db.query(TempoFase).filter(
        TempoFase.odl_id == tempo_fase.odl_id,
        TempoFase.fase == tempo_fase.fase,
        TempoFase.fine_fase == None
    ).first()
    
    if sovrapposizione:
        raise HTTPException(
            status_code=400, 
            detail=f"Esiste già una fase '{tempo_fase.fase}' attiva per l'ODL {tempo_fase.odl_id}. "
                   f"Completare prima quella esistente."
        )
    
    # Crea il record
    db_tempo_fase = TempoFase(**tempo_fase.dict())
    db.add(db_tempo_fase)
    db.commit()
    db.refresh(db_tempo_fase)
    return db_tempo_fase


@router.get("/", response_model=List[TempoFaseInDB])
def read_tempo_fasi(
    skip: int = 0, 
    limit: int = 100,
    odl_id: Optional[int] = None,
    fase: Optional[TipoFase] = None,
    db: Session = Depends(get_db)
):
    """Legge l'elenco dei tempi di fase, con possibilità di filtrare per ODL e tipo di fase."""
    query = db.query(TempoFase)
    
    if odl_id is not None:
        query = query.filter(TempoFase.odl_id == odl_id)
    
    if fase is not None:
        query = query.filter(TempoFase.fase == fase)
    
    return query.offset(skip).limit(limit).all()


@router.get("/{tempo_fase_id}", response_model=TempoFaseInDB)
def read_tempo_fase(tempo_fase_id: int, db: Session = Depends(get_db)):
    """Legge i dettagli di un singolo tempo di fase."""
    db_tempo_fase = db.query(TempoFase).filter(TempoFase.id == tempo_fase_id).first()
    if db_tempo_fase is None:
        raise HTTPException(status_code=404, detail=f"Tempo fase con ID {tempo_fase_id} non trovato")
    return db_tempo_fase


@router.put("/{tempo_fase_id}", response_model=TempoFaseInDB)
def update_tempo_fase(tempo_fase_id: int, tempo_fase: TempoFaseUpdate, db: Session = Depends(get_db)):
    """Aggiorna i dati di un tempo di fase esistente."""
    db_tempo_fase = db.query(TempoFase).filter(TempoFase.id == tempo_fase_id).first()
    if db_tempo_fase is None:
        raise HTTPException(status_code=404, detail=f"Tempo fase con ID {tempo_fase_id} non trovato")
    
    # Aggiorna i campi forniti
    update_data = tempo_fase.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tempo_fase, key, value)
    
    # Se è stato impostato fine_fase, calcoliamo automaticamente la durata in minuti
    if tempo_fase.fine_fase and db_tempo_fase.inizio_fase:
        delta = tempo_fase.fine_fase - db_tempo_fase.inizio_fase
        db_tempo_fase.durata_minuti = int(delta.total_seconds() / 60)
    
    db.commit()
    db.refresh(db_tempo_fase)
    return db_tempo_fase


@router.delete("/{tempo_fase_id}", status_code=204)
def delete_tempo_fase(tempo_fase_id: int, db: Session = Depends(get_db)):
    """Elimina un tempo di fase."""
    db_tempo_fase = db.query(TempoFase).filter(TempoFase.id == tempo_fase_id).first()
    if db_tempo_fase is None:
        raise HTTPException(status_code=404, detail=f"Tempo fase con ID {tempo_fase_id} non trovato")
    
    db.delete(db_tempo_fase)
    db.commit()
    return {"detail": "Tempo fase eliminato con successo"}


@router.get("/previsioni/{fase}", response_model=PrevisioneTempo)
def get_previsione_tempo(
    fase: TipoFase,
    part_number: Optional[str] = Query(None, description="Part number da utilizzare per filtrare le statistiche"),
    db: Session = Depends(get_db)
):
    """
    Calcola la previsione dei tempi per una determinata fase, basata sulle medie dei tempi passati.
    Se viene fornito un part_number, filtra i risultati solo per quel codice.
    """
    # Costruiamo la query base che seleziona solo i record con durata calcolata
    query = db.query(
        func.avg(TempoFase.durata_minuti).label("media_minuti"),
        func.count(TempoFase.id).label("numero_osservazioni")
    ).filter(
        TempoFase.fase == fase,
        TempoFase.durata_minuti != None  # Solo fasi completate con durata calcolata
    )
    
    # Se richiesto un part_number specifico, aggiungiamo la condizione di join
    if part_number:
        query = query.join(ODL, TempoFase.odl_id == ODL.id).\
                join(Parte, ODL.parte_id == Parte.id).\
                filter(Parte.part_number == part_number)
    
    result = query.first()
    
    # Se non ci sono osservazioni, restituiamo valori di default
    if not result or not result.numero_osservazioni:
        return PrevisioneTempo(
            fase=fase,
            media_minuti=0.0,
            numero_osservazioni=0
        )
    
    return PrevisioneTempo(
        fase=fase,
        media_minuti=float(result.media_minuti),
        numero_osservazioni=result.numero_osservazioni
    ) 