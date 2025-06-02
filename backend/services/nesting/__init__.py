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

__all__ = [
    'NestingModel',
    'NestingParameters', 
    'ToolInfo',
    'AutoclaveInfo',
    'NestingLayout',
    'NestingMetrics',
    'NestingSolution'
] 