"""
Crafta Revenue Control Room - JSON Schemas & Pydantic Models

These schemas define the core data structures for:
- Contract: Parsed contract with terms and clauses
- ContractClause: Individual extracted clause with confidence
- WorkEvent: Billing events from timesheets/systems
- InvoiceDraft: Generated invoice with explainability
- ApprovalLog: Human approval audit record
- ERPInvoicePayload: Formatted payload for ERP systems
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field, EmailStr


# =============================================================================
# ENUMS
# =============================================================================

class ContractStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"
    ARCHIVED = "archived"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    EXCEPTION = "exception"
    APPROVED = "approved"
    PUSHED = "pushed"
    REJECTED = "rejected"


class ClauseType(str, Enum):
    RATE_CARD = "rate_card"
    MILESTONE_PAYMENT = "milestone_payment"
    FIXED_FEE = "fixed_fee"
    RECURRING_FEE = "recurring_fee"
    PENALTY = "penalty"
    DISCOUNT = "discount"
    PAYMENT_TERMS = "payment_terms"
    REV_REC = "rev_rec"  # Revenue recognition clause
    OTHER = "other"


class ApprovalMethod(str, Enum):
    UI_CLICK = "UI-click"
    API = "API"
    BATCH = "batch"
    TWO_FA = "2FA"


class UserRole(str, Enum):
    VIEWER = "viewer"
    APPROVER = "approver"
    ADMIN = "admin"
    CFO = "cfo"


# =============================================================================
# CONTRACT SCHEMAS
# =============================================================================

class Party(BaseModel):
    """Contract party (vendor/client)"""
    role: str = Field(..., description="Party role: vendor, client, etc.")
    name: str = Field(..., description="Party name")
    identifier: str = Field(..., description="Internal identifier")


class ContractClause(BaseModel):
    """
    Individual extracted clause from a contract.

    Sample:
    {
        "clause_id": "c1",
        "type": "rate_card",
        "description": "Rate for consulting: $200/hour",
        "extracted_text": "Consultant rate is Two Hundred US Dollars per hour...",
        "value": "200",
        "unit": "hour",
        "confidence": 0.92
    }
    """
    clause_id: str = Field(..., description="Unique clause identifier")
    type: ClauseType = Field(..., description="Type of clause")
    description: str = Field(..., description="Human-readable description")
    extracted_text: str = Field(..., description="Raw text from contract")
    value: str = Field(..., description="Extracted value")
    unit: str = Field(..., description="Unit type: hour, fixed, monthly, etc.")
    confidence: float = Field(..., ge=0, le=1, description="Extraction confidence 0-1")

    # Optional fields for rev-rec sensitivity
    requires_cfo_approval: bool = Field(default=False)
    rev_rec_treatment: Optional[str] = None


class Contract(BaseModel):
    """
    Parsed contract with all extracted terms.

    Sample:
    {
        "contract_id": "ctr_20260115_001",
        "source_filename": "MSA-ACME.pdf",
        "uploaded_by": "u:ridho@example.com",
        "upload_time": "2026-01-15T10:12:00Z",
        "parties": [...],
        "currency": "USD",
        "terms": [...],
        "raw_text": "...",
        "parse_version": "v0.1",
        "status": "parsed"
    }
    """
    contract_id: str = Field(..., description="Unique contract identifier")
    source_filename: str = Field(..., description="Original filename")
    uploaded_by: str = Field(..., description="User ID who uploaded")
    upload_time: datetime = Field(..., description="Upload timestamp")
    parties: List[Party] = Field(default_factory=list, description="Contract parties")
    currency: str = Field(default="USD", description="Contract currency")
    terms: List[ContractClause] = Field(default_factory=list, description="Extracted terms")
    raw_text: Optional[str] = Field(None, description="Full extracted text")
    parse_version: str = Field(default="v0.1", description="Parser version")
    status: ContractStatus = Field(default=ContractStatus.UPLOADED)

    # Metadata
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    total_contract_value: Optional[Decimal] = None
    payment_terms_days: Optional[int] = Field(default=30)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# WORK EVENT SCHEMAS
# =============================================================================

class WorkEvent(BaseModel):
    """
    Billing event from timesheet or external system.

    CSV columns: event_id, date, description, units, unit_type, amount, external_ref

    Sample:
    {
        "event_id": "we_001",
        "date": "2025-12-12",
        "description": "Consulting hours for Dec",
        "units": 10,
        "unit_type": "hour",
        "amount": 2000,
        "external_ref": "PO-778"
    }
    """
    event_id: str = Field(..., description="Unique event identifier")
    contract_id: str = Field(..., description="Associated contract ID")
    date: datetime = Field(..., description="Event date")
    description: str = Field(..., description="Event description")
    units: Decimal = Field(..., description="Quantity of units")
    unit_type: str = Field(..., description="Type of unit: hour, day, item, etc.")
    amount: Optional[Decimal] = Field(None, description="Pre-calculated amount if any")
    external_ref: Optional[str] = Field(None, description="External reference (PO, etc.)")

    # Audit
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: Optional[str] = None


# =============================================================================
# INVOICE SCHEMAS
# =============================================================================

class InvoiceLine(BaseModel):
    """Individual invoice line item with explainability"""
    line_id: str = Field(..., description="Unique line identifier")
    description: str = Field(..., description="Line description")
    quantity: Decimal = Field(..., description="Quantity")
    unit: str = Field(..., description="Unit type")
    unit_price: Decimal = Field(..., description="Price per unit")
    amount: Decimal = Field(..., description="Line total")

    # Explainability
    source_clause_id: str = Field(..., description="Contract clause this derives from")
    source_event_ids: List[str] = Field(default_factory=list, description="Work events")
    explain: str = Field(..., description="Human-readable explanation")
    agent_reasoning: Optional[str] = Field(None, description="Detailed agent reasoning")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")

    # Flags
    is_exception: bool = Field(default=False)
    exception_reason: Optional[str] = None
    requires_cfo_approval: bool = Field(default=False)


class InvoiceDraft(BaseModel):
    """
    Generated invoice draft with full explainability.

    Sample:
    {
        "invoice_id": "inv_20260118_001",
        "contract_id": "ctr_20260115_001",
        "drafted_by": "agent_v0.1",
        "lines": [...],
        "subtotal": 2000,
        "tax": 0,
        "total": 2000,
        "status": "draft",
        "created_at": "2026-01-18T07:00:00Z",
        "explainability": "Invoice lines derived from clause c1 and work events we_001..."
    }
    """
    invoice_id: str = Field(..., description="Unique invoice identifier")
    contract_id: str = Field(..., description="Associated contract ID")
    drafted_by: str = Field(..., description="Agent or user who drafted")

    # Line items
    lines: List[InvoiceLine] = Field(default_factory=list)

    # Totals
    subtotal: Decimal = Field(..., description="Sum of line amounts")
    tax: Decimal = Field(default=Decimal("0"), description="Tax amount")
    total: Decimal = Field(..., description="Total invoice amount")

    # Dates
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None

    # Status
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT)

    # Explainability
    explainability: str = Field(..., description="Overall explanation")
    aggregate_confidence: float = Field(..., ge=0, le=1)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Approval tracking
    approval_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

    # ERP tracking
    erp_invoice_id: Optional[str] = None
    pushed_at: Optional[datetime] = None


# =============================================================================
# APPROVAL SCHEMAS
# =============================================================================

class ApprovalLog(BaseModel):
    """
    Human approval audit record.

    Sample:
    {
        "approval_id": "app_20260120_001",
        "invoice_id": "inv_20260118_001",
        "approver": "controller@client.com",
        "approver_name": "Jane Doe",
        "approved_at": "2026-01-20T09:11:00Z",
        "approval_note": "Reviewed. OK to push.",
        "signature_hash": "sha256:...",
        "approval_method": "UI-click",
        "approval_confidence_snapshot": 0.93
    }
    """
    approval_id: str = Field(..., description="Unique approval identifier")
    invoice_id: str = Field(..., description="Associated invoice ID")

    # Approver info
    approver: EmailStr = Field(..., description="Approver email")
    approver_name: str = Field(..., description="Approver display name")
    approver_role: UserRole = Field(default=UserRole.APPROVER)

    # Approval details
    approved_at: datetime = Field(..., description="Approval timestamp")
    approval_note: Optional[str] = Field(None, description="Approver notes")
    signature_hash: str = Field(..., description="SHA256 of approval payload")
    approval_method: ApprovalMethod = Field(default=ApprovalMethod.UI_CLICK)

    # Snapshot
    approval_confidence_snapshot: float = Field(..., ge=0, le=1)
    invoice_snapshot_hash: str = Field(..., description="Hash of invoice at approval time")

    # Two-factor (if used)
    two_fa_verified: bool = Field(default=False)

    # Revocation
    revoked: bool = Field(default=False)
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None


# =============================================================================
# ERP PAYLOAD SCHEMAS
# =============================================================================

class ERPInvoiceLine(BaseModel):
    """ERP invoice line item"""
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Optional[Decimal] = None
    taxable: bool = Field(default=False)
    tax_code: Optional[str] = None
    account_ref: Optional[str] = None
    item_ref: Optional[str] = None


class ERPInvoicePayload(BaseModel):
    """
    Formatted payload for ERP systems (QuickBooks-like).

    Sample:
    {
        "customer_ref": "BLUE-900",
        "lines": [...],
        "invoice_date": "2026-01-20",
        "due_date": "2026-02-19",
        "memo": "Generated by Crafta Control Room; pilot id pilot_001"
    }
    """
    # References
    customer_ref: str = Field(..., description="Customer identifier in ERP")
    vendor_ref: Optional[str] = None

    # Lines
    lines: List[ERPInvoiceLine] = Field(default_factory=list)

    # Dates
    invoice_date: datetime = Field(..., description="Invoice date")
    due_date: datetime = Field(..., description="Payment due date")

    # Amounts
    subtotal: Optional[Decimal] = None
    tax_total: Optional[Decimal] = None
    total: Optional[Decimal] = None

    # Metadata
    memo: Optional[str] = Field(None, description="Invoice memo/notes")
    reference_number: Optional[str] = None
    po_number: Optional[str] = None

    # Crafta tracking
    crafta_invoice_id: str = Field(..., description="Internal invoice ID")
    crafta_approval_id: str = Field(..., description="Internal approval ID")
    pilot_id: Optional[str] = None


# =============================================================================
# ACTION LOG SCHEMAS
# =============================================================================

class ActionKind(str, Enum):
    UPLOAD = "upload"
    PARSE = "parse"
    GENERATE = "generate"
    EDIT = "edit"
    APPROVE = "approve"
    REJECT = "reject"
    PUSH = "push"
    REVOKE = "revoke"
    VIEW = "view"
    EXPORT = "export"
    ANONYMIZE = "anonymize"


class ActionLog(BaseModel):
    """Audit log entry for any action"""
    log_id: str = Field(..., description="Unique log identifier")
    kind: ActionKind = Field(..., description="Type of action")
    entity_type: str = Field(..., description="contract, invoice, etc.")
    entity_id: str = Field(..., description="ID of affected entity")

    # Actor
    actor_id: str = Field(..., description="User or agent ID")
    actor_type: str = Field(default="user", description="user, agent, system")
    actor_email: Optional[str] = None

    # Payload
    payload_hash: str = Field(..., description="SHA256 of action payload")
    raw_input_refs: List[str] = Field(default_factory=list)

    # Details
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: Optional[float] = None
    explainability_text: Optional[str] = None

    # Request metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# =============================================================================
# SAMPLE DATA
# =============================================================================

SAMPLE_CONTRACT = {
    "contract_id": "ctr_20260115_001",
    "source_filename": "MSA-ACME.pdf",
    "uploaded_by": "u:ridho@example.com",
    "upload_time": "2026-01-15T10:12:00Z",
    "parties": [
        {"role": "vendor", "name": "ACME Services", "identifier": "ACME-001"},
        {"role": "client", "name": "BlueCo", "identifier": "BLUE-900"}
    ],
    "currency": "USD",
    "terms": [
        {
            "clause_id": "c1",
            "type": "rate_card",
            "description": "Rate for consulting: $200/hour",
            "extracted_text": "Consultant rate is Two Hundred US Dollars per hour...",
            "value": "200",
            "unit": "hour",
            "confidence": 0.92
        },
        {
            "clause_id": "c2",
            "type": "milestone_payment",
            "description": "Deliverable A -> $20,000 on acceptance",
            "extracted_text": "Upon acceptance of Deliverable A, client pays twenty thousand...",
            "value": "20000",
            "unit": "fixed",
            "confidence": 0.95
        }
    ],
    "raw_text": "...",
    "parse_version": "v0.1",
    "status": "parsed"
}

SAMPLE_WORK_EVENT = {
    "event_id": "we_001",
    "contract_id": "ctr_20260115_001",
    "date": "2025-12-12",
    "description": "Consulting hours for Dec",
    "units": 10,
    "unit_type": "hour",
    "amount": 2000,
    "external_ref": "PO-778"
}

SAMPLE_INVOICE_DRAFT = {
    "invoice_id": "inv_20260118_001",
    "contract_id": "ctr_20260115_001",
    "drafted_by": "agent_v0.1",
    "lines": [
        {
            "line_id": "l1",
            "description": "Consulting hours Dec (10h @ $200)",
            "quantity": 10,
            "unit": "hour",
            "unit_price": 200,
            "amount": 2000,
            "source_clause_id": "c1",
            "source_event_ids": ["we_001"],
            "explain": "Derived from timesheet event we_001",
            "agent_reasoning": "The contract clause c1 specifies a rate of $200/hour for consulting services. Work event we_001 records 10 hours of consulting on 2025-12-12. Multiplying 10 hours by $200/hour yields $2,000. This aligns with the pre-calculated amount in the work event.",
            "confidence": 0.93
        }
    ],
    "subtotal": 2000,
    "tax": 0,
    "total": 2000,
    "status": "draft",
    "created_at": "2026-01-18T07:00:00Z",
    "explainability": "Invoice lines derived from clause c1 and work events we_001; confidence aggregated 0.93",
    "aggregate_confidence": 0.93
}

SAMPLE_APPROVAL_LOG = {
    "approval_id": "app_20260120_001",
    "invoice_id": "inv_20260118_001",
    "approver": "controller@client.com",
    "approver_name": "Jane Doe",
    "approver_role": "approver",
    "approved_at": "2026-01-20T09:11:00Z",
    "approval_note": "Reviewed. OK to push.",
    "signature_hash": "sha256:a1b2c3d4e5f6...",
    "approval_method": "UI-click",
    "approval_confidence_snapshot": 0.93,
    "invoice_snapshot_hash": "sha256:...",
    "two_fa_verified": False,
    "revoked": False
}

SAMPLE_ERP_PAYLOAD = {
    "customer_ref": "BLUE-900",
    "lines": [
        {
            "description": "Consulting hours Dec",
            "quantity": 10,
            "unit_price": 200,
            "taxable": False
        }
    ],
    "invoice_date": "2026-01-20",
    "due_date": "2026-02-19",
    "memo": "Generated by Crafta Control Room; pilot id pilot_001",
    "crafta_invoice_id": "inv_20260118_001",
    "crafta_approval_id": "app_20260120_001"
}
