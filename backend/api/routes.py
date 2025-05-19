from fastapi import APIRouter

# Router principale che aggregherà tutti i sotto-router
router = APIRouter()

@router.get("/")
def read_api_root():
    """Endpoint root per l'API"""
    return {
        "message": "CarbonPilot API v0.1.0",
        "endpoints": [
            {"path": "/health", "description": "Verifica lo stato del servizio"},
            # Altri endpoint verranno aggiunti qui man mano che vengono implementati
        ]
    }

# Qui verranno inclusi gli altri router, ad esempio:
# from .users import users_router
# router.include_router(users_router, prefix="/users", tags=["users"])

# Preparazione per autenticazione futura
# from .auth import auth_router
# router.include_router(auth_router, prefix="/auth", tags=["authentication"]) 