from fastapi import APIRouter
from api.routers.catalogo import router as catalogo_router
from api.routers.parte import router as parte_router
from api.routers.tool import router as tool_router
from api.routers.autoclave import router as autoclave_router
from api.routers.ciclo_cura import router as ciclo_cura_router
from api.routers.odl import router as odl_router
from api.routers.tempo_fasi import router as tempo_fasi_router
from api.routers.schedule import router as schedule_router
from api.routers.reports import router as reports_router
from api.routers.odl_monitoring import router as odl_monitoring_router
from api.routers.admin import router as admin_router
from api.routers.system_logs import router as system_logs_router
from api.routers.batch_nesting import router as batch_nesting_router
from api.routers.produzione import router as produzione_router

router = APIRouter()

router.include_router(catalogo_router, prefix="/v1/catalogo")
router.include_router(parte_router, prefix="/v1/parti")
router.include_router(tool_router, prefix="/v1/tools")
router.include_router(autoclave_router, prefix="/v1/autoclavi")
router.include_router(ciclo_cura_router, prefix="/v1/cicli-cura")
router.include_router(odl_router, prefix="/v1/odl")
router.include_router(tempo_fasi_router, prefix="/v1/tempo-fasi")
router.include_router(schedule_router, prefix="/v1/schedules")
router.include_router(reports_router, prefix="/v1/reports")
router.include_router(odl_monitoring_router, prefix="/v1/odl-monitoring")
router.include_router(batch_nesting_router, prefix="/v1")
router.include_router(admin_router, prefix="/v1")
router.include_router(system_logs_router, prefix="/v1")
router.include_router(produzione_router, prefix="/v1")