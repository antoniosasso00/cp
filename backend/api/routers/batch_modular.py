"""
Router principale batch_nesting.py - Versione modulare

Aggrega tutti i moduli specializzati per batch nesting
"""

from fastapi import APIRouter

# Import tutti i router modulari dalla cartella batch_nesting_modules
from .batch_nesting_modules import (
    crud_router,
    generation_router,
    workflow_router,
    results_router,
    maintenance_router,
    draft_router
)

# Router principale con prefix batch_nesting
router = APIRouter(
    prefix="/batch_nesting",
    tags=["Batch Nesting"],
    responses={404: {"description": "Batch nesting non trovato"}}
)

# Inclusione di tutti i router modulari
# IMPORTANTE: Router con endpoint statici PRIMA di quelli con parametri dinamici
# ✅ FIX DRAFT SUPPORT: crud_router PRIMA di results_router per priorità endpoint /result/{batch_id}
router.include_router(generation_router, tags=["Batch Nesting - Generation"])  # /data, /genera, /solve
router.include_router(maintenance_router, tags=["Batch Nesting - Maintenance"])  # /diagnosi, /cleanup, /bulk
router.include_router(draft_router, tags=["Batch Nesting - Draft"])  # /draft, /draft/{id}/confirm
router.include_router(workflow_router, tags=["Batch Nesting - Workflow"])  # /{batch_id}/confirm, etc.
router.include_router(crud_router, tags=["Batch Nesting - CRUD"])  # /{batch_id} CON SUPPORTO DRAFT - PRIORITÀ
router.include_router(results_router, tags=["Batch Nesting - Results"])  # /{batch_id}/statistics, etc.

# Struttura modulare completata:
# ✅ CRUD: Operazioni base (CREATE, READ, UPDATE, DELETE)
# ✅ Generation: Algoritmi nesting, generazione singola e multi-batch
# ✅ Draft: Gestione batch DRAFT temporanei (solo in memoria)
# ✅ Workflow: Gestione stati batch (conferma, caricamento, cura, terminazione)
# ✅ Results: Risultati, statistiche, validazione layout
# ✅ Maintenance: Diagnosi sistema, cleanup automatico, operazioni bulk 