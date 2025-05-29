from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, func, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class NestingBatch(Base):
    """
    Modello per gestire batch di nesting multipli con assegnazione di autoclavi.
    Un batch raggruppa più NestingResult per ottimizzare l'utilizzo di più autoclavi.
    """
    __tablename__ = "nesting_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Informazioni del batch
    nome = Column(String(100), nullable=False, index=True,
                 doc="Nome identificativo del batch")
    
    descrizione = Column(Text, nullable=True,
                        doc="Descrizione dettagliata del batch")
    
    # Stato del batch
    stato = Column(
        Enum("Pianificazione", "Pronto", "In Esecuzione", "Completato", "Annullato", name="batch_status"),
        default="Pianificazione",
        nullable=False,
        doc="Stato corrente del batch"
    )
    
    # Priorità del batch (per ordinamento)
    priorita = Column(Integer, default=1, nullable=False,
                     doc="Priorità del batch (numero più alto = priorità maggiore)")
    
    # Statistiche aggregate del batch
    numero_autoclavi = Column(Integer, default=0,
                             doc="Numero di autoclavi utilizzate nel batch")
    
    numero_odl_totali = Column(Integer, default=0,
                              doc="Numero totale di ODL nel batch")
    
    peso_totale_kg = Column(Float, default=0.0,
                           doc="Peso totale di tutti i carichi nel batch")
    
    area_totale_utilizzata = Column(Float, default=0.0,
                                   doc="Area totale utilizzata in tutte le autoclavi")
    
    efficienza_media = Column(Float, default=0.0,
                             doc="Efficienza media di utilizzo delle autoclavi")
    
    # Parametri di nesting utilizzati
    parametri_nesting = Column(JSON, default=dict,
                              doc="Parametri utilizzati per il nesting del batch")
    
    # Tempi stimati
    tempo_stimato_minuti = Column(Integer, nullable=True,
                                 doc="Tempo stimato per completare tutto il batch")
    
    data_inizio_pianificata = Column(DateTime, nullable=True,
                                    doc="Data e ora pianificata per l'inizio del batch")
    
    data_fine_stimata = Column(DateTime, nullable=True,
                              doc="Data e ora stimata per la fine del batch")
    
    # Tempi effettivi
    data_inizio_effettiva = Column(DateTime, nullable=True,
                                  doc="Data e ora effettiva di inizio del batch")
    
    data_fine_effettiva = Column(DateTime, nullable=True,
                                doc="Data e ora effettiva di fine del batch")
    
    # Audit e controllo
    creato_da_ruolo = Column(String(50), nullable=True,
                            doc="Ruolo dell'utente che ha creato il batch")
    
    confermato_da_ruolo = Column(String(50), nullable=True,
                                doc="Ruolo dell'utente che ha confermato il batch")
    
    # Note aggiuntive
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sul batch")
    
    # Relazioni
    nesting_results = relationship("NestingResult", back_populates="batch", cascade="all, delete-orphan")
    
    # Metadati
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @property
    def autoclavi_utilizzate(self) -> list:
        """Restituisce la lista delle autoclavi utilizzate nel batch"""
        return [nr.autoclave for nr in self.nesting_results if nr.autoclave]
    
    @property
    def odl_totali(self) -> list:
        """Restituisce tutti gli ODL inclusi nel batch"""
        odl_list = []
        for nr in self.nesting_results:
            odl_list.extend(nr.odl_list)
        return odl_list
    
    @property
    def is_completato(self) -> bool:
        """Verifica se il batch è completato"""
        return self.stato == "Completato"
    
    @property
    def is_in_esecuzione(self) -> bool:
        """Verifica se il batch è in esecuzione"""
        return self.stato == "In Esecuzione"
    
    def calcola_statistiche(self):
        """Calcola e aggiorna le statistiche del batch"""
        if not self.nesting_results:
            return
        
        self.numero_autoclavi = len(set(nr.autoclave_id for nr in self.nesting_results if nr.autoclave_id))
        self.numero_odl_totali = sum(len(nr.odl_list) for nr in self.nesting_results)
        self.peso_totale_kg = sum(nr.peso_totale_kg for nr in self.nesting_results)
        self.area_totale_utilizzata = sum(nr.area_piano_1 + nr.area_piano_2 for nr in self.nesting_results)
        
        # Calcola efficienza media
        efficienze = [nr.efficienza_totale for nr in self.nesting_results if nr.efficienza_totale > 0]
        self.efficienza_media = sum(efficienze) / len(efficienze) if efficienze else 0.0
    
    def __repr__(self):
        return f"<NestingBatch id={self.id} nome='{self.nome}' stato={self.stato} autoclavi={self.numero_autoclavi} odl={self.numero_odl_totali}>" 