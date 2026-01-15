"""
Health check endpoints
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check - verifies all dependencies are available.
    """
    checks = {
        "database": True,  # TODO: Implement actual check
        "storage": True,   # TODO: Implement actual check
    }

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check - basic ping"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }
