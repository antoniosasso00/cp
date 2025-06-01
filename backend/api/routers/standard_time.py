import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from api.database import get_db
from models.standard_time import StandardTime
from models.catalogo import Catalogo
from services.standard_time_service import StandardTimeService, recalc_std_times

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    tags=["Standard Times"],
    responses={404: {"description": "Tempo standard non trovato"}}
)

@router.get("/", summary="Ottiene la lista dei tempi standard")
def read_standard_times(
    skip: int = 0, 
    limit: int = 100, 
    part_number: Optional[str] = Query(None, description="Filtra per part number"),
    part_id: Optional[int] = Query(None, description="Filtra per ID parte"),
    phase: Optional[str] = Query(None, description="Filtra per fase"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di tempi standard con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **part_number**: filtro opzionale per part number
    - **part_id**: filtro opzionale per ID parte
    - **phase**: filtro opzionale per fase
    """
    query = db.query(StandardTime)
    
    # Applicazione filtri
    if part_number:
        query = query.filter(StandardTime.part_number == part_number)
    if part_id:
        # Unisci con la tabella parti per filtrare per part_id
        from models.parte import Parte
        query = query.join(Parte, StandardTime.part_number == Parte.part_number).filter(Parte.id == part_id)
    if phase:
        query = query.filter(StandardTime.phase == phase)
    
    # Ordina per part_number e fase
    query = query.order_by(StandardTime.part_number, StandardTime.phase)
    
    standard_times = query.offset(skip).limit(limit).all()
    
    # Converti in formato JSON serializzabile
    result = []
    for st in standard_times:
        result.append({
            "id": st.id,
            "part_number": st.part_number,
            "phase": st.phase,
            "minutes": st.minutes,
            "note": st.note,
            "created_at": st.created_at.isoformat() if st.created_at else None,
            "updated_at": st.updated_at.isoformat() if st.updated_at else None
        })
    
    return result

@router.post("/recalc", summary="Ricalcola automaticamente i tempi standard")
def recalculate_standard_times(
    user_id: Optional[str] = Query("admin", description="ID dell'utente che richiede il ricalcolo"),
    user_role: Optional[str] = Query("ADMIN", description="Ruolo dell'utente (ADMIN o responsabile)"),
    db: Session = Depends(get_db)
):
    """
    Ricalcola automaticamente tutti i tempi standard basandosi sui dati storici delle fasi completate.
    
    **Questo endpoint:**
    - Analizza tutti gli ODL con `include_in_std=True` e status `Finito`
    - Raggruppa i tempi per part_number e fase
    - Calcola media, mediana e percentile 90 per ogni combinazione
    - Salva o aggiorna i record nella tabella standard_times
    
    **Accesso:** Solo utenti con ruolo ADMIN o responsabile
    """
    try:
        # Verifica autorizzazioni base (in un sistema reale si userebbe JWT)
        if user_role not in ["ADMIN", "responsabile"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accesso negato: solo ADMIN o responsabile possono eseguire il ricalcolo"
            )
        
        logger.info(f"🔄 Avvio ricalcolo tempi standard richiesto da {user_id} ({user_role})")
        
        # Esegui il ricalcolo
        result = recalc_std_times(db=db, user_id=user_id, user_role=user_role)
        
        return {
            "success": True,
            "message": "Ricalcolo tempi standard completato con successo",
            "statistics": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore durante il ricalcolo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il ricalcolo dei tempi standard: {str(e)}"
        )

@router.get("/statistics", summary="Ottiene statistiche sui tempi standard")
def get_standard_times_statistics(db: Session = Depends(get_db)):
    """
    Ottiene statistiche generali sui tempi standard presenti nel sistema.
    
    Returns:
        Dizionario con statistiche sui tempi standard
    """
    try:
        service = StandardTimeService(db)
        stats = service.get_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Errore durante il calcolo delle statistiche: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il calcolo delle statistiche: {str(e)}"
        )

@router.get("/top-delta", summary="Ottiene i part-number con maggiore scostamento percentuale")
def get_top_delta(
    limit: Optional[int] = Query(5, description="Numero massimo di risultati da restituire"),
    days: Optional[int] = Query(30, description="Numero di giorni da considerare per i tempi osservati"),
    db: Session = Depends(get_db)
):
    """
    Ottiene i part-number con il maggiore scostamento percentuale tra tempo reale e tempo standard.
    
    **Utilizzato per il pannello "Top 5 Part con maggiore scostamento %" nel dashboard di monitoraggio.**
    
    **Returns:**
    - Lista di part-number e fasi ordinati per scostamento percentuale decrescente
    - Delta percentuale con codifica colore (verde ≤ 5%, giallo 5-10%, rosso >10%)
    - Numero di osservazioni per validare la significatività del dato
    - Tempi osservati e standard per il confronto
    """
    try:
        logger.info(f"🔍 Richiesta top {limit} scostamenti per ultimi {days} giorni")
        
        service = StandardTimeService(db)
        top_variances = service.get_top_variances(limit=limit, days=days)
        
        return {
            "success": True,
            "data": top_variances,
            "parameters": {
                "limit": limit,
                "days": days,
                "data_analisi": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Errore durante il calcolo degli scostamenti: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il calcolo degli scostamenti: {str(e)}"
        )

@router.get("/{standard_time_id}", summary="Ottiene un tempo standard specifico")
def read_standard_time(standard_time_id: int, db: Session = Depends(get_db)):
    """
    Recupera un tempo standard specifico tramite il suo ID.
    """
    db_standard_time = db.query(StandardTime).filter(StandardTime.id == standard_time_id).first()
    if db_standard_time is None:
        logger.warning(f"Tentativo di accesso a tempo standard inesistente: {standard_time_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tempo standard con ID '{standard_time_id}' non trovato"
        )
    
    return {
        "id": db_standard_time.id,
        "part_number": db_standard_time.part_number,
        "phase": db_standard_time.phase,
        "minutes": db_standard_time.minutes,
        "note": db_standard_time.note,
        "created_at": db_standard_time.created_at.isoformat() if db_standard_time.created_at else None,
        "updated_at": db_standard_time.updated_at.isoformat() if db_standard_time.updated_at else None
    }

@router.get("/by-part-number/{part_number}", summary="Ottiene tutti i tempi standard per un part number")
def read_standard_times_by_part_number(part_number: str, db: Session = Depends(get_db)):
    """
    Recupera tutti i tempi standard per un part number specifico.
    """
    # Verifica che il part number esista nel catalogo
    catalogo = db.query(Catalogo).filter(Catalogo.part_number == part_number).first()
    if catalogo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Part number '{part_number}' non trovato nel catalogo"
        )
    
    standard_times = db.query(StandardTime).filter(
        StandardTime.part_number == part_number
    ).order_by(StandardTime.phase).all()
    
    result = []
    for st in standard_times:
        result.append({
            "id": st.id,
            "part_number": st.part_number,
            "phase": st.phase,
            "minutes": st.minutes,
            "note": st.note,
            "created_at": st.created_at.isoformat() if st.created_at else None,
            "updated_at": st.updated_at.isoformat() if st.updated_at else None
        })
    
    return result

@router.get("/comparison/{part_number}", summary="Confronto tra tempi osservati e standard per un part number")
def get_times_comparison(
    part_number: str, 
    giorni: Optional[int] = Query(30, description="Numero di giorni da considerare per i tempi osservati"),
    db: Session = Depends(get_db)
):
    """
    Ottiene un confronto completo tra tempi osservati e tempi standard per un part number.
    
    **Returns:**
    - Tempi osservati (media delle fasi completate negli ultimi giorni)
    - Tempi standard (dal database standard_times)
    - Delta percentuale
    - Numero di osservazioni per ogni fase
    - Flag "dati limitati" se < 5 ODL
    """
    try:
        from models.parte import Parte
        from models.odl import ODL
        from models.tempo_fase import TempoFase
        from sqlalchemy import and_, func
        from datetime import datetime, timedelta
        
        # Verifica che il part number esista nel catalogo
        catalogo = db.query(Catalogo).filter(Catalogo.part_number == part_number).first()
        if catalogo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Part number '{part_number}' non trovato nel catalogo"
            )
        
        # Calcola la data di inizio periodo
        data_limite = datetime.now() - timedelta(days=giorni)
        
        # Query per ottenere i tempi osservati raggruppati per fase
        tempi_osservati_query = (
            db.query(
                TempoFase.fase,
                func.avg(TempoFase.durata_minuti).label('media_minuti'),
                func.count(TempoFase.id).label('numero_osservazioni')
            )
            .join(ODL, TempoFase.odl_id == ODL.id)
            .join(Parte, ODL.parte_id == Parte.id)
            .filter(
                and_(
                    Parte.part_number == part_number,
                    TempoFase.durata_minuti.isnot(None),
                    TempoFase.durata_minuti > 0,
                    ODL.include_in_std == True,
                    ODL.status == "Finito",
                    TempoFase.created_at >= data_limite
                )
            )
            .group_by(TempoFase.fase)
        )
        
        tempi_osservati = {row.fase: {
            'media_minuti': float(row.media_minuti), 
            'numero_osservazioni': row.numero_osservazioni
        } for row in tempi_osservati_query.all()}
        
        # Ottieni i tempi standard
        tempi_standard_query = db.query(StandardTime).filter(
            StandardTime.part_number == part_number
        )
        
        tempi_standard = {st.phase: {
            'minutes': st.minutes,
            'note': st.note
        } for st in tempi_standard_query.all()}
        
        # Combina i dati per il confronto
        fasi_confronto = {}
        tutte_le_fasi = set(tempi_osservati.keys()) | set(tempi_standard.keys())
        
        for fase in tutte_le_fasi:
            osservato = tempi_osservati.get(fase, {'media_minuti': 0, 'numero_osservazioni': 0})
            standard = tempi_standard.get(fase, {'minutes': 0, 'note': None})
            
            # Calcola delta percentuale
            delta_percentuale = 0
            if standard['minutes'] > 0 and osservato['media_minuti'] > 0:
                delta_percentuale = ((osservato['media_minuti'] - standard['minutes']) / standard['minutes']) * 100
            
            # Determina se i dati sono limitati
            dati_limitati = osservato['numero_osservazioni'] < 5
            
            # Determina il colore del delta
            colore_delta = "verde"  # default
            if abs(delta_percentuale) > 20:
                colore_delta = "rosso"
            elif abs(delta_percentuale) > 10:
                colore_delta = "giallo"
            
            fasi_confronto[fase] = {
                "fase": fase,
                "tempo_osservato_minuti": osservato['media_minuti'],
                "tempo_standard_minuti": standard['minutes'],
                "numero_osservazioni": osservato['numero_osservazioni'],
                "delta_percentuale": round(delta_percentuale, 1),
                "dati_limitati": dati_limitati,
                "colore_delta": colore_delta,
                "note_standard": standard['note']
            }
        
        # Calcola scostamento medio (solo per fasi con dati validi)
        fasi_valide = [f for f in fasi_confronto.values() 
                      if f['tempo_osservato_minuti'] > 0 and f['tempo_standard_minuti'] > 0]
        
        scostamento_medio = 0
        if fasi_valide:
            scostamento_medio = sum(abs(f['delta_percentuale']) for f in fasi_valide) / len(fasi_valide)
        
        # Conta ODL totali per il part number
        odl_totali = (
            db.query(func.count(ODL.id))
            .join(Parte, ODL.parte_id == Parte.id)
            .filter(
                and_(
                    Parte.part_number == part_number,
                    ODL.include_in_std == True,
                    ODL.status == "Finito",
                    ODL.created_at >= data_limite
                )
            )
            .scalar()
        )
        
        return {
            "part_number": part_number,
            "periodo_giorni": giorni,
            "fasi": fasi_confronto,
            "scostamento_medio_percentuale": round(scostamento_medio, 1),
            "odl_totali_periodo": odl_totali,
            "dati_limitati_globale": odl_totali < 5,
            "ultima_analisi": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore durante il confronto tempi per {part_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il confronto dei tempi: {str(e)}"
        ) 