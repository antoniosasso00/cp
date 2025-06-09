# Router risultati e analisi batch

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave
from models.odl import ODL
from schemas.batch_nesting import BatchNestingResponse
from .utils import (
    handle_database_error,
    format_batch_for_response,
    format_odl_with_relations,
    find_related_batches
)

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Batch Nesting - Results"]
)

@router.get("/result/{batch_id}", summary="Ottiene risultati batch nesting, supporta multi-batch")
def get_batch_result(
    batch_id: str, 
    multi: bool = False,
    db: Session = Depends(get_db)
):
    """Ottiene risultati del batch con supporto multi-batch"""
    try:
        # Trova il batch principale
        main_batch = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(BatchNesting.id == batch_id).first()
        
        if not main_batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        logger.info(f"📊 Recupero risultati batch {batch_id}")
        
        # Recupera batch correlati se multi=True
        related_batches = []
        is_partial_multi_batch = False
        total_attempted_autoclavi = 1  # Almeno il batch principale
        
        if multi:
            related_batches = find_related_batches(db, main_batch)
            
            # 🔧 FIX MULTI-BATCH PARZIALE: Controlla se questo batch fa parte di un tentativo multi-batch
            # Cerca nelle note o metadati se era parte di una generazione multi-autoclave
            if hasattr(main_batch, 'batch_result') and main_batch.batch_result:
                batch_metadata = main_batch.batch_result
                if isinstance(batch_metadata, dict):
                    # Cerca indicatori di tentativo multi-batch nei metadati
                    is_partial_multi_batch = (
                        batch_metadata.get('was_multi_batch_attempt') or
                        batch_metadata.get('total_autoclavi_attempted', 0) > 1 or
                        'multi' in str(batch_metadata.get('generation_context', '')).lower()
                    )
                    total_attempted_autoclavi = batch_metadata.get('total_autoclavi_attempted', 1)
            
            # 🔧 SECOND CHECK: Controlla nelle note del batch per indicatori multi-batch
            if not is_partial_multi_batch and hasattr(main_batch, 'note') and main_batch.note:
                note_lower = str(main_batch.note).lower()
                if any(keyword in note_lower for keyword in ['multi', 'autoclavi', 'parziale', 'tentativo']):
                    logger.info(f"🔍 Indicatori multi-batch trovati nelle note: {main_batch.note}")
                    is_partial_multi_batch = True
            
            # 🔧 THIRD CHECK: Controlla nei parametri o configurazione_json
            if not is_partial_multi_batch and hasattr(main_batch, 'configurazione_json') and main_batch.configurazione_json:
                config = main_batch.configurazione_json
                if isinstance(config, dict):
                    context = config.get('generation_context', {})
                    if isinstance(context, dict):
                        is_partial_multi_batch = (
                            context.get('multi_batch_attempt') or
                            len(context.get('selected_autoclavi', [])) > 1
                        )
                        if context.get('selected_autoclavi'):
                            total_attempted_autoclavi = len(context['selected_autoclavi'])
                            logger.info(f"🔍 Multi-batch context trovato: {total_attempted_autoclavi} autoclavi tentate")
            
            # Se non abbiamo trovato batch correlati ma potrebbero essere falliti,
            # aggiungi un placeholder per indicare il tentativo multi-batch parziale
            if not related_batches and is_partial_multi_batch:
                logger.info(f"🚨 MULTI-BATCH PARZIALE RILEVATO: {batch_id} era parte di tentativo multi-autoclave")
            elif related_batches:
                logger.info(f"🔗 Trovati {len(related_batches)} batch correlati per multi-batch")
        
        # Calcola statistiche complete
        odls = []
        total_weight = 0.0
        total_volume = 0.0
        
        if main_batch.odl_ids:
            odls = db.query(ODL).options(joinedload(ODL.tool)).filter(ODL.id.in_(main_batch.odl_ids)).all()
            total_weight = sum(odl.tool.peso or 0 if odl.tool else 0 for odl in odls)
            total_volume = sum((odl.tool.lunghezza_piano * odl.tool.larghezza_piano * 0.1) if odl.tool else 0 for odl in odls)  # Stima volume in cm³
        
        # 🔧 FIX EFFICIENZA: Leggi efficienza dai metadati batch reali
        efficiency_percentage = 0.0
        
        # Prima prova: batch_result con dati del solver
        if hasattr(main_batch, 'batch_result') and main_batch.batch_result:
            efficiency_percentage = main_batch.batch_result.get('efficiency', 0.0)
        
        # Seconda prova: configurazione_json con metrics
        if not efficiency_percentage and hasattr(main_batch, 'configurazione_json') and main_batch.configurazione_json:
            config = main_batch.configurazione_json
            if isinstance(config, dict):
                efficiency_percentage = config.get('efficiency', 0.0)
                # Prova anche metrics se presente
                if not efficiency_percentage and 'metrics' in config:
                    metrics = config['metrics']
                    efficiency_percentage = metrics.get('efficiency_score', 0.0) or metrics.get('area_pct', 0.0)
        
        # Terza prova: campo diretto efficiency (non efficiency_percentage) dal modello
        if not efficiency_percentage:
            efficiency_percentage = getattr(main_batch, 'efficiency', 0.0)
        
        # Quarta prova: campo diretto efficiency_percentage (se presente nel modello)
        if not efficiency_percentage:
            efficiency_percentage = getattr(main_batch, 'efficiency_percentage', 0.0)
        
        logger.info(f"🔧 Efficienza recuperata: {efficiency_percentage:.1f}% per batch {batch_id}")
        
        # 🔧 FIX TOOL POSITIONS: Estrai tool_positions dalla configurazione_json
        tool_positions = []
        if hasattr(main_batch, 'configurazione_json') and main_batch.configurazione_json:
            config = main_batch.configurazione_json
            if isinstance(config, dict) and 'tool_positions' in config:
                tool_positions = config.get('tool_positions', [])
                if tool_positions:
                    logger.info(f"✅ Tool positions trovate: {len(tool_positions)} tool")
                else:
                    logger.warning(f"⚠️ Tool positions vuote nella configurazione")
            else:
                logger.warning(f"⚠️ Configurazione non contiene tool_positions")
        else:
            logger.warning(f"⚠️ Nessuna configurazione JSON trovata")
        
        # 🎯 DETERMINA TIPO BATCH: Multi-batch vs Single-batch vs Multi-batch parziale
        batch_type = "single"
        unique_autoclavi_count = 1
        
        if multi:
            if related_batches:
                batch_type = "multi_complete"
                unique_autoclavi_count = len(set([main_batch.autoclave_id] + [rb.autoclave_id for rb in related_batches]))
            elif is_partial_multi_batch:
                batch_type = "multi_partial"
                unique_autoclavi_count = total_attempted_autoclavi
        
        # 🔧 FIX FRONTEND COMPATIBILITY: Formare la struttura corretta per il frontend
        # Il frontend si aspetta una MultiBatchResponse con batch_results array
        
        # Costruisce il batch principale nel formato corretto
        main_batch_formatted = {
            "id": main_batch.id,
            "nome": main_batch.nome,
            "stato": main_batch.stato,
            "autoclave_id": main_batch.autoclave_id,
            "autoclave": {
                "id": main_batch.autoclave.id,
                "nome": main_batch.autoclave.nome,
                "lunghezza": main_batch.autoclave.lunghezza,
                "larghezza_piano": main_batch.autoclave.larghezza_piano,
                "codice": main_batch.autoclave.codice,
                "produttore": getattr(main_batch.autoclave, 'produttore', None)
            } if main_batch.autoclave else None,
            "odl_ids": main_batch.odl_ids or [],
            "configurazione_json": {
                "canvas_width": main_batch.configurazione_json.get('canvas_width', 0) if main_batch.configurazione_json else 0,
                "canvas_height": main_batch.configurazione_json.get('canvas_height', 0) if main_batch.configurazione_json else 0,
                "tool_positions": tool_positions,
                "plane_assignments": main_batch.configurazione_json.get('plane_assignments', {}) if main_batch.configurazione_json else {}
            },
            "parametri": getattr(main_batch, 'parametri', {}),
            "created_at": main_batch.created_at.isoformat() if main_batch.created_at else None,
            "updated_at": main_batch.updated_at.isoformat() if main_batch.updated_at else None,
            "numero_nesting": getattr(main_batch, 'numero_nesting', 1),
            "peso_totale_kg": total_weight,
            "area_totale_utilizzata": 0,  # Da calcolare se necessario
            "valvole_totali_utilizzate": 0,  # Da calcolare se necessario
            "note": getattr(main_batch, 'note', None),
            "metrics": {
                "efficiency_percentage": efficiency_percentage,
                "total_area_used_mm2": 0,  # Da calcolare se necessario
                "total_weight_kg": total_weight
            },
            "efficiency": efficiency_percentage,  # Campo legacy per compatibilità
            "data_conferma": main_batch.data_conferma.isoformat() if main_batch.data_conferma else None
        }
        
        # Costruisce batch correlati nel formato corretto
        related_batches_formatted = []
        for batch in related_batches:
            batch_odls = []
            batch_weight = 0.0
            batch_efficiency = getattr(batch, 'efficiency_percentage', 0.0) or getattr(batch, 'efficiency', 0.0)
            
            if hasattr(batch, 'batch_result') and batch.batch_result:
                batch_efficiency = batch.batch_result.get('efficiency', batch_efficiency)
            
            if batch.odl_ids:
                batch_odls = db.query(ODL).options(joinedload(ODL.tool)).filter(ODL.id.in_(batch.odl_ids)).all()
                batch_weight = sum(odl.tool.peso or 0 if odl.tool else 0 for odl in batch_odls)
            
            # Estrae tool_positions per batch correlato
            batch_tool_positions = []
            if hasattr(batch, 'configurazione_json') and batch.configurazione_json:
                if isinstance(batch.configurazione_json, dict):
                    batch_tool_positions = batch.configurazione_json.get('tool_positions', [])
            
            related_batches_formatted.append({
                "id": batch.id,
                "nome": batch.nome,
                "stato": batch.stato,
                "autoclave_id": batch.autoclave_id,
                "autoclave": {
                    "id": batch.autoclave.id,
                    "nome": batch.autoclave.nome,
                    "lunghezza": batch.autoclave.lunghezza,
                    "larghezza_piano": batch.autoclave.larghezza_piano,
                    "codice": batch.autoclave.codice,
                    "produttore": getattr(batch.autoclave, 'produttore', None)
                } if batch.autoclave else None,
                "odl_ids": batch.odl_ids or [],
                "configurazione_json": {
                    "canvas_width": batch.configurazione_json.get('canvas_width', 0) if batch.configurazione_json else 0,
                    "canvas_height": batch.configurazione_json.get('canvas_height', 0) if batch.configurazione_json else 0,
                    "tool_positions": batch_tool_positions,
                    "plane_assignments": batch.configurazione_json.get('plane_assignments', {}) if batch.configurazione_json else {}
                },
                "parametri": getattr(batch, 'parametri', {}),
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
                "numero_nesting": getattr(batch, 'numero_nesting', 1),
                "peso_totale_kg": batch_weight,
                "metrics": {
                    "efficiency_percentage": batch_efficiency,
                    "total_area_used_mm2": 0,
                    "total_weight_kg": batch_weight
                },
                "efficiency": batch_efficiency,
                "data_conferma": batch.data_conferma.isoformat() if batch.data_conferma else None
            })
        
        # Costruisce tutti i batch (principale + correlati)
        all_batches = [main_batch_formatted] + related_batches_formatted
        
        # 🎯 STRUTTURA FINALE COMPATIBILE CON FRONTEND
        result = {
            "batch_results": all_batches,
            "execution_id": None,  # Da implementare se necessario
            "total_batches": len(all_batches),
            "is_partial_multi_batch": is_partial_multi_batch,
            "batch_type": batch_type,
            "total_attempted_autoclavi": total_attempted_autoclavi
        }
        
        logger.info(f"🎯 Risposta formattata: {len(all_batches)} batch, tipo={batch_type}, parziale={is_partial_multi_batch}")
        logger.info(f"📊 Autoclavi: tentate={total_attempted_autoclavi}, riuscite={unique_autoclavi_count}")
        
        # Log aggiuntivo per debug multi-batch parziale
        if is_partial_multi_batch:
            logger.info(f"🚨 MULTI-BATCH PARZIALE confermato per batch {batch_id}")
            logger.info(f"   Batch principale: {main_batch.id} su autoclave {main_batch.autoclave.nome if main_batch.autoclave else 'N/A'}")
            logger.info(f"   Efficienza: {efficiency_percentage:.1f}%")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore recupero risultati batch {batch_id}: {e}")
        return handle_database_error(db, e, f"recupero risultati batch {batch_id}")

@router.get("/{batch_id}/statistics", summary="Ottiene statistiche dettagliate del batch")
def get_batch_statistics(batch_id: str, db: Session = Depends(get_db)):
    """Ottiene statistiche dettagliate del batch"""
    try:
        batch = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(BatchNesting.id == batch_id).first()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Calcola ODL associate
        odls = []
        if batch.odl_ids:
            odls = db.query(ODL).options(joinedload(ODL.tool), joinedload(ODL.parte)).filter(ODL.id.in_(batch.odl_ids)).all()
        
        # Calcola statistiche dettagliate
        total_weight = sum(odl.tool.peso or 0 if odl.tool else 0 for odl in odls)
        total_volume = sum((odl.tool.lunghezza_piano * odl.tool.larghezza_piano * 0.1) if odl.tool else 0 for odl in odls)
        
        # Statistiche per materiale
        material_stats = {}
        for odl in odls:
            material = odl.tool.materiale if odl.tool else 'N/A'
            if material not in material_stats:
                material_stats[material] = {"count": 0, "weight": 0.0, "volume": 0.0}
            material_stats[material]["count"] += 1
            material_stats[material]["weight"] += odl.tool.peso or 0 if odl.tool else 0
            material_stats[material]["volume"] += (odl.tool.lunghezza_piano * odl.tool.larghezza_piano * 0.1) if odl.tool else 0
        
        # Calcola tempi
        duration_hours = 0.0
        if batch.data_avvio_cura and batch.data_termine:
            duration = batch.data_termine - batch.data_avvio_cura
            duration_hours = duration.total_seconds() / 3600
        
        stats = {
            "batch_id": batch_id,
            "nome": batch.nome,
            "stato": batch.stato,
            "efficiency": getattr(batch, 'efficiency_percentage', 0.0),
            "total_weight": total_weight,
            "total_volume": total_volume,
            "odl_count": len(odls),
            "material_breakdown": material_stats,
            "autoclave_info": {
                "id": batch.autoclave_id,
                "nome": batch.autoclave.nome if batch.autoclave else None,
                "volume": getattr(batch.autoclave, 'volume', 0) if batch.autoclave else 0
            },
            "timing": {
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "data_conferma": batch.data_conferma.isoformat() if batch.data_conferma else None,
                "data_caricamento": batch.data_caricamento.isoformat() if batch.data_caricamento else None,
                "data_avvio_cura": batch.data_avvio_cura.isoformat() if batch.data_avvio_cura else None,
                "data_termine": batch.data_termine.isoformat() if batch.data_termine else None,
                "duration_hours": duration_hours
            },
            "users": {
                "creato_da": getattr(batch, 'creato_da_utente', None),
                "confermato_da": getattr(batch, 'confermato_da_utente', None),
                "caricato_da": getattr(batch, 'caricato_da_utente', None),
                "avviato_da": getattr(batch, 'avviato_da_utente', None),
                "terminato_da": getattr(batch, 'terminato_da_utente', None)
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore statistiche batch {batch_id}: {e}")
        return handle_database_error(db, e, f"statistiche batch {batch_id}")

@router.get("/{batch_id}/validate", summary="🔍 Valida layout nesting")
def validate_nesting_layout(batch_id: str, db: Session = Depends(get_db)):
    """Valida il layout del nesting"""
    try:
        batch = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(BatchNesting.id == batch_id).first()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        warnings = []
        errors = []
        
        # Validazione configurazione JSON
        configurazione = getattr(batch, 'configurazione_json', {})
        if not configurazione:
            warnings.append("Configurazione layout non presente")
        
        # Validazione ODL
        if batch.odl_ids:
            odls = db.query(ODL).options(joinedload(ODL.tool)).filter(ODL.id.in_(batch.odl_ids)).all()
            if len(odls) != len(batch.odl_ids):
                errors.append("Alcune ODL referenziate non esistono più")
            
            # Controlla stati ODL
            for odl in odls:
                if odl.status not in ['Cura', 'Finito']:
                    warnings.append(f"ODL {odl.id} in stato {odl.status} - dovrebbe essere in Cura o Finito")
        else:
            warnings.append("Nessuna ODL associata al batch")
        
        # Validazione autoclave
        if batch.autoclave:
            if batch.autoclave.stato == 'MANUTENZIONE':
                errors.append(f"Autoclave {batch.autoclave.nome} è in manutenzione")
            elif batch.autoclave.stato == 'FUORI_SERVIZIO':
                errors.append(f"Autoclave {batch.autoclave.nome} è fuori servizio")
        else:
            errors.append("Autoclave non trovata")
        
        # Validazione efficienza
        efficiency = getattr(batch, 'efficiency_percentage', 0.0)
        if efficiency < 60.0:
            warnings.append(f"Efficienza bassa: {efficiency:.1f}% (raccomandato >60%)")
        elif efficiency < 80.0:
            warnings.append(f"Efficienza moderata: {efficiency:.1f}% (ottimale >80%)")
        
        is_valid = len(errors) == 0
        
        validation_result = {
            "batch_id": batch_id,
            "is_valid": is_valid,
            "warnings": warnings,
            "errors": errors,
            "validation_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": 5,
                "warnings_count": len(warnings),
                "errors_count": len(errors),
                "status": "VALID" if is_valid else "INVALID"
            }
        }
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore validazione batch {batch_id}: {e}")
        return handle_database_error(db, e, f"validazione batch {batch_id}")

@router.get("/{batch_id}/full", summary="Ottiene un batch nesting con tutte le informazioni")
def read_batch_nesting_full(batch_id: str, db: Session = Depends(get_db)):
    """Ottiene batch con informazioni complete"""
    try:
        batch = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(BatchNesting.id == batch_id).first()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Recupera ODL associate con relazioni complete
        odls = []
        if batch.odl_ids:
            odls = db.query(ODL).options(joinedload(ODL.tool), joinedload(ODL.parte)).filter(ODL.id.in_(batch.odl_ids)).all()
        
        # Calcola statistiche
        total_weight = sum(odl.tool.peso or 0 if odl.tool else 0 for odl in odls)
        total_volume = sum((odl.tool.lunghezza_piano * odl.tool.larghezza_piano * 0.1) if odl.tool else 0 for odl in odls)
        
        # Informazioni complete del batch
        full_batch = {
            "id": batch.id,
            "nome": batch.nome,
            "stato": batch.stato,
            "autoclave_id": batch.autoclave_id,
            "autoclave": {
                "id": batch.autoclave.id,
                "nome": batch.autoclave.nome,
                "volume": getattr(batch.autoclave, 'volume', 0),
                "stato": batch.autoclave.stato
            } if batch.autoclave else None,
            "efficiency_percentage": getattr(batch, 'efficiency_percentage', 0.0),
            "peso_totale": total_weight,
            "volume_totale": total_volume,
            "numero_nesting": getattr(batch, 'numero_nesting', 1),
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
            
            # Dati workflow
            "data_conferma": batch.data_conferma.isoformat() if batch.data_conferma else None,
            "data_caricamento": batch.data_caricamento.isoformat() if batch.data_caricamento else None,
            "data_avvio_cura": batch.data_avvio_cura.isoformat() if batch.data_avvio_cura else None,
            "data_termine": batch.data_termine.isoformat() if batch.data_termine else None,
            
            # Utenti
            "creato_da_utente": getattr(batch, 'creato_da_utente', None),
            "creato_da_ruolo": getattr(batch, 'creato_da_ruolo', None),
            "confermato_da_utente": getattr(batch, 'confermato_da_utente', None),
            "confermato_da_ruolo": getattr(batch, 'confermato_da_ruolo', None),
            "caricato_da_utente": getattr(batch, 'caricato_da_utente', None),
            "caricato_da_ruolo": getattr(batch, 'caricato_da_ruolo', None),
            "avviato_da_utente": getattr(batch, 'avviato_da_utente', None),
            "avviato_da_ruolo": getattr(batch, 'avviato_da_ruolo', None),
            "terminato_da_utente": getattr(batch, 'terminato_da_utente', None),
            "terminato_da_ruolo": getattr(batch, 'terminato_da_ruolo', None),
            
            # Dati tecnici
            "odl_ids": batch.odl_ids or [],
            "odls": [format_odl_with_relations(odl) for odl in odls],
            "odl_count": len(odls),
            "parametri": getattr(batch, 'parametri', {}),
            "configurazione_json": getattr(batch, 'configurazione_json', {}),
            "batch_result": getattr(batch, 'batch_result', {}),
            "note": getattr(batch, 'note', None)
        }
        
        return full_batch
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore lettura completa batch {batch_id}: {e}")
        return handle_database_error(db, e, f"lettura completa batch {batch_id}")

@router.get("/{batch_id}/export", summary="📄 Esporta batch in formato PDF/Excel")
def export_batch_nesting(
    batch_id: str, 
    format: str = Query("pdf", regex="^(pdf|excel)$", description="Formato esportazione: pdf o excel"),
    db: Session = Depends(get_db)
):
    """Esporta i dati del batch in formato PDF o Excel"""
    try:
        batch = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(BatchNesting.id == batch_id).first()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Recupera ODL associate
        odls = []
        if batch.odl_ids:
            odls = db.query(ODL).options(joinedload(ODL.tool), joinedload(ODL.parte)).filter(ODL.id.in_(batch.odl_ids)).all()
        
        # Prepara dati per esportazione
        export_data = {
            "batch": {
                "id": batch.id,
                "nome": batch.nome,
                "stato": batch.stato,
                "autoclave": batch.autoclave.nome if batch.autoclave else "N/A",
                "efficiency_percentage": getattr(batch, 'efficiency_percentage', 0.0),
                "created_at": batch.created_at.strftime("%d/%m/%Y %H:%M") if batch.created_at else "N/A",
                "data_conferma": batch.data_conferma.strftime("%d/%m/%Y %H:%M") if batch.data_conferma else "N/A",
            },
            "odls": [
                {
                    "numero_odl": getattr(odl, 'numero_odl', 'N/A'),
                    "peso": odl.tool.peso or 0.0 if odl.tool else 0.0,
                    "volume": (odl.tool.lunghezza_piano * odl.tool.larghezza_piano * 0.1) if odl.tool else 0.0,
                    "materiale": odl.tool.materiale if odl.tool else 'N/A',
                    "cliente": getattr(odl.parte, 'cliente', 'N/A') if odl.parte else 'N/A',
                    "status": odl.status
                } for odl in odls
            ],
            "statistics": {
                "total_odls": len(odls),
                "total_weight": sum(odl.tool.peso or 0 if odl.tool else 0 for odl in odls),
                "total_volume": sum((odl.tool.lunghezza_piano * odl.tool.larghezza_piano * 0.1) if odl.tool else 0 for odl in odls)
            },
            "export_timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "format": format
        }
        
        if format == "pdf":
            # TODO: Implementare generazione PDF
            # Per ora restituisce dati per il frontend
            return {
                "success": True,
                "format": "pdf",
                "data": export_data,
                "download_url": f"/api/batch_nesting/{batch_id}/download?format=pdf",
                "message": "Export preparato - utilizzare download_url per scaricare"
            }
        
        elif format == "excel":
            # TODO: Implementare generazione Excel  
            return {
                "success": True,
                "format": "excel",
                "data": export_data,
                "download_url": f"/api/batch_nesting/{batch_id}/download?format=excel",
                "message": "Export preparato - utilizzare download_url per scaricare"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore export batch {batch_id}: {e}")
        return handle_database_error(db, e, f"export batch {batch_id}") 