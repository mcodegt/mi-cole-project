from fastapi import APIRouter

from app.routes.platform import billing, schools, subscription_plans, users

router = APIRouter(prefix="/platform")
router.include_router(schools.router)
router.include_router(users.router)
router.include_router(subscription_plans.router)
router.include_router(billing.router)
