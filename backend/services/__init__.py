"""
Services package initialization
"""

# Servizi dell'applicazione
# Contiene la logica di business separata dai controller API

from .nesting_service import NestingService, NestingParameters, ToolPosition, NestingResult

__all__ = [
    'NestingService',
    'NestingParameters', 
    'ToolPosition',
    'NestingResult'
] 