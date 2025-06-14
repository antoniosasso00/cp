"""
Models package initialization
"""

# Importa i moduli per un più facile accesso
from . import catalogo, ciclo_cura, parte, tool, autoclave, associations, cavalletto

# Esporta le classi principali per un più facile import
from .base import Base, TimestampMixin
from .catalogo import Catalogo
from .parte import Parte
from .tool import Tool
from .autoclave import Autoclave, StatoAutoclaveEnum
from .cavalletto import Cavalletto
from .ciclo_cura import CicloCura
from .associations import parte_tool_association
from .odl import ODL
from .odl_log import ODLLog
from .state_log import StateLog
from .tempo_fase import TempoFase
from .nesting_result import NestingResult
from .batch_nesting import BatchNesting, StatoBatchNestingEnum
from .batch_history import BatchHistory
from .schedule_entry import ScheduleEntry, ScheduleEntryStatus, ScheduleEntryType
from .tempo_produzione import TempoProduzione
from .report import Report, ReportTypeEnum
from .system_log import SystemLog, LogLevel, EventType, UserRole
from .standard_time import StandardTime

# Lista completa di tutti i modelli per le migrazioni
__all__ = [
    "Base", 
    "TimestampMixin", 
    "Catalogo",
    "Parte",
    "Tool", 
    "Autoclave",
    "StatoAutoclaveEnum",
    "Cavalletto",
    "CicloCura",
    "parte_tool_association",
    "ODL",
    "ODLLog",
    "StateLog",
    "TempoFase",
    "NestingResult",
    "BatchNesting",
    "StatoBatchNestingEnum",
    "BatchHistory",
    "ScheduleEntry",
    "ScheduleEntryStatus",
    "ScheduleEntryType",
    "TempoProduzione",
    "Report",
    "ReportTypeEnum",
    "SystemLog",
    "LogLevel",
    "EventType",
    "UserRole",
    "StandardTime"
] 