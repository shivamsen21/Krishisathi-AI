#!/usr/bin/env python
"""
AgroVision AI — Backend Development Server Startup Script
Run: python run.py
"""
import uvicorn
from backend.config import settings

if __name__ == "__main__":
    print("=" * 55)
    print("  🌱 AgroVision AI Backend Server")
    print(f"  📡 http://{settings.HOST}:{settings.PORT}")
    print(f"  📖 Docs: http://localhost:{settings.PORT}/docs")
    print(f"  🌍 Environment: {settings.APP_ENV}")
    print(f"  🔗 Supabase: {'Connected' if settings.SUPABASE_URL else 'Local Dev Mode'}")
    print("=" * 55)
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )
