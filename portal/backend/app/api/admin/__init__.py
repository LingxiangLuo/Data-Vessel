from fastapi import APIRouter

from .users import router as users_router
from .roles import router as roles_router
from .sso import router as sso_router
from .config import router as config_router
from .resource_access import router as resource_access_router
from .notify_channels import router as notify_channels_router

router = APIRouter(prefix="/admin", tags=["admin"])

router.include_router(users_router)
router.include_router(roles_router)
router.include_router(sso_router)
router.include_router(config_router)
router.include_router(resource_access_router)
router.include_router(notify_channels_router)
