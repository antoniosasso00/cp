# Importa i moduli per un più facile accesso
from . import catalogo, ciclo_cura, parte, tool, autoclave, associations

# Esporta le classi principali per un più facile import
from .base import Base, TimestampMixin
from .catalogo import Catalogo
from .parte import Parte
from .tool import Tool
from .autoclave import Autoclave, StatoAutoclaveEnum
from .ciclo_cura import CicloCura
from .associations import parte_tool_association
from .odl import ODL
from .tempo_fase import TempoFase

# Lista completa di tutti i modelli per le migrazioni
__all__ = [
    "Base", 
    "TimestampMixin", 
    "Catalogo",
    "Parte",
    "Tool", 
    "Autoclave",
    "StatoAutoclaveEnum",
    "CicloCura",
    "parte_tool_association",
    "ODL",
    "TempoFase"
] 