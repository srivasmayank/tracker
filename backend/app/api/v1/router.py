from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.expenses import router as expenses_router
from app.api.v1.groups import router as groups_router
from app.api.v1.recurring import router as recurring_router
from app.api.v1.exports import router as exports_router
from app.api.v1.fx import router as fx_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(expenses_router)
api_router.include_router(groups_router)
api_router.include_router(recurring_router)
api_router.include_router(exports_router)
api_router.include_router(fx_router)
