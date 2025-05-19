# Esporta i modelli principali per un più facile import
from .base import Base, TimestampMixin
from .catalogo import Catalogo
from .parte import Parte, parte_tool_association
from .tool import Tool
from .autoclave import Autoclave
from .ciclo_cura import CicloCura

# Lista completa di tutti i modelli per le migrazioni
__all__ = [
    "Base", 
    "TimestampMixin", 
    "Catalogo",
    "Parte",
    "Tool", 
    "Autoclave", 
    "CicloCura",
    "parte_tool_association"
] 