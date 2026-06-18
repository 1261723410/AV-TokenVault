from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import get_request_settings, router
from app.core.config import Settings, get_settings
from app.db.init_db import create_db_and_tables


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    active_settings.ensure_runtime_dirs()
    create_db_and_tables()

    app = FastAPI(title="AV-TokenVault API")
    app.state.settings = active_settings
    app.dependency_overrides[get_request_settings] = lambda: active_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
