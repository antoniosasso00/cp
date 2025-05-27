"""
Router per funzionalità amministrative: backup e ripristino database
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import sqlite3
import json
import os
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any
import logging

from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/backup")
async def export_database(db: Session = Depends(get_db)):
    """
    Esporta il database completo in formato JSON
    
    Returns:
        FileResponse: File JSON con tutti i dati del database
    """
    try:
        # Ottieni tutte le tabelle dal database
        tables_query = text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        tables_result = db.execute(tables_query)
        tables = [row[0] for row in tables_result]
        
        # Esporta i dati di tutte le tabelle
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "database_type": "sqlite",
            "tables": {}
        }
        
        for table in tables:
            try:
                # Ottieni tutti i record della tabella
                select_query = text(f"SELECT * FROM {table}")
                result = db.execute(select_query)
                
                # Ottieni i nomi delle colonne
                columns = result.keys()
                
                # Converti i risultati in lista di dizionari
                rows = []
                for row in result:
                    row_dict = {}
                    for i, column in enumerate(columns):
                        value = row[i]
                        # Converti datetime in stringa se necessario
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        row_dict[column] = value
                    rows.append(row_dict)
                
                export_data["tables"][table] = {
                    "columns": list(columns),
                    "data": rows,
                    "count": len(rows)
                }
                
                logger.info(f"Esportata tabella {table}: {len(rows)} record")
                
            except Exception as e:
                logger.error(f"Errore nell'esportazione della tabella {table}: {str(e)}")
                export_data["tables"][table] = {
                    "error": str(e),
                    "columns": [],
                    "data": [],
                    "count": 0
                }
        
        # Crea un file temporaneo per l'export
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"carbonpilot_backup_{timestamp}.json"
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as temp_file:
                json.dump(export_data, temp_file, indent=2, ensure_ascii=False)
                temp_path = temp_file.name
        except Exception as file_error:
            logger.error(f"Errore nella creazione del file temporaneo: {file_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Errore nella creazione del file di backup: {str(file_error)}"
            )
        
        logger.info(f"Backup creato con successo: {filename}")
        
        # Log dell'evento di backup (opzionale - non blocca l'operazione)
        try:
            from services.system_log_service import SystemLogService
            from models.system_log import UserRole
            
            SystemLogService.log_backup_create(
                db=db,
                backup_filename=filename,
                tables_count=len([t for t in export_data["tables"] if "error" not in export_data["tables"][t]]),
                user_role=UserRole.ADMIN,
                user_id="admin"  # In futuro si potrà passare l'ID utente reale
            )
            logger.info(f"Evento di backup loggato con successo")
        except Exception as log_error:
            logger.warning(f"Errore nel logging del backup (non critico): {log_error}")
            # Non interrompiamo l'operazione per errori di logging
        
        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type='application/json',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Errore durante il backup del database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'esportazione del database: {str(e)}"
        )

@router.post("/restore")
async def restore_database(
    backup_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Ripristina il database da un file di backup JSON
    
    Args:
        backup_file: File JSON di backup
        
    Returns:
        Dict: Risultato dell'operazione di ripristino
    """
    try:
        # Verifica che il file sia JSON
        if not backup_file.filename.endswith('.json'):
            raise HTTPException(
                status_code=400,
                detail="Il file deve essere in formato JSON"
            )
        
        # Leggi il contenuto del file
        content = await backup_file.read()
        
        try:
            backup_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"File JSON non valido: {str(e)}"
            )
        
        # Verifica la struttura del backup
        if "tables" not in backup_data:
            raise HTTPException(
                status_code=400,
                detail="Struttura del backup non valida: manca la sezione 'tables'"
            )
        
        restored_tables = []
        errors = []
        
        # Ripristina ogni tabella
        for table_name, table_data in backup_data["tables"].items():
            try:
                if "error" in table_data:
                    errors.append(f"Tabella {table_name} aveva errori nel backup")
                    continue
                
                # Svuota la tabella esistente
                delete_query = text(f"DELETE FROM {table_name}")
                db.execute(delete_query)
                
                # Inserisci i nuovi dati
                if table_data["data"]:
                    columns = table_data["columns"]
                    placeholders = ", ".join([f":{col}" for col in columns])
                    
                    insert_query = text(f"""
                        INSERT INTO {table_name} ({', '.join(columns)}) 
                        VALUES ({placeholders})
                    """)
                    
                    for row in table_data["data"]:
                        db.execute(insert_query, row)
                
                restored_tables.append({
                    "table": table_name,
                    "records": len(table_data["data"])
                })
                
                logger.info(f"Ripristinata tabella {table_name}: {len(table_data['data'])} record")
                
            except Exception as e:
                error_msg = f"Errore nel ripristino della tabella {table_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Commit delle modifiche
        db.commit()
        
        result = {
            "success": True,
            "message": "Ripristino completato",
            "backup_timestamp": backup_data.get("export_timestamp", "N/A"),
            "restored_tables": restored_tables,
            "errors": errors,
            "total_tables": len(restored_tables),
            "total_errors": len(errors)
        }
        
        logger.info(f"Ripristino completato: {len(restored_tables)} tabelle ripristinate, {len(errors)} errori")
        
        # Log dell'evento di ripristino
        try:
            from services.system_log_service import SystemLogService
            from models.system_log import UserRole
            
            SystemLogService.log_backup_restore(
                db=db,
                backup_filename=backup_file.filename,
                tables_restored=len(restored_tables),
                errors_count=len(errors),
                user_role=UserRole.ADMIN,
                user_id="admin"  # In futuro si potrà passare l'ID utente reale
            )
        except Exception as log_error:
            logger.warning(f"Errore nel logging del ripristino: {log_error}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante il ripristino del database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il ripristino del database: {str(e)}"
        )

@router.post("/database/reset")
async def reset_database(
    reset_confirmation: Dict[str, str],
    db: Session = Depends(get_db)
):
    """
    Svuota completamente il database (richiede conferma con parola chiave "reset")
    
    Args:
        reset_confirmation: Dict con chiave "confirmation" e valore "reset"
        
    Returns:
        Dict: Risultato dell'operazione di reset
    """
    try:
        # Verifica la parola chiave di conferma
        if not reset_confirmation.get("confirmation") == "reset":
            raise HTTPException(
                status_code=400,
                detail="Parola chiave di conferma non valida. Inserire 'reset' per confermare l'operazione."
            )
        
        # Ottieni tutte le tabelle dal database
        tables_query = text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        tables_result = db.execute(tables_query)
        tables = [row[0] for row in tables_result]
        
        deleted_tables = []
        errors = []
        total_deleted_records = 0
        
        # Svuota ogni tabella
        for table in tables:
            try:
                # Conta i record prima della cancellazione
                count_query = text(f"SELECT COUNT(*) FROM {table}")
                count_result = db.execute(count_query)
                record_count = count_result.scalar()
                
                # Svuota la tabella
                delete_query = text(f"DELETE FROM {table}")
                db.execute(delete_query)
                
                # Reset dell'auto-increment per SQLite
                reset_sequence_query = text(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                db.execute(reset_sequence_query)
                
                deleted_tables.append({
                    "table": table,
                    "deleted_records": record_count
                })
                total_deleted_records += record_count
                
                logger.info(f"Svuotata tabella {table}: {record_count} record eliminati")
                
            except Exception as e:
                error_msg = f"Errore nello svuotamento della tabella {table}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Commit delle modifiche
        db.commit()
        
        result = {
            "success": True,
            "message": "Database svuotato completamente",
            "reset_timestamp": datetime.now().isoformat(),
            "deleted_tables": deleted_tables,
            "errors": errors,
            "total_tables_reset": len(deleted_tables),
            "total_deleted_records": total_deleted_records,
            "total_errors": len(errors)
        }
        
        logger.info(f"Reset database completato: {len(deleted_tables)} tabelle svuotate, {total_deleted_records} record eliminati")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante il reset del database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il reset del database: {str(e)}"
        )

@router.get("/database/info")
async def get_database_info(db: Session = Depends(get_db)):
    """
    Ottieni informazioni sul database corrente
    
    Returns:
        Dict: Informazioni sul database
    """
    try:
        # Ottieni informazioni sulle tabelle
        tables_query = text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        tables_result = db.execute(tables_query)
        tables = [row[0] for row in tables_result]
        
        # Conta i record per ogni tabella
        table_info = []
        total_records = 0
        
        for table in tables:
            try:
                count_query = text(f"SELECT COUNT(*) FROM {table}")
                count_result = db.execute(count_query)
                count = count_result.scalar()
                
                table_info.append({
                    "name": table,
                    "records": count
                })
                total_records += count
                
            except Exception as e:
                table_info.append({
                    "name": table,
                    "records": 0,
                    "error": str(e)
                })
        
        return {
            "database_type": "SQLite",
            "total_tables": len(tables),
            "total_records": total_records,
            "tables": table_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Errore nell'ottenere informazioni sul database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore nell'ottenere informazioni sul database: {str(e)}"
        ) 