from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Catalogo(Base, TimestampMixin):
    """Modello che identifica univocamente i Part Number (PN) prodotti dall'azienda"""
    __tablename__ = "cataloghi"
    
    part_number = Column(String(50), primary_key=True, index=True, 
                         doc="Codice Part Number univoco")
    descrizione = Column(Text, nullable=False, 
                        doc="Descrizione dettagliata del part number")
    categoria = Column(String(100), nullable=True, 
                      doc="Categoria del prodotto")
    attivo = Column(Boolean, default=True, nullable=False,
                   doc="Indica se il part number è ancora attivo nel catalogo")
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sul part number")
    
    # Relazione con le parti
    parti = relationship("Parte", back_populates="catalogo")
    
    def __repr__(self):
        return f"<Catalogo(part_number='{self.part_number}', categoria='{self.categoria}')>" 