# Router risultati e analisi batch

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc
from datetime import datetime, timedelta

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
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

# ✅ FUNZIONE HELPER PER ARRICCHIRE TOOL POSITIONS
def enrich_tool_positions_with_odl_data(tool_positions: List[Dict[str, Any]], db: Session) -> List[Dict[str, Any]]:
    """
    Arricchisce tool_positions con i dati completi ODL (part_number, descrizione_breve, numero_odl, part_number_tool)
    
    Args:
        tool_positions: Lista di tool positions dal batch
        db: Sessione database
        
    Returns:
        Lista tool positions arricchita con dati ODL
    """
    if not tool_positions:
        return tool_positions
    
    # Estrai ODL IDs unici
    odl_ids = list(set(tool.get('odl_id') for tool in tool_positions if tool.get('odl_id')))
    
    if not odl_ids:
        return tool_positions
    
    # Carica ODL con relazioni complete
    odls = db.query(ODL).options(
        joinedload(ODL.parte),
        joinedload(ODL.tool)
    ).filter(ODL.id.in_(odl_ids)).all()
    
    # Crea mappa ODL ID -> dati completi
    odl_data_map = {}
    for odl in odls:
        # Genera numero ODL formattato
        numero_odl = f"ODL{str(odl.id).zfill(3)}"
        
        odl_data_map[odl.id] = {
            'numero_odl': numero_odl,
            'part_number': odl.parte.part_number if odl.parte else None,
            'descrizione_breve': odl.parte.descrizione_breve if odl.parte else None,
            'part_number_tool': odl.tool.part_number_tool if odl.tool else None,
            'tool_nome': odl.tool.descrizione if odl.tool else None
        }
        
        logger.debug(f"📋 ODL {odl.id} -> {numero_odl}: {odl.parte.part_number if odl.parte else 'N/A'}")
    
    # Arricchisci tool_positions
    enriched_positions = []
    for tool in tool_positions:
        tool_copy = tool.copy()
        odl_id = tool.get('odl_id')
        
        if odl_id and odl_id in odl_data_map:
            odl_data = odl_data_map[odl_id]
            tool_copy.update(odl_data)
            logger.debug(f"🔧 Tool ODL {odl_id} arricchito con: {odl_data}")
        else:
            # Fallback per tool senza dati ODL
            tool_copy.update({
                'numero_odl': f"ODL{str(odl_id).zfill(3)}" if odl_id else "ODL000",
                'part_number': None,
                'descrizione_breve': None,
                'part_number_tool': None,
                'tool_nome': None
            })
            
        enriched_positions.append(tool_copy)
    
    logger.info(f"✅ Arricchiti {len(enriched_positions)} tool positions con dati ODL")
    return enriched_positions

def format_batch_result(batch, db: Session) -> Dict[str, Any]:
    """Formatta un batch per la visualizzazione nei risultati"""
    try:
        # Carica autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
        
        # Carica ODL con relazioni
        odls = []
        if batch.odl_ids:
            odls = db.query(ODL).options(
                joinedload(ODL.parte),
                joinedload(ODL.tool)
            ).filter(ODL.id.in_(batch.odl_ids)).all()
        
        # Configurazione con fallback
        configurazione = getattr(batch, 'configurazione_json', {}) or {}
        
        # Tool positions con arricchimento ODL
        tool_positions = configurazione.get('tool_positions', [])
        positioned_tools = configurazione.get('positioned_tools', [])
        
        # Usa positioned_tools se tool_positions è vuoto (nuovo formato)
        if not tool_positions and positioned_tools:
            tool_positions = positioned_tools
        
        # Arricchisci tool positions con dati ODL
        enriched_tools = enrich_tool_positions_with_odl_data(tool_positions, db)
        
        return {
            "id": str(batch.id),
            "nome": batch.nome,
            "stato": batch.stato,
            "autoclave": {
                "id": batch.autoclave_id,
                "nome": autoclave.nome if autoclave else f"Autoclave {batch.autoclave_id}",
                "tipo": getattr(autoclave, 'tipo', 'N/A') if autoclave else 'N/A'
            },
            "metrics": {
                "efficiency_percentage": batch.efficiency or 0.0,
                "positioned_tools_count": len(enriched_tools),
                "total_weight_kg": batch.peso_totale_kg or 0,
                "valvole_utilizzate": batch.valvole_totali_utilizzate or 0,
                "area_utilizzata_cm2": batch.area_totale_utilizzata or 0
            },
            "odl_info": [format_odl_with_relations(odl) for odl in odls],
            "configurazione_json": {
                **configurazione,
                "positioned_tools": enriched_tools  # Tool positions arricchiti
            },
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"❌ Errore in format_batch_result per batch {batch.id}: {str(e)}")
        # Restituisce un risultato minimale invece di fallire completamente
        return {
            "id": str(batch.id),
            "nome": batch.nome or "Batch senza nome",
            "stato": batch.stato or "unknown",
            "autoclave": {"id": batch.autoclave_id, "nome": f"Autoclave {batch.autoclave_id}", "tipo": "N/A"},
            "metrics": {"efficiency_percentage": 0.0, "positioned_tools_count": 0, "total_weight_kg": 0, "valvole_utilizzate": 0, "area_utilizzata_cm2": 0},
            "odl_info": [],
            "configurazione_json": {},
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
            "error": str(e)
        }

@router.get("/result/{batch_id}", summary="🎯 Ottiene risultati di un batch nesting per la visualizzazione")
def get_batch_nesting_result(
    batch_id: str, 
    multi: bool = Query(False, description="Se True, cerca batch correlati nello stesso timeframe"),
    db: Session = Depends(get_db)
):
    """
    Ottiene i risultati di un batch nesting formattati per la visualizzazione frontend.
    
    Questo endpoint è specificamente progettato per la pagina di visualizzazione risultati
    e restituisce un formato diverso dall'endpoint CRUD base.
    """
    try:
        logger.info(f"🎯 GET result per batch_id: {batch_id}, multi: {multi}")
        
        # Carica il batch principale
        main_batch = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(BatchNesting.id == batch_id).first()
        
        if not main_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch con ID {batch_id} non trovato"
            )
        
        logger.info(f"✅ Batch trovato: {main_batch.nome}, stato: {main_batch.stato}")
        
        # Formato risultato principale
        batch_results = []
        try:
            formatted_batch = format_batch_result(main_batch, db)
            batch_results.append(formatted_batch)
            logger.info(f"✅ Batch principale formattato correttamente")
        except Exception as format_error:
            logger.error(f"❌ Errore formattazione batch principale: {str(format_error)}")
            # Continua senza il batch principale piuttosto che fallire completamente
        
        # Cerca batch correlati se richiesto multi-batch
        related_batches = []
        if multi and batch_results:  # Solo se il batch principale è stato formattato
            try:
                related_batches = find_related_batches(main_batch, db, max_results=10)
                logger.info(f"🔍 Trovati {len(related_batches)} batch correlati")
                
                for related_batch in related_batches:
                    try:
                        formatted_related = format_batch_result(related_batch, db)
                        batch_results.append(formatted_related)
                    except Exception as related_error:
                        logger.error(f"❌ Errore formattazione batch correlato {related_batch.id}: {str(related_error)}")
                        # Continua con gli altri batch
                        
            except Exception as related_error:
                logger.error(f"❌ Errore ricerca batch correlati: {str(related_error)}")
                # Continua senza batch correlati
        
        # Ordina per efficienza decrescente
        if len(batch_results) > 1:
            batch_results.sort(key=lambda x: x.get('metrics', {}).get('efficiency_percentage', 0), reverse=True)
        
        # Determina il batch migliore
        best_batch_id = batch_results[0]["id"] if batch_results else batch_id
        
        response = {
            "batch_results": batch_results,
            "total_batches": len(batch_results),
            "is_multi_batch": len(batch_results) > 1,
            "main_batch_id": batch_id,
            "best_batch_id": best_batch_id,
            "execution_timestamp": datetime.now().isoformat(),
            "success": len(batch_results) > 0
        }
        
        logger.info(f"✅ Risposta result preparata: {len(batch_results)} batch, is_multi: {response['is_multi_batch']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore imprevisto in get_batch_nesting_result: {str(e)}")
        return handle_database_error(db, e, f"risultati batch {batch_id}")

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
            "efficiency": batch.efficiency or 0.0,
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
        efficiency = batch.efficiency or 0.0
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
                                "efficiency_percentage": batch.efficiency or 0.0,
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
                "efficiency_percentage": batch.efficiency or 0.0,
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