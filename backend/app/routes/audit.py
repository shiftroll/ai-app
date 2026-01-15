"""
Audit Trail API Routes

Endpoints:
- GET /api/audit/{entity_id} - Get audit trail for an entity
- GET /api/audit/timeline/{entity_type}/{entity_id} - Get timeline view
- POST /api/audit/snapshot/{entity_id} - Generate signed audit snapshot PDF
- GET /api/audit/export - Export audit logs
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.audit_service import (
    get_audit_trail,
    get_audit_timeline,
    generate_audit_snapshot,
    export_audit_logs,
)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SnapshotRequest(BaseModel):
    """Request to generate audit snapshot"""
    entity_type: str
    include_related: bool = True
    sign_with_rsa: bool = True


class AuditExportRequest(BaseModel):
    """Request to export audit logs"""
    entity_types: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = "json"  # json or csv


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/{entity_id}")
async def get_entity_audit_trail(
    entity_id: str,
    entity_type: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> Dict[str, Any]:
    """
    Get audit trail for an entity (contract, invoice, approval, etc.).

    Returns chronological log of all actions taken on the entity.

    **Example Response:**
    ```json
    {
      "entity_id": "inv_20260118_001",
      "entity_type": "invoice",
      "logs": [
        {
          "log_id": "log_001",
          "kind": "generate",
          "actor_id": "agent_v0.1",
          "timestamp": "2026-01-18T07:00:00Z",
          "payload_hash": "sha256:...",
          "explainability_text": "Invoice generated from contract..."
        },
        {
          "log_id": "log_002",
          "kind": "approve",
          "actor_id": "controller@client.com",
          "timestamp": "2026-01-20T09:11:00Z",
          "confidence": 0.93
        }
      ],
      "total": 2
    }
    ```
    """
    logs = await get_audit_trail(
        entity_id=entity_id,
        entity_type=entity_type,
        limit=limit,
    )

    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "logs": logs,
        "total": len(logs),
    }


@router.get("/timeline/{entity_type}/{entity_id}")
async def get_timeline_view(
    entity_type: str,
    entity_id: str,
) -> Dict[str, Any]:
    """
    Get formatted timeline view for UI display.

    Returns a chronological view suitable for the Audit Timeline UI component.

    **Example Response:**
    ```json
    {
      "entity_id": "inv_20260118_001",
      "entity_type": "invoice",
      "timeline": [
        {
          "timestamp": "2026-01-15T10:12:00Z",
          "action": "Contract uploaded",
          "actor": "ridho@example.com",
          "icon": "upload",
          "details": "MSA-ACME.pdf"
        },
        {
          "timestamp": "2026-01-15T10:15:00Z",
          "action": "Contract parsed",
          "actor": "agent_v0.1",
          "icon": "cpu",
          "details": "Extracted 2 billing clauses"
        }
      ]
    }
    ```
    """
    timeline = await get_audit_timeline(entity_type, entity_id)

    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "timeline": timeline,
    }


@router.post("/snapshot/{entity_id}")
async def generate_snapshot(
    entity_id: str,
    request: SnapshotRequest,
    requested_by: str = Query(..., description="User ID requesting snapshot"),
) -> StreamingResponse:
    """
    Generate a signed PDF snapshot of an entity with its audit trail.

    The snapshot includes:
    - Entity data at current state
    - Complete audit trail
    - Related entities (if requested)
    - RSA signature (if enabled)
    - Hash of all included data

    This PDF serves as CFO/auditor-acceptable evidence.

    **Returns:** PDF file stream
    """
    pdf_bytes = await generate_audit_snapshot(
        entity_id=entity_id,
        entity_type=request.entity_type,
        include_related=request.include_related,
        sign_with_rsa=request.sign_with_rsa,
        requested_by=requested_by,
    )

    filename = f"audit_snapshot_{entity_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/export")
async def export_logs(
    request: AuditExportRequest,
    requested_by: str = Query(..., description="User ID requesting export"),
) -> Dict[str, Any]:
    """
    Export audit logs for compliance or analysis.

    **Query Parameters:**
    - `entity_types`: Filter by entity types (contract, invoice, approval)
    - `start_date`: Start of date range
    - `end_date`: End of date range
    - `format`: Output format (json or csv)

    **Example Response (JSON format):**
    ```json
    {
      "export_id": "exp_20260120_001",
      "format": "json",
      "record_count": 150,
      "download_url": "/api/audit/download/exp_20260120_001"
    }
    ```
    """
    result = await export_audit_logs(
        entity_types=request.entity_types,
        start_date=request.start_date,
        end_date=request.end_date,
        format=request.format,
        requested_by=requested_by,
    )

    return result


@router.get("/download/{export_id}")
async def download_export(export_id: str) -> StreamingResponse:
    """
    Download a previously generated export file.
    """
    # TODO: Implement actual file retrieval
    raise HTTPException(status_code=501, detail="Export download not implemented yet")
