"""
Package batch_nesting_modules - Moduli specializzati per la gestione batch nesting

Struttura modulare:
- crud.py: Operazioni CRUD base
- generation.py: Algoritmi di generazione nesting
- workflow.py: Gestione stati batch (conferma, caricamento, cura, terminazione)
- results.py: Risultati, statistiche, validazione
- maintenance.py: Diagnosi sistema, cleanup, operazioni bulk
"""

from .crud import router as crud_router
from .generation import router as generation_router
from .workflow import router as workflow_router
from .results import router as results_router
from .maintenance import router as maintenance_router

__all__ = [
    "crud_router",
    "generation_router", 
    "workflow_router",
    "results_router",
    "maintenance_router"
] 