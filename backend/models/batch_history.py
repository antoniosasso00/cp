from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Float, Text, func
from sqlalchemy.orm import relationship
from .base import Base

class BatchHistory(Base):
    """
    Modello per tracciare lo storico completo dei batch terminati.
    Salva informazioni dettagliate quando un batch passa allo stato "cured".
    """
    __tablename__ = "batch_history"
    
    # Chiave primaria
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                doc="ID auto-incrementale del record storico")
    
    # Relazione con il batch originale
    batch_id = Column(String(36), ForeignKey("batch_nesting.id"), nullable=False, index=True,
                     doc="ID del batch nesting che ha generato questo storico")
    batch = relationship("BatchNesting", back_populates="history_records")
    
    # Informazioni base copia del batch
    nome_batch = Column(String(255), nullable=True,
                       doc="Nome del batch al momento della chiusura")
    
    autoclave_id = Column(Integer, nullable=False,
                         doc="ID dell'autoclave utilizzata")
    
    autoclave_nome = Column(String(100), nullable=True,
                           doc="Nome dell'autoclave al momento della chiusura")
    
    # Dati di efficienza teorica vs reale
    efficienza_teorica = Column(Float, default=0.0,
                               doc="Efficienza calcolata al momento della conferma del batch")
    
    efficienza_reale = Column(Float, default=0.0,
                             doc="Efficienza reale calcolata dopo la cura (peso cura vs area)")
    
    # Statistiche del ciclo di cura
    peso_caricato_kg = Column(Float, nullable=True,
                             doc="Peso effettivamente caricato nell'autoclave in kg")
    
    area_utilizzata_cm2 = Column(Float, nullable=True,
                                doc="Area totale utilizzata in cm²")
    
    valvole_utilizzate = Column(Integer, nullable=True,
                               doc="Numero di valvole vuoto utilizzate")
    
    numero_odl_completati = Column(Integer, default=0,
                                  doc="Numero di ODL completati con successo")
    
    numero_odl_falliti = Column(Integer, default=0,
                               doc="Numero di ODL falliti durante la cura")
    
    # Tempi del ciclo
    data_conferma = Column(DateTime, nullable=True,
                          doc="Data e ora di conferma del batch")
    
    data_inizio_caricamento = Column(DateTime, nullable=True,
                                    doc="Data e ora di inizio caricamento in autoclave")
    
    data_inizio_cura = Column(DateTime, nullable=True,
                             doc="Data e ora di inizio del ciclo di cura")
    
    data_fine_cura = Column(DateTime, nullable=True,
                           doc="Data e ora di completamento del ciclo di cura")
    
    durata_caricamento_minuti = Column(Integer, nullable=True,
                                      doc="Tempo impiegato per il caricamento in minuti")
    
    durata_cura_minuti = Column(Integer, nullable=True,
                               doc="Durata effettiva del ciclo di cura in minuti")
    
    durata_totale_minuti = Column(Integer, nullable=True,
                                 doc="Durata totale del processo in minuti")
    
    # Parametri tecnici del ciclo di cura
    temperatura_max_raggiunta = Column(Float, nullable=True,
                                      doc="Temperatura massima raggiunta durante la cura in °C")
    
    pressione_max_raggiunta = Column(Float, nullable=True,
                                    doc="Pressione massima raggiunta durante la cura in bar")
    
    # Dati JSON di dettaglio
    configurazione_layout = Column(JSON, nullable=True,
                                  doc="Configurazione completa del layout utilizzato")
    
    parametri_cura = Column(JSON, nullable=True,
                           doc="Parametri del ciclo di cura utilizzato")
    
    eventi_critici = Column(JSON, default=list,
                           doc="Lista di eventi critici/anomalie durante il ciclo")
    
    odl_dettagli = Column(JSON, default=list,
                         doc="Dettagli completi degli ODL processati")
    
    # Note e osservazioni
    note_operatore = Column(Text, nullable=True,
                           doc="Note dell'operatore al completamento del ciclo")
    
    anomalie_rilevate = Column(Text, nullable=True,
                              doc="Descrizione di eventuali anomalie rilevate")
    
    # Tracciabilità
    creato_da_utente = Column(String(100), nullable=True,
                             doc="ID dell'utente che ha gestito il batch")
    
    creato_da_ruolo = Column(String(50), nullable=True,
                            doc="Ruolo dell'utente che ha gestito il batch")
    
    # Timestamp automatici
    created_at = Column(DateTime, nullable=False, default=func.now(),
                       doc="Data e ora di creazione del record storico")
    
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(),
                       doc="Data e ora dell'ultimo aggiornamento")
    
    def __repr__(self):
        return f"<BatchHistory(id={self.id}, batch_id={self.batch_id}, nome_batch={self.nome_batch})>"
    
    @property
    def efficienza_delta(self) -> float:
        """Calcola la differenza tra efficienza teorica e reale"""
        return self.efficienza_reale - self.efficienza_teorica
    
    @property
    def performance_rating(self) -> str:
        """Valuta la performance del batch basandosi sull'efficienza reale"""
        if self.efficienza_reale >= 85:
            return "excellent"
        elif self.efficienza_reale >= 70:
            return "good"
        elif self.efficienza_reale >= 55:
            return "average"
        else:
            return "poor"
    
    @property
    def efficienza_vs_teorica(self) -> str:
        """Compara l'efficienza reale con quella teorica"""
        delta = self.efficienza_delta
        if delta >= 5:
            return "better_than_expected"
        elif delta >= -5:
            return "as_expected"
        else:
            return "worse_than_expected" 