from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func, Text
from enum import Enum as PyEnum
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class ScheduleEntryStatus(str, PyEnum):
    """Enum per lo stato di una schedulazione"""
    SCHEDULED = "scheduled"      # Schedulato automaticamente
    MANUAL = "manual"           # Schedulato manualmente
    PREVISIONALE = "previsionale"  # Schedulazione previsionale (da frequenza)
    IN_ATTESA = "in_attesa"     # In attesa di avvio
    IN_CORSO = "in_corso"       # In corso di esecuzione
    DONE = "done"               # Completato
    POSTICIPATO = "posticipato" # Posticipato dall'operatore

class ScheduleEntryType(str, PyEnum):
    """Enum per il tipo di schedulazione"""
    ODL_SPECIFICO = "odl_specifico"        # Schedulazione per ODL specifico
    CATEGORIA = "categoria"                # Schedulazione per categoria
    SOTTO_CATEGORIA = "sotto_categoria"    # Schedulazione per sotto-categoria
    RICORRENTE = "ricorrente"             # Schedulazione ricorrente

class ScheduleEntry(Base, TimestampMixin):
    """Modello che rappresenta le schedulazioni degli ODL nelle autoclavi"""
    __tablename__ = "schedule_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Tipo di schedulazione
    schedule_type = Column(
        String(50),
        default=ScheduleEntryType.ODL_SPECIFICO.value,
        nullable=False,
        doc="Tipo di schedulazione"
    )
    
    # Relazione con l'ODL (opzionale per schedulazioni per categoria)
    odl_id = Column(Integer, ForeignKey('odl.id'), nullable=True, index=True,
                  doc="ID dell'ODL schedulato (opzionale per schedulazioni per categoria)")
    odl = relationship("ODL", backref="schedule_entries")
    
    # Relazione con l'autoclave
    autoclave_id = Column(Integer, ForeignKey('autoclavi.id'), nullable=False, index=True,
                        doc="ID dell'autoclave per cui è schedulato l'ODL")
    autoclave = relationship("Autoclave", backref="schedule_entries")
    
    # Campi per schedulazioni per categoria/sotto-categoria
    categoria = Column(String(100), nullable=True, index=True,
                      doc="Categoria per schedulazioni per categoria")
    sotto_categoria = Column(String(100), nullable=True, index=True,
                           doc="Sotto-categoria per schedulazioni per sotto-categoria")
    
    # Dettagli della schedulazione
    start_datetime = Column(DateTime, nullable=False,
                          doc="Data e ora di inizio della schedulazione")
    end_datetime = Column(DateTime, nullable=True,
                        doc="Data e ora di fine della schedulazione (calcolata automaticamente se disponibili dati storici)")
    
    # Stato della schedulazione
    status = Column(
        String(20),
        default=ScheduleEntryStatus.SCHEDULED.value,
        nullable=False,
        doc="Stato corrente della schedulazione"
    )
    
    # Informazioni aggiuntive
    created_by = Column(String(100), nullable=True,
                      doc="Utente che ha creato la schedulazione")
    priority_override = Column(Boolean, default=False, nullable=False,
                             doc="Indica se la priorità è stata sovrascritta manualmente")
    
    # Campi per schedulazioni ricorrenti
    is_recurring = Column(Boolean, default=False, nullable=False,
                         doc="Indica se è una schedulazione ricorrente")
    recurring_frequency = Column(String(50), nullable=True,
                               doc="Frequenza ricorrenza (monthly, weekly, etc.)")
    pieces_per_month = Column(Integer, nullable=True,
                            doc="Numero di pezzi da produrre al mese (per schedulazioni ricorrenti)")
    parent_schedule_id = Column(Integer, ForeignKey('schedule_entries.id'), nullable=True,
                              doc="ID della schedulazione padre (per schedulazioni generate da ricorrenza)")
    
    # Note e informazioni aggiuntive
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sulla schedulazione")
    estimated_duration_minutes = Column(Integer, nullable=True,
                                      doc="Durata stimata in minuti (da dati storici)")
    
    # Metadati
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ScheduleEntry(id={self.id}, type='{self.schedule_type}', odl_id={self.odl_id}, autoclave_id={self.autoclave_id}, status='{self.status}')>" 