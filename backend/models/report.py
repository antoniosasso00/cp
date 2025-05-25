from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base, TimestampMixin

class ReportTypeEnum(enum.Enum):
    """Enum per i tipi di report"""
    PRODUZIONE = "produzione"
    QUALITA = "qualita"
    TEMPI = "tempi"
    COMPLETO = "completo"
    NESTING = "nesting"

class Report(Base, TimestampMixin):
    """Modello per i report PDF generati"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)
    file_path = Column(String(500), nullable=False)
    report_type = Column(SQLEnum(ReportTypeEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False, index=True)
    generated_for_user_id = Column(Integer, nullable=True, index=True)  # Per ora nullable, futuro multi-utente
    
    # Metadati aggiuntivi
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    include_sections = Column(String(255), nullable=True)  # CSV delle sezioni incluse
    file_size_bytes = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Report(id={self.id}, filename='{self.filename}', type='{self.report_type.value}')>" 