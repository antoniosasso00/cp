from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import sessionmaker

# Creiamo Base qui direttamente
Base = declarative_base()

class TimestampMixin:
    """Mixin per aggiungere campi di timestamp ai modelli"""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# Esempio di modello per predisposizione per autenticazione
class User(Base, TimestampMixin):
    """Modello utente - predisposto per autenticazione futura"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    # Altri campi verranno aggiunti quando implementeremo l'autenticazione 