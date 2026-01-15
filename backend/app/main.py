"""
Crafta Revenue Control Room - Main FastAPI Application

Entry point for the backend API server.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import (
    contracts,
    workevents,
    invoices,
    approval,
    audit,
    erp,
    health,
)
from app.services.database import init_db, close_db
from app.services.logging_service import setup_logging, log_request

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Crafta Control Room API")

    # Create upload directory
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Initialize database
    await init_db()

    yield

    # Shutdown
    logger.info("Shutting down Crafta Control Room API")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Crafta Revenue Control Room API

    A human-in-the-loop contract-to-invoice automation platform.

    ## Features
    - Contract upload and AI-powered parsing
    - Invoice draft generation with explainability
    - Approval workflows with audit trail
    - ERP integration (QuickBooks, Xero, NetSuite)

    ## Important
    - No automatic ERP posting without human approval
    - All actions are logged for audit compliance
    - Low-confidence items flagged for review
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()

    # Process request
    response = await call_next(request)

    # Log request
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    log_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        client_ip=request.client.host if request.client else None,
    )

    return response


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["Contracts"])
app.include_router(workevents.router, prefix="/api/workevents", tags=["Work Events"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(approval.router, prefix="/api/approval", tags=["Approval"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(erp.router, prefix="/api/erp", tags=["ERP Integration"])


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """API root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "message": "Welcome to Crafta Revenue Control Room API",
        "note": "This is a supervised invoice automation platform. Human approval is required before posting to ERP.",
    }


# Static files for uploads (in development)
if settings.debug:
    os.makedirs(settings.upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
