from fastapi import APIRouter
from app.api.v1.endpoints import auth, employees, managers, hr, ai,unified_conversation, analytics, policy_routes

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(managers.router, prefix="/managers", tags=["Managers"])
api_router.include_router(hr.router, prefix="/hr", tags=["HR"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Features"])
api_router.include_router(
    unified_conversation.router,
    tags=["conversation"]
)
api_router.include_router(
    analytics.router,
    tags=["analytics"]
)
api_router.include_router(
    policy_routes.router,
    tags=["policy"]
)
