from sqlalchemy import Column, Integer, Float, String, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class CicloCura(Base, TimestampMixin):
    """Modello che rappresenta i cicli di cura applicabili in autoclave"""
    __tablename__ = "cicli_cura"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True,
                 doc="Nome identificativo del ciclo di cura")
    
    # Stasi 1 (obbligatoria)
    temperatura_stasi1 = Column(Float, nullable=False, 
                              doc="Temperatura della prima stasi in gradi Celsius")
    pressione_stasi1 = Column(Float, nullable=False, 
                            doc="Pressione della prima stasi in bar")
    durata_stasi1 = Column(Integer, nullable=False, 
                          doc="Durata della prima stasi in minuti")
    
    # Stasi 2 (opzionale)
    attiva_stasi2 = Column(Boolean, default=False, nullable=False,
                         doc="Indica se è presente la seconda stasi")
    temperatura_stasi2 = Column(Float, nullable=True, 
                              doc="Temperatura della seconda stasi in gradi Celsius")
    pressione_stasi2 = Column(Float, nullable=True, 
                            doc="Pressione della seconda stasi in bar")
    durata_stasi2 = Column(Integer, nullable=True, 
                          doc="Durata della seconda stasi in minuti")
    
    descrizione = Column(Text, nullable=True,
                        doc="Descrizione dettagliata del ciclo di cura")
    
    # Relazione con le parti
    parti = relationship("Parte", back_populates="ciclo_cura")
    
    @property
    def temperatura_max(self) -> float:
        """Calcola la temperatura massima tra le stasi"""
        if not self.attiva_stasi2 or self.temperatura_stasi2 is None:
            return self.temperatura_stasi1
        return max(self.temperatura_stasi1, self.temperatura_stasi2)
    
    @property
    def pressione_max(self) -> float:
        """Calcola la pressione massima tra le stasi"""
        if not self.attiva_stasi2 or self.pressione_stasi2 is None:
            return self.pressione_stasi1
        return max(self.pressione_stasi1, self.pressione_stasi2)
    
    def __repr__(self):
        return f"<CicloCura(id={self.id}, nome='{self.nome}', temp_max={self.temperatura_max}°C)>" 