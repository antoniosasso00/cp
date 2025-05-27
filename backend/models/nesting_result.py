from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, func, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from enum import Enum as PyEnum
from .base import Base

class StatoNestingEnum(str, PyEnum):
    """Enum per lo stato del nesting"""
    BOZZA = "bozza"
    IN_SOSPESO = "in_sospeso"
    CONFERMATO = "confermato"
    ANNULLATO = "annullato"
    COMPLETATO = "completato"

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
    
    # Stato del nesting con enum (compatibile SQLite)
    stato = Column(
        Enum(StatoNestingEnum, values_callable=lambda x: [e.value for e in x]),
        default=StatoNestingEnum.BOZZA,
        nullable=False,
        doc="Stato corrente del nesting"
    )
    
    # Ruolo che ha confermato il nesting (per audit)
    confermato_da_ruolo = Column(String(50), nullable=True, doc="Ruolo dell'utente che ha confermato il nesting")
    
    # Statistiche sul nesting
    area_utilizzata = Column(Float, default=0.0)
    area_totale = Column(Float, default=0.0)
    valvole_utilizzate = Column(Integer, default=0)
    valvole_totali = Column(Integer, default=0)
    
    # Note aggiuntive
    note = Column(Text, nullable=True, doc="Note aggiuntive sul nesting")
    
    # Relazione con report PDF (semplice, senza back_populates)
    report_id = Column(Integer, ForeignKey("reports.id"), index=True, nullable=True, doc="ID del report PDF generato per questo nesting")
    report = relationship("Report")
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @property
    def is_editable(self) -> bool:
        """Indica se il nesting può essere modificato"""
        return self.stato in [StatoNestingEnum.BOZZA, StatoNestingEnum.IN_SOSPESO]
    
    @property
    def is_confirmed(self) -> bool:
        """Indica se il nesting è stato confermato"""
        return self.stato == StatoNestingEnum.CONFERMATO
    
    def __repr__(self):
        return f"<NestingResult(id={self.id}, stato={self.stato.value}, autoclave_id={self.autoclave_id}, odl_count={len(self.odl_ids)})>" 