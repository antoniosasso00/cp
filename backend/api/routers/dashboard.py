"""
Router per endpoint di dashboard e KPI
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, distinct, func
from datetime import datetime, timedelta

from api.database import get_db
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.nesting_result import NestingResult
from models.schedule_entry import ScheduleEntry
from models.state_log import StateLog

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard KPI"],
    responses={404: {"description": "Risorsa non trovata"}}
)

@router.get("/odl-count")
def get_odl_count(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    🔢 ENDPOINT ODL COUNT
    =====================
    
    Ritorna statistiche sui conteggi ODL per il widget
    """
    try:
        logger.info("📊 Recupero statistiche ODL per widget dashboard...")
        
        # Conteggio totale ODL
        total_odl = db.query(ODL).count()
        
        # Conteggio per stato
        odl_preparazione = db.query(ODL).filter(ODL.status == "Preparazione").count()
        odl_attesa_cura = db.query(ODL).filter(ODL.status == "Attesa cura").count()
        odl_in_cura = db.query(ODL).filter(ODL.status == "In cura").count()
        odl_completati = db.query(ODL).filter(ODL.status == "Completato").count()
        
        # ODL completati oggi
        today = datetime.now().date()
        odl_completati_oggi = db.query(StateLog).filter(
            and_(
                StateLog.stato_nuovo == "Completato",
                func.date(StateLog.timestamp) == today
            )
        ).count()
        
        # Calcolo percentuale completamento
        completion_rate = round((odl_completati / total_odl * 100) if total_odl > 0 else 0, 1)
        
        # Trend ultima settimana per grafico
        trend_data = []
        for i in range(7):
            day = datetime.now().date() - timedelta(days=6-i)
            completati_day = db.query(StateLog).filter(
                and_(
                    StateLog.stato_nuovo == "Completato",
                    func.date(StateLog.timestamp) == day
                )
            ).count()
            
            totali_day = db.query(ODL).filter(
                func.date(ODL.created_at) <= day
            ).count()
            
            trend_data.append({
                "data": day.isoformat(),
                "completati": completati_day,
                "totali": totali_day
            })
        
        # Calcolo variazione giornaliera
        ieri = datetime.now().date() - timedelta(days=1)
        completati_ieri = db.query(StateLog).filter(
            and_(
                StateLog.stato_nuovo == "Completato",
                func.date(StateLog.timestamp) == ieri
            )
        ).count()
        
        variazione = odl_completati_oggi - completati_ieri
        
        result = {
            "totali": total_odl,
            "completati": odl_completati,
            "in_corso": odl_in_cura + odl_attesa_cura,
            "in_sospeso": odl_preparazione,
            "percentuale_completamento": completion_rate,
            "variazione_giornaliera": variazione,
            "trend_ultimi_7_giorni": trend_data,
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Statistiche ODL recuperate: {total_odl} totali, {completion_rate}% completati")
        return result
        
    except Exception as e:
        logger.error(f"❌ Errore nel recupero statistiche ODL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel caricamento statistiche ODL: {str(e)}")

@router.get("/autoclave-load")
def get_autoclave_load(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    🏭 ENDPOINT CARICO AUTOCLAVI
    ============================
    
    Ritorna statistiche sul carico delle autoclavi
    """
    try:
        logger.info("🏭 Recupero statistiche carico autoclavi per widget dashboard...")
        
        # Conta autoclavi per stato
        total_autoclavi = db.query(Autoclave).count()
        autoclavi_disponibili = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).count()
        autoclavi_occupate = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.IN_USO
        ).count()
        autoclavi_manutenzione = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.MANUTENZIONE
        ).count()
        
        # Calcolo carico percentuale
        carico_percentuale = round((autoclavi_occupate / total_autoclavi) * 100, 1) if total_autoclavi > 0 else 0
        
        # Capacità in kg
        capacita_massima = db.query(func.sum(Autoclave.max_load_kg)).filter(
            Autoclave.stato.in_([StatoAutoclaveEnum.DISPONIBILE, StatoAutoclaveEnum.IN_USO])
        ).scalar() or 0
        
        capacita_utilizzata = db.query(func.sum(Autoclave.max_load_kg)).filter(
            Autoclave.stato == StatoAutoclaveEnum.IN_USO
        ).scalar() or 0
        
        # Trend utilizzo 24h (simulato per ora)
        trend_24h = []
        for i in range(24):
            ora = f"{i:02d}:00"
            # Simulazione basata su pattern tipici di utilizzo
            percentuale = carico_percentuale + (i % 8 - 4) * 5
            percentuale = max(0, min(100, percentuale))
            
            trend_24h.append({
                "ora": ora,
                "percentuale": round(percentuale, 1),
                "autoclavi_attive": round(autoclavi_occupate * percentuale / 100)
            })
        
        # Variazione oraria (simulata)
        variazione_oraria = (carico_percentuale - 50) * 0.1  # Esempio di calcolo
        
        result = {
            "carico_totale_percentuale": carico_percentuale,
            "autoclavi_attive": autoclavi_occupate,
            "autoclavi_totali": total_autoclavi,
            "capacita_utilizzata_kg": capacita_utilizzata,
            "capacita_massima_kg": capacita_massima,
            "variazione_oraria": variazione_oraria,
            "autoclavi_per_stato": {
                "disponibili": autoclavi_disponibili,
                "occupate": autoclavi_occupate,
                "manutenzione": autoclavi_manutenzione,
                "errore": 0  # Non abbiamo questo stato nel nostro modello
            },
            "trend_utilizzo_24h": trend_24h,
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Statistiche autoclavi recuperate: {carico_percentuale}% carico")
        return result
        
    except Exception as e:
        logger.error(f"❌ Errore nel recupero statistiche autoclavi: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel caricamento statistiche autoclavi: {str(e)}")

@router.get("/nesting-active")
def get_nesting_active(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    📦 ENDPOINT NESTING ATTIVI
    ===========================
    
    Ritorna statistiche sui nesting attivi
    """
    try:
        logger.info("📦 Recupero statistiche nesting attivi per widget dashboard...")
        
        # Conta nesting per stato
        nesting_in_elaborazione = db.query(NestingResult).filter(
            NestingResult.stato == "In corso"
        ).count()
        
        nesting_in_sospeso = db.query(NestingResult).filter(
            NestingResult.stato == "In sospeso"
        ).count()
        
        nesting_confermati = db.query(NestingResult).filter(
            NestingResult.stato == "Confermato"
        ).count()
        
        nesting_completati = db.query(NestingResult).filter(
            NestingResult.stato == "Completato"
        ).count()
        
        # Nesting attivi = in elaborazione + confermati
        nesting_attivi = nesting_in_elaborazione + nesting_confermati
        
        # Batch oggi
        today = datetime.now().date()
        batch_totali_oggi = db.query(NestingResult).filter(
            func.date(NestingResult.created_at) == today
        ).count()
        
        batch_completati_oggi = db.query(NestingResult).filter(
            and_(
                NestingResult.stato == "Completato",
                func.date(NestingResult.updated_at) == today
            )
        ).count()
        
        # Tempo medio elaborazione (simulato - potremmo calcolarlo dai log)
        tempo_medio = 45  # minuti - da implementare calcolo reale
        
        # Variazione giornaliera
        ieri = datetime.now().date() - timedelta(days=1)
        nesting_attivi_ieri = db.query(NestingResult).filter(
            and_(
                NestingResult.stato.in_(["In corso", "Confermato"]),
                func.date(NestingResult.created_at) == ieri
            )
        ).count()
        
        variazione = nesting_attivi - nesting_attivi_ieri
        
        # Dettagli nesting attivi
        dettagli_nesting = []
        nesting_attivi_list = db.query(NestingResult).filter(
            NestingResult.stato.in_(["In corso", "Confermato", "In sospeso"])
        ).limit(5).all()
        
        for nesting in nesting_attivi_list:
            dettagli_nesting.append({
                "id": nesting.id,
                "stato": nesting.stato,
                "autoclave": nesting.autoclave.nome if nesting.autoclave else "N/A",
                "odl_count": len(nesting.odl_ids) if nesting.odl_ids else 0,
                "tempo_inizio": nesting.created_at.isoformat(),
                "tempo_stimato_fine": None  # Da implementare
            })
        
        result = {
            "nesting_attivi": nesting_attivi,
            "nesting_in_coda": nesting_in_sospeso,
            "batch_completati_oggi": batch_completati_oggi,
            "batch_totali_oggi": batch_totali_oggi,
            "tempo_medio_elaborazione_minuti": tempo_medio,
            "variazione_giornaliera": variazione,
            "nesting_per_stato": {
                "in_elaborazione": nesting_in_elaborazione,
                "in_sospeso": nesting_in_sospeso,
                "confermati": nesting_confermati,
                "completati": nesting_completati
            },
            "dettagli_nesting": dettagli_nesting,
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Statistiche nesting recuperate: {nesting_attivi} attivi")
        return result
        
    except Exception as e:
        logger.error(f"❌ Errore nel recupero statistiche nesting: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel caricamento statistiche nesting: {str(e)}")

@router.get("/kpi-summary")
def get_kpi_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    📈 ENDPOINT RIASSUNTO KPI
    =========================
    
    Ritorna un riassunto completo di tutti i KPI principali
    """
    try:
        logger.info("📈 Recupero riassunto completo KPI per dashboard...")
        
        # Riutilizza le funzioni già definite
        odl_stats = get_odl_count(db)
        autoclave_stats = get_autoclave_load(db)
        nesting_stats = get_nesting_active(db)
        
        # Calcolo score globale sistema
        completion_score = min(odl_stats["percentuale_completamento"], 100)
        utilization_score = min(100 - autoclave_stats["carico_totale_percentuale"], 100)
        efficiency_score = min((nesting_stats["nesting_attivi"] / max(nesting_stats["batch_totali_oggi"], 1)) * 100, 100)
        
        overall_score = round((completion_score + utilization_score + efficiency_score) / 3, 1)
        
        result = {
            "odl": odl_stats,
            "autoclavi": autoclave_stats,
            "nesting": nesting_stats,
            "overall_score": overall_score,
            "system_health": "excellent" if overall_score >= 80 else "good" if overall_score >= 60 else "needs_attention",
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"✅ KPI summary recuperato: score globale {overall_score}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Errore nel recupero KPI summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel caricamento KPI summary: {str(e)}") 