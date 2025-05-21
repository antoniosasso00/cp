from fastapi import APIRouter
from api.routers.catalogo import router as catalogo_router
from api.routers.parte import router as parte_router
from api.routers.tool import router as tool_router
from api.routers.autoclave import router as autoclave_router
from api.routers.ciclo_cura import router as ciclo_cura_router
from api.routers.odl import router as odl_router
from api.routers.tempo_fasi import router as tempo_fasi_router
from api.nesting import router as nesting_router

# Router principale senza prefisso /api (verrà aggiunto in main.py)
router = APIRouter()

# Inclusione di tutti i router con i prefissi appropriati
router.include_router(catalogo_router, prefix="/catalogo")
router.include_router(parte_router, prefix="/parti")
router.include_router(tool_router, prefix="/tools")
router.include_router(autoclave_router, prefix="/autoclavi")
router.include_router(ciclo_cura_router, prefix="/cicli-cura")
router.include_router(odl_router, prefix="/odl")
router.include_router(tempo_fasi_router, prefix="/tempo-fasi")
router.include_router(nesting_router)