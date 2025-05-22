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
from schemas.nesting import NestingResultSchema
from schemas.nesting import AutoclaveNestingInfo, ODLNestingInfo, NestingODLStatus

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
    odl_list = db.query(ODL).filter(ODL.status == "Attesa Cura").all()
    
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
            odl = db.query(ODL).filter(ODL.id == odl_id).first()
            if odl:
                # Aggiorna lo stato dell'ODL a "pianificato"
                odl.status = "Attesa Cura"  # Manteniamo lo stato attuale
                db.add(odl)
                
                # Recupera le informazioni sulla parte
                parte = db.query(Parte).filter(Parte.id == odl.parte_id).first()
                
                # Aggiungi all'elenco degli ODL pianificati
                odl_pianificati.append(ODLNestingInfo(
                    id=odl.id,
                    parte_descrizione=parte.descrizione_breve if parte else "Sconosciuta",
                    num_valvole=parte.num_valvole_richieste if parte else 0,
                    priorita=odl.priorita,
                    status=NestingODLStatus.PIANIFICATO
                ))
    
    # Aggiorna gli ODL non pianificabili
    for odl_id in result.odl_non_pianificabili:
        # Recupera l'ODL dal database
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if odl:
            # Aggiorna lo stato dell'ODL a "non_pianificabile"
            odl.status = "Attesa Cura"  # Manteniamo lo stato attuale
            db.add(odl)
            
            # Recupera le informazioni sulla parte
            parte = db.query(Parte).filter(Parte.id == odl.parte_id).first()
            
            # Aggiungi all'elenco degli ODL non pianificabili
            odl_non_pianificabili.append(ODLNestingInfo(
                id=odl.id,
                parte_descrizione=parte.descrizione_breve if parte else "Sconosciuta",
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