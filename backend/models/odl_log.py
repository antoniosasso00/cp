from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base

class ODLLog(Base):
    """Modello per tracciare i log di avanzamento degli ODL"""
    __tablename__ = "odl_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relazione con l'ODL
    odl_id = Column(Integer, ForeignKey('odl.id'), nullable=False, index=True,
                   doc="ID dell'ODL associato al log")
    odl = relationship("ODL", back_populates="logs")
    
    # Dettagli dell'evento
    evento = Column(String(100), nullable=False,
                   doc="Tipo di evento (creato, assegnato, caricato, curato, completato, etc.)")
    
    stato_precedente = Column(String(50), nullable=True,
                            doc="Stato precedente dell'ODL")
    
    stato_nuovo = Column(String(50), nullable=False,
                        doc="Nuovo stato dell'ODL")
    
    # Informazioni aggiuntive
    descrizione = Column(Text, nullable=True,
                        doc="Descrizione dettagliata dell'evento")
    
    responsabile = Column(String(100), nullable=True,
                         doc="Utente o sistema responsabile dell'evento")
    
    # Riferimenti a entità correlate
    nesting_id = Column(Integer, ForeignKey('nesting_results.id'), nullable=True, index=True,
                       doc="ID del nesting associato (se applicabile)")
    nesting = relationship("NestingResult")
    
    autoclave_id = Column(Integer, ForeignKey('autoclavi.id'), nullable=True, index=True,
                         doc="ID dell'autoclave utilizzata (se applicabile)")
    autoclave = relationship("Autoclave")
    
    schedule_entry_id = Column(Integer, ForeignKey('schedule_entries.id'), nullable=True, index=True,
                              doc="ID della schedulazione associata (se applicabile)")
    schedule_entry = relationship("ScheduleEntry")
    
    # Metadati
    timestamp = Column(DateTime, default=func.now(), nullable=False,
                      doc="Timestamp dell'evento")
    
    def __repr__(self):
        return f"<ODLLog(id={self.id}, odl_id={self.odl_id}, evento='{self.evento}', timestamp={self.timestamp})>" 