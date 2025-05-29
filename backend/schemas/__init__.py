"""
Package contenente tutti gli schema Pydantic dell'API CarbonPilot.

Gli schema definiscono la struttura dei dati per:
- Validazione dell'input
- Serializzazione dell'output
- Documentazione automatica dell'API
"""

# Esporta gli schemi principali per un più facile import
# Ad esempio:
# from .user import UserCreate, UserUpdate, UserResponse

# Questi verranno implementati durante lo sviluppo delle funzionalità 

from .catalogo import CatalogoCreate, CatalogoUpdate, CatalogoResponse
from .parte import ParteCreate, ParteUpdate, ParteResponse
from .tool import ToolCreate, ToolUpdate, ToolResponse
from .ciclo_cura import CicloCuraCreate, CicloCuraUpdate, CicloCuraResponse
from .autoclave import AutoclaveCreate, AutoclaveUpdate, AutoclaveResponse
from .odl import ODLCreate, ODLUpdate, ODLRead, ODLReadBasic
from .tempo_fase import TempoFaseCreate, TempoFaseUpdate, TempoFaseInDB, PrevisioneTempo, TipoFase
from .schedule import (
    ScheduleEntryCreate, ScheduleEntryUpdate, ScheduleEntryRead, 
    ScheduleEntryAutoCreate, AutoScheduleResponse, ScheduleEntryStatusEnum
)

__all__ = [
    'CatalogoCreate', 'CatalogoUpdate', 'CatalogoResponse',
    'ParteCreate', 'ParteUpdate', 'ParteResponse',
    'ToolCreate', 'ToolUpdate', 'ToolResponse',
    'CicloCuraCreate', 'CicloCuraUpdate', 'CicloCuraResponse',
    'AutoclaveCreate', 'AutoclaveUpdate', 'AutoclaveResponse',
    'ODLCreate', 'ODLUpdate', 'ODLRead', 'ODLReadBasic',
    'TempoFaseCreate', 'TempoFaseUpdate', 'TempoFaseInDB', 'PrevisioneTempo', 'TipoFase',
    'ScheduleEntryCreate', 'ScheduleEntryUpdate', 'ScheduleEntryRead', 
    'ScheduleEntryAutoCreate', 'AutoScheduleResponse', 'ScheduleEntryStatusEnum'
] 