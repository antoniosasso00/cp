from fastapi import APIRouter
from api.routers.catalogo import router as catalogo_router
from api.routers.parte import router as parte_router
from api.routers.tool import router as tool_router
from api.routers.autoclave import router as autoclave_router
from api.routers.ciclo_cura import router as ciclo_cura_router

router = APIRouter()

router.include_router(catalogo_router, prefix="/v1/catalogo")
router.include_router(parte_router, prefix="/v1/parte")
router.include_router(tool_router, prefix="/v1/tools")
router.include_router(autoclave_router, prefix="/v1/autoclavi")
router.include_router(ciclo_cura_router, prefix="/v1/cicli-cura")