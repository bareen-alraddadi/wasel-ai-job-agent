"""
Wasel — AI Career Agent
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.routes import router
from app.api.auth import router as auth_router
from app.rag.pipeline import rag_pipeline
from app.memory.manager import supabase_memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    logger.info("🚀 Starting Wasel API...")
    await supabase_memory.connect()
    try:
        await rag_pipeline.initialize()
        logger.info("✅ RAG pipeline initialized")
    except Exception as e:
        logger.warning(f"⚠️  RAG pipeline init warning: {e}")
    yield
    logger.info("👋 Shutting down Wasel API")


app = FastAPI(
    title="Wasel — AI Career Agent",
    description="Multi-agent AI platform for personalized career guidance",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])



@app.get("/health")
async def health():
    return {"status": "ok", "service": "wasel-api", "version": "1.0.0"}
