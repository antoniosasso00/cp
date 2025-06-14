"""
CarbonPilot - Nesting Module
Modulo ottimizzato per algoritmi di nesting 2D
"""

from .solver import (
    NestingModel,
    NestingParameters,
    ToolInfo,
    AutoclaveInfo,
    NestingLayout,
    NestingMetrics,
    NestingSolution
)

# Modulo per nesting a due livelli
from .solver_2l import (
    NestingModel2L,
    NestingParameters2L,
    ToolInfo2L,
    AutoclaveInfo2L,
    NestingLayout2L,
    NestingMetrics2L,
    NestingSolution2L
)

__all__ = [
    # Solver originale
    'NestingModel',
    'NestingParameters', 
    'ToolInfo',
    'AutoclaveInfo',
    'NestingLayout',
    'NestingMetrics',
    'NestingSolution',
    
    # Solver a due livelli
    'NestingModel2L',
    'NestingParameters2L',
    'ToolInfo2L', 
    'AutoclaveInfo2L',
    'NestingLayout2L',
    'NestingMetrics2L',
    'NestingSolution2L'
] 