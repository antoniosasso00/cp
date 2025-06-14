from sqlalchemy import Column, Integer, Float, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Cavalletto(Base, TimestampMixin):
    """Modello che rappresenta i cavalletti (supporti) utilizzati nelle autoclavi"""
    __tablename__ = "cavalletti"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True,
                 doc="Nome identificativo del cavalletto")
    codice = Column(String(50), unique=True, index=True,
                   doc="Codice univoco del cavalletto")
    
    # Caratteristiche fisiche
    altezza = Column(Float, nullable=False,
                    doc="Altezza del cavalletto in cm")
    larghezza = Column(Float, nullable=True,
                      doc="Larghezza del cavalletto in cm")
    profondita = Column(Float, nullable=True,
                       doc="Profondità del cavalletto in cm")
    peso = Column(Float, nullable=True,
                 doc="Peso del cavalletto in kg")
    
    # Capacità di carico
    portata_max = Column(Float, nullable=True,
                        doc="Portata massima del cavalletto in kg")
    
    # Relazione con autoclave (opzionale - un cavalletto può essere specifico per un'autoclave)
    autoclave_id = Column(Integer, ForeignKey("autoclavi.id"), nullable=True,
                         doc="ID dell'autoclave a cui è associato questo cavalletto (opzionale)")
    
    # Stato e disponibilità
    disponibile = Column(Boolean, default=True, nullable=False,
                        doc="Indica se il cavalletto è disponibile per l'uso")
    in_manutenzione = Column(Boolean, default=False, nullable=False,
                           doc="Indica se il cavalletto è in manutenzione")
    
    # Informazioni aggiuntive
    materiale = Column(String(100), nullable=True,
                      doc="Materiale di costruzione del cavalletto")
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sul cavalletto")
    
    # Relazioni
    autoclave = relationship("Autoclave", back_populates="cavalletti")
    
    @property
    def volume_occupato(self) -> float:
        """Calcola il volume occupato dal cavalletto in cm³"""
        if self.larghezza and self.profondita and self.altezza:
            return self.larghezza * self.profondita * self.altezza
        return 0.0
    
    @property
    def stato_utilizzo(self) -> str:
        """Restituisce lo stato di utilizzo del cavalletto"""
        if self.in_manutenzione:
            return "IN_MANUTENZIONE"
        elif not self.disponibile:
            return "IN_USO"
        else:
            return "DISPONIBILE"
    
    def __repr__(self):
        return f"<Cavalletto(id={self.id}, nome='{self.nome}', altezza={self.altezza}cm, stato={self.stato_utilizzo})>" 