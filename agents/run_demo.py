#!/usr/bin/env python3
"""
Crafta Revenue Control Room - Demo Script

This script runs an end-to-end demonstration of the contract-to-invoice
pipeline, generating pilot deliverables:
- recovered_invoices.csv
- executive_summary.pdf
- audit_snapshot.pdf

Usage:
    python agents/run_demo.py --contract tests/data/sample_contract_text.txt \
                              --events tests/data/sample_workevents.csv \
                              --output outputs/

For real contracts (PDF/DOCX):
    python agents/run_demo.py --contract path/to/contract.pdf \
                              --events path/to/workevents.csv
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
import hashlib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agents
from agents.parse_contract import ContractParser, parse_contract_file
from agents.derive_invoice_lines import derive_invoice_lines, InvoiceDerivationEngine


def load_contract_text(file_path: str) -> Dict[str, Any]:
    """
    Load and parse a contract.
    Supports .txt (for demo), .pdf, and .docx files.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        # For demo purposes, create a mock parsed contract from text
        with open(file_path, 'r') as f:
            text = f.read()

        return create_mock_parsed_contract(text, file_path)

    else:
        # Use the full parser for PDF/DOCX
        return parse_contract_file(
            file_path=file_path,
            uploaded_by="demo_user",
            use_llm=os.getenv("OPENAI_API_KEY") is not None,
        )


def create_mock_parsed_contract(text: str, filename: str) -> Dict[str, Any]:
    """
    Create a mock parsed contract from plain text.
    This demonstrates the expected output structure.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    contract_id = f"ctr_demo_{timestamp[:8]}"

    # Extract terms using simple pattern matching for demo
    terms = []

    # Senior consultant rate
    if "$200" in text and "Senior Consultant" in text:
        terms.append({
            "clause_id": "c1_senior_rate",
            "type": "rate_card",
            "description": "Senior Consultant rate: $200/hour",
            "extracted_text": "Senior Consultant: Two Hundred US Dollars ($200.00) per hour",
            "value": "200",
            "unit": "hour",
            "confidence": 0.95,
        })

    # Junior consultant rate
    if "$125" in text and "Junior Consultant" in text:
        terms.append({
            "clause_id": "c1_junior_rate",
            "type": "rate_card",
            "description": "Junior Consultant rate: $125/hour",
            "extracted_text": "Junior Consultant: One Hundred Twenty-Five US Dollars ($125.00) per hour",
            "value": "125",
            "unit": "hour",
            "confidence": 0.92,
        })

    # Technical Specialist rate
    if "$175" in text and "Technical Specialist" in text:
        terms.append({
            "clause_id": "c1_tech_rate",
            "type": "rate_card",
            "description": "Technical Specialist rate: $175/hour",
            "extracted_text": "Technical Specialist: One Hundred Seventy-Five US Dollars ($175.00) per hour",
            "value": "175",
            "unit": "hour",
            "confidence": 0.93,
        })

    # Project Management rate
    if "$150" in text and "Project management" in text.lower():
        terms.append({
            "clause_id": "c1_pm_rate",
            "type": "rate_card",
            "description": "Project Management rate: $150/hour",
            "extracted_text": "Project management services shall be billed at a fixed rate of One Hundred Fifty Dollars ($150.00) per hour",
            "value": "150",
            "unit": "hour",
            "confidence": 0.94,
        })

    # Phase 1 Milestone
    if "$20,000" in text and "Phase 1" in text:
        terms.append({
            "clause_id": "c2_milestone_1",
            "type": "milestone_payment",
            "description": "Phase 1 milestone: $20,000",
            "extracted_text": "Upon completion and Client acceptance of Phase 1 deliverables, Client shall pay Vendor a milestone payment of Twenty Thousand US Dollars ($20,000.00)",
            "value": "20000",
            "unit": "fixed",
            "confidence": 0.97,
        })

    # Phase 2 Milestone
    if "$35,000" in text and "Phase 2" in text:
        terms.append({
            "clause_id": "c2_milestone_2",
            "type": "milestone_payment",
            "description": "Phase 2 milestone: $35,000",
            "extracted_text": "Upon completion and Client acceptance of Phase 2 deliverables, Client shall pay Vendor a milestone payment of Thirty-Five Thousand US Dollars ($35,000.00)",
            "value": "35000",
            "unit": "fixed",
            "confidence": 0.96,
        })

    # Expense reimbursement
    if "10%" in text and "expense" in text.lower():
        terms.append({
            "clause_id": "c4_expenses",
            "type": "other",
            "description": "Expense reimbursement at cost + 10%",
            "extracted_text": "Client shall reimburse Vendor for pre-approved travel and out-of-pocket expenses at cost plus a 10% administrative fee",
            "value": "10",
            "unit": "percent",
            "confidence": 0.88,
        })

    # Payment terms
    if "Net 30" in text:
        terms.append({
            "clause_id": "c3_payment_terms",
            "type": "payment_terms",
            "description": "Payment terms: Net 30 days",
            "extracted_text": "Payment terms are Net 30 days from the date of invoice",
            "value": "30",
            "unit": "days",
            "confidence": 0.98,
        })

    return {
        "contract_id": contract_id,
        "source_filename": os.path.basename(filename),
        "uploaded_by": "demo_user",
        "upload_time": datetime.utcnow().isoformat(),
        "parties": [
            {"role": "vendor", "name": "ACME Services LLC", "identifier": "ACME-001"},
            {"role": "client", "name": "BlueCo Inc.", "identifier": "BLUE-900"},
        ],
        "currency": "USD",
        "terms": terms,
        "raw_text": text[:500] + "..." if len(text) > 500 else text,
        "parse_version": "v0.1-demo",
        "status": "parsed",
        "payment_terms_days": 30,
    }


def load_work_events(file_path: str, contract_id: str) -> List[Dict[str, Any]]:
    """Load work events from CSV file."""
    events = []

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append({
                "event_id": row.get("event_id", ""),
                "contract_id": contract_id,
                "date": row.get("date", ""),
                "description": row.get("description", ""),
                "units": float(row.get("units", 0)),
                "unit_type": row.get("unit_type", "unit"),
                "amount": float(row["amount"]) if row.get("amount") else None,
                "external_ref": row.get("external_ref", ""),
            })

    return events


def generate_recovered_invoices_csv(
    invoice: Dict[str, Any],
    contract: Dict[str, Any],
    output_path: str,
):
    """Generate the recovered_invoices.csv file."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "invoice_id",
            "contract_id",
            "line_description",
            "quantity",
            "unit",
            "unit_price",
            "amount",
            "source_clause",
            "confidence",
            "explainability",
            "status",
        ])

        for line in invoice.get("lines", []):
            writer.writerow([
                invoice["invoice_id"],
                invoice["contract_id"],
                line["description"],
                line["quantity"],
                line["unit"],
                line["unit_price"],
                line["amount"],
                line["source_clause_id"],
                line["confidence"],
                line["explain"],
                invoice["status"],
            ])

    print(f"  Generated: {output_path}")


def generate_executive_summary(
    invoice: Dict[str, Any],
    contract: Dict[str, Any],
    output_path: str,
):
    """Generate the executive_summary.pdf (as text for demo)."""
    # Calculate summary statistics
    total_amount = invoice.get("total", 0)
    line_count = len(invoice.get("lines", []))
    avg_confidence = invoice.get("aggregate_confidence", 0)

    # Categorize lines
    rate_lines = [l for l in invoice.get("lines", []) if "rate" in l.get("source_clause_id", "")]
    milestone_lines = [l for l in invoice.get("lines", []) if "milestone" in l.get("source_clause_id", "")]
    expense_lines = [l for l in invoice.get("lines", []) if "expense" in l.get("source_clause_id", "")]

    rate_total = sum(l["amount"] for l in rate_lines)
    milestone_total = sum(l["amount"] for l in milestone_lines)
    expense_total = sum(l["amount"] for l in expense_lines)

    # Generate summary content
    summary = f"""
================================================================================
                    CRAFTA REVENUE CONTROL ROOM
                       EXECUTIVE SUMMARY
================================================================================

Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
Contract:  {contract.get("source_filename", "N/A")}
Invoice:   {invoice.get("invoice_id", "N/A")}

--------------------------------------------------------------------------------
                         RECOVERY SUMMARY
--------------------------------------------------------------------------------

Total Recoverable Amount:     ${total_amount:,.2f}
Number of Line Items:         {line_count}
Average Confidence Score:     {avg_confidence:.0%}

Breakdown by Category:
  - Time & Materials:         ${rate_total:,.2f} ({len(rate_lines)} lines)
  - Milestone Payments:       ${milestone_total:,.2f} ({len(milestone_lines)} lines)
  - Expenses:                 ${expense_total:,.2f} ({len(expense_lines)} lines)

--------------------------------------------------------------------------------
                      TOP FINDINGS / LEAKAGE REASONS
--------------------------------------------------------------------------------

1. RATE CARD COMPLIANCE
   - All consultant rates extracted from contract terms
   - Rates verified against timesheet entries
   - Total T&M revenue: ${rate_total:,.2f}

2. MILESTONE RECOGNITION
   - Phase 1 milestone triggered by completion event
   - Milestone amount: ${milestone_total:,.2f}
   - Recommend: Verify acceptance documentation

3. EXPENSE RECOVERY
   - Expenses include 10% administrative fee per contract
   - Total expense recovery: ${expense_total:,.2f}

--------------------------------------------------------------------------------
                       CONFIDENCE ANALYSIS
--------------------------------------------------------------------------------

High Confidence (>90%):       {len([l for l in invoice.get("lines", []) if l["confidence"] >= 0.9])} lines
Medium Confidence (80-90%):   {len([l for l in invoice.get("lines", []) if 0.8 <= l["confidence"] < 0.9])} lines
Low Confidence (<80%):        {len([l for l in invoice.get("lines", []) if l["confidence"] < 0.8])} lines

--------------------------------------------------------------------------------
                         RECOMMENDED ACTIONS
--------------------------------------------------------------------------------

1. Review all line items in the Invoice Draft Queue
2. Verify milestone acceptance documentation for Phase 1
3. Approve invoice after controller review
4. Push to ERP system (QuickBooks/Xero/NetSuite)

--------------------------------------------------------------------------------
                            NEXT STEPS
--------------------------------------------------------------------------------

[ ] Controller reviews invoice in Control Room UI
[ ] Approve/reject each line item
[ ] Generate audit snapshot PDF
[ ] Push approved invoice to ERP
[ ] Archive audit trail for compliance

================================================================================
                    Generated by Crafta Revenue Control Room
                           Human-in-the-Loop Required
================================================================================
"""

    # For demo, save as text file
    text_path = output_path.replace('.pdf', '.txt')
    with open(text_path, 'w') as f:
        f.write(summary)
    print(f"  Generated: {text_path}")

    # If reportlab is available, generate PDF
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # Simple PDF generation
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 1 * inch, "CRAFTA REVENUE CONTROL ROOM")
        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, height - 1.3 * inch, "Executive Summary")

        y = height - 2 * inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1 * inch, y, f"Total Recoverable: ${total_amount:,.2f}")

        y -= 0.4 * inch
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, y, f"Contract: {contract.get('source_filename', 'N/A')}")
        y -= 0.25 * inch
        c.drawString(1 * inch, y, f"Invoice: {invoice.get('invoice_id', 'N/A')}")
        y -= 0.25 * inch
        c.drawString(1 * inch, y, f"Line Items: {line_count}")
        y -= 0.25 * inch
        c.drawString(1 * inch, y, f"Confidence: {avg_confidence:.0%}")

        y -= 0.5 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1 * inch, y, "Breakdown:")
        y -= 0.25 * inch
        c.setFont("Helvetica", 9)
        c.drawString(1.2 * inch, y, f"Time & Materials: ${rate_total:,.2f}")
        y -= 0.2 * inch
        c.drawString(1.2 * inch, y, f"Milestones: ${milestone_total:,.2f}")
        y -= 0.2 * inch
        c.drawString(1.2 * inch, y, f"Expenses: ${expense_total:,.2f}")

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(1 * inch, 0.75 * inch, "Generated by Crafta Control Room - Human approval required")
        c.drawString(1 * inch, 0.5 * inch, f"Generated: {datetime.utcnow().isoformat()}")

        c.save()
        print(f"  Generated: {output_path}")
    except ImportError:
        print(f"  Note: Install reportlab for PDF generation (pip install reportlab)")


def generate_audit_snapshot(
    invoice: Dict[str, Any],
    contract: Dict[str, Any],
    output_path: str,
):
    """Generate audit snapshot."""
    # Create audit log
    audit_data = {
        "snapshot_id": f"snap_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "generated_at": datetime.utcnow().isoformat(),
        "contract": contract,
        "invoice": invoice,
        "audit_trail": [
            {
                "action": "contract_uploaded",
                "timestamp": contract.get("upload_time"),
                "actor": contract.get("uploaded_by"),
            },
            {
                "action": "contract_parsed",
                "timestamp": contract.get("upload_time"),
                "actor": "agent_v0.1",
                "details": f"Extracted {len(contract.get('terms', []))} terms",
            },
            {
                "action": "invoice_generated",
                "timestamp": invoice.get("created_at"),
                "actor": invoice.get("drafted_by"),
                "details": f"Generated {len(invoice.get('lines', []))} lines",
            },
        ],
    }

    # Calculate hash
    data_str = json.dumps(audit_data, sort_keys=True, default=str)
    data_hash = hashlib.sha256(data_str.encode()).hexdigest()
    audit_data["data_hash"] = f"sha256:{data_hash}"

    # Save as JSON
    json_path = output_path.replace('.pdf', '.json')
    with open(json_path, 'w') as f:
        json.dump(audit_data, f, indent=2, default=str)
    print(f"  Generated: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Crafta Revenue Control Room - Demo Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with sample data
  python agents/run_demo.py --contract tests/data/sample_contract_text.txt \\
                            --events tests/data/sample_workevents.csv

  # Run with custom output directory
  python agents/run_demo.py --contract contract.pdf --events events.csv --output results/
        """
    )
    parser.add_argument(
        "--contract",
        required=True,
        help="Path to contract file (PDF, DOCX, or TXT)",
    )
    parser.add_argument(
        "--events",
        required=True,
        help="Path to work events CSV file",
    )
    parser.add_argument(
        "--output",
        default="outputs",
        help="Output directory for generated files (default: outputs/)",
    )
    parser.add_argument(
        "--tax-rate",
        type=float,
        default=0.0,
        help="Tax rate as decimal (e.g., 0.1 for 10%%)",
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    print("\n" + "=" * 60)
    print("  CRAFTA REVENUE CONTROL ROOM - DEMO")
    print("=" * 60)

    # Step 1: Parse contract
    print("\n[Step 1] Parsing contract...")
    print(f"  Input: {args.contract}")
    contract = load_contract_text(args.contract)
    print(f"  Contract ID: {contract['contract_id']}")
    print(f"  Parties: {' ↔ '.join(p['name'] for p in contract['parties'])}")
    print(f"  Terms extracted: {len(contract['terms'])}")

    # Step 2: Load work events
    print("\n[Step 2] Loading work events...")
    print(f"  Input: {args.events}")
    events = load_work_events(args.events, contract['contract_id'])
    print(f"  Events loaded: {len(events)}")

    # Step 3: Generate invoice
    print("\n[Step 3] Generating invoice draft...")
    invoice = derive_invoice_lines(
        contract=contract,
        work_events=events,
        tax_rate=args.tax_rate,
    )
    print(f"  Invoice ID: {invoice['invoice_id']}")
    print(f"  Lines: {len(invoice['lines'])}")
    print(f"  Total: ${invoice['total']:,.2f}")
    print(f"  Confidence: {invoice['aggregate_confidence']:.0%}")

    # Step 4: Generate outputs
    print("\n[Step 4] Generating pilot deliverables...")

    csv_path = os.path.join(args.output, "recovered_invoices.csv")
    generate_recovered_invoices_csv(invoice, contract, csv_path)

    summary_path = os.path.join(args.output, "executive_summary.pdf")
    generate_executive_summary(invoice, contract, summary_path)

    audit_path = os.path.join(args.output, "audit_snapshot.pdf")
    generate_audit_snapshot(invoice, contract, audit_path)

    # Summary
    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)
    print(f"\nOutputs generated in: {args.output}/")
    print("  - recovered_invoices.csv")
    print("  - executive_summary.txt (and .pdf if reportlab installed)")
    print("  - audit_snapshot.json")
    print("\nNext steps:")
    print("  1. Review outputs in the Crafta Control Room UI")
    print("  2. Controller approves invoice lines")
    print("  3. Push approved invoice to ERP")
    print("\n")


if __name__ == "__main__":
    main()
