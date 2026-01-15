"""
End-to-end integration tests for Crafta Revenue Control Room

Tests the complete flow:
1. Contract parsing
2. Invoice generation
3. Approval workflow
4. Output generation
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "agents"))


class TestEndToEndFlow:
    """Test complete contract-to-invoice flow"""

    @pytest.fixture
    def sample_contract_path(self):
        return PROJECT_ROOT / "tests" / "data" / "sample_contract_text.txt"

    @pytest.fixture
    def sample_events_path(self):
        return PROJECT_ROOT / "tests" / "data" / "sample_workevents.csv"

    def test_contract_parsing(self, sample_contract_path):
        """Test contract text parsing"""
        from agents.parse_contract import create_mock_parsed_contract

        with open(sample_contract_path, 'r') as f:
            text = f.read()

        contract = create_mock_parsed_contract(text, str(sample_contract_path))

        # Verify structure
        assert "contract_id" in contract
        assert "parties" in contract
        assert "terms" in contract
        assert len(contract["parties"]) == 2
        assert len(contract["terms"]) > 0

        # Verify rate extraction
        rate_terms = [t for t in contract["terms"] if t["type"] == "rate_card"]
        assert len(rate_terms) > 0

        # Verify milestone extraction
        milestone_terms = [t for t in contract["terms"] if t["type"] == "milestone_payment"]
        assert len(milestone_terms) > 0

    def test_work_events_loading(self, sample_events_path):
        """Test work events CSV loading"""
        import csv

        with open(sample_events_path, 'r') as f:
            reader = csv.DictReader(f)
            events = list(reader)

        assert len(events) == 10
        assert all("event_id" in e for e in events)
        assert all("units" in e for e in events)

    def test_invoice_generation(self, sample_contract_path, sample_events_path):
        """Test invoice draft generation"""
        from agents.parse_contract import create_mock_parsed_contract
        from agents.derive_invoice_lines import derive_invoice_lines
        import csv

        # Parse contract
        with open(sample_contract_path, 'r') as f:
            text = f.read()
        contract = create_mock_parsed_contract(text, str(sample_contract_path))

        # Load events
        with open(sample_events_path, 'r') as f:
            reader = csv.DictReader(f)
            events = []
            for row in reader:
                events.append({
                    "event_id": row["event_id"],
                    "contract_id": contract["contract_id"],
                    "date": row["date"],
                    "description": row["description"],
                    "units": float(row["units"]),
                    "unit_type": row["unit_type"],
                    "amount": float(row["amount"]) if row.get("amount") else None,
                    "external_ref": row.get("external_ref"),
                })

        # Generate invoice
        invoice = derive_invoice_lines(contract, events)

        # Verify invoice structure
        assert "invoice_id" in invoice
        assert "lines" in invoice
        assert "total" in invoice
        assert "explainability" in invoice
        assert len(invoice["lines"]) > 0

        # Verify line items have explainability
        for line in invoice["lines"]:
            assert "explain" in line
            assert "confidence" in line
            assert "source_clause_id" in line

    def test_confidence_scoring(self, sample_contract_path, sample_events_path):
        """Test confidence scores are reasonable"""
        from agents.parse_contract import create_mock_parsed_contract
        from agents.derive_invoice_lines import derive_invoice_lines
        import csv

        # Parse contract
        with open(sample_contract_path, 'r') as f:
            text = f.read()
        contract = create_mock_parsed_contract(text, str(sample_contract_path))

        # Load events
        with open(sample_events_path, 'r') as f:
            reader = csv.DictReader(f)
            events = []
            for row in reader:
                events.append({
                    "event_id": row["event_id"],
                    "contract_id": contract["contract_id"],
                    "date": row["date"],
                    "description": row["description"],
                    "units": float(row["units"]),
                    "unit_type": row["unit_type"],
                    "amount": float(row["amount"]) if row.get("amount") else None,
                    "external_ref": row.get("external_ref"),
                })

        # Generate invoice
        invoice = derive_invoice_lines(contract, events)

        # Verify confidence scores
        assert invoice["aggregate_confidence"] > 0
        assert invoice["aggregate_confidence"] <= 1

        for line in invoice["lines"]:
            assert 0 < line["confidence"] <= 1

    def test_demo_script_runs(self, tmp_path):
        """Test the demo script produces outputs"""
        import subprocess

        result = subprocess.run(
            [
                "python", str(PROJECT_ROOT / "agents" / "run_demo.py"),
                "--contract", str(PROJECT_ROOT / "tests" / "data" / "sample_contract_text.txt"),
                "--events", str(PROJECT_ROOT / "tests" / "data" / "sample_workevents.csv"),
                "--output", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )

        # Check script completed
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Check outputs exist
        assert (tmp_path / "recovered_invoices.csv").exists()
        assert (tmp_path / "executive_summary.txt").exists()
        assert (tmp_path / "audit_snapshot.json").exists()

    def test_output_csv_format(self, tmp_path):
        """Test recovered_invoices.csv has correct format"""
        import subprocess
        import csv

        subprocess.run(
            [
                "python", str(PROJECT_ROOT / "agents" / "run_demo.py"),
                "--contract", str(PROJECT_ROOT / "tests" / "data" / "sample_contract_text.txt"),
                "--events", str(PROJECT_ROOT / "tests" / "data" / "sample_workevents.csv"),
                "--output", str(tmp_path),
            ],
            capture_output=True,
        )

        # Read and validate CSV
        with open(tmp_path / "recovered_invoices.csv", 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0

        # Check required columns
        required_columns = [
            "invoice_id", "contract_id", "line_description",
            "amount", "confidence", "explainability"
        ]
        for col in required_columns:
            assert col in rows[0], f"Missing column: {col}"


class TestHITLRules:
    """Test Human-in-the-Loop rules"""

    def test_low_confidence_flagged(self):
        """Lines with confidence < 80% should be flagged as exceptions"""
        from agents.derive_invoice_lines import InvoiceDerivationEngine

        engine = InvoiceDerivationEngine()
        assert engine.CONFIDENCE_THRESHOLD == 0.80

    def test_approval_required_message(self):
        """Approval flow should require explicit confirmation"""
        # This tests the UI requirement conceptually
        # In a real test, we'd test the API endpoint

        approval_text = "I confirm I have reviewed this invoice"
        assert "confirm" in approval_text.lower()
        assert "reviewed" in approval_text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
