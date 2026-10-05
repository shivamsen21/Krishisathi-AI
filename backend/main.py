import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from services.supabase_service import supabase_service
from services.model_service import model_service
from routes import auth, prediction, history, chatbot, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agrovision.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AgroVision AI Backend...")
    logger.info(f"Loading MobileNetV2 model on {model_service.device}...")
    model_loaded = model_service.load_model()
    if model_loaded:
        logger.info("MobileNetV2 model loaded successfully")
    else:
        logger.warning(f"Model not loaded: {model_service.get_load_error()}. Using fallback predictions.")
    yield
    logger.info("Shutting down AgroVision AI Backend...")


app = FastAPI(
    title="AgroVision AI Backend API",
    description="High-performance FastAPI backend integrated with Supabase Database and Supabase Auth for AI-powered crop disease detection, farmer history, and management.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration allowing requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded crop leaf images
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Mount frontend files if desired for unified serving
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend_static")

# Health Check Endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint reporting API status and Supabase connectivity.
    """
    return {
        "status": "ok",
        "service": "AgroVision AI Backend",
        "version": "1.0.0",
        "supabase_connected": supabase_service.is_connected,
        "environment": settings.APP_ENV,
        "model_loaded": model_service.is_model_ready(),
        "model_classes": len(model_service.class_names) if model_service.class_names else 0,
    }

# Include API Routers
app.include_router(auth.router)
app.include_router(prediction.router)
app.include_router(history.router)
app.include_router(chatbot.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)