"""FastAPI app entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers import jobs, match

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    # Validacao lazy: tenta abrir uma conexao
    try:
        async with engine.connect() as conn:
            pass
    except Exception as exc:
        print(f"⚠️  Nao conectou ao banco no startup: {exc}")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(match.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)


@app.get("/", tags=["health"])
async def root():
    """Health check basico."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check com detalhes."""
    return {
        "status": "healthy",
        "debug": settings.debug,
        "api_prefix": settings.api_prefix,
    }
