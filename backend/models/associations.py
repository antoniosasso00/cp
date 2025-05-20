from sqlalchemy import Column, Integer, Table, ForeignKey
from .base import Base

# Tabella di associazione molti-a-molti tra Parti e Tools
parte_tool_association = Table(
    'parte_tool_association',
    Base.metadata,
    Column('parte_id', Integer, ForeignKey('parti.id'), primary_key=True),
    Column('tool_id', Integer, ForeignKey('tools.id'), primary_key=True)
) 