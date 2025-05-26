from sqlalchemy import Column, Integer, String, Text, DateTime, func, Enum
from sqlalchemy.orm import relationship
from .base import Base
import enum

class LogLevel(enum.Enum):
    """Livelli di log"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class EventType(enum.Enum):
    """Tipi di eventi tracciabili"""
    ODL_STATE_CHANGE = "odl_state_change"
    NESTING_CONFIRM = "nesting_confirm"
    NESTING_MODIFY = "nesting_modify"
    CURA_START = "cura_start"
    CURA_COMPLETE = "cura_complete"
    TOOL_MODIFY = "tool_modify"
    AUTOCLAVE_MODIFY = "autoclave_modify"
    CICLO_MODIFY = "ciclo_modify"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    SYSTEM_ERROR = "system_error"

class UserRole(enum.Enum):
    """Ruoli utente"""
    ADMIN = "admin"
    RESPONSABILE = "responsabile"
    AUTOCLAVISTA = "autoclavista"
    LAMINATORE = "laminatore"
    SISTEMA = "sistema"

class SystemLog(Base):
    """Modello per tracciare tutti gli eventi del sistema"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Timestamp dell'evento
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True,
                      doc="Timestamp dell'evento")
    
    # Livello del log
    level = Column(Enum(LogLevel), default=LogLevel.INFO, nullable=False,
                  doc="Livello di importanza del log")
    
    # Tipo di evento
    event_type = Column(Enum(EventType), nullable=False, index=True,
                       doc="Tipo di evento")
    
    # Ruolo dell'utente che ha scatenato l'evento
    user_role = Column(Enum(UserRole), nullable=False, index=True,
                      doc="Ruolo dell'utente")
    
    # Identificativo dell'utente (se disponibile)
    user_id = Column(String(100), nullable=True,
                    doc="Identificativo dell'utente")
    
    # Azione specifica
    action = Column(String(200), nullable=False,
                   doc="Descrizione breve dell'azione")
    
    # Entità coinvolta (ID dell'ODL, tool, autoclave, etc.)
    entity_type = Column(String(50), nullable=True,
                        doc="Tipo di entità coinvolta (odl, tool, autoclave, etc.)")
    
    entity_id = Column(Integer, nullable=True, index=True,
                      doc="ID dell'entità coinvolta")
    
    # Dettagli dell'evento
    details = Column(Text, nullable=True,
                    doc="Dettagli completi dell'evento in formato JSON o testo")
    
    # Dati aggiuntivi per il tracciamento
    old_value = Column(Text, nullable=True,
                      doc="Valore precedente (per modifiche)")
    
    new_value = Column(Text, nullable=True,
                      doc="Nuovo valore (per modifiche)")
    
    # IP address per sicurezza (opzionale)
    ip_address = Column(String(45), nullable=True,
                       doc="Indirizzo IP dell'utente")
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, event_type={self.event_type.value}, user_role={self.user_role.value}, timestamp={self.timestamp})>"
    
    def to_dict(self):
        """Converte il log in dizionario per serializzazione"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level.value if self.level else None,
            'event_type': self.event_type.value if self.event_type else None,
            'user_role': self.user_role.value if self.user_role else None,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'ip_address': self.ip_address
        } 