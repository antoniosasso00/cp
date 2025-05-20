from sqlalchemy import Column, Integer, Float, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .associations import parte_tool_association

class Tool(Base, TimestampMixin):
    """Modello che rappresenta gli stampi (tool) utilizzati per la laminazione"""
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(50), nullable=False, unique=True,
                   doc="Codice identificativo univoco dello stampo")
    descrizione = Column(Text, nullable=True,
                        doc="Descrizione dettagliata dello stampo")
    
    # Dimensioni fisiche
    lunghezza_piano = Column(Float, nullable=False, doc="Lunghezza utile del tool")
    larghezza_piano = Column(Float, nullable=False, doc="Larghezza utile del tool")
    
    # Stato e disponibilità
    disponibile = Column(Boolean, default=True, nullable=False,
                        doc="Indica se lo stampo è attualmente disponibile")
    in_manutenzione = Column(Boolean, default=False, nullable=False,
                           doc="Indica se lo stampo è in manutenzione")
    data_ultima_manutenzione = Column(DateTime, nullable=True,
                                    doc="Data dell'ultima manutenzione")
    cicli_completati = Column(Integer, default=0, nullable=False,
                            doc="Numero di cicli di produzione completati")
    
    # Capacità e limitazioni
    max_temperatura = Column(Float, nullable=True,
                           doc="Temperatura massima supportata in gradi Celsius")
    max_pressione = Column(Float, nullable=True,
                         doc="Pressione massima supportata in bar")
    
    note = Column(Text, nullable=True, doc="Note aggiuntive sullo stampo")
    
    # Relazione molti-a-molti con le parti
    parti = relationship("Parte", secondary=parte_tool_association, back_populates="tools")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, codice='{self.codice}', disponibile={self.disponibile})>" 