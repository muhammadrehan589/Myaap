import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes import upload, extract, retrieve, compliance, scoring, proposal
from config.database import init_db, enable_pgvector, IS_POSTGRES

load_dotenv()

logger = logging.getLogger(__name__)

# Configurable CORS origins for production deployment
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:5173"
).split(",")

app = FastAPI(
    title="Bid & Proposal Response Engine",
    description="AI-powered RFP analysis, compliance checking, and proposal generation",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and extensions on startup."""
    try:
        init_db()
        logger.info("Database tables initialized")

        if IS_POSTGRES:
            if enable_pgvector():
                logger.info("pgvector extension enabled")
        else:
            logger.info("Using SQLite database")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.info("Continuing without database (Excel fallback)")

# Register routes
app.include_router(upload.router, tags=["Upload"])
app.include_router(extract.router, tags=["Extraction"])
app.include_router(retrieve.router, tags=["RAG"])
app.include_router(compliance.router, tags=["Compliance"])
app.include_router(scoring.router, tags=["Scoring"])
app.include_router(proposal.router, tags=["Proposal"])


@app.get("/")
async def root():
    return {"status": "ok", "service": "Bid & Proposal Response Engine", "version": "2.0.0"}


@app.get("/health")
async def health():
    """Health check with database status."""
    from config.database import SessionLocal
    from sqlalchemy import text
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status,
        "database_type": "PostgreSQL" if IS_POSTGRES else "SQLite",
    }


@app.get("/llm-stats")
async def llm_stats():
    """LLM service statistics — providers, cache, request counts."""
    from services.llm_service import get_llm_stats
    return get_llm_stats()
