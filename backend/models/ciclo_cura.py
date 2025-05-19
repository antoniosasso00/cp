from sqlalchemy import Column, Integer, Float, String, Boolean, Text
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
    tempo_totale = Column(Integer, nullable=False,
                         doc="Tempo totale del ciclo in minuti")
    
    # Parametri per la prima stasi
    stasi1_attiva = Column(Boolean, default=True, nullable=False,
                         doc="Indica se è presente la prima stasi")
    stasi1_temperatura = Column(Float, nullable=True,
                              doc="Temperatura della prima stasi in gradi Celsius")
    stasi1_pressione = Column(Float, nullable=True,
                            doc="Pressione della prima stasi in bar")
    stasi1_durata = Column(Integer, nullable=True,
                          doc="Durata della prima stasi in minuti")
    
    # Parametri per la seconda stasi (opzionale)
    stasi2_attiva = Column(Boolean, default=False, nullable=False,
                         doc="Indica se è presente la seconda stasi")
    stasi2_temperatura = Column(Float, nullable=True,
                              doc="Temperatura della seconda stasi in gradi Celsius")
    stasi2_pressione = Column(Float, nullable=True,
                            doc="Pressione della seconda stasi in bar")
    stasi2_durata = Column(Integer, nullable=True,
                          doc="Durata della seconda stasi in minuti")
    
    descrizione = Column(Text, nullable=True,
                        doc="Descrizione dettagliata del ciclo di cura")
    
    def __repr__(self):
        return f"<CicloCura(id={self.id}, nome='{self.nome}', temp_max={self.temperatura_max}°C)>" 