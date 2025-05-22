from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, func
from sqlalchemy.orm import relationship
from .base import Base

class NestingResult(Base):
    """
    Modello per salvare i risultati delle operazioni di nesting.
    """
    __tablename__ = "nesting_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relazione con l'autoclave
    autoclave_id = Column(Integer, ForeignKey("autoclavi.id"), index=True)
    autoclave = relationship("Autoclave", back_populates="nesting_results")
    
    # Lista degli ODL inclusi nel nesting (come array di ID)
    odl_ids = Column(JSON, default=list)
    
    # ODL inclusi nel nesting (relazione)
    odl_list = relationship("ODL", secondary="nesting_result_odl")
    
    # Statistiche sul nesting
    area_utilizzata = Column(Float, default=0.0)
    area_totale = Column(Float, default=0.0)
    valvole_utilizzate = Column(Integer, default=0)
    valvole_totali = Column(Integer, default=0)
    
    # Metadati
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<NestingResult id={self.id} autoclave_id={self.autoclave_id} created_at={self.created_at}>" 