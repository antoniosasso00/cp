from fastapi import APIRouter
from api.routers.catalogo import router as catalogo_router
from api.routers.parte import router as parte_router
from api.routers.tool import router as tool_router
from api.routers.autoclave import router as autoclave_router
from api.routers.ciclo_cura import router as ciclo_cura_router
from api.routers.odl import router as odl_router
from api.routers.tempo_fasi import router as tempo_fasi_router
from api.routers.nesting import router as nesting_router
from api.routers.schedule import router as schedule_router
from api.routers.reports import router as reports_router

router = APIRouter()

router.include_router(catalogo_router, prefix="/v1/catalogo")
router.include_router(parte_router, prefix="/v1/parti")
router.include_router(tool_router, prefix="/v1/tools")
router.include_router(autoclave_router, prefix="/v1/autoclavi")
router.include_router(ciclo_cura_router, prefix="/v1/cicli-cura")
router.include_router(odl_router, prefix="/v1/odl")
router.include_router(tempo_fasi_router, prefix="/v1/tempo-fasi")
router.include_router(nesting_router, prefix="/v1/nesting")
router.include_router(schedule_router, prefix="/v1/schedules")
router.include_router(reports_router, prefix="/v1/reports")