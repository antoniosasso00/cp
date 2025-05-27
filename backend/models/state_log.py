from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base

class StateLog(Base):
    """Modello per tracciare specificamente i cambi di stato degli ODL con timestamp precisi"""
    __tablename__ = "state_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relazione con l'ODL
    odl_id = Column(Integer, ForeignKey('odl.id'), nullable=False, index=True,
                   doc="ID dell'ODL associato al cambio di stato")
    odl = relationship("ODL", back_populates="state_logs")
    
    # Dettagli del cambio di stato
    stato_precedente = Column(String(50), nullable=True,
                            doc="Stato precedente dell'ODL")
    
    stato_nuovo = Column(String(50), nullable=False,
                        doc="Nuovo stato dell'ODL")
    
    # Timestamp preciso del cambio
    timestamp = Column(DateTime, default=func.now(), nullable=False,
                      doc="Timestamp preciso del cambio di stato")
    
    # Informazioni aggiuntive
    responsabile = Column(String(100), nullable=True,
                         doc="Utente o sistema responsabile del cambio")
    
    ruolo_responsabile = Column(String(50), nullable=True,
                               doc="Ruolo dell'utente responsabile (Clean Room, Curing, Management, ADMIN)")
    
    note = Column(String(500), nullable=True,
                 doc="Note aggiuntive sul cambio di stato")
    
    def __repr__(self):
        return f"<StateLog(id={self.id}, odl_id={self.odl_id}, '{self.stato_precedente}' → '{self.stato_nuovo}', timestamp={self.timestamp})>" 