from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base

class ODLStatus(enum.Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ODLPhase(enum.Enum):
    LAMINAZIONE = "laminazione"
    PRE_NESTING = "pre_nesting"
    NESTING = "nesting"
    AUTOCLAVE = "autoclave"
    POST = "post"

# Tabella di associazione tra ODL e Parte
odl_parts = Table(
    'odl_parts',
    Base.metadata,
    Column('odl_id', Integer, ForeignKey('odl.id'), primary_key=True),
    Column('parte_id', Integer, ForeignKey('parti.id'), primary_key=True),
    Column('quantity', Integer, nullable=False, default=1),
    Column('status', String(50), nullable=False, default='created'),
    Column('last_updated', DateTime, default=datetime.utcnow)
)

class ODL(Base):
    __tablename__ = 'odl'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    status = Column(Enum(ODLStatus), nullable=False, default=ODLStatus.CREATED)
    current_phase = Column(Enum(ODLPhase), nullable=False, default=ODLPhase.LAMINAZIONE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    parti = relationship("Parte", secondary=odl_parts, back_populates="odls")
    
    def __repr__(self):
        return f"<ODL {self.code}>" 