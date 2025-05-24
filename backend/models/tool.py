from sqlalchemy import Column, Integer, Float, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .associations import parte_tool_association

class Tool(Base, TimestampMixin):
    """Modello che rappresenta gli stampi (tool) utilizzati per la laminazione"""
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True)
    part_number_tool = Column(String(50), nullable=False, unique=True,
                             doc="Part Number Tool identificativo univoco dello stampo")
    descrizione = Column(Text, nullable=True,
                        doc="Descrizione dettagliata dello stampo")
    
    # Dimensioni fisiche
    lunghezza_piano = Column(Float, nullable=False, doc="Lunghezza utile del tool")
    larghezza_piano = Column(Float, nullable=False, doc="Larghezza utile del tool")
    
    # Stato e disponibilità
    disponibile = Column(Boolean, default=True, nullable=False,
                        doc="Indica se lo stampo è attualmente disponibile")
    
    note = Column(Text, nullable=True, doc="Note aggiuntive sullo stampo")
    
    # Relazione molti-a-molti con le parti
    parti = relationship("Parte", secondary=parte_tool_association, back_populates="tools")
    
    # Relazione con gli ODL
    odl = relationship("ODL", back_populates="tool")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, part_number_tool='{self.part_number_tool}', disponibile={self.disponibile})>" 