"""
FastAPI Admin Dashboard API for the Rideshare Bot.
Provides RESTful endpoints for managing drivers, riders, rides, and platform analytics.
"""
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.admin import router as admin_router

# Initialize FastAPI
app = FastAPI(
    title="RideShare Admin API",
    description="Backend API for the RideShare Bot Admin Dashboard",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration - allow our Next.js dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/", tags=["Health"])
async def root():
    """API health check."""
    return {"status": "ok", "service": "RideShare Admin API", "version": "1.0.0"}


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    from database.db import init_db
    await init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8001, reload=True)
