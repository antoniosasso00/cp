from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, func, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum as PyEnum
from .base import Base

class StatoBatchNestingEnum(PyEnum):
    """Enum per rappresentare i vari stati di un batch nesting"""
    DRAFT = "draft"
    SOSPESO = "sospeso"
    CONFERMATO = "confermato"
    LOADED = "loaded"
    CURED = "cured"
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
    
    # ✅ NUOVO: Campo efficiency per il sistema di valutazione
    efficiency = Column(Float, default=0.0,
                       doc="Efficienza complessiva del batch: 0.7·area_pct + 0.3·vacuum_util_pct")
    
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
    
    data_completamento = Column(DateTime, nullable=True,
                               doc="Data e ora di completamento del ciclo di cura")
    
    durata_ciclo_minuti = Column(Integer, nullable=True,
                                doc="Durata del ciclo di cura in minuti (calcolata automaticamente)")
    
    # Timestamp automatici
    created_at = Column(DateTime, nullable=False, default=func.now(),
                       doc="Data e ora di creazione del record")
    
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(),
                       doc="Data e ora dell'ultimo aggiornamento")
    
    # Relazioni
    nesting_results = relationship("NestingResult", back_populates="batch")
    history_records = relationship("BatchHistory", back_populates="batch")
    
    def __repr__(self):
        return f"<BatchNesting(id={self.id}, nome={self.nome}, stato={self.stato})>"

    @property
    def area_pct(self) -> float:
        """Calcola la percentuale di area utilizzata con formula corretta"""
        if not self.autoclave or not self.autoclave.lunghezza or not self.autoclave.larghezza_piano:
            return 0.0
        
        # Area totale disponibile in mm²
        area_totale_mm2 = self.autoclave.lunghezza * self.autoclave.larghezza_piano
        
        if area_totale_mm2 <= 0:
            return 0.0
        
        # area_totale_utilizzata è già in cm², convertiamo in mm² per il calcolo
        area_utilizzata_mm2 = self.area_totale_utilizzata * 100
        
        # Calcola percentuale con controllo per evitare valori > 100%
        percentuale = (area_utilizzata_mm2 / area_totale_mm2) * 100
        return min(100.0, max(0.0, percentuale))
    
    @property
    def vacuum_util_pct(self) -> float:
        """Calcola la percentuale di utilizzo delle linee vuoto"""
        if not self.autoclave or not self.autoclave.num_linee_vuoto:
            return 0.0
        
        return min(100.0, (self.valvole_totali_utilizzate / self.autoclave.num_linee_vuoto) * 100)
    
    @property
    def efficiency_score(self) -> float:
        """Calcola l'efficiency score secondo la formula corretta: 0.7·area_pct + 0.3·vacuum_util_pct"""
        area_efficiency = self.area_pct
        vacuum_efficiency = self.vacuum_util_pct
        
        # Formula bilanciata per efficienza complessiva
        efficiency = (0.7 * area_efficiency) + (0.3 * vacuum_efficiency)
        
        # Assicura che il valore sia tra 0 e 100
        return min(100.0, max(0.0, efficiency))
    
    @property
    def efficiency_level(self) -> str:
        """Ritorna il livello di efficienza (green/yellow/red)"""
        score = self.efficiency_score
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        else:
            return "red"
    
    @property
    def efficiency_color_class(self) -> str:
        """Ritorna la classe CSS per colorare il badge"""
        level = self.efficiency_level
        if level == "green":
            return "bg-green-500"
        elif level == "yellow":
            return "bg-amber-500"
        else:
            return "bg-red-500"

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
            StatoBatchNestingEnum.DRAFT: "Bozza in preparazione",
            StatoBatchNestingEnum.SOSPESO: "In attesa di conferma",
            StatoBatchNestingEnum.CONFERMATO: "Confermato e pronto per produzione",
            StatoBatchNestingEnum.LOADED: "Caricato in autoclave",
            StatoBatchNestingEnum.CURED: "Cura completata",
            StatoBatchNestingEnum.TERMINATO: "Completato"
        }
        return descrizioni.get(self.stato, "Stato sconosciuto")
    
    def update_efficiency(self):
        """Aggiorna il campo efficiency con il valore calcolato correttamente"""
        # Usa il calcolo più accurato dell'area_pct
        calculated_efficiency = self.area_pct
        
        # Se abbiamo anche dati sulle valvole, usa l'efficiency_score combinato
        if self.valvole_totali_utilizzate > 0 and self.autoclave and self.autoclave.num_linee_vuoto:
            calculated_efficiency = self.efficiency_score
        
        self.efficiency = calculated_efficiency 