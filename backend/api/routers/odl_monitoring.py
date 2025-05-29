import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from api.database import get_db
from schemas.odl_monitoring import (
    ODLMonitoringRead,
    ODLMonitoringSummary,
    ODLMonitoringStats,
    ODLLogCreate,
    ODLLogRead
)
from schemas.odl_alerts import ODLAlertsResponse
from services.odl_monitoring_service import ODLMonitoringService
from services.odl_log_service import ODLLogService
from services.odl_alerts_service import ODLAlertsService
from services.state_tracking_service import StateTrackingService

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoraggio ODL"],
    responses={404: {"description": "Risorsa non trovata"}}
)

@router.get("/stats", response_model=ODLMonitoringStats,
            summary="Ottiene statistiche generali del monitoraggio ODL")
def get_monitoring_stats(db: Session = Depends(get_db)):
    """
    Restituisce statistiche generali del monitoraggio ODL:
    - Numero totale di ODL
    - Conteggio per stato
    - ODL in ritardo
    - ODL completati oggi
    - Tempo medio di completamento
    """
    try:
        stats = ODLMonitoringService.ottieni_statistiche_monitoraggio(db)
        return stats
    except Exception as e:
        logger.error(f"Errore durante il recupero delle statistiche: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche di monitoraggio"
        )



@router.get("/", response_model=List[ODLMonitoringSummary],
            summary="Ottiene lista riassuntiva del monitoraggio ODL")
def get_monitoring_list(
    skip: int = Query(0, ge=0, description="Numero di elementi da saltare"),
    limit: int = Query(50, ge=1, le=200, description="Numero massimo di elementi da restituire"),
    status_filter: Optional[str] = Query(None, description="Filtro per stato ODL"),
    priorita_min: Optional[int] = Query(None, ge=1, description="Priorità minima"),
    solo_attivi: bool = Query(True, description="Se True, esclude ODL completati"),
    db: Session = Depends(get_db)
):
    """
    Restituisce una lista riassuntiva del monitoraggio ODL con:
    - Informazioni base dell'ODL
    - Stato nesting e autoclave
    - Ultimo evento registrato
    - Tempo nello stato corrente
    
    Supporta filtri per stato, priorità e inclusione/esclusione ODL completati.
    """
    try:
        monitoring_list = ODLMonitoringService.ottieni_lista_monitoraggio(
            db=db,
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            priorita_min=priorita_min,
            solo_attivi=solo_attivi
        )
        
        logger.info(f"Restituiti {len(monitoring_list)} elementi di monitoraggio ODL")
        return monitoring_list
        
    except Exception as e:
        logger.error(f"Errore durante il recupero della lista monitoraggio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero della lista di monitoraggio"
        )



@router.get("/{odl_id}", response_model=ODLMonitoringRead,
            summary="Ottiene monitoraggio completo di un ODL specifico")
def get_odl_monitoring_detail(odl_id: int, db: Session = Depends(get_db)):
    """
    Restituisce il monitoraggio completo di un ODL specifico con:
    - Tutte le informazioni base dell'ODL
    - Dettagli nesting, autoclave e ciclo di cura
    - Log completo di avanzamento
    - Statistiche temporali dettagliate
    - Informazioni schedulazione
    """
    try:
        monitoring_detail = ODLMonitoringService.ottieni_odl_monitoraggio_completo(
            db=db,
            odl_id=odl_id
        )
        
        if not monitoring_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        # ✅ CORREZIONE: Validazione robusta dei logs nella risposta
        if not hasattr(monitoring_detail, 'logs') or monitoring_detail.logs is None:
            logger.warning(f"ODL {odl_id}: logs mancanti, impostando array vuoto")
            monitoring_detail.logs = []
        elif not isinstance(monitoring_detail.logs, list):
            logger.warning(f"ODL {odl_id}: logs non è una lista, convertendo in array vuoto")
            monitoring_detail.logs = []
        
        logger.info(f"Restituito monitoraggio completo per ODL {odl_id} con {len(monitoring_detail.logs)} logs")
        return monitoring_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante il recupero del monitoraggio ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero del monitoraggio ODL"
        )

@router.get("/{odl_id}/logs", response_model=List[ODLLogRead],
            summary="Ottiene i log di un ODL specifico")
def get_odl_logs(
    odl_id: int,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limite numero di log da restituire"),
    db: Session = Depends(get_db)
):
    """
    Restituisce i log di avanzamento di un ODL specifico, ordinati per timestamp decrescente.
    """
    try:
        logs = ODLLogService.ottieni_logs_odl(db=db, odl_id=odl_id, limit=limit)
        
        # Arricchisci i log con informazioni correlate
        logs_arricchiti = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "odl_id": log.odl_id,
                "evento": log.evento,
                "stato_precedente": log.stato_precedente,
                "stato_nuovo": log.stato_nuovo,
                "descrizione": log.descrizione,
                "responsabile": log.responsabile,
                "nesting_id": log.nesting_id,
                "autoclave_id": log.autoclave_id,
                "schedule_entry_id": log.schedule_entry_id,
                "timestamp": log.timestamp,
                "nesting_stato": None,
                "autoclave_nome": None
            }
            
            # Aggiungi informazioni correlate se disponibili
            if log.nesting and hasattr(log, 'nesting'):
                log_dict["nesting_stato"] = log.nesting.stato
            
            if log.autoclave and hasattr(log, 'autoclave'):
                log_dict["autoclave_nome"] = log.autoclave.nome
            
            logs_arricchiti.append(ODLLogRead(**log_dict))
        
        logger.info(f"Restituiti {len(logs_arricchiti)} log per ODL {odl_id}")
        return logs_arricchiti
        
    except Exception as e:
        logger.error(f"Errore durante il recupero dei log ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei log ODL"
        )

@router.post("/{odl_id}/logs", response_model=ODLLogRead, status_code=status.HTTP_201_CREATED,
             summary="Crea un nuovo log evento per un ODL")
def create_odl_log(
    odl_id: int,
    log_data: ODLLogCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuovo log evento per un ODL specifico.
    
    Questo endpoint permette di registrare manualmente eventi specifici
    per un ODL, utile per integrazioni esterne o eventi manuali.
    """
    try:
        # Verifica che l'ODL esista
        from models.odl import ODL
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if not odl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        # Assicurati che l'odl_id nel log corrisponda al parametro URL
        log_data.odl_id = odl_id
        
        # Crea il log
        new_log = ODLLogService.crea_log_evento(
            db=db,
            odl_id=log_data.odl_id,
            evento=log_data.evento,
            stato_nuovo=log_data.stato_nuovo,
            stato_precedente=log_data.stato_precedente,
            descrizione=log_data.descrizione,
            responsabile=log_data.responsabile,
            nesting_id=log_data.nesting_id,
            autoclave_id=log_data.autoclave_id,
            schedule_entry_id=log_data.schedule_entry_id
        )
        
        # Prepara la risposta
        response_dict = {
            "id": new_log.id,
            "odl_id": new_log.odl_id,
            "evento": new_log.evento,
            "stato_precedente": new_log.stato_precedente,
            "stato_nuovo": new_log.stato_nuovo,
            "descrizione": new_log.descrizione,
            "responsabile": new_log.responsabile,
            "nesting_id": new_log.nesting_id,
            "autoclave_id": new_log.autoclave_id,
            "schedule_entry_id": new_log.schedule_entry_id,
            "timestamp": new_log.timestamp,
            "nesting_stato": None,
            "autoclave_nome": None
        }
        
        logger.info(f"Creato nuovo log '{log_data.evento}' per ODL {odl_id}")
        return ODLLogRead(**response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante la creazione del log per ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la creazione del log ODL"
        )



@router.get("/{odl_id}/timeline", 
            summary="Ottiene timeline completa per un ODL con statistiche temporali")
def get_odl_timeline(odl_id: int, db: Session = Depends(get_db)):
    """
    Restituisce una timeline completa degli eventi di un ODL con:
    - Dati temporali per ogni stato
    - Statistiche di durata
    - Log dettagliati con informazioni correlate
    - Calcoli di efficienza
    """
    try:
        from models.odl import ODL
        from models.parte import Parte
        from models.tool import Tool
        from models.autoclave import Autoclave
        from models.nesting_result import NestingResult
        from datetime import datetime, timedelta
        
        # Recupera l'ODL con le relazioni
        odl = db.query(ODL).options(
            joinedload(ODL.parte),
            joinedload(ODL.tool),
            joinedload(ODL.logs)
        ).filter(ODL.id == odl_id).first()
        
        if not odl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        # ✅ CORREZIONE: Usa StateTrackingService per i cambi di stato
        timeline_stati = StateTrackingService.ottieni_timeline_stati(db=db, odl_id=odl_id)
        
        # ✅ CORREZIONE: Gestione robusta quando non ci sono dati timeline
        if not timeline_stati or not isinstance(timeline_stati, list):
            logger.warning(f"ODL {odl_id}: timeline_stati vuoto o non valido, usando fallback")
            timeline_stati = []
        
        # Arricchisci i dati della timeline
        logs_arricchiti = []
        if timeline_stati:  # Solo se ci sono dati
            for evento in timeline_stati:
                if not evento or not isinstance(evento, dict):
                    logger.warning(f"ODL {odl_id}: evento timeline non valido, saltato")
                    continue
                    
                log_dict = {
                    "id": evento.get("id", 0),
                    "evento": f"Cambio stato: {evento.get('stato_precedente', 'N/A')} → {evento.get('stato_nuovo', 'N/A')}",
                    "stato_precedente": evento.get("stato_precedente"),
                    "stato_nuovo": evento.get("stato_nuovo"),
                    "descrizione": evento.get("note", ""),
                    "responsabile": evento.get("responsabile", "sistema"),
                    "timestamp": evento.get("timestamp", datetime.now()).isoformat() if hasattr(evento.get("timestamp"), 'isoformat') else str(evento.get("timestamp", datetime.now())),
                    "nesting_stato": None,
                    "autoclave_nome": None,
                    "nesting_id": None,
                    "autoclave_id": None,
                    "schedule_entry_id": None
                }
                logs_arricchiti.append(log_dict)
        
        # Calcola le durate per stato
        durata_per_stato = {}
        timestamps_stati = []
        
        # Raggruppa gli eventi per transizioni di stato
        for i, evento in enumerate(timeline_stati):
            if i < len(timeline_stati) - 1:
                prossimo_evento = timeline_stati[i + 1]
                durata_delta = prossimo_evento["timestamp"] - evento["timestamp"]
                durata_minuti = int(durata_delta.total_seconds() / 60)
                
                stato = evento["stato_nuovo"]
                if stato not in durata_per_stato:
                    durata_per_stato[stato] = 0
                durata_per_stato[stato] += durata_minuti
                
                # Aggiungi timestamp per la barra di progresso
                timestamps_stati.append({
                    "stato": stato,
                    "inizio": evento["timestamp"].isoformat(),
                    "fine": prossimo_evento["timestamp"].isoformat(),
                    "durata_minuti": durata_minuti
                })
            else:
                # Ultimo evento - stato corrente
                if odl.status != 'Finito':
                    durata_corrente = int((datetime.now() - evento["timestamp"]).total_seconds() / 60)
                    stato = evento["stato_nuovo"]
                    if stato not in durata_per_stato:
                        durata_per_stato[stato] = 0
                    durata_per_stato[stato] += durata_corrente
                    
                    timestamps_stati.append({
                        "stato": stato,
                        "inizio": evento["timestamp"].isoformat(),
                        "fine": None,
                        "durata_minuti": durata_corrente
                    })
        
        # Calcola statistiche
        durata_totale_minuti = sum(durata_per_stato.values())
        numero_transizioni = len(timeline_stati) - 1 if len(timeline_stati) > 1 else 0
        
        # Calcola tempo medio per transizione
        tempo_medio_per_transizione = {}
        if numero_transizioni > 0:
            for stato, durata in durata_per_stato.items():
                tempo_medio_per_transizione[stato] = durata
        
        # Stima efficienza (basata su tempi standard se disponibili)
        efficienza_stimata = None
        if durata_totale_minuti > 0:
            # Tempo stimato base (esempio: 8 ore per un ODL completo)
            tempo_stimato_base = 8 * 60  # 480 minuti
            efficienza_stimata = min(100, int((tempo_stimato_base / durata_totale_minuti) * 100))
        
        # Prepara la risposta completa
        timeline_data = {
            "odl_id": odl_id,
            "parte_nome": odl.parte.descrizione_breve,
            "tool_nome": odl.tool.part_number_tool,
            "status_corrente": odl.status,
            "created_at": odl.created_at.isoformat(),
            "updated_at": odl.updated_at.isoformat(),
            "logs": logs_arricchiti,
            "timestamps": timestamps_stati,
            "statistiche": {
                "durata_totale_minuti": durata_totale_minuti,
                "durata_per_stato": durata_per_stato,
                "tempo_medio_per_transizione": tempo_medio_per_transizione,
                "numero_transizioni": numero_transizioni,
                "efficienza_stimata": efficienza_stimata
            }
        }
        
        logger.info(f"Restituita timeline completa per ODL {odl_id} con {len(logs_arricchiti)} eventi")
        return timeline_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante il recupero della timeline ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero della timeline ODL"
        )

@router.get("/{odl_id}/progress", 
            summary="Ottiene dati di progresso per la barra temporale di un ODL")
def get_odl_progress(odl_id: int, db: Session = Depends(get_db)):
    """
    Restituisce i dati ottimizzati per la visualizzazione della barra di progresso temporale.
    Include solo i timestamp degli stati e le durate necessarie per il rendering.
    
    MIGLIORAMENTO ROBUSTEZZA:
    1. Prima prova con StateTrackingService (dati precisi)
    2. Se non disponibile, usa ODLLogService (dati base)  
    3. Se nemmeno quelli, restituisce dati fallback calcolati
    """
    try:
        from models.odl import ODL
        from datetime import datetime
        
        # Recupera l'ODL
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if not odl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        timestamps_stati = []
        has_real_timeline_data = False
        data_source = "fallback"
        
        # 🎯 TENTATIVO 1: StateTrackingService (dati precisi da state_log)
        try:
            timeline_stati = StateTrackingService.ottieni_timeline_stati(db=db, odl_id=odl_id)
            
            if timeline_stati and len(timeline_stati) > 0:
                has_real_timeline_data = True
                data_source = "state_tracking"
                
                # Elabora i dati del StateTrackingService
                for i, evento in enumerate(timeline_stati):
                    if i < len(timeline_stati) - 1:
                        # Non è l'ultimo evento, calcola durata fino al prossimo
                        prossimo_evento = timeline_stati[i + 1]
                        durata_delta = prossimo_evento["timestamp"] - evento["timestamp"]
                        durata_minuti = int(durata_delta.total_seconds() / 60)
                        
                        timestamps_stati.append({
                            "stato": evento["stato_nuovo"],
                            "inizio": evento["timestamp"].isoformat(),
                            "fine": prossimo_evento["timestamp"].isoformat(),
                            "durata_minuti": durata_minuti
                        })
                    else:
                        # Ultimo evento - stato corrente
                        if odl.status != 'Finito':
                            durata_corrente = int((datetime.now() - evento["timestamp"]).total_seconds() / 60)
                            timestamps_stati.append({
                                "stato": evento["stato_nuovo"],
                                "inizio": evento["timestamp"].isoformat(),
                                "fine": None,
                                "durata_minuti": durata_corrente
                            })
                        else:
                            # ODL finito
                            timestamps_stati.append({
                                "stato": evento["stato_nuovo"],
                                "inizio": evento["timestamp"].isoformat(),
                                "fine": evento["timestamp"].isoformat(),
                                "durata_minuti": 0
                            })
                
                logger.info(f"📊 Dati progresso da StateTrackingService per ODL {odl_id}: {len(timestamps_stati)} timestamp")
                
        except Exception as state_error:
            logger.warning(f"⚠️ StateTrackingService non disponibile per ODL {odl_id}: {str(state_error)}")
        
        # 🎯 TENTATIVO 2: ODLLogService (fallback con i log base)
        if not has_real_timeline_data:
            try:
                logs = ODLLogService.ottieni_logs_odl(db, odl_id)
                
                if logs and len(logs) > 0:
                    # Filtra solo i cambi di stato
                    cambi_stato = [log for log in logs if 'stato' in log.evento.lower() and 'cambio' in log.evento.lower()]
                    
                    if cambi_stato:
                        has_real_timeline_data = True
                        data_source = "odl_logs"
                        
                        # Ordina per timestamp
                        cambi_stato.sort(key=lambda x: x.timestamp)
                        
                        for i, log in enumerate(cambi_stato):
                            if i < len(cambi_stato) - 1:
                                # Calcola durata fino al prossimo cambio
                                prossimo_log = cambi_stato[i + 1]
                                durata_delta = prossimo_log.timestamp - log.timestamp
                                durata_minuti = int(durata_delta.total_seconds() / 60)
                                
                                # Estrai lo stato dal log (semplificato)
                                stato = log.stato_nuovo if hasattr(log, 'stato_nuovo') else odl.status
                                
                                timestamps_stati.append({
                                    "stato": stato,
                                    "inizio": log.timestamp.isoformat(),
                                    "fine": prossimo_log.timestamp.isoformat(),
                                    "durata_minuti": durata_minuti
                                })
                            else:
                                # Ultimo cambio - stato corrente
                                stato = log.stato_nuovo if hasattr(log, 'stato_nuovo') else odl.status
                                durata_corrente = int((datetime.now() - log.timestamp).total_seconds() / 60)
                                
                                timestamps_stati.append({
                                    "stato": stato,
                                    "inizio": log.timestamp.isoformat(),
                                    "fine": None if odl.status != 'Finito' else log.timestamp.isoformat(),
                                    "durata_minuti": durata_corrente if odl.status != 'Finito' else 0
                                })
                        
                        logger.info(f"📊 Dati progresso da ODLLogService per ODL {odl_id}: {len(timestamps_stati)} timestamp")
                        
            except Exception as log_error:
                logger.warning(f"⚠️ ODLLogService non disponibile per ODL {odl_id}: {str(log_error)}")
        
        # Calcola tempo totale stimato
        tempo_totale_stimato = None
        if len(timestamps_stati) > 0:
            tempo_totale_stimato = sum(t["durata_minuti"] for t in timestamps_stati)
        else:
            # 🎯 FALLBACK FINALE: calcola durata dall'inizio dell'ODL
            durata_dall_inizio = int((datetime.now() - odl.created_at).total_seconds() / 60)
            tempo_totale_stimato = durata_dall_inizio
            data_source = "odl_created_time"
        
        # Prepara la risposta
        progress_data = {
            "id": odl_id,
            "status": odl.status,
            "created_at": odl.created_at.isoformat(),
            "updated_at": odl.updated_at.isoformat(),
            "timestamps": timestamps_stati,  # Può essere vuoto, il frontend gestirà il fallback
            "tempo_totale_stimato": tempo_totale_stimato,
            "has_timeline_data": has_real_timeline_data,  # Flag per indicare se ci sono dati reali
            "data_source": data_source  # 🆕 Indica la fonte dei dati per debug
        }
        
        # Log di debug
        if has_real_timeline_data:
            logger.info(f"✅ Dati progresso per ODL {odl_id}: {len(timestamps_stati)} timestamp da {data_source}")
        else:
            logger.info(f"📊 Dati progresso per ODL {odl_id}: modalità fallback ({data_source})")
        
        return progress_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore durante il recupero dei dati di progresso ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei dati di progresso ODL"
        )

@router.post("/generate-missing-logs", 
             summary="Genera log mancanti per ODL esistenti")
def generate_missing_logs(db: Session = Depends(get_db)):
    """
    Genera automaticamente log di creazione per ODL esistenti che non hanno log.
    
    Questo endpoint è utile per inizializzare il sistema di monitoraggio
    su un database esistente con ODL già presenti.
    """
    try:
        logs_creati = ODLLogService.genera_logs_mancanti_per_odl_esistenti(db)
        
        logger.info(f"Generati {logs_creati} log mancanti")
        return {
            "message": f"Generati {logs_creati} log di creazione per ODL esistenti",
            "logs_creati": logs_creati
        }
        
    except Exception as e:
        logger.error(f"Errore durante la generazione dei log mancanti: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la generazione dei log mancanti"
        )

@router.post("/initialize-state-tracking", 
             summary="Inizializza il tracking degli stati per ODL esistenti")
def initialize_state_tracking(db: Session = Depends(get_db)):
    """
    Inizializza il sistema di tracking degli stati per ODL esistenti.
    
    Crea i record StateLog iniziali per tutti gli ODL che non hanno ancora
    un tracking degli stati attivo.
    """
    try:
        from models.odl import ODL
        from models.state_log import StateLog
        
        # Trova tutti gli ODL che non hanno state logs
        odl_senza_tracking = db.query(ODL).filter(
            ~ODL.id.in_(
                db.query(StateLog.odl_id).distinct()
            )
        ).all()
        
        logs_creati = 0
        
        for odl in odl_senza_tracking:
            # Crea il log di stato iniziale
            state_log = StateTrackingService.registra_cambio_stato(
                db=db,
                odl_id=odl.id,
                stato_precedente=None,  # Primo stato
                stato_nuovo=odl.status,
                responsabile="sistema",
                ruolo_responsabile="ADMIN",
                note=f"Inizializzazione tracking stati per ODL esistente (creato: {odl.created_at})"
            )
            logs_creati += 1
        
        # Commit delle modifiche
        db.commit()
        
        logger.info(f"✅ Inizializzato tracking stati per {logs_creati} ODL")
        return {
            "message": f"Inizializzato tracking stati per {logs_creati} ODL esistenti",
            "logs_creati": logs_creati,
            "odl_processati": [odl.id for odl in odl_senza_tracking]
        }
        
    except Exception as e:
        logger.error(f"❌ Errore durante l'inizializzazione del tracking stati: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'inizializzazione del tracking stati"
        )