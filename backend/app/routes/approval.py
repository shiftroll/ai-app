"""
Approval Management API Routes

Endpoints:
- GET /api/approval/{approval_id} - Get approval details
- GET /api/approval/invoice/{invoice_id} - Get approvals for an invoice
- POST /api/approval/{approval_id}/revoke - Revoke an approval
"""

from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr

from app.services.audit_service import log_action
from app.services.approval_service import (
    get_approval,
    get_approvals_for_invoice,
    revoke_approval,
)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RevokeApprovalRequest(BaseModel):
    """Request to revoke an approval"""
    revoker_email: EmailStr
    revoker_name: str
    revocation_reason: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/{approval_id}")
async def get_approval_by_id(approval_id: str) -> Dict[str, Any]:
    """
    Get approval details by ID.

    Returns the full ApprovalLog including:
    - Approver identity
    - Timestamp
    - Signature hash
    - Confidence snapshot
    - Revocation status

    **Example Response:**
    ```json
    {
      "approval_id": "app_20260120_001",
      "invoice_id": "inv_20260118_001",
      "approver": "controller@client.com",
      "approver_name": "Jane Doe",
      "approved_at": "2026-01-20T09:11:00Z",
      "approval_note": "Reviewed. OK to push.",
      "signature_hash": "sha256:...",
      "approval_method": "UI-click",
      "approval_confidence_snapshot": 0.93,
      "revoked": false
    }
    ```
    """
    approval = await get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.get("/invoice/{invoice_id}")
async def get_invoice_approvals(invoice_id: str) -> Dict[str, Any]:
    """
    Get all approvals for an invoice.

    Returns history of approvals including any revoked ones.
    """
    approvals = await get_approvals_for_invoice(invoice_id)
    return {
        "invoice_id": invoice_id,
        "approvals": approvals,
        "count": len(approvals),
    }


@router.post("/{approval_id}/revoke")
async def revoke_approval_endpoint(
    approval_id: str,
    request: RevokeApprovalRequest,
) -> Dict[str, Any]:
    """
    Revoke an approval.

    **HITL Rule 4:** Revoked approvals mark the invoice as "needs manual remediation"
    and produce a remediation ticket.

    This should be used when:
    - An error is discovered after approval
    - The invoice was pushed but needs correction
    - Audit requirements necessitate reversal

    **Example Request:**
    ```json
    {
      "revoker_email": "cfo@client.com",
      "revoker_name": "John CFO",
      "revocation_reason": "Discovered billing error in line 3"
    }
    ```

    **Example Response:**
    ```json
    {
      "approval_id": "app_20260120_001",
      "status": "revoked",
      "revoked_at": "2026-01-21T10:00:00Z",
      "remediation_required": true,
      "message": "Approval revoked. Invoice marked for remediation."
    }
    ```
    """
    approval = await get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.get("revoked"):
        raise HTTPException(status_code=400, detail="Approval already revoked")

    result = await revoke_approval(
        approval_id=approval_id,
        revoker_email=request.revoker_email,
        revoker_name=request.revoker_name,
        revocation_reason=request.revocation_reason,
    )

    # Log action
    await log_action(
        kind="revoke",
        entity_type="approval",
        entity_id=approval_id,
        actor_id=request.revoker_email,
        payload={
            "reason": request.revocation_reason,
            "invoice_id": approval.get("invoice_id"),
        },
    )

    return {
        "approval_id": approval_id,
        "status": "revoked",
        "revoked_at": result.get("revoked_at"),
        "remediation_required": result.get("remediation_required", True),
        "message": "Approval revoked. Invoice marked for remediation.",
    }
