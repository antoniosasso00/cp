from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, func, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum as PyEnum
from .base import Base

class StatoBatchNestingEnum(PyEnum):
    """Enum per rappresentare i vari stati di un batch nesting"""
    SOSPESO = "sospeso"
    CONFERMATO = "confermato"
    TERMINATO = "terminato"

class BatchNesting(Base):
    """
    Modello per salvare i batch di nesting con configurazioni e parametri.
    Un batch raggruppa più nesting results e mantiene i parametri di generazione.
    """
    __tablename__ = "batch_nesting"
    
    # Chiave primaria UUID
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True,
                doc="UUID identificativo univoco del batch")
    
    # Informazioni base del batch
    nome = Column(String(255), nullable=True,
                  doc="Nome opzionale del batch assegnabile dall'operatore")
    
    # Stato del batch - uso String per compatibilità SQLite
    stato = Column(String(20), nullable=False, default=StatoBatchNestingEnum.SOSPESO.value,
                   doc="Stato corrente del batch nesting")
    
    # Relazione con autoclave
    autoclave_id = Column(Integer, ForeignKey("autoclavi.id"), nullable=False, index=True,
                         doc="ID dell'autoclave per cui è stato generato il batch")
    autoclave = relationship("Autoclave", back_populates="batch_nesting")
    
    # Dati del nesting
    odl_ids = Column(JSON, default=list, 
                     doc="Lista degli ID degli ODL inclusi nel batch nesting")
    
    configurazione_json = Column(JSON, nullable=True,
                                doc="Configurazione completa del layout nesting generato dal frontend")
    
    parametri = Column(JSON, default=dict,
                      doc="Parametri utilizzati per la generazione del nesting")
    
    # Statistiche aggregate
    numero_nesting = Column(Integer, default=0,
                           doc="Numero totale di nesting results contenuti nel batch")
    
    peso_totale_kg = Column(Integer, default=0,
                           doc="Peso totale aggregato di tutti i nesting del batch in kg")
    
    area_totale_utilizzata = Column(Integer, default=0,
                                   doc="Area totale utilizzata aggregata in cm²")
    
    valvole_totali_utilizzate = Column(Integer, default=0,
                                      doc="Numero totale di valvole utilizzate nel batch")
    
    # Note e metadati
    note = Column(Text, nullable=True,
                  doc="Note aggiuntive sul batch nesting")
    
    # Tracciabilità utenti
    creato_da_utente = Column(String(100), nullable=True,
                             doc="ID dell'utente che ha creato il batch")
    
    creato_da_ruolo = Column(String(50), nullable=True,
                            doc="Ruolo dell'utente che ha creato il batch")
    
    confermato_da_utente = Column(String(100), nullable=True,
                                 doc="ID dell'utente che ha confermato il batch")
    
    confermato_da_ruolo = Column(String(50), nullable=True,
                                doc="Ruolo dell'utente che ha confermato il batch")
    
    data_conferma = Column(DateTime, nullable=True,
                          doc="Data e ora di conferma del batch")
    
    # Timestamp automatici
    created_at = Column(DateTime, nullable=False, default=func.now(),
                       doc="Data e ora di creazione del record")
    
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(),
                       doc="Data e ora dell'ultimo aggiornamento")
    
    # Relazioni
    nesting_results = relationship("NestingResult", back_populates="batch")
    
    def __repr__(self):
        return f"<BatchNesting(id={self.id}, nome={self.nome}, stato={self.stato})>"

    @property
    def efficienza_media(self) -> float:
        """Calcola l'efficienza media di utilizzo del batch"""
        if self.numero_nesting > 0 and hasattr(self, 'nesting_results'):
            efficienza_totale = sum(
                nr.efficienza_totale for nr in self.nesting_results 
                if hasattr(nr, 'efficienza_totale')
            )
            return efficienza_totale / self.numero_nesting
        return 0.0
    
    @property
    def stato_descrizione(self) -> str:
        """Ritorna la descrizione testuale dello stato"""
        descrizioni = {
            StatoBatchNestingEnum.SOSPESO: "In attesa di conferma",
            StatoBatchNestingEnum.CONFERMATO: "Confermato e pronto per produzione",
            StatoBatchNestingEnum.TERMINATO: "Completato"
        }
        return descrizioni.get(self.stato, "Stato sconosciuto") 