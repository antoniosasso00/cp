from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, func, Enum, Text
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
    
    # Lista degli ODL esclusi dal nesting (con motivazione)
    odl_esclusi_ids = Column(JSON, default=list, 
                           doc="Lista degli ID degli ODL esclusi dal nesting")
    
    # Motivazioni esclusione (come JSON array di dict)
    motivi_esclusione = Column(JSON, default=list,
                             doc="Lista dei motivi per cui gli ODL sono stati esclusi")
    
    # ODL inclusi nel nesting (relazione)
    odl_list = relationship("ODL", secondary="nesting_result_odl")
    
    # Stato del nesting
    stato = Column(
        Enum("Schedulato", "In attesa schedulazione", "Completato", "Annullato", name="nesting_stato"),
        default="In attesa schedulazione",
        nullable=False,
        doc="Stato corrente del nesting"
    )
    
    # Statistiche sul nesting
    area_utilizzata = Column(Float, default=0.0)
    area_totale = Column(Float, default=0.0)
    valvole_utilizzate = Column(Integer, default=0)
    valvole_totali = Column(Integer, default=0)
    
    # Note aggiuntive
    note = Column(Text, nullable=True, doc="Note aggiuntive sul nesting")
    
    # Metadati
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NestingResult id={self.id} autoclave_id={self.autoclave_id} stato={self.stato} created_at={self.created_at}>" 