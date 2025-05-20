from sqlalchemy import Column, Integer, Float, String, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class CicloCura(Base, TimestampMixin):
    """Modello che rappresenta i cicli di cura applicabili in autoclave"""
    __tablename__ = "cicli_cura"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True,
                 doc="Nome identificativo del ciclo di cura")
    temperatura_max = Column(Float, nullable=False,
                           doc="Temperatura massima in gradi Celsius")
    pressione_max = Column(Float, nullable=False,
                         doc="Pressione massima in bar")
    
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
    
    def __repr__(self):
        return f"<CicloCura(id={self.id}, nome='{self.nome}', temp_max={self.temperatura_max}°C)>" 