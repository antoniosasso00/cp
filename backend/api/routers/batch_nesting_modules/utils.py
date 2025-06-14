"""
Modulo utilities per batch nesting - Implementazione modulare completa

Questo modulo contiene funzioni di utilità condivise tra i diversi router:
- Validazione dati
- Formattazione risposte
- Gestione errori comuni
- Helper per relazioni database
"""

import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DatabaseError
from fastapi import HTTPException, status

from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL

logger = logging.getLogger(__name__)

# ========== VALIDATORI ==========

class ValidationError(Exception):
    """Eccezione personalizzata per errori di validazione"""
    pass

def _convert_to_enum(state: Union[str, StatoBatchNestingEnum]) -> StatoBatchNestingEnum:
    """Converte uno stato (stringa o enum) nell'enum corrispondente"""
    if isinstance(state, StatoBatchNestingEnum):
        return state
    
    # Prova a convertire la stringa in enum
    try:
        return StatoBatchNestingEnum(state)
    except ValueError:
        # Se non trova una corrispondenza diretta, prova a cercare per valore
        for enum_item in StatoBatchNestingEnum:
            if enum_item.value == state:
                return enum_item
        
        # Se non trova niente, solleva eccezione
        raise ValueError(f"Stato '{state}' non riconosciuto")

def validate_batch_state_transition(current_state: Union[str, StatoBatchNestingEnum], target_state: Union[str, StatoBatchNestingEnum]) -> bool:
    """Valida se una transizione di stato è permessa
    
    Args:
        current_state: Stato corrente (stringa dal database o enum)
        target_state: Stato target (stringa o enum)
        
    Returns:
        True se la transizione è valida
        
    Raises:
        HTTPException: Se la transizione non è permessa
    """
    try:
        # Converte entrambi gli stati in enum per il confronto
        current_enum = _convert_to_enum(current_state)
        target_enum = _convert_to_enum(target_state)
        
        if current_enum not in STATE_TRANSITIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stato corrente '{current_enum.value}' non riconosciuto"
            )
        
        allowed_transitions = STATE_TRANSITIONS[current_enum]
        if target_enum not in allowed_transitions:
            allowed_values = [t.value for t in allowed_transitions]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transizione non permessa da '{current_enum.value}' a '{target_enum.value}'. "
                       f"Transizioni possibili: {allowed_values}"
            )
        
        return True
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

def validate_user_permission(user_role: str, action: str) -> bool:
    """Valida se un ruolo utente ha i permessi per un'azione"""
    if user_role not in ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Ruolo {user_role} non riconosciuto"
        )
    
    allowed_actions = ROLE_PERMISSIONS[user_role]
    if action not in allowed_actions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Ruolo {user_role} non autorizzato per l'azione {action}"
        )
    
    return True

# ========== FORMATTATORI ==========

def format_batch_for_response(batch: BatchNesting, include_relations: bool = False) -> Dict[str, Any]:
    """Formatta un batch nesting per la risposta API"""
    result = {
        "id": batch.id,
        "nome": batch.nome,
        "stato": batch.stato,
        "autoclave_id": batch.autoclave_id,
        "odl_ids": batch.odl_ids or [],
        "configurazione_json": batch.configurazione_json,
        "parametri": batch.parametri,
        "numero_nesting": batch.numero_nesting,
        "peso_totale_kg": batch.peso_totale_kg,
        "area_totale_utilizzata": batch.area_totale_utilizzata,
        "valvole_totali_utilizzate": batch.valvole_totali_utilizzate,
        "note": batch.note,
        "creato_da_utente": batch.creato_da_utente,
        "creato_da_ruolo": batch.creato_da_ruolo,
        "confermato_da_utente": batch.confermato_da_utente,
        "confermato_da_ruolo": batch.confermato_da_ruolo,
        "data_conferma": batch.data_conferma.isoformat() if batch.data_conferma else None,
        "data_completamento": batch.data_completamento.isoformat() if batch.data_completamento else None,
        "durata_ciclo_minuti": batch.durata_ciclo_minuti,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None
    }
    
    # Includi relazioni se richiesto
    if include_relations and batch.autoclave:
        result['autoclave'] = {
            "id": batch.autoclave.id,
            "nome": batch.autoclave.nome,
            "codice": batch.autoclave.codice,
            "lunghezza": batch.autoclave.lunghezza,
            "larghezza_piano": batch.autoclave.larghezza_piano,
            "stato": batch.autoclave.stato
        }
    
    return result

def format_odl_with_relations(odl: ODL) -> Dict[str, Any]:
    """Formatta un ODL con le sue relazioni (parte, tool, ciclo_cura)"""
    try:
        result = {
            "id": getattr(odl, 'id', None),
            "status": getattr(odl, 'status', 'Unknown'),
            "priorita": getattr(odl, 'priorita', 1),
            "created_at": odl.created_at.isoformat() if hasattr(odl, 'created_at') and odl.created_at else None,
            "note": getattr(odl, 'note', None)
        }
        
        # Parte data
        if hasattr(odl, 'parte') and odl.parte is not None:
            ciclo_cura_data = None
            if hasattr(odl.parte, 'ciclo_cura') and odl.parte.ciclo_cura is not None:
                ciclo_cura_data = {
                    "nome": getattr(odl.parte.ciclo_cura, 'nome', None),
                    "durata_stasi1": getattr(odl.parte.ciclo_cura, 'durata_stasi1', None),
                    "temperatura_stasi1": getattr(odl.parte.ciclo_cura, 'temperatura_stasi1', None),
                    "pressione_stasi1": getattr(odl.parte.ciclo_cura, 'pressione_stasi1', None)
                }
            
            result["parte"] = {
                "id": getattr(odl.parte, 'id', None),
                "part_number": getattr(odl.parte, 'part_number', None),
                "descrizione_breve": getattr(odl.parte, 'descrizione_breve', None),
                "num_valvole_richieste": getattr(odl.parte, 'num_valvole_richieste', 1),
                "ciclo_cura": ciclo_cura_data
            }
        else:
            result["parte"] = None
        
        # Tool data
        if hasattr(odl, 'tool') and odl.tool is not None:
            result["tool"] = {
                "id": getattr(odl.tool, 'id', None),
                "part_number_tool": getattr(odl.tool, 'part_number_tool', None),
                "descrizione": getattr(odl.tool, 'descrizione', None),
                "larghezza_piano": getattr(odl.tool, 'larghezza_piano', 0.0),
                "lunghezza_piano": getattr(odl.tool, 'lunghezza_piano', 0.0),
                "peso": getattr(odl.tool, 'peso', 10.0),
                "disponibile": getattr(odl.tool, 'disponibile', True)
            }
        else:
            result["tool"] = None
        
        return result
        
    except Exception as e:
        logger.warning(f"⚠️ Errore formattando ODL {getattr(odl, 'id', 'unknown')}: {str(e)}")
        return {
            "id": getattr(odl, 'id', None),
            "status": getattr(odl, 'status', 'Unknown'),
            "priorita": getattr(odl, 'priorita', 1),
            "created_at": odl.created_at.isoformat() if hasattr(odl, 'created_at') and odl.created_at else None,
            "note": getattr(odl, 'note', None),
            "parte": None,
            "tool": None
        }

# ========== GESTIONE ERRORI ==========

def handle_database_error(db: Session, error: Exception, operation: str) -> None:
    """Gestisce errori del database con rollback e logging"""
    db.rollback()
    
    if isinstance(error, IntegrityError):
        logger.error(f"❌ Errore integrità durante {operation}: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Errore di integrità dei dati. Verificare che tutti i riferimenti siano validi."
        )
    elif isinstance(error, DatabaseError):
        logger.error(f"❌ Errore database durante {operation}: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore di connessione al database. Riprovare più tardi."
        )
    else:
        logger.error(f"❌ Errore imprevisto durante {operation}: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante {operation}: {str(error)}"
        )

# ========== UTILITIES COMUNI ==========

def generate_batch_name(autoclave_name: str, timestamp: datetime = None) -> str:
    """Genera un nome automatico per il batch"""
    if timestamp is None:
        timestamp = datetime.now()
    
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"Batch_{autoclave_name}_{timestamp_str}"

def find_related_batches(db: Session, main_batch: BatchNesting, time_window_minutes: int = 5, include_failed: bool = False) -> List[BatchNesting]:
    """Trova batch correlati (generati nello stesso periodo)
    
    Args:
        db: Sessione database
        main_batch: Batch principale di riferimento
        time_window_minutes: Finestra temporale in minuti per cercare batch correlati
        include_failed: Se True, include informazioni sui batch falliti (per multi-batch parziali)
    
    Returns:
        Lista di batch correlati trovati nel database
    """
    if not main_batch.created_at:
        return []
    
    time_window = timedelta(minutes=time_window_minutes)
    start_time = main_batch.created_at - time_window
    end_time = main_batch.created_at + time_window
    
    related_batches = db.query(BatchNesting).filter(
        BatchNesting.id != main_batch.id,
        BatchNesting.created_at >= start_time,
        BatchNesting.created_at <= end_time,
        BatchNesting.stato.in_(['sospeso', 'in_cura', 'terminato'])
    ).all()
    
    # Filtra per autoclavi diverse (caratteristica del multi-batch)
    truly_related = []
    for rb in related_batches:
        if rb.autoclave_id != main_batch.autoclave_id:
            truly_related.append(rb)
    
    return truly_related

def convert_string_ids_to_int(string_ids: List[str], field_name: str = "ID") -> List[int]:
    """Converte una lista di ID da string a int con validazione"""
    try:
        return [int(id_str) for id_str in string_ids]
    except (ValueError, TypeError) as e:
        raise ValidationError(f"{field_name} non validi forniti: {str(e)}")

# ========== COSTANTI ==========

# Stati batch che possono essere eliminati senza conferma
DELETABLE_STATES_NO_CONFIRM = [StatoBatchNestingEnum.SOSPESO.value]

# Stati batch che richiedono conferma per eliminazione  
DELETABLE_STATES_WITH_CONFIRM = [
    StatoBatchNestingEnum.IN_CURA.value,
]

# Stati batch non eliminabili (storico)
NON_DELETABLE_STATES = [StatoBatchNestingEnum.TERMINATO.value]

# Transizioni di stato permesse - NUOVO FLUSSO SEMPLIFICATO
STATE_TRANSITIONS = {
    StatoBatchNestingEnum.DRAFT: [StatoBatchNestingEnum.SOSPESO],        # Conferma operatore
    StatoBatchNestingEnum.SOSPESO: [StatoBatchNestingEnum.IN_CURA],      # Caricamento autoclave
    StatoBatchNestingEnum.IN_CURA: [StatoBatchNestingEnum.TERMINATO],    # Fine cura
    StatoBatchNestingEnum.TERMINATO: [],  # Stato finale
}

ROLE_PERMISSIONS = {
    "ADMIN": ["CREATE", "READ", "UPDATE", "DELETE", "CONFIRM", "LOAD_CURE", "TERMINATE"],
    "MANAGER": ["CREATE", "READ", "UPDATE", "CONFIRM", "LOAD_CURE", "TERMINATE"], 
    "OPERATOR": ["READ", "LOAD_CURE", "TERMINATE"],
    "AUTOCLAVISTA": ["READ", "LOAD_CURE", "TERMINATE"],
    "VIEWER": ["READ"]
}

# === STATISTICHE ===
def get_batch_statistics_summary(batches: List[BatchNesting]) -> Dict[str, Any]:
    """Calcola statistiche riassuntive per una lista di batch"""
    if not batches:
        return {
            "total_batches": 0,
            "avg_efficiency": 0.0,
            "total_weight": 0.0,
            "states_distribution": {}
        }
    
    total_efficiency = sum(batch.efficiency or 0.0 for batch in batches)
    total_weight = sum(getattr(batch, 'peso_totale', 0.0) for batch in batches)
    
    # Distribuzione stati
    states_distribution = {}
    for batch in batches:
        state = batch.stato
        states_distribution[state] = states_distribution.get(state, 0) + 1
    
    return {
        "total_batches": len(batches),
        "avg_efficiency": total_efficiency / len(batches),
        "total_weight": total_weight,
        "states_distribution": states_distribution
    } 