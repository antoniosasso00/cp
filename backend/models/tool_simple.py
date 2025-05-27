from sqlalchemy import Column, Integer, Float, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class ToolSimple(Base, TimestampMixin):
    """Modello Tool semplificato che corrisponde alla struttura del database attuale"""
    __tablename__ = "tools"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    part_number_tool = Column(String(50), nullable=False, unique=True,
                             doc="Part Number Tool identificativo univoco dello stampo")
    descrizione = Column(Text, nullable=True,
                        doc="Descrizione dettagliata dello stampo")
    
    # Dimensioni fisiche (solo quelle che esistono nel DB)
    lunghezza_piano = Column(Float, nullable=False, doc="Lunghezza utile del tool")
    larghezza_piano = Column(Float, nullable=False, doc="Larghezza utile del tool")
    
    # Stato e disponibilità
    disponibile = Column(Boolean, default=True, nullable=False,
                        doc="Indica se lo stampo è attualmente disponibile")
    
    note = Column(Text, nullable=True, doc="Note aggiuntive sullo stampo")
    
    # Relazione con gli ODL
    odl = relationship("ODL", back_populates="tool")
    
    @property
    def area(self) -> float:
        """Calcola l'area del tool in cm²"""
        return (self.lunghezza_piano * self.larghezza_piano) / 100  # conversione da mm² a cm²
    
    @property
    def peso(self) -> float:
        """Peso stimato del tool (per compatibilità)"""
        return 10.0  # Peso di default
    
    @property
    def stato(self) -> str:
        """Stato del tool (per compatibilità)"""
        return "Disponibile" if self.disponibile else "Non Disponibile"
    
    @property
    def codice(self) -> str:
        """Codice del tool (alias per part_number_tool)"""
        return self.part_number_tool
    
    def __repr__(self):
        return f"<ToolSimple(id={self.id}, part_number_tool='{self.part_number_tool}', disponibile={self.disponibile})>" 