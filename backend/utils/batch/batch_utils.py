"""
Utility helper per batch nesting

Questo modulo contiene funzioni di utilità:
- Formattazione risultati batch
- Validazione dati
- Helper per cicli di cura
- Generazione nomi batch
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.batch_nesting import BatchNesting
from models.odl import ODL
from models.ciclo_cura import CicloCura

logger = logging.getLogger(__name__)

def format_batch_result(batch: BatchNesting) -> Dict[str, Any]:
    """
    Formatta risultato batch per response API
    
    Args:
        batch: Batch nesting da formattare
        
    Returns:
        Dict con dati formattati
    """
    return {
        "id": batch.id,
        "nome": batch.nome,
        "stato": batch.stato,
        "efficienza_area": batch.efficienza_area,
        "peso_totale": batch.peso_totale
    }

def generate_batch_name(autoclave_nome: str, batch_type: str = "Batch") -> str:
    """
    Genera nome batch automatico
    
    Args:
        autoclave_nome: Nome dell'autoclave
        batch_type: Tipo di batch (default: "Batch")
        
    Returns:
        Nome batch generato
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{batch_type}_{autoclave_nome}_{timestamp}"

def find_compatible_cure_cycles(odls: List[ODL]) -> List[Dict[str, Any]]:
    """
    Trova cicli di cura compatibili tra ODL
    
    Args:
        odls: Lista ODL da analizzare
        
    Returns:
        Lista cicli compatibili
    """
    # TODO: Implementare logica cicli compatibili
    # Questa funzione dovrebbe:
    # 1. Raccogliere tutti i cicli di cura degli ODL
    # 2. Trovare parametri compatibili (temperatura ±10°C, tempo ±20%, pressione ±0.1 bar)
    # 3. Raggruppare cicli compatibili
    # 4. Gestire cicli NULL come gruppo separato
    
    logger.info(f"🔍 Analizzando compatibilità cicli per {len(odls)} ODL")
    
    compatible_cycles = []
    
    # Placeholder implementation
    for odl in odls:
        if hasattr(odl, 'ciclo_cura_id') and odl.ciclo_cura_id:
            compatible_cycles.append({
                "odl_id": odl.id,
                "ciclo_id": odl.ciclo_cura_id,
                "compatible": True  # TODO: Implementare logica reale
            })
    
    return compatible_cycles

def are_cycles_compatible(cycle1: CicloCura, cycle2: CicloCura) -> bool:
    """
    Verifica se due cicli di cura sono compatibili
    
    Args:
        cycle1: Primo ciclo di cura
        cycle2: Secondo ciclo di cura
        
    Returns:
        True se compatibili, False altrimenti
    """
    if not cycle1 or not cycle2:
        return False
    
    # Tolleranze per compatibilità
    temp_tolerance = 10  # ±10°C
    time_tolerance = 0.2  # ±20%
    pressure_tolerance = 0.1  # ±0.1 bar
    
    # Verifica temperatura
    if abs(cycle1.temperatura - cycle2.temperatura) > temp_tolerance:
        return False
    
    # Verifica tempo (se disponibile)
    if hasattr(cycle1, 'durata') and hasattr(cycle2, 'durata'):
        if cycle1.durata and cycle2.durata:
            time_diff = abs(cycle1.durata - cycle2.durata) / max(cycle1.durata, cycle2.durata)
            if time_diff > time_tolerance:
                return False
    
    # Verifica pressione (se disponibile)
    if hasattr(cycle1, 'pressione') and hasattr(cycle2, 'pressione'):
        if cycle1.pressione and cycle2.pressione:
            if abs(cycle1.pressione - cycle2.pressione) > pressure_tolerance:
                return False
    
    return True

def validate_odl_for_nesting(odl: ODL) -> Dict[str, Any]:
    """
    Valida un ODL per l'inclusione nel nesting
    
    Args:
        odl: ODL da validare
        
    Returns:
        Dict con risultati validazione
    """
    validation = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "odl_id": odl.id
    }
    
    # Verifica stato
    if odl.status != "Attesa Cura":
        validation["warnings"].append(f"ODL non in 'Attesa Cura' (stato: {odl.status})")
    
    # Verifica peso
    if not odl.peso or odl.peso <= 0:
        validation["warnings"].append("Peso ODL mancante o non valido")
    
    # Verifica parte associata
    if not odl.parte_id:
        validation["errors"].append("Parte non associata all'ODL")
        validation["valid"] = False
    
    # Verifica tool associato
    if hasattr(odl, 'parte') and odl.parte:
        if not hasattr(odl.parte, 'tool') or not odl.parte.tool:
            validation["errors"].append("Tool non associato alla parte")
            validation["valid"] = False
    
    return validation

def calculate_batch_metrics(batch: BatchNesting) -> Dict[str, Any]:
    """
    Calcola metriche dettagliate per un batch
    
    Args:
        batch: Batch da analizzare
        
    Returns:
        Dict con metriche calcolate
    """
    metrics = {
        "batch_id": batch.id,
        "odl_count": len(batch.odl_ids) if batch.odl_ids else 0,
        "efficienza_area": batch.efficienza_area or 0.0,
        "peso_totale": batch.peso_totale or 0.0,
        "algorithm_status": batch.algorithm_status,
        "stato": batch.stato,
        "age_hours": 0,
        "is_old": False
    }
    
    # Calcola età batch
    if batch.created_at:
        age_delta = datetime.now() - batch.created_at
        metrics["age_hours"] = age_delta.total_seconds() / 3600
        metrics["is_old"] = metrics["age_hours"] > 168  # > 7 giorni
    
    # Calcola efficienza relativa
    if metrics["efficienza_area"] > 0:
        if metrics["efficienza_area"] >= 80:
            metrics["efficiency_grade"] = "EXCELLENT"
        elif metrics["efficienza_area"] >= 60:
            metrics["efficiency_grade"] = "GOOD"
        elif metrics["efficienza_area"] >= 40:
            metrics["efficiency_grade"] = "FAIR"
        else:
            metrics["efficiency_grade"] = "POOR"
    else:
        metrics["efficiency_grade"] = "UNKNOWN"
    
    return metrics

def extract_nesting_summary(configurazione_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estrae sommario dal JSON di configurazione nesting
    
    Args:
        configurazione_json: Configurazione nesting
        
    Returns:
        Dict con sommario estratto
    """
    if not configurazione_json:
        return {"error": "Configurazione mancante"}
    
    summary = {
        "positioned_tools": len(configurazione_json.get("positioned_tools", [])),
        "excluded_odls": len(configurazione_json.get("excluded_odls", [])),
        "efficiency": configurazione_json.get("efficiency", 0.0),
        "total_weight": configurazione_json.get("total_weight", 0.0),
        "algorithm_status": configurazione_json.get("algorithm_status", "UNKNOWN"),
        "fixes_applied": configurazione_json.get("fixes_applied", []),
        "validation_report": configurazione_json.get("validation_report", {})
    }
    
    return summary 