"""
AI Job Hunter API - Main Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.s3_refresh import refresh_loop
import asyncio

from api.config import settings
from api.routes import applications, dashboard, jobs, profiles

app = FastAPI(
    title="AI Job Hunter API",
    description="API for AI Job Hunter - Job search, scoring, and ranking platform",
    version="1.0.0",
)


@app.on_event("startup")
async def start_s3_refresh() -> None:
    asyncio.create_task(
        asyncio.to_thread(refresh_loop)
    )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(profiles.router, prefix="/api/v1", tags=["Profiles"])
app.include_router(applications.router, prefix="/api/v1", tags=["Applications"])


@app.get("/")
async def root():
    return {
        "name": "AI Job Hunter API",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}