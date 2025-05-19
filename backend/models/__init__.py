# Esporta i modelli principali per un più facile import
from .base import Base, TimestampMixin
from .catalogo import Catalogo
from .parte import Parte, parte_tool_association
from .tool import Tool
from .autoclave import Autoclave, StatoAutoclave
from .ciclo_cura import CicloCura

# Lista completa di tutti i modelli per le migrazioni
__all__ = [
    "Base", 
    "TimestampMixin", 
    "Catalogo",
    "Parte",
    "Tool", 
    "Autoclave", 
    "StatoAutoclave",
    "CicloCura",
    "parte_tool_association"
] 