"""
Servizio per la gestione del nesting automatico degli ODL nelle autoclavi.
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.nesting_result import NestingResult
from nesting_optimizer.auto_nesting import compute_nesting, NestingResult as OptimizationResult
from schemas.nesting import NestingResultSchema, NestingPreviewSchema, AutoclavePreviewInfo, ODLPreviewInfo
from schemas.nesting import AutoclaveNestingInfo, ODLNestingInfo, NestingODLStatus
import random

def get_all_nesting_results(db: Session) -> List[NestingResult]:
    """
    Recupera tutti i risultati di nesting dal database con le loro relazioni
    
    Args:
        db: Sessione del database
        
    Returns:
        Lista di oggetti NestingResult
    """
    return db.query(NestingResult).options(
        joinedload(NestingResult.autoclave),
        joinedload(NestingResult.odl_list).joinedload(ODL.parte),
        joinedload(NestingResult.odl_list).joinedload(ODL.tool)
    ).order_by(NestingResult.created_at.desc()).all()

def generate_color_for_odl(odl_id: int) -> str:
    """
    Genera un colore consistente per un ODL basato sul suo ID
    """
    colors = [
        "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
        "#06B6D4", "#84CC16", "#F97316", "#EC4899", "#6366F1"
    ]
    return colors[odl_id % len(colors)]

async def get_nesting_preview(db: Session) -> NestingPreviewSchema:
    """
    Genera un'anteprima del nesting senza salvarlo nel database
    
    Args:
        db: Sessione del database
        
    Returns:
        Schema NestingPreviewSchema con l'anteprima del nesting
    """
    # Recupera tutti gli ODL in stato "Attesa Cura"
    odl_list = db.query(ODL).options(
        joinedload(ODL.parte).joinedload(Parte.catalogo),
        joinedload(ODL.tool)
    ).filter(ODL.status == "Attesa Cura").all()
    
    # Recupera tutte le autoclavi disponibili
    autoclavi = db.query(Autoclave).filter(
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).all()
    
    # Se non ci sono ODL o autoclavi, restituisci un risultato vuoto
    if not odl_list or not autoclavi:
        return NestingPreviewSchema(
            success=False,
            message="Nessun ODL in attesa o nessuna autoclave disponibile",
            autoclavi=[],
            odl_esclusi=[]
        )
    
    # Esegui l'algoritmo di nesting
    result = compute_nesting(db, odl_list, autoclavi)
    
    # Prepara le informazioni sulle autoclavi per la preview
    autoclavi_preview = []
    
    for autoclave in autoclavi:
        # Verifica se questa autoclave è stata utilizzata nel nesting
        if autoclave.id in result.assegnamenti:
            # Recupera le statistiche per questa autoclave
            stats = result.statistiche_autoclavi.get(autoclave.id, {})
            
            # Prepara la lista degli ODL inclusi con le loro informazioni
            odl_inclusi = []
            for odl_id in result.assegnamenti[autoclave.id]:
                odl = db.query(ODL).options(
                    joinedload(ODL.parte).joinedload(Parte.catalogo)
                ).filter(ODL.id == odl_id).first()
                
                if odl and odl.parte and odl.parte.catalogo:
                    catalogo = odl.parte.catalogo
                    odl_inclusi.append(ODLPreviewInfo(
                        id=odl.id,
                        part_number=catalogo.part_number,
                        descrizione=odl.parte.descrizione_breve,
                        area_cm2=catalogo.area_cm2,
                        num_valvole=odl.parte.num_valvole_richieste,
                        priorita=odl.priorita,
                        color=generate_color_for_odl(odl.id)
                    ))
            
            # Calcola l'area totale dell'autoclave in cm²
            area_totale_cm2 = (autoclave.lunghezza * autoclave.larghezza_piano) / 100
            
            autoclavi_preview.append(AutoclavePreviewInfo(
                id=autoclave.id,
                nome=autoclave.nome,
                codice=autoclave.codice,
                lunghezza=autoclave.lunghezza,
                larghezza_piano=autoclave.larghezza_piano,
                area_totale_cm2=area_totale_cm2,
                area_utilizzata_cm2=float(stats.get("area_utilizzata", 0.0)),
                valvole_totali=autoclave.num_linee_vuoto,
                valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
                odl_inclusi=odl_inclusi
            ))
    
    # Prepara la lista degli ODL esclusi
    odl_esclusi = []
    for item in result.odl_non_pianificabili:
        odl_id = item["odl_id"]
        motivo = item["motivo"]
        
        # Recupera l'ODL dal database
        odl = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo)
        ).filter(ODL.id == odl_id).first()
        
        if odl:
            parte = odl.parte
            catalogo = parte.catalogo if parte else None
            
            odl_esclusi.append({
                "id": odl.id,
                "part_number": catalogo.part_number if catalogo else "N/A",
                "descrizione": parte.descrizione_breve if parte else "Sconosciuta",
                "motivo": motivo,
                "priorita": odl.priorita,
                "num_valvole": parte.num_valvole_richieste if parte else 0
            })
    
    # Restituisci l'anteprima
    return NestingPreviewSchema(
        success=True,
        message=f"Anteprima generata: {len([odl for autoclave in autoclavi_preview for odl in autoclave.odl_inclusi])} ODL pianificati, {len(odl_esclusi)} esclusi",
        autoclavi=autoclavi_preview,
        odl_esclusi=odl_esclusi
    )

async def run_automatic_nesting(db: Session) -> NestingResultSchema:
    """
    Esegue l'algoritmo di nesting automatico per ottimizzare il posizionamento 
    degli ODL nelle autoclavi disponibili.
    
    Args:
        db: Sessione del database
        
    Returns:
        Schema NestingResult con i risultati dell'ottimizzazione
    """
    # Recupera tutti gli ODL in stato "Attesa Cura"
    odl_list = db.query(ODL).options(
        joinedload(ODL.parte).joinedload(Parte.catalogo),
        joinedload(ODL.tool)
    ).filter(ODL.status == "Attesa Cura").all()
    
    # Recupera tutte le autoclavi disponibili
    autoclavi = db.query(Autoclave).filter(
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).all()
    
    # Se non ci sono ODL o autoclavi, restituisci un risultato vuoto
    if not odl_list or not autoclavi:
        return NestingResultSchema(
            success=False,
            message="Nessun ODL in attesa o nessuna autoclave disponibile",
            autoclavi=[],
            odl_pianificati=[],
            odl_non_pianificabili=[]
        )
    
    # Esegui l'algoritmo di nesting
    result = compute_nesting(db, odl_list, autoclavi)
    
    # Aggiorna lo stato degli ODL nel database
    odl_pianificati = []
    odl_non_pianificabili = []
    
    # Salva il risultato nel database per ogni autoclave usata
    for autoclave_id, odl_ids in result.assegnamenti.items():
        if not odl_ids:
            continue
            
        # Trova l'autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
        
        # Crea un nuovo record NestingResult
        stats = result.statistiche_autoclavi.get(autoclave_id, {})
        nesting_record = NestingResult(
            autoclave_id=autoclave_id,
            odl_ids=odl_ids,
            odl_esclusi_ids=[item["odl_id"] for item in result.odl_non_pianificabili],
            motivi_esclusione=result.odl_non_pianificabili,
            stato="In attesa schedulazione",
            area_utilizzata=float(stats.get("area_utilizzata", 0.0)),
            area_totale=float(stats.get("area_totale", 0.0)),
            valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
            valvole_totali=autoclave.num_linee_vuoto if autoclave else 0
        )
        
        # Aggiungi gli ODL al nesting
        for odl_id in odl_ids:
            odl = db.query(ODL).filter(ODL.id == odl_id).first()
            if odl:
                nesting_record.odl_list.append(odl)
        
        # Salva nel database
        db.add(nesting_record)
    
    # Aggiorna gli ODL pianificati
    for autoclave_id, odl_ids in result.assegnamenti.items():
        for odl_id in odl_ids:
            # Recupera l'ODL dal database
            odl = db.query(ODL).options(
                joinedload(ODL.parte).joinedload(Parte.catalogo)
            ).filter(ODL.id == odl_id).first()
            if odl:
                # Manteniamo lo stato "Attesa Cura" finché non viene schedulato
                
                # Recupera le informazioni sulla parte
                parte = odl.parte
                catalogo = parte.catalogo if parte else None
                
                # Aggiungi all'elenco degli ODL pianificati
                odl_pianificati.append(ODLNestingInfo(
                    id=odl.id,
                    parte_descrizione=parte.descrizione_breve if parte else "Sconosciuta",
                    num_valvole=parte.num_valvole_richieste if parte else 0,
                    priorita=odl.priorita,
                    status=NestingODLStatus.PIANIFICATO
                ))
    
    # Aggiorna gli ODL non pianificabili
    for item in result.odl_non_pianificabili:
        odl_id = item["odl_id"]
        motivo = item["motivo"]
        
        # Recupera l'ODL dal database
        odl = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo)
        ).filter(ODL.id == odl_id).first()
        if odl:
            # Manteniamo lo stato "Attesa Cura"
            
            # Recupera le informazioni sulla parte
            parte = odl.parte
            
            # Aggiungi all'elenco degli ODL non pianificabili
            odl_non_pianificabili.append(ODLNestingInfo(
                id=odl.id,
                parte_descrizione=f"{parte.descrizione_breve if parte else 'Sconosciuta'} (Motivo: {motivo})",
                num_valvole=parte.num_valvole_richieste if parte else 0,
                priorita=odl.priorita,
                status=NestingODLStatus.NON_PIANIFICABILE
            ))
    
    # Commit delle modifiche al database
    db.commit()
    
    # Prepara le informazioni sulle autoclavi
    autoclavi_info = []
    for autoclave in autoclavi:
        # Verifica se questa autoclave è stata utilizzata nel nesting
        if autoclave.id in result.assegnamenti:
            # Recupera le statistiche per questa autoclave
            stats = result.statistiche_autoclavi.get(autoclave.id, {})
            
            autoclavi_info.append(AutoclaveNestingInfo(
                id=autoclave.id,
                nome=autoclave.nome,
                odl_assegnati=result.assegnamenti[autoclave.id],
                valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
                valvole_totali=autoclave.num_linee_vuoto,
                area_utilizzata=float(stats.get("area_utilizzata", 0.0)),
                area_totale=float(stats.get("area_totale", 0.0))
            ))
    
    # Restituisci il risultato
    return NestingResultSchema(
        success=True,
        message=f"Nesting completato: {len(odl_pianificati)} ODL pianificati, {len(odl_non_pianificabili)} non pianificabili",
        autoclavi=autoclavi_info,
        odl_pianificati=odl_pianificati,
        odl_non_pianificabili=odl_non_pianificabili
    )

async def update_nesting_status(db: Session, nesting_id: int, nuovo_stato: str, note: str = None) -> NestingResult:
    """
    Aggiorna lo stato di un nesting e gestisce il cambio di stato degli ODL associati
    
    Args:
        db: Sessione del database
        nesting_id: ID del nesting da aggiornare
        nuovo_stato: Nuovo stato del nesting
        note: Note opzionali
        
    Returns:
        Il nesting aggiornato
        
    Raises:
        ValueError: Se il nesting non viene trovato
    """
    # Recupera il nesting dal database
    nesting = db.query(NestingResult).options(
        joinedload(NestingResult.autoclave),
        joinedload(NestingResult.odl_list).joinedload(ODL.parte),
        joinedload(NestingResult.odl_list).joinedload(ODL.tool)
    ).filter(NestingResult.id == nesting_id).first()
    
    if not nesting:
        raise ValueError(f"Nesting con ID {nesting_id} non trovato")
    
    # Aggiorna lo stato del nesting
    nesting.stato = nuovo_stato
    if note:
        nesting.note = note
    
    # Se il nesting viene schedulato, aggiorna lo stato degli ODL
    if nuovo_stato == "Schedulato":
        for odl in nesting.odl_list:
            if odl.status == "Attesa Cura":
                odl.status = "Cura"  # Cambia lo stato a "Cura" (In Autoclave)
                db.add(odl)
    
    # Se il nesting viene annullato, riporta gli ODL in "Attesa Cura"
    elif nuovo_stato == "Annullato":
        for odl in nesting.odl_list:
            if odl.status == "Cura":
                odl.status = "Attesa Cura"  # Riporta in attesa
                db.add(odl)
    
    # Salva le modifiche
    db.add(nesting)
    db.commit()
    db.refresh(nesting)
    
    return nesting 