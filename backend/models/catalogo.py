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
    
    # Relazione con le parti
    parti = relationship("Parte", back_populates="catalogo")
    
    # Relazione con i tempi standard
    standard_times = relationship("StandardTime", back_populates="catalogo", cascade="all, delete-orphan")
    
    @property
    def area_cm2(self) -> float:
        """
        Calcola l'area occupata dal pezzo in cm² basandosi sui tools associati.
        Le dimensioni vengono prese dal primo tool disponibile associato a questo part_number.
        """
        # Trova il primo tool associato a questo part_number
        for parte in self.parti:
            for tool in parte.tools:
                if tool.lunghezza_piano and tool.larghezza_piano:
                    # Conversione da mm² a cm²
                    return (tool.lunghezza_piano * tool.larghezza_piano) / 100
        
        # Se non ci sono tools associati, cerca direttamente per part_number_tool
        from sqlalchemy.orm import Session
        from .tool import Tool
        from .db import SessionLocal
        
        db = SessionLocal()
        try:
            tool = db.query(Tool).filter(Tool.part_number_tool == self.part_number).first()
            if tool and tool.lunghezza_piano and tool.larghezza_piano:
                return (tool.lunghezza_piano * tool.larghezza_piano) / 100
        finally:
            db.close()
        
        return 0.0
    
    def __repr__(self):
        return f"<Catalogo(part_number='{self.part_number}', categoria='{self.categoria}', sotto_categoria='{self.sotto_categoria}')>" 