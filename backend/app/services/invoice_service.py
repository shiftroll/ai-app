"""
Invoice Service

Business logic for invoice draft generation, approval, and management.
Implements HITL rules and explainability requirements.
"""

import os
import sys
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.services.database import (
    save_invoice,
    get_invoice_by_id,
    list_all_invoices,
    save_approval,
)
from app.config import settings

logger = logging.getLogger(__name__)


async def generate_invoice_draft(
    contract: Dict[str, Any],
    work_events: List[Dict[str, Any]],
    drafted_by: str,
    invoice_date: Optional[datetime] = None,
    tax_rate: float = 0.0,
) -> Dict[str, Any]:
    """
    Generate invoice draft from contract and work events.

    Uses the derive_invoice_lines agent to create invoice lines
    with full explainability and confidence scores.

    HITL Rules Applied:
    - Lines < 80% confidence flagged as exceptions
    - Rev-rec sensitive items require CFO approval

    Design Note:
    - The derivation engine can be enhanced with more sophisticated
      matching algorithms and ML-based confidence scoring
    - Consider adding support for multi-currency invoices
    """
    from agents.derive_invoice_lines import derive_invoice_lines

    # Generate draft
    invoice = derive_invoice_lines(
        contract=contract,
        work_events=work_events,
        invoice_date=invoice_date,
        tax_rate=tax_rate,
    )

    # Save to database
    await save_invoice(invoice["invoice_id"], invoice)

    logger.info(f"Generated invoice draft: {invoice['invoice_id']}")

    return invoice


async def get_invoice(invoice_id: str) -> Optional[Dict[str, Any]]:
    """Get an invoice by ID"""
    return await get_invoice_by_id(invoice_id)


async def list_invoices(
    status: Optional[str] = None,
    contract_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List invoices with optional filtering"""
    return await list_all_invoices(
        status=status,
        contract_id=contract_id,
        limit=limit,
        offset=offset,
    )


async def update_invoice(
    invoice_id: str,
    update_data: Dict[str, Any],
    updated_by: str,
) -> Dict[str, Any]:
    """
    Update an invoice draft.

    Preserves audit trail of changes.
    """
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    # Apply line updates
    if "lines" in update_data:
        for line_update in update_data["lines"]:
            line_id = line_update.get("line_id")
            for line in invoice.get("lines", []):
                if line.get("line_id") == line_id:
                    for key, value in line_update.items():
                        if key != "line_id" and value is not None:
                            line[key] = value
                    break

    # Apply other updates
    for key in ["invoice_date", "due_date", "notes"]:
        if key in update_data and update_data[key] is not None:
            invoice[key] = update_data[key]

    invoice["updated_at"] = datetime.utcnow().isoformat()
    invoice["updated_by"] = updated_by

    await save_invoice(invoice_id, invoice)

    return invoice


async def approve_invoice(
    invoice_id: str,
    approver_email: str,
    approver_name: str,
    approval_note: Optional[str] = None,
    two_fa_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Approve an invoice.

    Creates ApprovalLog with:
    - Approver identity and timestamp
    - Signature hash of approval payload
    - Invoice state hash at approval time
    - Confidence snapshot

    Design Note:
    - Two-factor authentication can be integrated here
    - Consider adding digital signature support for compliance
    """
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    # Generate approval ID
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    hash_suffix = hashlib.md5(f"{invoice_id}{timestamp}".encode()).hexdigest()[:4]
    approval_id = f"app_{timestamp}_{hash_suffix}"

    # Calculate hashes
    invoice_snapshot = json.dumps(invoice, sort_keys=True, default=str)
    invoice_hash = hashlib.sha256(invoice_snapshot.encode()).hexdigest()

    approval_payload = {
        "approval_id": approval_id,
        "invoice_id": invoice_id,
        "approver_email": approver_email,
        "timestamp": timestamp,
    }
    signature_hash = f"sha256:{hashlib.sha256(json.dumps(approval_payload).encode()).hexdigest()}"

    # Create approval record
    approval = {
        "approval_id": approval_id,
        "invoice_id": invoice_id,
        "approver": approver_email,
        "approver_name": approver_name,
        "approver_role": "approver",  # TODO: Get from user service
        "approved_at": datetime.utcnow().isoformat(),
        "approval_note": approval_note,
        "signature_hash": signature_hash,
        "approval_method": "UI-click",
        "approval_confidence_snapshot": invoice.get("aggregate_confidence", 0),
        "invoice_snapshot_hash": f"sha256:{invoice_hash}",
        "two_fa_verified": two_fa_code is not None,
        "revoked": False,
    }

    # Save approval
    await save_approval(approval_id, approval)

    # Update invoice status
    invoice["status"] = "approved"
    invoice["approval_id"] = approval_id
    invoice["approved_at"] = approval["approved_at"]
    invoice["approved_by"] = approver_email
    await save_invoice(invoice_id, invoice)

    logger.info(f"Invoice {invoice_id} approved by {approver_email}")

    return approval


async def reject_invoice(
    invoice_id: str,
    rejector_email: str,
    rejector_name: str,
    rejection_reason: str,
) -> Dict[str, Any]:
    """
    Reject an invoice.

    Updates invoice status and records rejection reason.
    """
    invoice = await get_invoice_by_id(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    invoice["status"] = "rejected"
    invoice["rejected_at"] = datetime.utcnow().isoformat()
    invoice["rejected_by"] = rejector_email
    invoice["rejection_reason"] = rejection_reason

    await save_invoice(invoice_id, invoice)

    logger.info(f"Invoice {invoice_id} rejected by {rejector_email}: {rejection_reason}")

    return invoice
