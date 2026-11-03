import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Executes database schema creation and startup procedures.
    """
    logger.info("Initializing database schema...")
    try:
        # Create tables if they do not exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Error during schema initialization: {e}")
    yield
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Multi-Tier Expense Tracker & Splitwise Engine API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs",
        "status": "operational"
    }


@app.get("/health", tags=["Health"])
def healthcheck():
    return {"status": "healthy"}

