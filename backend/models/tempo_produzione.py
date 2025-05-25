from sqlalchemy import Column, Integer, String, Float, DateTime, func, Text, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class TempoProduzione(Base, TimestampMixin):
    """Modello che rappresenta i tempi di produzione storici per part number, categoria e sotto-categoria"""
    __tablename__ = "tempi_produzione"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificatori del prodotto
    part_number = Column(String(100), nullable=True, index=True,
                        doc="Part number specifico (se disponibile)")
    categoria = Column(String(100), nullable=True, index=True,
                      doc="Categoria del prodotto")
    sotto_categoria = Column(String(100), nullable=True, index=True,
                           doc="Sotto-categoria del prodotto")
    
    # Tempi di produzione in minuti
    tempo_medio_minuti = Column(Float, nullable=False,
                               doc="Tempo medio di produzione in minuti")
    tempo_minimo_minuti = Column(Float, nullable=True,
                                doc="Tempo minimo registrato in minuti")
    tempo_massimo_minuti = Column(Float, nullable=True,
                                 doc="Tempo massimo registrato in minuti")
    
    # Statistiche
    numero_osservazioni = Column(Integer, default=1, nullable=False,
                                doc="Numero di osservazioni utilizzate per calcolare la media")
    ultima_osservazione = Column(DateTime, nullable=False,
                                doc="Data dell'ultima osservazione registrata")
    
    # Informazioni aggiuntive
    note = Column(Text, nullable=True,
                 doc="Note aggiuntive sui tempi di produzione")
    
    # Metadati
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indici composti per ottimizzare le query
    __table_args__ = (
        Index('idx_part_number_categoria', 'part_number', 'categoria'),
        Index('idx_categoria_sotto_categoria', 'categoria', 'sotto_categoria'),
    )
    
    def __repr__(self):
        return f"<TempoProduzione(id={self.id}, part_number='{self.part_number}', categoria='{self.categoria}', tempo_medio={self.tempo_medio_minuti})>"
    
    @classmethod
    def get_tempo_stimato(cls, db_session, part_number=None, categoria=None, sotto_categoria=None):
        """
        Recupera il tempo stimato di produzione basato sui dati storici.
        Priorità: part_number > sotto_categoria > categoria
        
        Args:
            db_session: Sessione del database
            part_number: Part number specifico
            categoria: Categoria del prodotto
            sotto_categoria: Sotto-categoria del prodotto
            
        Returns:
            Tempo stimato in minuti o None se non trovato
        """
        # Prima prova con part_number specifico
        if part_number:
            tempo = db_session.query(cls).filter(
                cls.part_number == part_number
            ).first()
            if tempo:
                return tempo.tempo_medio_minuti
        
        # Poi prova con sotto_categoria
        if sotto_categoria:
            tempo = db_session.query(cls).filter(
                cls.sotto_categoria == sotto_categoria
            ).first()
            if tempo:
                return tempo.tempo_medio_minuti
        
        # Infine prova con categoria
        if categoria:
            tempo = db_session.query(cls).filter(
                cls.categoria == categoria
            ).first()
            if tempo:
                return tempo.tempo_medio_minuti
        
        return None 