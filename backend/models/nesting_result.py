from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, func, Enum, Text
from sqlalchemy.orm import relationship
from .base import Base

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
    
    # Stato del nesting
    stato = Column(
        String(50),
        default="In sospeso",
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
    
    # ✅ NUOVO: Statistiche per nesting su due piani
    peso_totale_kg = Column(Float, default=0.0, doc="Peso totale del carico in kg")
    area_piano_1 = Column(Float, default=0.0, doc="Area utilizzata sul piano 1 in cm²")
    area_piano_2 = Column(Float, default=0.0, doc="Area utilizzata sul piano 2 in cm²")
    superficie_piano_2_max = Column(Float, nullable=True, doc="Superficie massima configurabile del piano 2 in cm²")
    
    # Note aggiuntive
    note = Column(Text, nullable=True, doc="Note aggiuntive sul nesting")
    
    # ✅ NUOVO: Posizioni 2D dei tool sul piano dell'autoclave con assegnazione piano
    posizioni_tool = Column(JSON, default=list, 
                           doc="Posizioni 2D dei tool: [{'odl_id': int, 'piano': int, 'x': float, 'y': float, 'width': float, 'height': float}, ...]")
    
    # ✅ NUOVO: Collegamento ai report generati
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True, index=True,
                      doc="ID del report PDF generato per questo nesting")
    report = relationship("Report", backref="nesting_results")
    
    # Metadati
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @property
    def efficienza_piano_1(self) -> float:
        """Calcola l'efficienza di utilizzo del piano 1"""
        if self.area_totale > 0:
            return (self.area_piano_1 / self.area_totale) * 100
        return 0.0
    
    @property
    def efficienza_piano_2(self) -> float:
        """Calcola l'efficienza di utilizzo del piano 2"""
        if self.superficie_piano_2_max and self.superficie_piano_2_max > 0:
            return (self.area_piano_2 / self.superficie_piano_2_max) * 100
        return 0.0
    
    @property
    def efficienza_totale(self) -> float:
        """Calcola l'efficienza totale di utilizzo"""
        area_totale_disponibile = self.area_totale + (self.superficie_piano_2_max or 0)
        if area_totale_disponibile > 0:
            return ((self.area_piano_1 + self.area_piano_2) / area_totale_disponibile) * 100
        return 0.0
    
    def __repr__(self):
        return f"<NestingResult id={self.id} autoclave_id={self.autoclave_id} peso={self.peso_totale_kg}kg stato={self.stato} created_at={self.created_at}>" 