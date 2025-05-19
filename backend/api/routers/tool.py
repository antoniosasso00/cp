import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from models.tool import Tool
from schemas.tool import ToolCreate, ToolResponse, ToolUpdate

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    tags=["tools"],
    responses={404: {"description": "Tool non trovato"}}
)

@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED,
             summary="Crea un nuovo stampo (tool)")
def create_tool(tool: ToolCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo stampo (tool) con le seguenti informazioni:
    - **codice**: codice identificativo univoco dello stampo
    - **descrizione**: descrizione dettagliata (opzionale)
    - **lunghezza_piano**: lunghezza utile del tool in mm
    - **larghezza_piano**: larghezza utile del tool in mm
    - **disponibile**: se lo stampo è attualmente disponibile
    - **in_manutenzione**: se lo stampo è in manutenzione
    - **data_ultima_manutenzione**: data dell'ultima manutenzione (opzionale)
    - **max_temperatura**: temperatura massima supportata (opzionale)
    - **max_pressione**: pressione massima supportata (opzionale)
    - **note**: note aggiuntive (opzionale)
    """
    db_tool = Tool(**tool.model_dump())
    
    try:
        db.add(db_tool)
        db.commit()
        db.refresh(db_tool)
        return db_tool
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante la creazione del tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il codice '{tool.codice}' è già utilizzato da un altro tool."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore imprevisto durante la creazione del tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante la creazione del tool."
        )

@router.get("/", response_model=List[ToolResponse], 
            summary="Ottiene la lista degli stampi (tools)")
def read_tools(
    skip: int = 0, 
    limit: int = 100,
    codice: Optional[str] = Query(None, description="Filtra per codice"),
    disponibile: Optional[bool] = Query(None, description="Filtra per disponibilità"),
    in_manutenzione: Optional[bool] = Query(None, description="Filtra per stato di manutenzione"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di stampi (tools) con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **codice**: filtro opzionale per codice
    - **disponibile**: filtro opzionale per disponibilità
    - **in_manutenzione**: filtro opzionale per stato di manutenzione
    """
    query = db.query(Tool)
    
    # Applicazione filtri
    if codice:
        query = query.filter(Tool.codice == codice)
    if disponibile is not None:
        query = query.filter(Tool.disponibile == disponibile)
    if in_manutenzione is not None:
        query = query.filter(Tool.in_manutenzione == in_manutenzione)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{tool_id}", response_model=ToolResponse, 
            summary="Ottiene uno stampo (tool) specifico")
def read_tool(tool_id: int, db: Session = Depends(get_db)):
    """
    Recupera uno stampo (tool) specifico tramite il suo ID.
    """
    db_tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if db_tool is None:
        logger.warning(f"Tentativo di accesso a tool inesistente: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tool con ID {tool_id} non trovato"
        )
    return db_tool

@router.get("/by-codice/{codice}", response_model=ToolResponse, 
            summary="Ottiene uno stampo (tool) tramite il codice")
def read_tool_by_codice(codice: str, db: Session = Depends(get_db)):
    """
    Recupera uno stampo (tool) specifico tramite il suo codice univoco.
    """
    db_tool = db.query(Tool).filter(Tool.codice == codice).first()
    if db_tool is None:
        logger.warning(f"Tentativo di accesso a tool con codice inesistente: {codice}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tool con codice '{codice}' non trovato"
        )
    return db_tool

@router.put("/{tool_id}", response_model=ToolResponse, 
            summary="Aggiorna uno stampo (tool)")
def update_tool(tool_id: int, tool: ToolUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna i dati di uno stampo (tool) esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    """
    db_tool = db.query(Tool).filter(Tool.id == tool_id).first()
    
    if db_tool is None:
        logger.warning(f"Tentativo di aggiornamento di tool inesistente: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tool con ID {tool_id} non trovato"
        )
    
    # Aggiornamento dei campi presenti nella richiesta
    update_data = tool.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tool, key, value)
    
    try:
        db.commit()
        db.refresh(db_tool)
        return db_tool
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del tool {tool_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il codice specificato è già utilizzato da un altro tool."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del tool {tool_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento del tool."
        )

@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina uno stampo (tool)")
def delete_tool(tool_id: int, db: Session = Depends(get_db)):
    """
    Elimina uno stampo (tool) tramite il suo ID.
    """
    db_tool = db.query(Tool).filter(Tool.id == tool_id).first()
    
    if db_tool is None:
        logger.warning(f"Tentativo di cancellazione di tool inesistente: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tool con ID {tool_id} non trovato"
        )
    
    try:
        db.delete(db_tool)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione del tool {tool_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'eliminazione del tool."
        ) 