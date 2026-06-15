from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import auth, campuses, health, parent_portal, parents, public, school_profile, student_portal, students, subscription, team
from app.routes.platform import router as platform_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Mi Cole API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(public.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(campuses.router, prefix="/api/v1")
    app.include_router(school_profile.router, prefix="/api/v1")
    app.include_router(subscription.router, prefix="/api/v1")
    app.include_router(students.router, prefix="/api/v1")
    app.include_router(parents.router, prefix="/api/v1")
    app.include_router(parent_portal.router, prefix="/api/v1")
    app.include_router(student_portal.router, prefix="/api/v1")
    app.include_router(team.router, prefix="/api/v1")
    app.include_router(platform_router, prefix="/api/v1")

    if settings.static_root:
        static_path = Path(settings.static_root)
        if static_path.is_dir():
            app.mount("/", StaticFiles(directory=static_path, html=True), name="spa")

    return app


app = create_app()
