"""
Schemas package initialization
"""

# Esporta gli schemi principali per un più facile import
# Ad esempio:
# from .user import UserCreate, UserUpdate, UserResponse

# Questi verranno implementati durante lo sviluppo delle funzionalità 

from .catalogo import CatalogoCreate, CatalogoUpdate, CatalogoResponse
from .parte import ParteCreate, ParteUpdate, ParteResponse
from .tool import ToolCreate, ToolUpdate, ToolResponse
from .ciclo_cura import CicloCuraCreate, CicloCuraUpdate, CicloCuraResponse
from .autoclave import AutoclaveCreate, AutoclaveUpdate, AutoclaveResponse, StatoAutoclaveEnum
from .odl import ODLCreate, ODLUpdate, ODLRead, ODLReadBasic
from .tempo_fase import TempoFaseCreate, TempoFaseUpdate, TempoFaseInDB, PrevisioneTempo, TipoFase
from .schedule import (
    ScheduleEntryCreate, ScheduleEntryUpdate, ScheduleEntryRead, 
    ScheduleEntryAutoCreate, AutoScheduleResponse, ScheduleEntryStatusEnum
)
from .batch_nesting import (
    BatchNestingCreate, 
    BatchNestingResponse, 
    BatchNestingUpdate, 
    BatchNestingList,
    StatoBatchNestingEnum,
    ParametriNesting,
    ConfigurazioneLayout
)

__all__ = [
    'CatalogoCreate', 'CatalogoUpdate', 'CatalogoResponse',
    'ParteCreate', 'ParteUpdate', 'ParteResponse',
    'ToolCreate', 'ToolUpdate', 'ToolResponse',
    'CicloCuraCreate', 'CicloCuraUpdate', 'CicloCuraResponse',
    'AutoclaveCreate', 'AutoclaveUpdate', 'AutoclaveResponse', 'StatoAutoclaveEnum',
    'ODLCreate', 'ODLUpdate', 'ODLRead', 'ODLReadBasic',
    'TempoFaseCreate', 'TempoFaseUpdate', 'TempoFaseInDB', 'PrevisioneTempo', 'TipoFase',
    'ScheduleEntryCreate', 'ScheduleEntryUpdate', 'ScheduleEntryRead', 
    'ScheduleEntryAutoCreate', 'AutoScheduleResponse', 'ScheduleEntryStatusEnum',
    'BatchNestingCreate', 'BatchNestingResponse', 'BatchNestingUpdate', 'BatchNestingList',
    'StatoBatchNestingEnum', 'ParametriNesting', 'ConfigurazioneLayout'
] 