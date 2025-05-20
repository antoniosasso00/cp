from sqlalchemy import Column, Integer, Float, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .ciclo_cura import CicloCura
from .tool import Tool
from .catalogo import Catalogo
from .associations import parte_tool_association

class Parte(Base, TimestampMixin):
    """Modello che rappresenta le parti prodotte associate a un PN del Catalogo"""
    __tablename__ = "parti"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relazione con il catalogo (Part Number)
    part_number = Column(String(50), ForeignKey('cataloghi.part_number'), nullable=False, index=True,
                        doc="Part Number associato dal catalogo")
    
    # Dettagli della parte
    descrizione_breve = Column(String(255), nullable=False,
                              doc="Descrizione breve della parte")
    
    # Requisiti tecnici
    num_valvole_richieste = Column(Integer, nullable=False, default=1,
                                  doc="Numero di valvole richieste per la cura")
    
    # Relazione con il ciclo di cura
    ciclo_cura_id = Column(Integer, ForeignKey('cicli_cura.id'), nullable=True,
                          doc="ID del ciclo di cura associato")
    ciclo_cura = relationship(CicloCura, back_populates="parti")
    
    # Relazione molti-a-molti con i Tools
    tools = relationship(Tool, secondary=parte_tool_association, back_populates="parti")
    
    # Campi aggiuntivi
    note_produzione = Column(Text, nullable=True,
                            doc="Note specifiche per la produzione")
    
    # Relazione con il catalogo
    catalogo = relationship(Catalogo, back_populates="parti")
    
    def __repr__(self):
        return f"<Parte(id={self.id}, part_number='{self.part_number}', desc='{self.descrizione_breve[:20]}')>" 