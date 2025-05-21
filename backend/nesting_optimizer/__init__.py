"""
Modulo per l'ottimizzazione del nesting delle parti in autoclave.
Utilizza algoritmi di OR-Tools per ottimizzare la disposizione degli ODL nelle autoclavi.
"""

from .optimizer import NestingOptimizer
from .schemas import (
    NestingRequest, 
    NestingResponse, 
    NestingParameters, 
    NestingConfirmRequest, 
    NestingResultResponse
)

__all__ = [
    "NestingOptimizer", 
    "NestingRequest", 
    "NestingResponse", 
    "NestingParameters", 
    "NestingConfirmRequest", 
    "NestingResultResponse"
] 