"""
Invoice Management API Routes

Endpoints:
- POST /api/invoices/draft - Generate invoice draft(s) for a contract
- GET /api/invoices/{id} - Read invoice draft
- GET /api/invoices - List all invoice drafts
- PUT /api/invoices/{id} - Update invoice draft
- POST /api/invoices/{id}/approve - Approve invoice (creates ApprovalLog)
- POST /api/invoices/{id}/reject - Reject invoice
- POST /api/invoices/{id}/push - Push to ERP (requires approval)
"""

import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr

from app.config import settings
from app.services.audit_service import log_action
from app.services.invoice_service import (
    generate_invoice_draft,
    get_invoice,
    list_invoices,
    update_invoice,
    approve_invoice,
    reject_invoice,
)
from app.services.contract_service import get_contract
from app.services.workevent_service import get_work_events
from app.services.erp_service import push_invoice_to_erp

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class GenerateDraftRequest(BaseModel):
    """Request to generate invoice draft"""
    contract_id: str
    event_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific event IDs to include. If None, includes all unbilled events."
    )
    invoice_date: Optional[datetime] = None
    tax_rate: float = Field(default=0.0, ge=0, le=1)


class InvoiceLineUpdate(BaseModel):
    """Update for a single invoice line"""
    line_id: str
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    reviewed: bool = Field(default=False, description="Mark line as reviewed")


class InvoiceUpdateRequest(BaseModel):
    """Request to update invoice"""
    lines: Optional[List[InvoiceLineUpdate]] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Request to approve invoice"""
    approver_email: EmailStr
    approver_name: str
    approval_note: Optional[str] = None
    confirm_reviewed: bool = Field(..., description="Must be True to approve")
    two_fa_code: Optional[str] = Field(default=None, description="Optional 2FA code")


class RejectRequest(BaseModel):
    """Request to reject invoice"""
    rejector_email: EmailStr
    rejector_name: str
    rejection_reason: str


class PushToERPRequest(BaseModel):
    """Request to push invoice to ERP"""
    erp_type: str = Field(..., description="quickbooks, xero, or netsuite")
    approval_id: str
    customer_ref: str
    auto_push: bool = Field(
        default=False,
        description="MUST be False in Phase 1. Set True only for trusted low-risk automation."
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/draft")
async def create_invoice_draft(
    request: GenerateDraftRequest,
    drafted_by: str = Query(..., description="User or agent ID generating draft"),
) -> Dict[str, Any]:
    """
    Generate invoice draft(s) for a contract.

    Takes contract terms and work events, generates draft invoice lines
    with explainability and confidence scores.

    **HITL Rules Applied:**
    - Lines < 80% confidence flagged as exceptions
    - Rev-rec sensitive items require CFO approval
    - No auto-posting to ERP

    **Example Request:**
    ```json
    {
      "contract_id": "ctr_20260115_001",
      "event_ids": ["we_001", "we_002"],
      "tax_rate": 0.0
    }
    ```

    **Example Response:**
    ```json
    {
      "invoice_id": "inv_20260118_001",
      "contract_id": "ctr_20260115_001",
      "lines": [...],
      "subtotal": 2000,
      "tax": 0,
      "total": 2000,
      "status": "draft",
      "explainability": "...",
      "aggregate_confidence": 0.93
    }
    ```
    """
    # Get contract
    contract = await get_contract(request.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get work events
    events_result = await get_work_events(request.contract_id)
    events = events_result.get("events", [])

    # Filter to specific events if requested
    if request.event_ids:
        events = [e for e in events if e.get("event_id") in request.event_ids]

    if not events:
        raise HTTPException(status_code=400, detail="No work events found for invoice generation")

    # Generate draft
    invoice = await generate_invoice_draft(
        contract=contract,
        work_events=events,
        drafted_by=drafted_by,
        invoice_date=request.invoice_date,
        tax_rate=request.tax_rate,
    )

    # Log action
    await log_action(
        kind="generate",
        entity_type="invoice",
        entity_id=invoice["invoice_id"],
        actor_id=drafted_by,
        payload={
            "contract_id": request.contract_id,
            "event_count": len(events),
            "total": float(invoice["total"]),
        },
    )

    return invoice


@router.get("/{invoice_id}")
async def get_invoice_by_id(invoice_id: str) -> Dict[str, Any]:
    """
    Retrieve an invoice draft by ID.

    Includes all line items, explainability, and audit information.
    """
    invoice = await get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("")
async def list_all_invoices(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    contract_id: Optional[str] = Query(default=None, description="Filter by contract"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """
    List all invoice drafts with optional filtering.

    **Query Parameters:**
    - `status`: Filter by status (draft, pending_review, exception, approved, pushed)
    - `contract_id`: Filter by contract ID
    - `limit`: Maximum results
    - `offset`: Pagination offset
    """
    result = await list_invoices(
        status=status,
        contract_id=contract_id,
        limit=limit,
        offset=offset,
    )
    return result


@router.put("/{invoice_id}")
async def update_invoice_draft(
    invoice_id: str,
    update: InvoiceUpdateRequest,
    updated_by: str = Query(..., description="User ID making the update"),
) -> Dict[str, Any]:
    """
    Update an invoice draft.

    Used for manual corrections before approval.
    All changes are logged.
    """
    invoice = await get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.get("status") in ["approved", "pushed"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify approved or pushed invoices"
        )

    updated = await update_invoice(
        invoice_id=invoice_id,
        update_data=update.dict(exclude_none=True),
        updated_by=updated_by,
    )

    # Log action
    await log_action(
        kind="edit",
        entity_type="invoice",
        entity_id=invoice_id,
        actor_id=updated_by,
        payload=update.dict(exclude_none=True),
    )

    return {
        "message": "Invoice updated successfully",
        "invoice_id": invoice_id,
    }


@router.post("/{invoice_id}/approve")
async def approve_invoice_endpoint(
    invoice_id: str,
    request: ApprovalRequest,
) -> Dict[str, Any]:
    """
    Approve an invoice draft.

    Creates an ApprovalLog with:
    - Approver identity and timestamp
    - Signature hash
    - Confidence snapshot
    - Invoice state hash

    **Requirements:**
    - `confirm_reviewed` must be True
    - Invoice must be in draft or pending_review status
    - For rev-rec sensitive items, approver must have CFO role

    **Example Request:**
    ```json
    {
      "approver_email": "controller@client.com",
      "approver_name": "Jane Doe",
      "approval_note": "Reviewed. OK to push.",
      "confirm_reviewed": true
    }
    ```

    **Example Response:**
    ```json
    {
      "approval_id": "app_20260120_001",
      "invoice_id": "inv_20260118_001",
      "status": "approved",
      "message": "Invoice approved. Ready for ERP push."
    }
    ```
    """
    if not request.confirm_reviewed:
        raise HTTPException(
            status_code=400,
            detail="You must confirm you have reviewed this invoice (confirm_reviewed=true)"
        )

    invoice = await get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.get("status") not in ["draft", "pending_review", "exception"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve invoice with status: {invoice.get('status')}"
        )

    # Check if any lines require CFO approval
    requires_cfo = any(
        line.get("requires_cfo_approval") for line in invoice.get("lines", [])
    )
    # TODO: Verify approver role if requires_cfo

    # Create approval
    approval = await approve_invoice(
        invoice_id=invoice_id,
        approver_email=request.approver_email,
        approver_name=request.approver_name,
        approval_note=request.approval_note,
        two_fa_code=request.two_fa_code,
    )

    # Log action
    await log_action(
        kind="approve",
        entity_type="invoice",
        entity_id=invoice_id,
        actor_id=request.approver_email,
        payload={
            "approval_id": approval["approval_id"],
            "note": request.approval_note,
        },
        confidence=invoice.get("aggregate_confidence"),
    )

    return {
        "approval_id": approval["approval_id"],
        "invoice_id": invoice_id,
        "status": "approved",
        "approved_at": approval["approved_at"],
        "message": "Invoice approved. Ready for ERP push.",
    }


@router.post("/{invoice_id}/reject")
async def reject_invoice_endpoint(
    invoice_id: str,
    request: RejectRequest,
) -> Dict[str, Any]:
    """
    Reject an invoice draft.

    Moves invoice to rejected status with reason.
    """
    invoice = await get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    await reject_invoice(
        invoice_id=invoice_id,
        rejector_email=request.rejector_email,
        rejector_name=request.rejector_name,
        rejection_reason=request.rejection_reason,
    )

    # Log action
    await log_action(
        kind="reject",
        entity_type="invoice",
        entity_id=invoice_id,
        actor_id=request.rejector_email,
        payload={"reason": request.rejection_reason},
    )

    return {
        "invoice_id": invoice_id,
        "status": "rejected",
        "message": "Invoice rejected",
    }


@router.post("/{invoice_id}/push")
async def push_to_erp_endpoint(
    invoice_id: str,
    request: PushToERPRequest,
) -> Dict[str, Any]:
    """
    Push approved invoice to ERP system.

    **CRITICAL: Requires prior approval.**
    - `approval_id` must be valid and not revoked
    - `auto_push` must be False in Phase 1

    Supported ERPs:
    - quickbooks
    - xero
    - netsuite

    **Example Request:**
    ```json
    {
      "erp_type": "quickbooks",
      "approval_id": "app_20260120_001",
      "customer_ref": "BLUE-900",
      "auto_push": false
    }
    ```

    **Example Response:**
    ```json
    {
      "invoice_id": "inv_20260118_001",
      "erp_invoice_id": "QB-12345",
      "status": "pushed",
      "message": "Invoice successfully pushed to QuickBooks"
    }
    ```
    """
    # HITL Rule 1: No auto-post without explicit approval
    if request.auto_push:
        raise HTTPException(
            status_code=400,
            detail="Auto-push is disabled in Phase 1. All invoices require manual approval."
        )

    invoice = await get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.get("status") != "approved":
        raise HTTPException(
            status_code=400,
            detail="Invoice must be approved before pushing to ERP"
        )

    if invoice.get("approval_id") != request.approval_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid approval_id"
        )

    # Push to ERP
    result = await push_invoice_to_erp(
        invoice=invoice,
        erp_type=request.erp_type,
        customer_ref=request.customer_ref,
    )

    # Log action
    await log_action(
        kind="push",
        entity_type="invoice",
        entity_id=invoice_id,
        actor_id=invoice.get("approved_by", "system"),
        payload={
            "erp_type": request.erp_type,
            "erp_invoice_id": result.get("erp_invoice_id"),
            "approval_id": request.approval_id,
        },
    )

    return {
        "invoice_id": invoice_id,
        "erp_invoice_id": result.get("erp_invoice_id"),
        "status": "pushed",
        "pushed_at": datetime.utcnow().isoformat(),
        "message": f"Invoice successfully pushed to {request.erp_type}",
    }
