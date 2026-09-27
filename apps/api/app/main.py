from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.auth_routes import router as auth_router
from app.api.me_routes import router as me_router
from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import PrismError
from app.core.logging import configure_logging
from app.services.cache import InMemoryCache


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="PRISM API",
        version=__version__,
        description="Deterministic GitHub pull request analyzer",
    )
    app.state.cache = InMemoryCache()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(PrismError)
    async def prism_error_handler(_: Request, exc: PrismError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "ANALYSIS_FAILED",
                    "message": "An unexpected error occurred during analysis.",
                    "details": {"type": type(exc).__name__},
                }
            },
        )

    app.include_router(router)
    app.include_router(auth_router)
    app.include_router(me_router)
    return app


app = create_app()
