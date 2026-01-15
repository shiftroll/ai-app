"""
Approval Service

Business logic for approval management and revocation.
Implements HITL Rule 4: rollback procedure with remediation tickets.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from app.services.database import (
    get_approval_by_id,
    get_approvals_by_invoice,
    save_approval,
    get_invoice_by_id,
    save_invoice,
)

logger = logging.getLogger(__name__)


async def get_approval(approval_id: str) -> Optional[Dict[str, Any]]:
    """Get approval by ID"""
    return await get_approval_by_id(approval_id)


async def get_approvals_for_invoice(invoice_id: str) -> List[Dict[str, Any]]:
    """Get all approvals for an invoice"""
    return await get_approvals_by_invoice(invoice_id)


async def revoke_approval(
    approval_id: str,
    revoker_email: str,
    revoker_name: str,
    revocation_reason: str,
) -> Dict[str, Any]:
    """
    Revoke an approval.

    Implements HITL Rule 4:
    - Marks invoice as "needs_remediation"
    - Creates remediation ticket (placeholder)
    - Preserves full audit trail

    Design Note:
    - In production, integrate with ticketing system (Linear, Asana)
    - Consider adding automatic notification to relevant parties
    - If invoice was pushed to ERP, may need manual reversal steps
    """
    approval = await get_approval_by_id(approval_id)
    if not approval:
        raise ValueError("Approval not found")

    # Update approval record
    approval["revoked"] = True
    approval["revoked_at"] = datetime.utcnow().isoformat()
    approval["revoked_by"] = revoker_email
    approval["revocation_reason"] = revocation_reason

    await save_approval(approval_id, approval)

    # Update associated invoice
    invoice_id = approval.get("invoice_id")
    if invoice_id:
        invoice = await get_invoice_by_id(invoice_id)
        if invoice:
            was_pushed = invoice.get("status") == "pushed"

            invoice["status"] = "needs_remediation"
            invoice["remediation_required"] = True
            invoice["remediation_reason"] = revocation_reason
            invoice["remediation_created_at"] = datetime.utcnow().isoformat()

            # If already pushed to ERP, note that manual remediation needed
            if was_pushed:
                invoice["erp_remediation_required"] = True
                invoice["erp_remediation_note"] = (
                    "Invoice was pushed to ERP before approval revocation. "
                    "Manual correction in ERP system required."
                )

            await save_invoice(invoice_id, invoice)

    logger.info(f"Approval {approval_id} revoked by {revoker_email}: {revocation_reason}")

    return {
        "approval_id": approval_id,
        "revoked": True,
        "revoked_at": approval["revoked_at"],
        "remediation_required": True,
        "invoice_id": invoice_id,
    }
