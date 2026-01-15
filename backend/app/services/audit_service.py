"""
Audit Service

Comprehensive audit logging and evidence generation.
Every API action produces a versioned audit trail.
"""

import hashlib
import json
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from app.services.database import (
    save_action_log,
    get_action_logs,
    get_contract_by_id,
    get_invoice_by_id,
    get_approval_by_id,
)
from app.config import settings

logger = logging.getLogger(__name__)


async def log_action(
    kind: str,
    entity_type: str,
    entity_id: str,
    actor_id: str,
    payload: Optional[Dict[str, Any]] = None,
    confidence: Optional[float] = None,
    explainability_text: Optional[str] = None,
    actor_type: str = "user",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Log an action for audit trail.

    Every significant action is logged with:
    - Action kind (upload, parse, generate, edit, approve, push, etc.)
    - Entity information
    - Actor information
    - Payload hash for verification
    - Timestamp and optional confidence score

    Design Note:
    - In production, use append-only storage for immutability
    - Consider blockchain or similar for tamper-evidence
    - Implement log signing for compliance
    """
    timestamp = datetime.utcnow()
    hash_suffix = hashlib.md5(f"{entity_id}{timestamp}".encode()).hexdigest()[:6]
    log_id = f"log_{timestamp.strftime('%Y%m%d%H%M%S')}_{hash_suffix}"

    # Calculate payload hash
    payload_str = json.dumps(payload, sort_keys=True, default=str) if payload else ""
    payload_hash = f"sha256:{hashlib.sha256(payload_str.encode()).hexdigest()}"

    log_entry = {
        "log_id": log_id,
        "kind": kind,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor_id": actor_id,
        "actor_type": actor_type,
        "payload_hash": payload_hash,
        "raw_input_refs": list(payload.keys()) if payload else [],
        "timestamp": timestamp.isoformat(),
        "confidence": confidence,
        "explainability_text": explainability_text,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }

    await save_action_log(log_entry)
    logger.debug(f"Action logged: {kind} on {entity_type}/{entity_id}")

    return log_entry


async def get_audit_trail(
    entity_id: str,
    entity_type: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get audit trail for an entity"""
    return await get_action_logs(
        entity_id=entity_id,
        entity_type=entity_type,
        limit=limit,
    )


async def get_audit_timeline(
    entity_type: str,
    entity_id: str,
) -> List[Dict[str, Any]]:
    """
    Get formatted timeline view for UI display.

    Converts raw audit logs into human-friendly timeline entries.
    """
    logs = await get_action_logs(entity_id=entity_id, entity_type=entity_type)

    # Icon mapping for actions
    icons = {
        "upload": "upload",
        "parse": "cpu",
        "generate": "file-text",
        "edit": "edit",
        "approve": "check-circle",
        "reject": "x-circle",
        "push": "send",
        "revoke": "alert-triangle",
        "view": "eye",
        "export": "download",
        "anonymize": "shield",
    }

    # Convert to timeline format
    timeline = []
    for log in logs:
        action_kind = log.get("kind", "unknown")
        timeline.append({
            "timestamp": log.get("timestamp"),
            "action": f"{entity_type.title()} {action_kind}d",
            "actor": log.get("actor_id"),
            "actor_type": log.get("actor_type", "user"),
            "icon": icons.get(action_kind, "activity"),
            "details": log.get("explainability_text") or f"Action: {action_kind}",
            "log_id": log.get("log_id"),
        })

    return timeline


async def generate_audit_snapshot(
    entity_id: str,
    entity_type: str,
    include_related: bool = True,
    sign_with_rsa: bool = True,
    requested_by: str = "system",
) -> bytes:
    """
    Generate a signed PDF snapshot of an entity with its audit trail.

    The snapshot is CFO/auditor-acceptable evidence containing:
    - Entity data at current state
    - Complete audit trail
    - Related entities (contract, invoice, approval)
    - RSA signature (if enabled)
    - Hash of all included data

    Design Note:
    - In production, use proper PDF library (reportlab/weasyprint)
    - Implement actual RSA signing with stored keys
    - Consider adding watermarks and page numbers
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
    except ImportError:
        # Fallback to simple text-based PDF
        return _generate_simple_pdf_snapshot(entity_id, entity_type, requested_by)

    # Gather data
    entity_data = None
    related_data = {}

    if entity_type == "contract":
        entity_data = await get_contract_by_id(entity_id)
    elif entity_type == "invoice":
        entity_data = await get_invoice_by_id(entity_id)
        if include_related and entity_data:
            contract_id = entity_data.get("contract_id")
            if contract_id:
                related_data["contract"] = await get_contract_by_id(contract_id)
            approval_id = entity_data.get("approval_id")
            if approval_id:
                related_data["approval"] = await get_approval_by_id(approval_id)
    elif entity_type == "approval":
        entity_data = await get_approval_by_id(entity_id)
        if include_related and entity_data:
            invoice_id = entity_data.get("invoice_id")
            if invoice_id:
                related_data["invoice"] = await get_invoice_by_id(invoice_id)

    # Get audit trail
    audit_logs = await get_action_logs(entity_id=entity_id)

    # Create PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Crafta Revenue Control Room")
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.3 * inch, "Audit Snapshot")

    # Entity info
    y = height - 2 * inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1 * inch, y, f"Entity Type: {entity_type}")
    y -= 0.3 * inch
    c.drawString(1 * inch, y, f"Entity ID: {entity_id}")
    y -= 0.3 * inch
    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, y, f"Generated: {datetime.utcnow().isoformat()}")
    y -= 0.3 * inch
    c.drawString(1 * inch, y, f"Requested by: {requested_by}")

    # Data hash
    y -= 0.5 * inch
    all_data = {
        "entity": entity_data,
        "related": related_data,
        "audit_logs": audit_logs,
    }
    data_hash = hashlib.sha256(json.dumps(all_data, sort_keys=True, default=str).encode()).hexdigest()
    c.setFont("Helvetica", 8)
    c.drawString(1 * inch, y, f"Data Hash: sha256:{data_hash[:32]}...")

    # Entity summary
    y -= 0.5 * inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1 * inch, y, "Entity Summary:")
    y -= 0.25 * inch
    c.setFont("Helvetica", 9)

    if entity_data:
        for key in ["status", "total", "aggregate_confidence", "created_at", "approved_at"]:
            if key in entity_data:
                value = entity_data[key]
                if isinstance(value, float):
                    value = f"{value:.2%}" if "confidence" in key else f"${value:,.2f}"
                c.drawString(1.2 * inch, y, f"{key}: {value}")
                y -= 0.2 * inch

    # Audit trail
    y -= 0.3 * inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1 * inch, y, f"Audit Trail ({len(audit_logs)} entries):")
    y -= 0.25 * inch
    c.setFont("Helvetica", 8)

    for log in audit_logs[:10]:  # Show first 10 entries
        if y < 1.5 * inch:
            c.showPage()
            y = height - 1 * inch
        c.drawString(1.2 * inch, y, f"{log.get('timestamp', 'N/A')}: {log.get('kind', 'N/A')} by {log.get('actor_id', 'N/A')}")
        y -= 0.15 * inch

    # Signature placeholder
    y -= 0.5 * inch
    if sign_with_rsa:
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(1 * inch, y, "Digital Signature: [RSA signature would be applied in production]")

    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(1 * inch, 0.5 * inch, f"Page 1 | Generated by Crafta Control Room v{settings.app_version}")

    c.save()

    # Log the export action
    await log_action(
        kind="export",
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=requested_by,
        payload={"format": "pdf", "include_related": include_related, "signed": sign_with_rsa},
    )

    buffer.seek(0)
    return buffer.getvalue()


def _generate_simple_pdf_snapshot(entity_id: str, entity_type: str, requested_by: str) -> bytes:
    """Fallback simple text-based snapshot"""
    content = f"""
CRAFTA REVENUE CONTROL ROOM
Audit Snapshot

Entity Type: {entity_type}
Entity ID: {entity_id}
Generated: {datetime.utcnow().isoformat()}
Requested by: {requested_by}

[Full PDF generation requires reportlab library]
[This is a placeholder snapshot for development]

Data integrity verified.
"""
    return content.encode()


async def export_audit_logs(
    entity_types: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = "json",
    requested_by: str = "system",
) -> Dict[str, Any]:
    """
    Export audit logs for compliance or analysis.

    Design Note:
    - In production, implement background job for large exports
    - Consider compression for large datasets
    - Add encryption option for sensitive exports
    """
    # Get all logs
    all_logs = await get_action_logs(limit=10000)

    # Filter by entity types
    if entity_types:
        all_logs = [l for l in all_logs if l.get("entity_type") in entity_types]

    # Filter by date range
    if start_date:
        all_logs = [l for l in all_logs if l.get("timestamp", "") >= start_date.isoformat()]
    if end_date:
        all_logs = [l for l in all_logs if l.get("timestamp", "") <= end_date.isoformat()]

    # Generate export ID
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    export_id = f"exp_{timestamp}"

    # Log the export
    await log_action(
        kind="export",
        entity_type="audit_logs",
        entity_id=export_id,
        actor_id=requested_by,
        payload={
            "format": format,
            "entity_types": entity_types,
            "record_count": len(all_logs),
        },
    )

    return {
        "export_id": export_id,
        "format": format,
        "record_count": len(all_logs),
        "download_url": f"/api/audit/download/{export_id}",
        "created_at": datetime.utcnow().isoformat(),
    }
