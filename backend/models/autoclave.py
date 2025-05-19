from sqlalchemy import Column, Integer, Float, String, Boolean, Text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from .base import Base, TimestampMixin
from schemas.autoclave import StatoAutoclaveEnum

class Autoclave(Base, TimestampMixin):
    """Modello che rappresenta le autoclavi utilizzate per la cura delle parti"""
    __tablename__ = "autoclavi"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True,
                 doc="Nome identificativo dell'autoclave")
    codice = Column(String(50), nullable=False, unique=True,
                   doc="Codice univoco dell'autoclave")
    
    # Dimensioni fisiche
    lunghezza = Column(Float, nullable=False, doc="Lunghezza interna in mm")
    larghezza_piano = Column(Float, nullable=False, doc="Larghezza utile del piano di carico")
    
    # Capacità e specifiche tecniche
    num_linee_vuoto = Column(Integer, nullable=False, 
                           doc="Numero di linee vuoto disponibili")
    temperatura_max = Column(Float, nullable=False,
                           doc="Temperatura massima in gradi Celsius")
    pressione_max = Column(Float, nullable=False,
                         doc="Pressione massima in bar")
    
    # Stato operativo
    stato = Column(
        PgEnum(StatoAutoclaveEnum, name="statoautoclave", create_type=True, validate_strings=True),
        nullable=False,
        default=StatoAutoclaveEnum.DISPONIBILE,
        doc="Stato attuale dell'autoclave"
    )
    in_manutenzione = Column(Boolean, default=False, nullable=False,
                           doc="Indica se l'autoclave è in manutenzione programmata")
    
    # Informazioni aggiuntive
    produttore = Column(String(100), nullable=True, 
                       doc="Nome del produttore dell'autoclave")
    anno_produzione = Column(Integer, nullable=True,
                           doc="Anno di produzione dell'autoclave")
    note = Column(Text, nullable=True, doc="Note aggiuntive sull'autoclave")
    
    def __repr__(self):
        return f"<Autoclave(id={self.id}, nome='{self.nome}', stato={self.stato.value})>" 