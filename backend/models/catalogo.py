from sqlalchemy import Column, String, Boolean, Text, Float
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
    sotto_categoria = Column(String(100), nullable=True,
                            doc="Sotto-categoria del prodotto")
    attivo = Column(Boolean, default=True, nullable=False,
                   doc="Indica se il part number è ancora attivo nel catalogo")
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sul part number")
    
    # Dimensioni fisiche del pezzo (aggiunte per il calcolo dell'area)
    lunghezza = Column(Float, nullable=True, 
                      doc="Lunghezza del pezzo in mm")
    larghezza = Column(Float, nullable=True, 
                      doc="Larghezza del pezzo in mm")
    altezza = Column(Float, nullable=True, 
                    doc="Altezza del pezzo in mm")
    
    # Relazione con le parti
    parti = relationship("Parte", back_populates="catalogo")
    
    @property
    def area_cm2(self) -> float:
        """Calcola l'area occupata dal pezzo in cm²"""
        if self.lunghezza and self.larghezza:
            # Conversione da mm² a cm²
            return (self.lunghezza * self.larghezza) / 100
        return 0.0
    
    def __repr__(self):
        return f"<Catalogo(part_number='{self.part_number}', categoria='{self.categoria}', sotto_categoria='{self.sotto_categoria}')>" 