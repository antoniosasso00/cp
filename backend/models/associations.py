from sqlalchemy import Column, Integer, Table, ForeignKey
from .base import Base

# Tabella di associazione molti-a-molti tra Parti e Tools
parte_tool_association = Table(
    'parte_tool_association',
    Base.metadata,
    Column('parte_id', Integer, ForeignKey('parti.id'), primary_key=True),
    Column('tool_id', Integer, ForeignKey('tools.id'), primary_key=True)
)

# Associazione molti-a-molti tra NestingResult e ODL
nesting_result_odl = Table(
    "nesting_result_odl",
    Base.metadata,
    Column("nesting_result_id", Integer, ForeignKey("nesting_results.id"), primary_key=True),
    Column("odl_id", Integer, ForeignKey("odl.id"), primary_key=True),
) 