"""
Router per il nesting automatico multi-autoclave.
Gestisce la selezione, generazione, preview e conferma del nesting su più autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from api.database import get_db
from models import ODL, Autoclave, NestingResult, NestingBatch, Tool
from services.nesting_optimizer import NestingOptimizerService

# Configurazione logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nesting/auto-multi", tags=["nesting-multi"])

@router.get("/odl-disponibili")
async def get_odl_disponibili(
    db: Session = Depends(get_db),
    ciclo_cura_id: Optional[int] = None,
    priorita: Optional[str] = None
):
    """
    Recupera tutti gli ODL con stato 'Attesa Cura' disponibili per il nesting.
    """
    try:
        # Query diretta per ODL con stato 'Attesa Cura'
        all_odl = db.query(ODL).filter(ODL.status == "Attesa Cura").all()
        
        odl_data = []
        for odl in all_odl:
            # Controlla se ha un tool e se è disponibile
            if not odl.tool or not odl.tool.disponibile:
                continue
            
            tool = odl.tool
            
            # Determina la priorità
            priorita_str = "Alta" if odl.priorita >= 3 else "Media" if odl.priorita >= 2 else "Bassa"
            
            # Applica filtro priorità se specificato
            if priorita and priorita != "all" and priorita_str != priorita:
                continue
                
            # Ciclo di cura
            try:
                if odl.parte and odl.parte.ciclo_cura:
                    ciclo_cura_info = {
                        "id": odl.parte.ciclo_cura.id,
                        "nome": odl.parte.ciclo_cura.nome
                    }
                    
                    # Applica filtro ciclo se specificato
                    if ciclo_cura_id and ciclo_cura_info["id"] != ciclo_cura_id:
                        continue
                else:
                    ciclo_cura_info = {"id": 1, "nome": "Standard"}
            except:
                ciclo_cura_info = {"id": 1, "nome": "Standard"}
            
            # Calcola area stimata
            area_stimata = 0
            if tool.lunghezza_piano and tool.larghezza_piano:
                area_stimata = (tool.lunghezza_piano * tool.larghezza_piano) / 100
            
            odl_item = {
                "id": odl.id,
                "numero_odl": f"ODL-{odl.id:06d}",
                "parte_nome": odl.parte.descrizione_breve if odl.parte else "N/A",
                "tool_nome": tool.part_number_tool,
                "tool_dimensioni": {
                    "lunghezza": tool.lunghezza_piano or 0,
                    "larghezza": tool.larghezza_piano or 0
                },
                "peso_kg": tool.peso or 0.0,
                "area_stimata": area_stimata,
                "ciclo_cura": ciclo_cura_info,
                "priorita": priorita_str,
                "data_creazione": odl.created_at.isoformat() if odl.created_at else None
            }
            
            odl_data.append(odl_item)
        
        return {
            "success": True,
            "data": odl_data,
            "total": len(odl_data)
        }
        
    except Exception as e:
        logger.error(f"Errore nel recupero ODL disponibili: {str(e)}")
        return {
            "success": False,
            "error": f"Errore nel recupero degli ODL: {str(e)}",
            "data": [],
            "total": 0
        }

@router.get("/autoclavi-disponibili")
async def get_autoclavi_disponibili(db: Session = Depends(get_db)):
    """
    Recupera tutte le autoclavi disponibili per il nesting.
    """
    try:
        autoclavi = db.query(Autoclave).filter(
            Autoclave.stato == "DISPONIBILE"
        ).all()
        
        autoclavi_data = []
        for autoclave in autoclavi:
            autoclavi_data.append({
                "id": autoclave.id,
                "nome": autoclave.nome,
                "dimensioni": {
                    "lunghezza": autoclave.lunghezza,
                    "larghezza": autoclave.larghezza_piano
                },
                "capacita_peso_kg": autoclave.max_load_kg or 1000.0,
                "superficie_piano_1": autoclave.area_piano,
                "superficie_piano_2": autoclave.area_piano / 2 if autoclave.use_secondary_plane else 0,
                "stato": autoclave.stato.value
            })
        
        return {
            "success": True,
            "data": autoclavi_data,
            "total": len(autoclavi_data)
        }
        
    except Exception as e:
        logger.error(f"Errore nel recupero autoclavi disponibili: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero delle autoclavi: {str(e)}"
        )

@router.post("/genera")
async def genera_nesting_automatico(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Genera automaticamente il nesting ottimale per gli ODL selezionati
    distribuendoli su più autoclavi disponibili.
    """
    try:
        odl_ids = request.get("odl_ids", [])
        autoclave_ids = request.get("autoclave_ids", [])
        parametri = request.get("parametri", {})
        
        if not odl_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessun ODL selezionato"
            )
        
        # Recupera ODL selezionati
        odl_list = db.query(ODL).filter(ODL.id.in_(odl_ids)).all()
        if len(odl_list) != len(odl_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alcuni ODL selezionati non sono stati trovati"
            )
        
        # Recupera autoclavi (se non specificate, prende tutte quelle disponibili)
        if autoclave_ids:
            autoclavi = db.query(Autoclave).filter(
                Autoclave.id.in_(autoclave_ids),
                Autoclave.stato == "DISPONIBILE"
            ).all()
        else:
            autoclavi = db.query(Autoclave).filter(
                Autoclave.stato == "DISPONIBILE"
            ).all()
        
        if not autoclavi:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessuna autoclave disponibile"
            )
        
        # Inizializza il servizio di ottimizzazione
        optimizer = NestingOptimizerService()
        
        # Esegue l'algoritmo di nesting automatico
        risultato_ottimizzazione = optimizer.ottimizza_multi_autoclave(
            odl_list=odl_list,
            autoclavi=autoclavi,
            parametri=parametri
        )
        
        # Crea il batch per raggruppare i nesting
        batch = NestingBatch(
            nome=f"Nesting Automatico {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            descrizione=f"Nesting automatico per {len(odl_list)} ODL su {len(autoclavi)} autoclavi",
            stato="Pianificazione",
            numero_autoclavi=len(risultato_ottimizzazione["nesting_results"]),
            numero_odl_totali=len(odl_list),
            parametri_nesting=parametri
        )
        db.add(batch)
        db.flush()  # Per ottenere l'ID del batch
        
        # Crea i NestingResult per ogni autoclave
        nesting_results = []
        for autoclave_result in risultato_ottimizzazione["nesting_results"]:
            nesting_result = NestingResult(
                autoclave_id=autoclave_result["autoclave_id"],
                batch_id=batch.id,
                odl_ids=[odl["id"] for odl in autoclave_result["odl_assegnati"]],
                stato="generato",
                area_utilizzata=autoclave_result["statistiche"]["area_utilizzata"],
                area_totale=autoclave_result["statistiche"]["area_totale"],
                peso_totale_kg=autoclave_result["statistiche"]["peso_totale"],
                area_piano_1=autoclave_result["statistiche"]["area_piano_1"],
                area_piano_2=autoclave_result["statistiche"]["area_piano_2"],
                superficie_piano_2_max=autoclave_result["statistiche"]["superficie_piano_2_max"],
                posizioni_tool=autoclave_result["posizioni_tool"],
                note=f"Nesting automatico generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            db.add(nesting_result)
            nesting_results.append(nesting_result)
        
        # Commit prima di calcolare le statistiche
        db.commit()
        
        # Aggiorna le statistiche del batch dopo il commit
        batch.calcola_statistiche()
        db.commit()  # Commit delle statistiche aggiornate
        
        return {
            "success": True,
            "batch_id": batch.id,
            "nesting_results": [
                {
                    "id": nr.id,
                    "autoclave_id": nr.autoclave_id,
                    "autoclave_nome": nr.autoclave.nome,
                    "odl_count": len(nr.odl_ids),
                    "efficienza": nr.efficienza_totale,
                    "peso_kg": nr.peso_totale_kg
                }
                for nr in nesting_results
            ],
            "statistiche_globali": risultato_ottimizzazione["statistiche_globali"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore nella generazione nesting automatico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nella generazione del nesting: {str(e)}"
        )

@router.get("/preview/{batch_id}")
async def get_nesting_preview(batch_id: int, db: Session = Depends(get_db)):
    """
    Recupera i dati di preview per un batch di nesting generato.
    """
    try:
        # Recupera il batch
        batch = db.query(NestingBatch).filter(NestingBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch di nesting non trovato"
            )
        
        # Recupera tutti i nesting results del batch
        nesting_results = db.query(NestingResult).filter(
            NestingResult.batch_id == batch_id
        ).all()
        
        preview_data = {
            "batch": {
                "id": batch.id,
                "nome": batch.nome,
                "descrizione": batch.descrizione,
                "stato": batch.stato,
                "numero_autoclavi": batch.numero_autoclavi,
                "numero_odl_totali": batch.numero_odl_totali,
                "peso_totale_kg": batch.peso_totale_kg,
                "efficienza_media": batch.efficienza_media
            },
            "nesting_layouts": []
        }
        
        for nr in nesting_results:
            # Recupera i dettagli degli ODL
            odl_details = []
            for odl_id in nr.odl_ids:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                if odl and odl.tool:
                    odl_details.append({
                        "id": odl.id,
                        "numero_odl": f"ODL-{odl.id:06d}",
                        "parte_nome": odl.parte.descrizione_breve if odl.parte else "N/A",
                        "tool_nome": odl.tool.part_number_tool,
                        "peso_kg": odl.tool.peso or 0.0
                    })
            
            layout_data = {
                "nesting_result_id": nr.id,
                "autoclave": {
                    "id": nr.autoclave.id,
                    "nome": nr.autoclave.nome,
                    "dimensioni": {
                        "lunghezza": nr.autoclave.lunghezza,
                        "larghezza": nr.autoclave.larghezza_piano
                    }
                },
                "statistiche": {
                    "efficienza_totale": nr.efficienza_totale,
                    "efficienza_piano_1": nr.efficienza_piano_1,
                    "efficienza_piano_2": nr.efficienza_piano_2,
                    "peso_totale_kg": nr.peso_totale_kg,
                    "area_piano_1": nr.area_piano_1,
                    "area_piano_2": nr.area_piano_2
                },
                "posizioni_tool": nr.posizioni_tool,
                "odl_details": odl_details
            }
            preview_data["nesting_layouts"].append(layout_data)
        
        return {
            "success": True,
            "data": preview_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore nel recupero preview nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero del preview: {str(e)}"
        )

@router.post("/conferma/{batch_id}")
async def conferma_nesting(
    batch_id: int,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Conferma il nesting automatico, bloccando le risorse e avviando la cura.
    """
    try:
        ruolo_utente = request.get("ruolo_utente", "Operatore")
        note_aggiuntive = request.get("note", "")
        
        # Recupera il batch
        batch = db.query(NestingBatch).filter(NestingBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch di nesting non trovato"
            )
        
        if batch.stato != "Pianificazione":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Il batch è già in stato '{batch.stato}' e non può essere confermato"
            )
        
        # Recupera tutti i nesting results del batch
        nesting_results = db.query(NestingResult).filter(
            NestingResult.batch_id == batch_id
        ).all()
        
        # Verifica che tutte le autoclavi siano ancora disponibili
        for nr in nesting_results:
            autoclave = db.query(Autoclave).filter(Autoclave.id == nr.autoclave_id).first()
            if not autoclave or autoclave.stato.value != "DISPONIBILE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"L'autoclave {autoclave.nome if autoclave else 'sconosciuta'} non è più disponibile"
                )
        
        # Verifica che tutti gli ODL siano ancora in attesa di cura
        for nr in nesting_results:
            for odl_id in nr.odl_ids:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                if not odl or odl.status != "Attesa Cura":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"L'ODL {odl.numero_odl if odl else odl_id} non è più in attesa di cura"
                    )
        
        # Aggiorna gli stati
        # 1. Batch
        batch.stato = "Pronto"
        batch.confermato_da_ruolo = ruolo_utente
        batch.data_inizio_pianificata = datetime.now() + timedelta(minutes=30)  # Inizio tra 30 minuti
        if note_aggiuntive:
            batch.note = note_aggiuntive
        
        # 2. Nesting Results
        for nr in nesting_results:
            nr.stato = "sospeso"
            nr.confermato_da_ruolo = ruolo_utente
            if note_aggiuntive:
                nr.note = note_aggiuntive
        
        # 3. Autoclavi (blocca per il nesting)
        for nr in nesting_results:
            autoclave = db.query(Autoclave).filter(Autoclave.id == nr.autoclave_id).first()
            from models.autoclave import StatoAutoclaveEnum
            autoclave.stato = StatoAutoclaveEnum.IN_USO
        
        # 4. ODL (cambia stato a "Cura")
        for nr in nesting_results:
            for odl_id in nr.odl_ids:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                odl.status = "Cura"
        
        # 5. Tool (blocca i tool utilizzati)
        for nr in nesting_results:
            for odl_id in nr.odl_ids:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                if odl.tool:
                    odl.tool.disponibile = False
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Nesting confermato con successo. {batch.numero_autoclavi} autoclavi bloccate, {batch.numero_odl_totali} ODL in cura.",
            "batch_id": batch.id,
            "stato_batch": batch.stato
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore nella conferma nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nella conferma del nesting: {str(e)}"
        )

@router.delete("/elimina/{batch_id}")
async def elimina_nesting(batch_id: int, db: Session = Depends(get_db)):
    """
    Elimina un batch di nesting non confermato.
    """
    try:
        # Recupera il batch
        batch = db.query(NestingBatch).filter(NestingBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch di nesting non trovato"
            )
        
        if batch.stato not in ["Pianificazione", "generato"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Il batch in stato '{batch.stato}' non può essere eliminato"
            )
        
        # Elimina tutti i nesting results associati
        db.query(NestingResult).filter(NestingResult.batch_id == batch_id).delete()
        
        # Elimina il batch
        db.delete(batch)
        db.commit()
        
        return {
            "success": True,
            "message": "Nesting eliminato con successo"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore nell'eliminazione nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nell'eliminazione del nesting: {str(e)}"
        )

@router.get("/batch-attivi")
async def get_batch_attivi(db: Session = Depends(get_db)):
    """
    Recupera tutti i batch di nesting attivi (in sospeso, in cura, ecc.).
    """
    try:
        batches = db.query(NestingBatch).filter(
            NestingBatch.stato.in_(["Pronto", "In Esecuzione"])
        ).all()
        
        batch_data = []
        for batch in batches:
            # Calcola statistiche aggiornate
            nesting_results = db.query(NestingResult).filter(
                NestingResult.batch_id == batch.id
            ).all()
            
            autoclavi_info = []
            for nr in nesting_results:
                autoclavi_info.append({
                    "id": nr.autoclave.id,
                    "nome": nr.autoclave.nome,
                    "efficienza": nr.efficienza_totale,
                    "stato_nesting": nr.stato
                })
            
            batch_data.append({
                "id": batch.id,
                "nome": batch.nome,
                "stato": batch.stato,
                "numero_autoclavi": batch.numero_autoclavi,
                "numero_odl_totali": batch.numero_odl_totali,
                "peso_totale_kg": batch.peso_totale_kg,
                "efficienza_media": batch.efficienza_media,
                "data_inizio_pianificata": batch.data_inizio_pianificata.isoformat() if batch.data_inizio_pianificata else None,
                "autoclavi": autoclavi_info,
                "created_at": batch.created_at.isoformat() if batch.created_at else None
            })
        
        return {
            "success": True,
            "data": batch_data,
            "total": len(batch_data)
        }
        
    except Exception as e:
        logger.error(f"Errore nel recupero batch attivi: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero dei batch: {str(e)}"
        )

@router.post("/termina-ciclo/{batch_id}")
async def termina_ciclo_batch(
    batch_id: int,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Termina il ciclo di cura per un batch, liberando tutte le risorse.
    """
    try:
        ruolo_utente = request.get("ruolo_utente", "Operatore")
        
        # Recupera il batch
        batch = db.query(NestingBatch).filter(NestingBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch di nesting non trovato"
            )
        
        if batch.stato not in ["Pronto", "In Esecuzione"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Il batch in stato '{batch.stato}' non può essere terminato"
            )
        
        # Recupera tutti i nesting results del batch
        nesting_results = db.query(NestingResult).filter(
            NestingResult.batch_id == batch_id
        ).all()
        
        # Aggiorna gli stati
        # 1. Batch
        batch.stato = "Completato"
        batch.data_fine_effettiva = datetime.now()
        
        # 2. Nesting Results
        for nr in nesting_results:
            nr.stato = "completato"
        
        # 3. Autoclavi (libera)
        for nr in nesting_results:
            autoclave = db.query(Autoclave).filter(Autoclave.id == nr.autoclave_id).first()
            from models.autoclave import StatoAutoclaveEnum
            autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
        
        # 4. ODL (cambia stato a "Completato")
        for nr in nesting_results:
            for odl_id in nr.odl_ids:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                odl.status = "Completato"
        
        # 5. Tool (libera i tool)
        for nr in nesting_results:
            for odl_id in nr.odl_ids:
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                if odl.tool:
                    odl.tool.disponibile = True
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Ciclo di cura terminato con successo. {batch.numero_autoclavi} autoclavi liberate, {batch.numero_odl_totali} ODL completati.",
            "batch_id": batch.id,
            "stato_batch": batch.stato
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore nella terminazione ciclo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nella terminazione del ciclo: {str(e)}"
        ) 