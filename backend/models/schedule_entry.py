from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from enum import Enum as PyEnum
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class ScheduleEntryStatus(str, PyEnum):
    """Enum per lo stato di una schedulazione"""
    SCHEDULED = "scheduled"  # Schedulato automaticamente
    MANUAL = "manual"        # Schedulato manualmente
    DONE = "done"            # Completato

class ScheduleEntry(Base, TimestampMixin):
    """Modello che rappresenta le schedulazioni degli ODL nelle autoclavi"""
    __tablename__ = "schedule_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relazione con l'ODL
    odl_id = Column(Integer, ForeignKey('odl.id'), nullable=False, index=True,
                  doc="ID dell'ODL schedulato")
    odl = relationship("ODL", backref="schedule_entries")
    
    # Relazione con l'autoclave
    autoclave_id = Column(Integer, ForeignKey('autoclavi.id'), nullable=False, index=True,
                        doc="ID dell'autoclave per cui è schedulato l'ODL")
    autoclave = relationship("Autoclave", backref="schedule_entries")
    
    # Dettagli della schedulazione
    start_datetime = Column(DateTime, nullable=False,
                          doc="Data e ora di inizio della schedulazione")
    end_datetime = Column(DateTime, nullable=False,
                        doc="Data e ora di fine della schedulazione")
    
    # Stato della schedulazione
    status = Column(
        PgEnum(ScheduleEntryStatus, name="schedule_entry_status", create_type=True, validate_strings=True),
        default=ScheduleEntryStatus.SCHEDULED,
        nullable=False,
        doc="Stato corrente della schedulazione"
    )
    
    # Informazioni aggiuntive
    created_by = Column(String(100), nullable=True,
                      doc="Utente che ha creato la schedulazione")
    priority_override = Column(Boolean, default=False, nullable=False,
                             doc="Indica se la priorità è stata sovrascritta manualmente")
    
    # Metadati
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ScheduleEntry(id={self.id}, odl_id={self.odl_id}, autoclave_id={self.autoclave_id}, status='{self.status}')>" 