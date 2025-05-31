from sqlalchemy import Column, Integer, Float, String, Boolean, Text, DateTime, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base, TimestampMixin

class StatoAutoclaveEnum(str, PyEnum):
    """Enum per lo stato operativo dell'autoclave"""
    DISPONIBILE = "DISPONIBILE"
    IN_USO = "IN_USO"
    MANUTENZIONE = "MANUTENZIONE"
    GUASTO = "GUASTO"
    SPENTA = "SPENTA"

class Autoclave(Base, TimestampMixin):
    """Modello che rappresenta le autoclavi utilizzate per la cura delle parti"""
    __tablename__ = "autoclavi"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, index=True,
                 doc="Nome identificativo dell'autoclave")
    codice = Column(String(50), unique=True, index=True,
                   doc="Codice univoco dell'autoclave")
    
    # Dimensioni fisiche
    lunghezza = Column(Float, doc="Lunghezza interna in mm")
    larghezza_piano = Column(Float, doc="Larghezza utile del piano di carico")
    
    # Capacità e specifiche tecniche
    num_linee_vuoto = Column(Integer, doc="Numero di linee vuoto disponibili")
    temperatura_max = Column(Float, doc="Temperatura massima in gradi Celsius")
    pressione_max = Column(Float, doc="Pressione massima in bar")
    
    # ✅ NUOVO: Carico massimo per nesting su due piani
    max_load_kg = Column(Float, nullable=True, default=1000.0, 
                        doc="Carico massimo supportato dall'autoclave in kg")
    
    # ✅ NUOVO: Supporto per piano secondario
    use_secondary_plane = Column(Boolean, nullable=False, default=False,
                               doc="Indica se l'autoclave può utilizzare un piano secondario per aumentare la capacità")
    
    # Stato operativo
    stato = Column(
        PgEnum(StatoAutoclaveEnum, name="statoautoclave", create_type=True, validate_strings=True),
        default=StatoAutoclaveEnum.DISPONIBILE,
        nullable=False,
        doc="Stato attuale dell'autoclave"
    )
    
    # Informazioni aggiuntive
    produttore = Column(String(100), nullable=True, 
                       doc="Nome del produttore dell'autoclave")
    anno_produzione = Column(Integer, nullable=True,
                           doc="Anno di produzione dell'autoclave")
    note = Column(Text, nullable=True, doc="Note aggiuntive sull'autoclave")
    
    # Relazioni
    nesting_results = relationship("NestingResult", back_populates="autoclave")
    
    # ✅ NUOVO: Relazione con i batch nesting
    batch_nesting = relationship("BatchNesting", back_populates="autoclave")
    
    @property
    def disponibile(self) -> bool:
        """Indica se l'autoclave è disponibile per l'uso"""
        return self.stato == StatoAutoclaveEnum.DISPONIBILE
    
    @property
    def area_piano(self) -> float:
        """Calcola l'area del piano dell'autoclave in cm²"""
        if self.lunghezza and self.larghezza_piano:
            return (self.lunghezza * self.larghezza_piano) / 100  # conversione da mm² a cm²
        return 0.0
    
    def __repr__(self):
        return f"<Autoclave(id={self.id}, nome='{self.nome}', max_load={self.max_load_kg}kg, stato={self.stato.value})>" 