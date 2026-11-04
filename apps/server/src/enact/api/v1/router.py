from fastapi import APIRouter

from enact.api.auth import router as auth_router
from enact.api.health import router as health_router
from enact.api.organizations import router as organizations_router
from enact.api.users import router as users_router

router = APIRouter(prefix='/v1')
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(organizations_router)
router.include_router(users_router)
