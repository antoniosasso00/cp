from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class StandardTime(Base, TimestampMixin):
    """
    Modello per i tempi standard di produzione per fase.
    Utilizzato per benchmarking e controllo delle performance.
    """
    __tablename__ = "standard_times"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relazione con il catalogo (part_number)
    part_number = Column(String(50), ForeignKey('cataloghi.part_number'), nullable=False, index=True,
                        doc="Part Number dal catalogo associato al tempo standard")
    
    # Fase di produzione
    phase = Column(String(50), nullable=False, index=True,
                  doc="Fase di produzione (es. Laminazione, Cura, Preparazione, etc.)")
    
    # Tempo standard in minuti
    minutes = Column(Float, nullable=False,
                    doc="Tempo standard per questa fase in minuti")
    
    # Note aggiuntive
    note = Column(String(500), nullable=True,
                 doc="Note aggiuntive sui tempi standard")
    
    # Relazione verso il catalogo
    catalogo = relationship("Catalogo", back_populates="standard_times")
    
    def __repr__(self):
        return f"<StandardTime(id={self.id}, part_number='{self.part_number}', phase='{self.phase}', minutes={self.minutes})>" 