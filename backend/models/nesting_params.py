from sqlalchemy import Column, Integer, Float, String, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class NestingParams(Base, TimestampMixin):
    """Modello che rappresenta i parametri per l'algoritmo di nesting"""
    __tablename__ = "nesting_params"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Nome della configurazione
    nome = Column(String(100), nullable=False, unique=True,
                 doc="Nome identificativo della configurazione")
    
    # Parametri di ottimizzazione
    peso_valvole = Column(Float, nullable=False, default=1.0,
                        doc="Peso assegnato all'utilizzo delle valvole (0-10)")
    
    peso_area = Column(Float, nullable=False, default=1.0,
                      doc="Peso assegnato all'utilizzo dell'area (0-10)")
    
    peso_priorita = Column(Float, nullable=False, default=1.0,
                         doc="Peso assegnato alla priorità degli ODL (0-10)")
    
    spazio_minimo_mm = Column(Float, nullable=False, default=50.0,
                            doc="Spazio minimo in mm tra gli ODL nell'autoclave")
    
    attivo = Column(Boolean, nullable=False, default=False,
                   doc="Indica se questa è la configurazione attualmente attiva")
    
    descrizione = Column(Text, nullable=True,
                        doc="Descrizione dettagliata della configurazione")
    
    def __repr__(self):
        return f"<NestingParams(id={self.id}, nome='{self.nome}', attivo={self.attivo})>" 