"""
Tests for data schemas
"""

import pytest
from datetime import datetime
from decimal import Decimal

# Import schemas
import sys
sys.path.insert(0, '..')
from schemas.json_schemas import (
    Contract,
    ContractClause,
    WorkEvent,
    InvoiceDraft,
    InvoiceLine,
    ApprovalLog,
    ERPInvoicePayload,
    SAMPLE_CONTRACT,
    SAMPLE_WORK_EVENT,
    SAMPLE_INVOICE_DRAFT,
    SAMPLE_APPROVAL_LOG,
)


class TestContractSchema:
    """Test Contract schema validation"""

    def test_sample_contract_valid(self):
        """Sample contract should be valid"""
        contract = Contract(**SAMPLE_CONTRACT)
        assert contract.contract_id == "ctr_20260115_001"
        assert contract.currency == "USD"
        assert len(contract.terms) == 2

    def test_contract_clause_confidence(self):
        """Clause confidence should be between 0 and 1"""
        clause = ContractClause(
            clause_id="c1",
            type="rate_card",
            description="Test",
            extracted_text="Test text",
            value="100",
            unit="hour",
            confidence=0.95,
        )
        assert 0 <= clause.confidence <= 1

    def test_invalid_confidence_rejected(self):
        """Invalid confidence should raise error"""
        with pytest.raises(ValueError):
            ContractClause(
                clause_id="c1",
                type="rate_card",
                description="Test",
                extracted_text="Test text",
                value="100",
                unit="hour",
                confidence=1.5,  # Invalid
            )


class TestWorkEventSchema:
    """Test WorkEvent schema validation"""

    def test_sample_work_event_valid(self):
        """Sample work event should be valid"""
        # Add required fields
        event_data = {**SAMPLE_WORK_EVENT, "date": datetime.now()}
        event = WorkEvent(**event_data)
        assert event.event_id == "we_001"
        assert event.units == Decimal("10")


class TestInvoiceDraftSchema:
    """Test InvoiceDraft schema validation"""

    def test_sample_invoice_valid(self):
        """Sample invoice should be valid"""
        # Fix the sample data to match schema
        invoice_data = SAMPLE_INVOICE_DRAFT.copy()
        invoice_data["subtotal"] = Decimal(str(invoice_data["subtotal"]))
        invoice_data["tax"] = Decimal(str(invoice_data["tax"]))
        invoice_data["total"] = Decimal(str(invoice_data["total"]))

        # Fix lines
        lines = []
        for line in invoice_data["lines"]:
            line_copy = line.copy()
            line_copy["quantity"] = Decimal(str(line_copy["quantity"]))
            line_copy["unit_price"] = Decimal(str(line_copy["unit_price"]))
            line_copy["amount"] = Decimal(str(line_copy["amount"]))
            lines.append(line_copy)
        invoice_data["lines"] = lines

        invoice = InvoiceDraft(**invoice_data)
        assert invoice.invoice_id == "inv_20260118_001"
        assert len(invoice.lines) == 1

    def test_invoice_line_explainability(self):
        """Invoice lines should have explanation"""
        line = InvoiceLine(
            line_id="l1",
            description="Test line",
            quantity=Decimal("10"),
            unit="hour",
            unit_price=Decimal("200"),
            amount=Decimal("2000"),
            source_clause_id="c1",
            explain="Test explanation",
            confidence=0.9,
        )
        assert line.explain is not None
        assert line.source_clause_id == "c1"


class TestApprovalLogSchema:
    """Test ApprovalLog schema validation"""

    def test_sample_approval_valid(self):
        """Sample approval should be valid"""
        approval_data = SAMPLE_APPROVAL_LOG.copy()
        approval_data["approved_at"] = datetime.now()
        approval_data["invoice_snapshot_hash"] = "sha256:test"

        approval = ApprovalLog(**approval_data)
        assert approval.approval_id == "app_20260120_001"
        assert approval.revoked == False


class TestERPPayloadSchema:
    """Test ERPInvoicePayload schema validation"""

    def test_erp_payload_structure(self):
        """ERP payload should have required fields"""
        payload = ERPInvoicePayload(
            customer_ref="CUST-001",
            lines=[],
            invoice_date=datetime.now(),
            due_date=datetime.now(),
            crafta_invoice_id="inv_001",
            crafta_approval_id="app_001",
        )
        assert payload.customer_ref == "CUST-001"
