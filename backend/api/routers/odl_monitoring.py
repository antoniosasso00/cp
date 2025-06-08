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
        
        logger.info(f"Restituito monitoraggio completo per ODL {odl_id}")
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
        
        # Arricchisci i dati della timeline
        logs_arricchiti = []
        for evento in timeline_stati:
            log_dict = {
                "id": evento["id"],
                "evento": f"Cambio stato: {evento['stato_precedente']} → {evento['stato_nuovo']}",
                "stato_precedente": evento["stato_precedente"],
                "stato_nuovo": evento["stato_nuovo"],
                "descrizione": evento.get("note", ""),
                "responsabile": evento.get("responsabile", "sistema"),
                "timestamp": evento["timestamp"].isoformat(),
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
    Include i timestamp degli stati e le durate necessarie per il rendering.
    
    ✅ NOVITÀ: Integra i tempi di preparazione dal modello TempoFase per maggiore precisione.
    
    Se non ci sono log disponibili, restituisce comunque i dati base dell'ODL
    per permettere la visualizzazione stimata nel frontend.
    """
    try:
        from models.odl import ODL
        from models.tempo_fase import TempoFase
        from datetime import datetime
        
        # Recupera l'ODL
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if not odl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        # ✅ NOVITÀ: Recupera i tempi delle fasi da TempoFase
        tempi_fasi = db.query(TempoFase).filter(
            TempoFase.odl_id == odl_id
        ).order_by(TempoFase.inizio_fase).all()
        
        # Mappa i tempi delle fasi per stato
        tempi_fase_per_stato = {}
        for tempo_fase in tempi_fasi:
            stato_corrispondente = {
                "preparazione": "Preparazione",
                "laminazione": "Laminazione", 
                "attesa_cura": "Attesa Cura",
                "cura": "Cura"
            }.get(tempo_fase.fase)
            
            if stato_corrispondente:
                tempi_fase_per_stato[stato_corrispondente] = tempo_fase
        
        # Recupera la timeline degli stati da StateTrackingService
        timeline_stati = StateTrackingService.ottieni_timeline_stati(db=db, odl_id=odl_id)
        
        # Calcola i timestamp per ogni stato
        timestamps_stati = []
        
        # Se ci sono cambi di stato, elaborali e integra con TempoFase
        if timeline_stati and len(timeline_stati) > 0:
            for i, evento in enumerate(timeline_stati):
                stato = evento["stato_nuovo"]
                
                # ✅ INTEGRAZIONE: Prova prima a usare TempoFase, poi fallback a StateLog
                if stato in tempi_fase_per_stato:
                    tempo_fase = tempi_fase_per_stato[stato]
                    
                    # Usa i dati precisi di TempoFase
                    inizio = tempo_fase.inizio_fase.isoformat()
                    fine = tempo_fase.fine_fase.isoformat() if tempo_fase.fine_fase else None
                    durata_minuti = tempo_fase.durata_minuti
                    
                    # Se la fase non è completata, calcola durata corrente
                    if not fine and not durata_minuti:
                        durata_corrente = int((datetime.now() - tempo_fase.inizio_fase).total_seconds() / 60)
                        durata_minuti = durata_corrente
                    
                    timestamps_stati.append({
                        "stato": stato,
                        "inizio": inizio,
                        "fine": fine,
                        "durata_minuti": durata_minuti,
                        "fonte_dati": "tempo_fase"  # Indica che proviene da TempoFase
                    })
                    
                else:
                    # ✅ FALLBACK: Usa la logica originale basata su StateLog
                    if i < len(timeline_stati) - 1:
                        # Non è l'ultimo evento, calcola durata fino al prossimo
                        prossimo_evento = timeline_stati[i + 1]
                        durata_delta = prossimo_evento["timestamp"] - evento["timestamp"]
                        durata_minuti = int(durata_delta.total_seconds() / 60)
                        
                        timestamps_stati.append({
                            "stato": stato,
                            "inizio": evento["timestamp"].isoformat(),
                            "fine": prossimo_evento["timestamp"].isoformat(),
                            "durata_minuti": durata_minuti,
                            "fonte_dati": "state_log"  # Indica che proviene da StateLog
                        })
                    else:
                        # Ultimo evento - stato corrente
                        if odl.status != 'Finito':
                            durata_corrente = int((datetime.now() - evento["timestamp"]).total_seconds() / 60)
                            timestamps_stati.append({
                                "stato": stato,
                                "inizio": evento["timestamp"].isoformat(),
                                "fine": None,
                                "durata_minuti": durata_corrente,
                                "fonte_dati": "state_log"
                            })
                        else:
                            # ODL finito
                            timestamps_stati.append({
                                "stato": stato,
                                "inizio": evento["timestamp"].isoformat(),
                                "fine": evento["timestamp"].isoformat(),
                                "durata_minuti": 0,
                                "fonte_dati": "state_log"
                            })
        
        # ✅ NOVITÀ: Se non ci sono dati StateLog ma ci sono TempoFase, usa solo quelli
        elif tempi_fasi:
            for tempo_fase in tempi_fasi:
                stato_corrispondente = {
                    "preparazione": "Preparazione",
                    "laminazione": "Laminazione", 
                    "attesa_cura": "Attesa Cura",
                    "cura": "Cura"
                }.get(tempo_fase.fase)
                
                if stato_corrispondente:
                    inizio = tempo_fase.inizio_fase.isoformat()
                    fine = tempo_fase.fine_fase.isoformat() if tempo_fase.fine_fase else None
                    durata_minuti = tempo_fase.durata_minuti
                    
                    # Se la fase non è completata, calcola durata corrente
                    if not fine and not durata_minuti:
                        durata_corrente = int((datetime.now() - tempo_fase.inizio_fase).total_seconds() / 60)
                        durata_minuti = durata_corrente
                    
                    timestamps_stati.append({
                        "stato": stato_corrispondente,
                        "inizio": inizio,
                        "fine": fine,
                        "durata_minuti": durata_minuti,
                        "fonte_dati": "tempo_fase"
                    })
        
        # Calcola tempo totale stimato
        tempo_totale_stimato = None
        if len(timestamps_stati) > 0:
            tempo_totale_stimato = sum(t["durata_minuti"] or 0 for t in timestamps_stati)
        else:
            # Fallback: calcola durata dall'inizio dell'ODL
            durata_dall_inizio = int((datetime.now() - odl.created_at).total_seconds() / 60)
            tempo_totale_stimato = durata_dall_inizio
        
        # ✅ NOVITÀ: Aggiungi informazioni sui tempi di preparazione
        fonte_tempo_preparazione = None
        tempo_preparazione_minuti = None
        
        for timestamp in timestamps_stati:
            if timestamp["stato"] == "Preparazione" and timestamp["fonte_dati"] == "tempo_fase":
                fonte_tempo_preparazione = "preciso"
                tempo_preparazione_minuti = timestamp["durata_minuti"]
                break
        
        if not fonte_tempo_preparazione:
            for timestamp in timestamps_stati:
                if timestamp["stato"] == "Preparazione":
                    fonte_tempo_preparazione = "stimato"
                    tempo_preparazione_minuti = timestamp["durata_minuti"]
                    break
        
        progress_data = {
            "id": odl_id,
            "status": odl.status,
            "created_at": odl.created_at.isoformat(),
            "updated_at": odl.updated_at.isoformat(),
            "timestamps": timestamps_stati,
            "tempo_totale_stimato": tempo_totale_stimato,
            "has_timeline_data": len(timestamps_stati) > 0,
            # ✅ NOVITÀ: Dati specifici per preparazione
            "tempo_preparazione": {
                "minuti": tempo_preparazione_minuti,
                "fonte": fonte_tempo_preparazione,
                "disponibile": tempo_preparazione_minuti is not None
            },
            "fonti_dati": {
                "tempo_fasi_count": len(tempi_fasi),
                "state_logs_count": len(timeline_stati) if timeline_stati else 0,
                "integrazione_attiva": len(tempi_fasi) > 0
            }
        }
        
        if len(timestamps_stati) > 0:
            fonti_usate = set(t["fonte_dati"] for t in timestamps_stati)
            logger.info(f"Restituiti dati di progresso per ODL {odl_id} con {len(timestamps_stati)} timestamps (fonti: {fonti_usate})")
        else:
            logger.info(f"Restituiti dati di progresso per ODL {odl_id} senza timeline (fallback mode)")
        
        return progress_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante il recupero dei dati di progresso ODL {odl_id}: {str(e)}")
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