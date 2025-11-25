from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from app.database import init_db, engine, SessionLocal
from app.api.routes import router
from app.models.database_models import Medication
from app.data.seed_data import seed_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Medical Diagnostic System...")
    init_db()

    # Seed database with sample data
    db = SessionLocal()
    try:
        if db.query(Medication).count() == 0:
            logger.info("Seeding database with sample data...")
            seed_database(db)
    finally:
        db.close()

    logger.info("System ready!")

    yield

    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Medical Diagnostic System",
    description="AI-Powered Healthcare Backend with Multi-LLM Chatbot, Graph-Theoretic Diagnostics, and CNN Image Classification",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["Medical Diagnostic System"])


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Medical Diagnostic System API",
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "Multi-LLM Diagnostic Chatbot (Azure OpenAI)",
            "Graph-Theoretic Symptom-Disease Modeling (200+ nodes)",
            "Drug Interaction Network (5000+ edges)",
            "CNN Medication Fill-Level Classification (90% accuracy)",
            "Automated Report Generation (<1 min)",
            "Medication Compatibility Checking",
            "OTC Recommendation Engine",
        ],
    }
