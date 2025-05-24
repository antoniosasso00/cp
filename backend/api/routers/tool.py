import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from models.tool import Tool
from models.odl import ODL
from schemas.tool import ToolCreate, ToolResponse, ToolUpdate

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    tags=["Tools"],
    responses={404: {"description": "Tool non trovato"}}
)

@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED,
             summary="Crea un nuovo stampo (tool)")
def create_tool(tool: ToolCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo stampo (tool) con le seguenti informazioni:
    - **part_number_tool**: part number identificativo univoco dello stampo
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
            detail=f"Il part number '{tool.part_number_tool}' è già utilizzato da un altro tool."
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
    part_number_tool: Optional[str] = Query(None, description="Filtra per part number"),
    disponibile: Optional[bool] = Query(None, description="Filtra per disponibilità"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di stampi (tools) con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **part_number_tool**: filtro opzionale per part number
    - **disponibile**: filtro opzionale per disponibilità
    """
    query = db.query(Tool)
    
    # Applicazione filtri
    if part_number_tool:
        query = query.filter(Tool.part_number_tool == part_number_tool)
    if disponibile is not None:
        query = query.filter(Tool.disponibile == disponibile)
    
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

@router.get("/by-part-number/{part_number_tool}", response_model=ToolResponse, 
            summary="Ottiene uno stampo (tool) tramite il part number")
def read_tool_by_part_number(part_number_tool: str, db: Session = Depends(get_db)):
    """
    Recupera uno stampo (tool) specifico tramite il suo part number univoco.
    """
    db_tool = db.query(Tool).filter(Tool.part_number_tool == part_number_tool).first()
    if db_tool is None:
        logger.warning(f"Tentativo di accesso a tool con part number inesistente: {part_number_tool}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tool con part number '{part_number_tool}' non trovato"
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
            detail=f"Il part number specificato è già utilizzato da un altro tool."
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

@router.put("/update-status-from-odl", 
            summary="Aggiorna lo stato dei Tool basato sugli ODL attivi")
def update_tools_status_from_odl(db: Session = Depends(get_db)):
    """
    Aggiorna automaticamente lo stato di disponibilità e dettagli dei Tool basandosi sugli ODL attivi.
    
    Stati considerati come "in uso":
    - Preparazione → Tool "In uso – Preparazione"
    - Laminazione → Tool "In Laminazione"
    - Attesa Cura → Tool "In Attesa di Cura"
    - Cura → Tool "In Autoclave"
    
    I Tool non associati o con ODL "Finito" vengono marcati come disponibili.
    Se un tool è usato da più ODL, prende lo stato del più avanzato cronologicamente.
    """
    try:
        # Ottieni tutti i Tool
        all_tools = db.query(Tool).all()
        
        # Ottieni tutti gli ODL attivi (non "Finito")
        active_odl = db.query(ODL).filter(ODL.status.in_([
            "Preparazione", "Laminazione", "Attesa Cura", "Cura"
        ])).order_by(ODL.updated_at.desc()).all()
        
        # Crea un mapping tool_id -> informazioni ODL più avanzato
        tool_status_map = {}
        
        # Ordine di priorità degli stati (più alto = più avanzato)
        status_priority = {
            "Preparazione": 1,
            "Laminazione": 2,
            "Attesa Cura": 3,
            "Cura": 4
        }
        
        for odl in active_odl:
            if odl.tool_id:
                current_priority = status_priority.get(odl.status, 0)
                
                if (odl.tool_id not in tool_status_map or 
                    current_priority > status_priority.get(tool_status_map[odl.tool_id]["status"], 0)):
                    
                    tool_status_map[odl.tool_id] = {
                        "status": odl.status,
                        "odl_id": odl.id,
                        "parte_id": odl.parte_id,
                        "priority": current_priority,
                        "updated_at": odl.updated_at
                    }
        
        # Mapping stato ODL → stato tool display
        status_display_map = {
            "Preparazione": "In uso – Preparazione",
            "Laminazione": "In Laminazione",
            "Attesa Cura": "In Attesa di Cura",
            "Cura": "In Autoclave"
        }
        
        updated_tools = []
        
        # Aggiorna lo stato di tutti i Tool
        for tool in all_tools:
            old_disponibile = tool.disponibile
            
            if tool.id in tool_status_map:
                # Tool in uso
                new_disponibile = False
                odl_info = tool_status_map[tool.id]
                status_display = status_display_map.get(odl_info["status"], "In uso")
            else:
                # Tool disponibile
                new_disponibile = True
                status_display = "Disponibile"
                odl_info = None
            
            # Aggiorna solo se necessario
            if tool.disponibile != new_disponibile:
                tool.disponibile = new_disponibile
                
                updated_tools.append({
                    "id": tool.id,
                    "part_number_tool": tool.part_number_tool,
                    "old_status": "Disponibile" if old_disponibile else "In uso",
                    "new_status": status_display,
                    "odl_info": odl_info
                })
        
        db.commit()
        
        # Statistiche per il response
        tools_by_status = {}
        for tool_id, info in tool_status_map.items():
            status = status_display_map.get(info["status"], "In uso")
            tools_by_status[status] = tools_by_status.get(status, 0) + 1
        
        available_tools = len(all_tools) - len(tool_status_map)
        if available_tools > 0:
            tools_by_status["Disponibile"] = available_tools
        
        logger.info(f"Aggiornato stato di {len(updated_tools)} Tool basato su ODL attivi")
        
        return {
            "message": f"Stato aggiornato per {len(updated_tools)} Tool",
            "updated_tools": updated_tools,
            "total_tools": len(all_tools),
            "tools_in_use": len(tool_status_map),
            "tools_available": available_tools,
            "tools_by_status": tools_by_status
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento stato Tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento dello stato dei Tool."
        )

@router.get("/with-status", response_model=List[dict], 
            summary="Ottiene la lista degli stampi (tools) con stato dettagliato")
def read_tools_with_status(
    skip: int = 0, 
    limit: int = 100,
    part_number_tool: Optional[str] = Query(None, description="Filtra per part number"),
    disponibile: Optional[bool] = Query(None, description="Filtra per disponibilità"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di stampi (tools) con informazioni dettagliate sullo stato basato sugli ODL attivi:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **part_number_tool**: filtro opzionale per part number
    - **disponibile**: filtro opzionale per disponibilità
    
    Ogni tool include:
    - Informazioni base del tool
    - Stato dettagliato ("Disponibile", "In uso – Preparazione", "In Laminazione", "In Attesa di Cura", "In Autoclave")
    - Informazioni sull'ODL associato (se presente)
    """
    query = db.query(Tool)
    
    # Applicazione filtri
    if part_number_tool:
        query = query.filter(Tool.part_number_tool == part_number_tool)
    if disponibile is not None:
        query = query.filter(Tool.disponibile == disponibile)
    
    tools = query.offset(skip).limit(limit).all()
    
    # Ottieni tutti gli ODL attivi per calcolare gli stati
    active_odl = db.query(ODL).filter(ODL.status.in_([
        "Preparazione", "Laminazione", "Attesa Cura", "Cura"
    ])).order_by(ODL.updated_at.desc()).all()
    
    # Crea mapping tool_id -> stato ODL
    tool_status_map = {}
    status_priority = {
        "Preparazione": 1,
        "Laminazione": 2,
        "Attesa Cura": 3,
        "Cura": 4
    }
    
    for odl in active_odl:
        if odl.tool_id:
            current_priority = status_priority.get(odl.status, 0)
            
            if (odl.tool_id not in tool_status_map or 
                current_priority > status_priority.get(tool_status_map[odl.tool_id]["status"], 0)):
                
                tool_status_map[odl.tool_id] = {
                    "status": odl.status,
                    "odl_id": odl.id,
                    "parte_id": odl.parte_id,
                    "priority": current_priority,
                    "updated_at": odl.updated_at
                }
    
    # Mapping stato ODL → stato display
    status_display_map = {
        "Preparazione": "In uso – Preparazione",
        "Laminazione": "In Laminazione",
        "Attesa Cura": "In Attesa di Cura",
        "Cura": "In Autoclave"
    }
    
    # Costruisci la risposta con stato dettagliato
    result = []
    for tool in tools:
        tool_data = {
            "id": tool.id,
            "part_number_tool": tool.part_number_tool,
            "descrizione": tool.descrizione,
            "lunghezza_piano": tool.lunghezza_piano,
            "larghezza_piano": tool.larghezza_piano,
            "disponibile": tool.disponibile,
            "note": tool.note,
            "created_at": tool.created_at.isoformat() if tool.created_at else None,
            "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
        }
        
        # Aggiungi informazioni di stato
        if tool.id in tool_status_map:
            odl_info = tool_status_map[tool.id]
            tool_data["status_display"] = status_display_map.get(odl_info["status"], "In uso")
            tool_data["current_odl"] = {
                "id": odl_info["odl_id"],
                "status": odl_info["status"],
                "parte_id": odl_info["parte_id"],
                "updated_at": odl_info["updated_at"].isoformat() if odl_info["updated_at"] else None
            }
        else:
            tool_data["status_display"] = "Disponibile"
            tool_data["current_odl"] = None
        
        result.append(tool_data)
    
    return result 