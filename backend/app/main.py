"""
HiRA - Human Rights Assistant
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import chat, documents, health, meetings, zoom, extension, bot, voice_relay, rag

app = FastAPI(
    title="HiRA API",
    description="Human Rights Assistant - Backend API",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(meetings.router, prefix="/api/v1", tags=["meetings"])
app.include_router(zoom.router, prefix="/api/v1", tags=["zoom"])
app.include_router(extension.router, prefix="/api/v1", tags=["extension"])
app.include_router(bot.router, prefix="/api/v1", tags=["bot"])
app.include_router(voice_relay.router, prefix="/api/v1", tags=["voice"])
app.include_router(rag.router, prefix="/api/v1", tags=["rag"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 HiRA API starting up...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")

    # Initialize database
    from app.core.database import init_db
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 HiRA API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
