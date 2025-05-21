from sqlalchemy import Column, Integer, Float, String, Boolean, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base, TimestampMixin
from .autoclave import Autoclave

class NestingResult(Base, TimestampMixin):
    """Modello che rappresenta i risultati dell'algoritmo di nesting"""
    __tablename__ = "nesting_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificazione
    codice = Column(String(50), nullable=False, unique=True,
                   doc="Codice identificativo univoco del risultato di nesting")
    
    # Dati di nesting
    autoclave_id = Column(Integer, ForeignKey('autoclavi.id'), nullable=False,
                        doc="ID dell'autoclave utilizzata")
    autoclave = relationship(Autoclave)
    
    # Stato e informazioni
    confermato = Column(Boolean, nullable=False, default=False,
                      doc="Indica se il nesting è stato confermato e gli ODL sono stati aggiornati")
    
    data_conferma = Column(DateTime, nullable=True,
                         doc="Data e ora della conferma del nesting")
    
    # Metriche
    area_totale_mm2 = Column(Float, nullable=False,
                           doc="Area totale dell'autoclave in mm²")
    
    area_utilizzata_mm2 = Column(Float, nullable=False,
                              doc="Area utilizzata dagli ODL in mm²")
    
    efficienza_area = Column(Float, nullable=False,
                           doc="Percentuale di area utilizzata rispetto al totale")
    
    valvole_totali = Column(Integer, nullable=False,
                          doc="Numero totale di valvole disponibili")
    
    valvole_utilizzate = Column(Integer, nullable=False,
                              doc="Numero di valvole utilizzate")
    
    # Layout e ODL
    layout = Column(JSON, nullable=False,
                  doc="Layout completo con posizionamento degli ODL, in formato JSON")
    
    odl_ids = Column(JSON, nullable=False,
                   doc="Lista degli ID degli ODL inclusi nel nesting, in formato JSON")
    
    generato_manualmente = Column(Boolean, nullable=False, default=False,
                                doc="Indica se il nesting è stato generato manualmente o automaticamente")
    
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sul risultato di nesting")
    
    def __repr__(self):
        return f"<NestingResult(id={self.id}, codice='{self.codice}', confermato={self.confermato})>" 