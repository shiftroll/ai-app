"""
Crafta Invoice Derivation Agent

Given a Contract and WorkEvent dataset, generates InvoiceDraft objects with:
- Line items with amounts
- Tax handling
- Due date calculation
- Rationale notes per line (explainable text)
- Confidence scores

Implements HITL rules:
- Lines < 80% confidence flagged as exceptions
- Rev-rec sensitive items require CFO approval
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class InvoiceLineResult:
    """Result of deriving a single invoice line"""
    line_id: str
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    amount: Decimal
    source_clause_id: str
    source_event_ids: List[str]
    explain: str
    agent_reasoning: str
    confidence: float
    is_exception: bool = False
    exception_reason: Optional[str] = None
    requires_cfo_approval: bool = False


@dataclass
class InvoiceDraftResult:
    """Result of generating an invoice draft"""
    invoice_id: str
    contract_id: str
    drafted_by: str
    lines: List[InvoiceLineResult]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    invoice_date: datetime
    due_date: datetime
    status: str
    explainability: str
    aggregate_confidence: float
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# INVOICE DERIVATION ENGINE
# =============================================================================

class InvoiceDerivationEngine:
    """
    Derives invoice lines from contracts and work events.

    Rules:
    1. Match work events to contract clauses by unit type
    2. Calculate amounts using contract rates
    3. Apply tax rules if configured
    4. Flag low-confidence lines as exceptions
    5. Require CFO approval for rev-rec sensitive items
    """

    CONFIDENCE_THRESHOLD = 0.80  # Below this = exception
    AGENT_VERSION = "agent_v0.1"

    def __init__(self, tax_rate: Decimal = Decimal("0")):
        """Initialize the derivation engine"""
        self.tax_rate = tax_rate

    def derive_invoice(
        self,
        contract: Dict[str, Any],
        work_events: List[Dict[str, Any]],
        invoice_id: Optional[str] = None,
        invoice_date: Optional[datetime] = None,
    ) -> InvoiceDraftResult:
        """
        Generate invoice draft from contract and work events.

        Args:
            contract: Parsed contract dictionary
            work_events: List of work event dictionaries
            invoice_id: Optional invoice ID
            invoice_date: Optional invoice date (defaults to now)

        Returns:
            InvoiceDraftResult with all derived lines
        """
        logger.info(f"Deriving invoice for contract: {contract.get('contract_id')}")

        # Generate invoice ID
        if not invoice_id:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            hash_suffix = hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:4]
            invoice_id = f"inv_{timestamp}_{hash_suffix}"

        # Set dates
        invoice_date = invoice_date or datetime.utcnow()
        payment_terms_days = contract.get("payment_terms_days", 30)
        due_date = invoice_date + timedelta(days=payment_terms_days)

        # Build clause lookup
        clause_lookup = self._build_clause_lookup(contract.get("terms", []))

        # Derive lines
        lines = []
        line_count = 0
        total_confidence = 0
        reasons_for_invoice = []

        for event in work_events:
            line_result = self._derive_line_from_event(
                event, clause_lookup, contract, line_count + 1
            )
            if line_result:
                lines.append(line_result)
                line_count += 1
                total_confidence += line_result.confidence
                reasons_for_invoice.append(
                    f"{line_result.source_clause_id}: {line_result.explain}"
                )

        # Check for unmatched milestones/fixed fees
        milestone_lines = self._check_milestone_triggers(
            contract, work_events, clause_lookup, line_count
        )
        for ml in milestone_lines:
            lines.append(ml)
            line_count += 1
            total_confidence += ml.confidence
            reasons_for_invoice.append(f"{ml.source_clause_id}: {ml.explain}")

        # Calculate totals
        subtotal = sum(l.amount for l in lines)
        tax = (subtotal * self.tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = subtotal + tax

        # Aggregate confidence
        aggregate_confidence = (
            total_confidence / len(lines) if lines else 0.0
        )

        # Determine status
        has_exceptions = any(l.is_exception for l in lines)
        requires_cfo = any(l.requires_cfo_approval for l in lines)

        if has_exceptions:
            status = "exception"
        elif requires_cfo:
            status = "pending_cfo_review"
        else:
            status = "draft"

        # Build explainability summary
        explainability = self._build_explainability_summary(
            lines, contract, reasons_for_invoice, aggregate_confidence
        )

        return InvoiceDraftResult(
            invoice_id=invoice_id,
            contract_id=contract.get("contract_id", ""),
            drafted_by=self.AGENT_VERSION,
            lines=lines,
            subtotal=subtotal,
            tax=tax,
            total=total,
            invoice_date=invoice_date,
            due_date=due_date,
            status=status,
            explainability=explainability,
            aggregate_confidence=round(aggregate_confidence, 2),
        )

    def _build_clause_lookup(
        self, terms: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Build lookup tables for clauses by type and unit"""
        lookup = {
            "by_unit": {},
            "by_type": {},
            "by_id": {},
        }

        for term in terms:
            clause_id = term.get("clause_id", "")
            clause_type = term.get("type", "")
            unit = term.get("unit", "").lower()

            lookup["by_id"][clause_id] = term
            lookup["by_type"].setdefault(clause_type, []).append(term)
            lookup["by_unit"].setdefault(unit, []).append(term)

        return lookup

    def _derive_line_from_event(
        self,
        event: Dict[str, Any],
        clause_lookup: Dict[str, Any],
        contract: Dict[str, Any],
        line_number: int,
    ) -> Optional[InvoiceLineResult]:
        """Derive a single invoice line from a work event"""
        event_id = event.get("event_id", "")
        units = Decimal(str(event.get("units", 0)))
        unit_type = event.get("unit_type", "").lower()
        description = event.get("description", "")
        event_date = event.get("date", "")
        pre_calculated_amount = event.get("amount")

        # Find matching clause
        matching_clauses = clause_lookup["by_unit"].get(unit_type, [])
        rate_clauses = clause_lookup["by_type"].get("rate_card", [])

        # Try to find exact unit match first
        matched_clause = None
        for clause in matching_clauses:
            if clause.get("type") == "rate_card":
                matched_clause = clause
                break

        # Fall back to any rate card
        if not matched_clause and rate_clauses:
            matched_clause = rate_clauses[0]

        if not matched_clause:
            # Can't derive without a rate
            logger.warning(f"No matching clause for event {event_id}")
            return None

        # Extract values
        clause_id = matched_clause.get("clause_id", "")
        clause_value = Decimal(str(matched_clause.get("value", "0")))
        clause_unit = matched_clause.get("unit", unit_type)
        clause_confidence = matched_clause.get("confidence", 0.7)

        # Calculate amount
        calculated_amount = (units * clause_value).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Validate against pre-calculated if available
        confidence = clause_confidence
        validation_note = ""

        if pre_calculated_amount is not None:
            pre_calc = Decimal(str(pre_calculated_amount))
            if calculated_amount == pre_calc:
                confidence = min(confidence + 0.05, 1.0)
                validation_note = "Amount matches pre-calculated value."
            else:
                diff_pct = abs(calculated_amount - pre_calc) / pre_calc * 100
                if diff_pct > 5:
                    confidence = max(confidence - 0.15, 0.3)
                    validation_note = f"Amount differs from pre-calculated by {diff_pct:.1f}%."
                else:
                    validation_note = f"Minor variance ({diff_pct:.1f}%) from pre-calculated."

        # Build description
        line_description = f"{description} ({units}{clause_unit} @ ${clause_value}/{clause_unit})"

        # Build explanation
        explain = f"Derived from work event {event_id} on {event_date}"

        # Build detailed reasoning
        agent_reasoning = self._build_agent_reasoning(
            event, matched_clause, units, clause_value, calculated_amount, validation_note
        )

        # Check for exceptions
        is_exception = confidence < self.CONFIDENCE_THRESHOLD
        exception_reason = None
        if is_exception:
            exception_reason = f"Confidence {confidence:.0%} below threshold {self.CONFIDENCE_THRESHOLD:.0%}"

        # Check for CFO approval requirement
        requires_cfo = matched_clause.get("requires_cfo_approval", False)

        return InvoiceLineResult(
            line_id=f"l{line_number}",
            description=line_description,
            quantity=units,
            unit=clause_unit,
            unit_price=clause_value,
            amount=calculated_amount,
            source_clause_id=clause_id,
            source_event_ids=[event_id],
            explain=explain,
            agent_reasoning=agent_reasoning,
            confidence=round(confidence, 2),
            is_exception=is_exception,
            exception_reason=exception_reason,
            requires_cfo_approval=requires_cfo,
        )

    def _check_milestone_triggers(
        self,
        contract: Dict[str, Any],
        work_events: List[Dict[str, Any]],
        clause_lookup: Dict[str, Any],
        current_line_count: int,
    ) -> List[InvoiceLineResult]:
        """Check if any milestone payments should be triggered"""
        milestone_lines = []
        milestone_clauses = clause_lookup["by_type"].get("milestone_payment", [])

        for clause in milestone_clauses:
            clause_id = clause.get("clause_id", "")
            description = clause.get("description", "")
            value = Decimal(str(clause.get("value", "0")))
            confidence = clause.get("confidence", 0.8)
            extracted_text = clause.get("extracted_text", "")

            # Check if milestone is triggered by any event
            # This is a simplified check - in production would need more sophisticated matching
            trigger_events = []
            for event in work_events:
                event_desc = event.get("description", "").lower()
                if any(kw in event_desc for kw in ["milestone", "deliverable", "acceptance", "complete"]):
                    trigger_events.append(event.get("event_id", ""))

            if trigger_events:
                current_line_count += 1
                agent_reasoning = (
                    f"The contract clause {clause_id} specifies a milestone payment of ${value:,.2f}. "
                    f"Work events {', '.join(trigger_events)} indicate potential milestone completion. "
                    f"The original clause text states: '{extracted_text[:100]}...'. "
                    f"Manual verification of milestone acceptance is recommended."
                )

                milestone_lines.append(InvoiceLineResult(
                    line_id=f"l{current_line_count}",
                    description=description,
                    quantity=Decimal("1"),
                    unit="fixed",
                    unit_price=value,
                    amount=value,
                    source_clause_id=clause_id,
                    source_event_ids=trigger_events,
                    explain=f"Milestone payment triggered by events: {', '.join(trigger_events)}",
                    agent_reasoning=agent_reasoning,
                    confidence=confidence * 0.9,  # Slightly lower for milestone detection
                    is_exception=confidence * 0.9 < self.CONFIDENCE_THRESHOLD,
                    requires_cfo_approval=clause.get("requires_cfo_approval", False),
                ))

        return milestone_lines

    def _build_agent_reasoning(
        self,
        event: Dict[str, Any],
        clause: Dict[str, Any],
        units: Decimal,
        rate: Decimal,
        amount: Decimal,
        validation_note: str,
    ) -> str:
        """Build detailed agent reasoning for a line item"""
        clause_id = clause.get("clause_id", "")
        clause_type = clause.get("type", "")
        extracted_text = clause.get("extracted_text", "")[:150]
        event_id = event.get("event_id", "")
        event_date = event.get("date", "")
        event_desc = event.get("description", "")

        reasoning = (
            f"The contract clause {clause_id} ({clause_type}) specifies a rate of ${rate:,.2f} per {clause.get('unit', 'unit')}. "
            f"The original clause text states: '{extracted_text}...'. "
            f"Work event {event_id} recorded on {event_date} describes '{event_desc}' with {units} units. "
            f"Calculation: {units} units × ${rate:,.2f}/unit = ${amount:,.2f}. "
        )

        if validation_note:
            reasoning += validation_note

        return reasoning

    def _build_explainability_summary(
        self,
        lines: List[InvoiceLineResult],
        contract: Dict[str, Any],
        reasons: List[str],
        aggregate_confidence: float,
    ) -> str:
        """Build overall explainability summary for the invoice"""
        contract_id = contract.get("contract_id", "")
        num_lines = len(lines)
        exception_count = sum(1 for l in lines if l.is_exception)
        cfo_count = sum(1 for l in lines if l.requires_cfo_approval)

        clauses_used = list(set(l.source_clause_id for l in lines))
        events_used = list(set(eid for l in lines for eid in l.source_event_ids))

        summary = (
            f"Invoice derived from contract {contract_id} with {num_lines} line(s). "
            f"Used clauses: {', '.join(clauses_used)}. "
            f"Linked work events: {', '.join(events_used)}. "
            f"Aggregate confidence: {aggregate_confidence:.0%}. "
        )

        if exception_count > 0:
            summary += f"{exception_count} line(s) flagged as exceptions requiring review. "

        if cfo_count > 0:
            summary += f"{cfo_count} line(s) require CFO approval due to revenue recognition complexity. "

        return summary

    def to_dict(self, result: InvoiceDraftResult) -> Dict[str, Any]:
        """Convert InvoiceDraftResult to dictionary"""
        return {
            "invoice_id": result.invoice_id,
            "contract_id": result.contract_id,
            "drafted_by": result.drafted_by,
            "lines": [
                {
                    "line_id": l.line_id,
                    "description": l.description,
                    "quantity": float(l.quantity),
                    "unit": l.unit,
                    "unit_price": float(l.unit_price),
                    "amount": float(l.amount),
                    "source_clause_id": l.source_clause_id,
                    "source_event_ids": l.source_event_ids,
                    "explain": l.explain,
                    "agent_reasoning": l.agent_reasoning,
                    "confidence": l.confidence,
                    "is_exception": l.is_exception,
                    "exception_reason": l.exception_reason,
                    "requires_cfo_approval": l.requires_cfo_approval,
                }
                for l in result.lines
            ],
            "subtotal": float(result.subtotal),
            "tax": float(result.tax),
            "total": float(result.total),
            "invoice_date": result.invoice_date.isoformat(),
            "due_date": result.due_date.isoformat(),
            "status": result.status,
            "explainability": result.explainability,
            "aggregate_confidence": result.aggregate_confidence,
            "created_at": result.created_at.isoformat(),
        }


def derive_invoice_lines(
    contract: Dict[str, Any],
    work_events: List[Dict[str, Any]],
    invoice_id: Optional[str] = None,
    invoice_date: Optional[datetime] = None,
    tax_rate: float = 0.0,
) -> Dict[str, Any]:
    """
    Main entry point for invoice derivation.

    Args:
        contract: Parsed contract dictionary
        work_events: List of work event dictionaries
        invoice_id: Optional invoice ID
        invoice_date: Optional invoice date
        tax_rate: Tax rate as decimal (e.g., 0.1 for 10%)

    Returns:
        Dictionary with invoice draft data
    """
    engine = InvoiceDerivationEngine(tax_rate=Decimal(str(tax_rate)))
    result = engine.derive_invoice(contract, work_events, invoice_id, invoice_date)
    return engine.to_dict(result)


if __name__ == "__main__":
    # Example usage with sample data
    from backend.schemas.json_schemas import SAMPLE_CONTRACT, SAMPLE_WORK_EVENT

    # Convert sample to proper format
    work_events = [SAMPLE_WORK_EVENT]

    result = derive_invoice_lines(SAMPLE_CONTRACT, work_events)
    print(json.dumps(result, indent=2))
