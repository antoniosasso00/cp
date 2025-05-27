import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from models.system_log import SystemLog, LogLevel, EventType, UserRole
from schemas.system_log import SystemLogCreate, SystemLogFilter, SystemLogStats, SystemLogResponse

logger = logging.getLogger(__name__)

class SystemLogService:
    """Servizio centralizzato per la gestione dei log di sistema"""
    
    @staticmethod
    def log_event(
        db: Session,
        event_type: EventType,
        user_role: UserRole,
        action: str,
        level: LogLevel = LogLevel.INFO,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """
        Registra un evento nel sistema
        
        Args:
            db: Sessione database
            event_type: Tipo di evento
            user_role: Ruolo dell'utente
            action: Descrizione dell'azione
            level: Livello di importanza
            user_id: ID dell'utente (opzionale)
            entity_type: Tipo di entità coinvolta
            entity_id: ID dell'entità
            details: Dettagli aggiuntivi
            old_value: Valore precedente (per modifiche)
            new_value: Nuovo valore (per modifiche)
            ip_address: Indirizzo IP
        
        Returns:
            SystemLog: Il log creato
        """
        try:
            # Crea direttamente l'oggetto SQLAlchemy senza passare attraverso Pydantic
            # per evitare problemi di serializzazione degli enum
            db_log = SystemLog(
                level=level,
                event_type=event_type,
                user_role=user_role,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address
            )
            
            db.add(db_log)
            db.commit()
            db.refresh(db_log)
            
            logger.info(f"Registrato evento {event_type.value} da {user_role.value}: {action}")
            return db_log
            
        except Exception as e:
            db.rollback()
            logger.error(f"Errore durante la registrazione del log: {str(e)}")
            raise
    
    @staticmethod
    def log_odl_state_change(
        db: Session,
        odl_id: int,
        old_state: str,
        new_state: str,
        user_role: UserRole,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra un cambio di stato ODL"""
        action = f"ODL #{odl_id} cambiato da '{old_state}' a '{new_state}'"
        details = json.dumps({
            "odl_id": odl_id,
            "old_state": old_state,
            "new_state": new_state
        })
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.ODL_STATE_CHANGE,
            user_role=user_role,
            action=action,
            user_id=user_id,
            entity_type="odl",
            entity_id=odl_id,
            details=details,
            old_value=old_state,
            new_value=new_state,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_odl_operation(
        db: Session,
        operation_type: str,
        user_role: UserRole,
        details: Optional[dict] = None,
        result: str = "SUCCESS",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra operazioni generiche sugli ODL (creazione, modifica, eliminazione)"""
        action = f"Operazione ODL: {operation_type}"
        
        # Converti i dettagli in JSON se forniti
        details_json = json.dumps(details) if details else None
        
        # Determina il livello di log in base al risultato
        level = LogLevel.INFO if result == "SUCCESS" else LogLevel.ERROR
        
        # Estrai l'ID dell'ODL dai dettagli se disponibile
        entity_id = details.get("odl_id") if details else None
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.ODL_STATE_CHANGE,  # Usiamo ODL_STATE_CHANGE per operazioni generiche ODL
            user_role=user_role,
            action=action,
            level=level,
            user_id=user_id,
            entity_type="odl",
            entity_id=entity_id,
            details=details_json,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_nesting_confirm(
        db: Session,
        nesting_id: int,
        autoclave_id: int,
        user_role: UserRole,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra la conferma di un nesting"""
        action = f"Nesting #{nesting_id} confermato per autoclave #{autoclave_id}"
        details = json.dumps({
            "nesting_id": nesting_id,
            "autoclave_id": autoclave_id
        })
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.NESTING_CONFIRM,
            user_role=user_role,
            action=action,
            user_id=user_id,
            entity_type="nesting",
            entity_id=nesting_id,
            details=details,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_nesting_modify(
        db: Session,
        nesting_id: int,
        modification_type: str,
        user_role: UserRole,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra la modifica di un nesting"""
        action = f"Nesting #{nesting_id} modificato: {modification_type}"
        details = json.dumps({
            "nesting_id": nesting_id,
            "modification_type": modification_type
        })
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.NESTING_MODIFY,
            user_role=user_role,
            action=action,
            user_id=user_id,
            entity_type="nesting",
            entity_id=nesting_id,
            details=details,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_nesting_operation(
        db: Session,
        operation_type: str,
        user_role: UserRole,
        details: Optional[dict] = None,
        result: str = "SUCCESS",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra operazioni generiche sui nesting"""
        action = f"Operazione nesting: {operation_type}"
        
        # Converti i dettagli in JSON se forniti
        details_json = json.dumps(details) if details else None
        
        # Determina il livello di log in base al risultato
        level = LogLevel.INFO if result == "SUCCESS" else LogLevel.ERROR
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.NESTING_MODIFY,  # Usiamo NESTING_MODIFY per operazioni generiche
            user_role=user_role,
            action=action,
            level=level,
            user_id=user_id,
            entity_type="nesting",
            details=details_json,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_cura_start(
        db: Session,
        schedule_entry_id: int,
        autoclave_id: int,
        user_role: UserRole,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra l'avvio di un ciclo di cura"""
        action = f"Avviato ciclo di cura #{schedule_entry_id} su autoclave #{autoclave_id}"
        details = json.dumps({
            "schedule_entry_id": schedule_entry_id,
            "autoclave_id": autoclave_id
        })
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.CURA_START,
            user_role=user_role,
            action=action,
            user_id=user_id,
            entity_type="schedule_entry",
            entity_id=schedule_entry_id,
            details=details,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_cura_complete(
        db: Session,
        schedule_entry_id: int,
        autoclave_id: int,
        user_role: UserRole,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra il completamento di un ciclo di cura"""
        action = f"Completato ciclo di cura #{schedule_entry_id} su autoclave #{autoclave_id}"
        details = json.dumps({
            "schedule_entry_id": schedule_entry_id,
            "autoclave_id": autoclave_id
        })
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.CURA_COMPLETE,
            user_role=user_role,
            action=action,
            user_id=user_id,
            entity_type="schedule_entry",
            entity_id=schedule_entry_id,
            details=details,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_tool_modify(
        db: Session,
        tool_id: int,
        modification_details: str,
        user_role: UserRole,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra la modifica di un tool"""
        action = f"Tool #{tool_id} modificato: {modification_details}"
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.TOOL_MODIFY,
            user_role=user_role,
            action=action,
            user_id=user_id,
            entity_type="tool",
            entity_id=tool_id,
            details=modification_details,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_autoclave_modify(
        db: Session,
        autoclave_id: int,
        modification_details: str,
        user_role: UserRole,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra la modifica di un'autoclave"""
        action = f"Autoclave #{autoclave_id} modificata: {modification_details}"
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.AUTOCLAVE_MODIFY,
            user_role=user_role,
            action=action,
            user_id=user_id,
            entity_type="autoclave",
            entity_id=autoclave_id,
            details=modification_details,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_ciclo_modify(
        db: Session,
        ciclo_id: int,
        modification_details: str,
        user_role: UserRole,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra la modifica di un ciclo di cura"""
        action = f"Ciclo di cura #{ciclo_id} modificato: {modification_details}"
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.CICLO_MODIFY,
            user_role=user_role,
            action=action,
            user_id=user_id,
            entity_type="ciclo_cura",
            entity_id=ciclo_id,
            details=modification_details,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_backup_create(
        db: Session,
        backup_filename: str,
        tables_count: int,
        user_role: UserRole,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra la creazione di un backup"""
        action = f"Backup database creato: {backup_filename}"
        
        details = json.dumps({
            "backup_filename": backup_filename,
            "tables_exported": tables_count,
            "operation": "create"
        })
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.BACKUP_CREATE,
            user_role=user_role,
            action=action,
            user_id=user_id,
            details=details,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_backup_restore(
        db: Session,
        backup_filename: str,
        tables_restored: int,
        errors_count: int,
        user_role: UserRole,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra il ripristino da backup"""
        action = f"Database ripristinato da backup: {backup_filename}"
        level = LogLevel.WARNING if errors_count > 0 else LogLevel.INFO
        
        details = json.dumps({
            "backup_filename": backup_filename,
            "tables_restored": tables_restored,
            "errors_count": errors_count,
            "operation": "restore"
        })
        
        return SystemLogService.log_event(
            db=db,
            event_type=EventType.BACKUP_RESTORE,
            user_role=user_role,
            action=action,
            level=level,
            user_id=user_id,
            details=details,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_backup_operation(
        db: Session,
        operation_type: str,  # "create" o "restore"
        backup_file: str,
        user_role: UserRole,
        success: bool = True,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """Registra operazioni di backup/ripristino (metodo generico)"""
        event_type = EventType.BACKUP_CREATE if operation_type == "create" else EventType.BACKUP_RESTORE
        action = f"Backup {operation_type}: {backup_file}"
        level = LogLevel.INFO if success else LogLevel.ERROR
        
        details = json.dumps({
            "operation_type": operation_type,
            "backup_file": backup_file,
            "success": success
        })
        
        return SystemLogService.log_event(
            db=db,
            event_type=event_type,
            user_role=user_role,
            action=action,
            level=level,
            user_id=user_id,
            details=details,
            ip_address=ip_address
        )
    
    @staticmethod
    def get_logs(
        db: Session,
        filters: SystemLogFilter
    ) -> List[SystemLog]:
        """
        Ottiene i log filtrati
        
        Args:
            db: Sessione database
            filters: Filtri da applicare
        
        Returns:
            List[SystemLog]: Lista dei log
        """
        query = db.query(SystemLog)
        
        # Applica filtri
        if filters.event_type:
            query = query.filter(SystemLog.event_type == filters.event_type)
        
        if filters.user_role:
            query = query.filter(SystemLog.user_role == filters.user_role)
        
        if filters.level:
            query = query.filter(SystemLog.level == filters.level)
        
        if filters.entity_type:
            query = query.filter(SystemLog.entity_type == filters.entity_type)
        
        if filters.entity_id:
            query = query.filter(SystemLog.entity_id == filters.entity_id)
        
        if filters.start_date:
            query = query.filter(SystemLog.timestamp >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(SystemLog.timestamp <= filters.end_date)
        
        # Ordina per timestamp decrescente
        query = query.order_by(desc(SystemLog.timestamp))
        
        # Applica paginazione
        if filters.offset:
            query = query.offset(filters.offset)
        
        if filters.limit:
            query = query.limit(filters.limit)
        
        return query.all()
    
    @staticmethod
    def get_log_stats(
        db: Session,
        days: int = 30
    ) -> SystemLogStats:
        """
        Ottiene statistiche sui log
        
        Args:
            db: Sessione database
            days: Numero di giorni da considerare
        
        Returns:
            SystemLogStats: Statistiche
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # Conta totale log
        total_logs = db.query(SystemLog).filter(
            SystemLog.timestamp >= start_date
        ).count()
        
        # Log per tipo
        logs_by_type = {}
        type_counts = db.query(
            SystemLog.event_type,
            func.count(SystemLog.id)
        ).filter(
            SystemLog.timestamp >= start_date
        ).group_by(SystemLog.event_type).all()
        
        for event_type, count in type_counts:
            logs_by_type[event_type.value] = count
        
        # Log per ruolo
        logs_by_role = {}
        role_counts = db.query(
            SystemLog.user_role,
            func.count(SystemLog.id)
        ).filter(
            SystemLog.timestamp >= start_date
        ).group_by(SystemLog.user_role).all()
        
        for user_role, count in role_counts:
            logs_by_role[user_role.value] = count
        
        # Log per livello
        logs_by_level = {}
        level_counts = db.query(
            SystemLog.level,
            func.count(SystemLog.id)
        ).filter(
            SystemLog.timestamp >= start_date
        ).group_by(SystemLog.level).all()
        
        for level, count in level_counts:
            logs_by_level[level.value] = count
        
        # Errori recenti
        recent_errors = db.query(SystemLog).filter(
            and_(
                SystemLog.timestamp >= start_date,
                or_(
                    SystemLog.level == LogLevel.ERROR,
                    SystemLog.level == LogLevel.CRITICAL
                )
            )
        ).order_by(desc(SystemLog.timestamp)).limit(10).all()
        
        return SystemLogStats(
            total_logs=total_logs,
            logs_by_type=logs_by_type,
            logs_by_role=logs_by_role,
            logs_by_level=logs_by_level,
            recent_errors=[SystemLogResponse.from_orm(log) for log in recent_errors]
        ) 