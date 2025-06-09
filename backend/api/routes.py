from fastapi import APIRouter
from .routers.catalogo import router as catalogo_router
from .routers.parte import router as parte_router
from .routers.tool import router as tool_router
from .routers.autoclave import router as autoclave_router
from .routers.ciclo_cura import router as ciclo_cura_router
from .routers.odl import router as odl_router
from .routers.tempo_fasi import router as tempo_fasi_router
from .routers.schedule import router as schedule_router
from .routers.reports import router as reports_router
from .routers.odl_monitoring import router as odl_monitoring_router
from .routers.admin import router as admin_router
from .routers.system_logs import router as system_logs_router
# from .routers.batch_nesting_BACKUP import router as batch_nesting_router  # ← BACKUP ORIGINALE SOSPESO
from .routers.batch_modular import router as batch_nesting_router  # ← ROUTER MODULARE ATTIVO

from .routers.nesting_result import router as nesting_result_router
from .routers.produzione import router as produzione_router
from .routers.standard_time import router as standard_time_router
from .routers.dashboard import router as dashboard_router

router = APIRouter()

router.include_router(catalogo_router, prefix="/catalogo")
router.include_router(parte_router, prefix="/parti")
router.include_router(tool_router, prefix="/tools")
router.include_router(autoclave_router, prefix="/autoclavi")
router.include_router(ciclo_cura_router, prefix="/cicli-cura")
router.include_router(odl_router, prefix="/odl")
router.include_router(tempo_fasi_router, prefix="/tempo-fasi")
router.include_router(schedule_router, prefix="/schedules")
router.include_router(reports_router, prefix="/reports")
router.include_router(odl_monitoring_router, prefix="/odl-monitoring")
router.include_router(batch_nesting_router)
router.include_router(nesting_result_router)
router.include_router(admin_router)
router.include_router(system_logs_router)
router.include_router(produzione_router)
router.include_router(standard_time_router, prefix="/standard-times")
router.include_router(dashboard_router)