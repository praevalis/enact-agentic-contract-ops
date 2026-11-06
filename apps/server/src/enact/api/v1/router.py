from fastapi import APIRouter

from enact.api.cases.routes import router as cases_router
from enact.api.customers.routes import router as customers_router
from enact.api.health import router as health_router
from enact.api.identity.auth_routes import router as auth_router
from enact.api.identity.organization_routes import router as organizations_router
from enact.api.identity.user_routes import router as users_router

router = APIRouter(prefix='/v1')
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(customers_router)
router.include_router(cases_router)
router.include_router(organizations_router)
router.include_router(users_router)
