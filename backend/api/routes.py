from fastapi import APIRouter

# Importazione dei router
from api.routers.catalogo import router as catalogo_router
from api.routers.parte import router as parte_router
from api.routers.tool import router as tool_router
from api.routers.autoclave import router as autoclave_router
from api.routers.ciclo_cura import router as ciclo_cura_router

# Router principale che aggregherà tutti i sotto-router
router = APIRouter()

@router.get("/")
def read_api_root():
    """Endpoint root per l'API"""
    return {
        "message": "CarbonPilot API v0.3.0",
        "endpoints": [
            {"path": "/health", "description": "Verifica lo stato del servizio"},
            {"path": "/api/v1/catalogo", "description": "Operazioni su catalogo prodotti"},
            {"path": "/api/v1/parti", "description": "Operazioni su parti prodotte"},
            {"path": "/api/v1/tools", "description": "Operazioni su tools/stampi"},
            {"path": "/api/v1/autoclavi", "description": "Operazioni su autoclavi"},
            {"path": "/api/v1/cicli-cura", "description": "Operazioni su cicli di cura"}
        ]
    }

# Inclusione dei router
router.include_router(catalogo_router, prefix="/v1/catalogo", tags=["catalogo"])
router.include_router(parte_router, prefix="/v1/parti", tags=["parti"])
router.include_router(tool_router, prefix="/v1/tools", tags=["tools"])
router.include_router(autoclave_router, prefix="/v1/autoclavi", tags=["autoclavi"])
router.include_router(ciclo_cura_router, prefix="/v1/cicli-cura", tags=["cicli_cura"])

# Preparazione per autenticazione futura
# from .auth import auth_router
# router.include_router(auth_router, prefix="/auth", tags=["authentication"]) 