from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class ODL(Base, TimestampMixin):
    """Modello che rappresenta gli Ordini di Lavoro (ODL)"""
    __tablename__ = "odl"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relazione con la parte (obbligatoria)
    parte_id = Column(Integer, ForeignKey('parti.id'), nullable=False, index=True,
                    doc="ID della parte associata all'ordine di lavoro")
    parte = relationship("Parte", back_populates="odl")
    
    # Relazione con il tool (obbligatoria)
    tool_id = Column(Integer, ForeignKey('tools.id'), nullable=False, index=True,
                   doc="ID del tool utilizzato per l'ordine di lavoro")
    tool = relationship("Tool", back_populates="odl")
    
    # Attributi dell'ordine di lavoro
    priorita = Column(Integer, default=1, nullable=False,
                     doc="Priorità dell'ordine di lavoro (numero più alto = priorità maggiore)")
    
    status = Column(
        Enum("Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito", name="odl_status"),
        default="Preparazione",
        nullable=False,
        doc="Stato corrente dell'ordine di lavoro"
    )
    
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sull'ordine di lavoro")
    
    motivo_blocco = Column(Text, nullable=True,
                          doc="Motivo per cui l'ODL è bloccato (es. tool occupati)")
    
    # Relazione con i tempi delle fasi
    tempo_fasi = relationship("TempoFase", back_populates="odl", cascade="all, delete-orphan")
    
    # Relazioni inverse
    nesting_results = relationship("NestingResult", secondary="nesting_result_odl", back_populates="odl_list")
    logs = relationship("ODLLog", back_populates="odl", cascade="all, delete-orphan")
    
    # Metadati
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ODL(id={self.id}, parte_id={self.parte_id}, tool_id={self.tool_id}, status='{self.status}')>" 