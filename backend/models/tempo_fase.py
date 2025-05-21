from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Enum, func
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class TempoFase(Base, TimestampMixin):
    """Modello che rappresenta i tempi di lavorazione per le diverse fasi di produzione"""
    __tablename__ = "tempo_fasi"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relazione con l'ODL (obbligatoria)
    odl_id = Column(Integer, ForeignKey('odl.id'), nullable=False, index=True,
                    doc="ID dell'ordine di lavoro associato")
    
    # Tipo di fase
    fase = Column(
        Enum("laminazione", "attesa_cura", "cura", name="tipo_fase"),
        nullable=False,
        doc="Tipo di fase di produzione monitorata"
    )
    
    # Timestamp di inizio e fine
    inizio_fase = Column(DateTime(timezone=True), nullable=False, default=func.now(),
                       doc="Timestamp di inizio della fase")
    
    fine_fase = Column(DateTime(timezone=True), nullable=True,
                     doc="Timestamp di fine della fase (null se ancora in corso)")
    
    # Durata calcolata in minuti (null se fase non completata)
    durata_minuti = Column(Integer, nullable=True,
                          doc="Durata della fase in minuti (calcolata da inizio e fine)")
    
    # Note opzionali
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sulla fase")
    
    # Relazione inversa con ODL
    odl = relationship("ODL", back_populates="tempo_fasi")
    
    def __repr__(self):
        stato = "in corso" if not self.fine_fase else "completata"
        return f"<TempoFase(id={self.id}, odl_id={self.odl_id}, fase='{self.fase}', stato='{stato}')>" 