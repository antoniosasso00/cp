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
    
    # ✅ NUOVO: Proprietà relative ai cavalletti
    usa_cavalletti = Column(Boolean, default=False, nullable=False,
                           doc="Indica se l'autoclave supporta l'utilizzo di cavalletti")
    altezza_cavalletto_standard = Column(Float, nullable=True,
                                       doc="Altezza standard del cavalletto per questa autoclave in cm")
    max_cavalletti = Column(Integer, nullable=True, default=2,
                           doc="Numero massimo di cavalletti supportati dall'autoclave")
    clearance_verticale = Column(Float, nullable=True,
                               doc="Spazio verticale minimo richiesto tra cavalletti in cm")
    
    # 🆕 NUOVO: Peso massimo sopportabile per singolo cavalletto
    peso_max_per_cavalletto_kg = Column(Float, nullable=True, default=300.0,
                                       doc="Peso massimo sopportabile per singolo cavalletto in kg")
    
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
    
    # Relazione con i cavalletti
    cavalletti = relationship("Cavalletto", back_populates="autoclave")
    
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
    
    @property
    def volume_disponibile_con_cavalletti(self) -> float:
        """Calcola il volume disponibile quando si usano cavalletti in cm³"""
        if not self.usa_cavalletti or not self.altezza_cavalletto_standard:
            return 0.0
        
        # Volume base dell'autoclave
        base_area = self.area_piano
        if not base_area:
            return 0.0
            
        # Altezza utilizzabile sopra il cavalletto (assumendo un'altezza interna standard)
        altezza_interna_stimata = 200  # cm, valore stimato
        altezza_utile = altezza_interna_stimata - self.altezza_cavalletto_standard
        
        if self.clearance_verticale:
            altezza_utile -= self.clearance_verticale
            
        return base_area * max(0, altezza_utile)
    
    def __repr__(self):
        return f"<Autoclave(id={self.id}, nome='{self.nome}', max_load={self.max_load_kg}kg, stato={self.stato.value}, usa_cavalletti={self.usa_cavalletti})>" 