import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.auth import router as auth_router
from src.api.routes.market import router as market_router
from src.api.routes.skills import router as skills_router
from src.api.routes.trainings import router as trainings_router
from src.api.services.auth_service import create_default_admin

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_default_admin()
    except Exception as exc:
        logger.warning("create_default_admin failed: %s", exc)
    yield


app = FastAPI(
    title="SkillWatch API",
    description="Observatoire du marché de l'emploi Data & IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(skills_router, prefix="/skills", tags=["skills"])
app.include_router(market_router, prefix="/market", tags=["market"])
app.include_router(trainings_router, prefix="/trainings", tags=["trainings"])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "SkillWatch API"}
