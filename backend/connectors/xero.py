"""
Xero Connector

Handles OAuth authentication and invoice creation for Xero.
Never auto-posts without explicit approval.

Design Notes:
- In production, use the xero-python SDK
- Handle token refresh automatically
- Map Crafta fields to Xero schema
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class XeroConnector:
    """
    Xero connector for invoice creation.

    Field Mapping (Crafta → Xero):
    - customer_ref → Contact.ContactID
    - invoice_date → Date
    - due_date → DueDate
    - line.description → LineItems[].Description
    - line.quantity → LineItems[].Quantity
    - line.unit_price → LineItems[].UnitAmount
    - line.amount → LineItems[].LineAmount
    - reference → Reference
    """

    AUTH_URL = "https://login.xero.com/identity/connect/authorize"
    TOKEN_URL = "https://identity.xero.com/connect/token"
    API_URL = "https://api.xero.com/api.xro/2.0"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("XERO_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("XERO_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("XERO_REDIRECT_URI")

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def get_auth_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email accounting.transactions accounting.contacts",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        # TODO: Implement actual token exchange
        self.access_token = f"mock_xero_access_{code[:8]}"
        self.refresh_token = f"mock_xero_refresh_{code[:8]}"

        logger.info("Xero connected")

        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }

    async def refresh_access_token(self) -> bool:
        """Refresh the access token"""
        if not self.refresh_token:
            return False

        # TODO: Implement actual token refresh
        logger.info("Xero token refreshed")
        return True

    def validate_auth(self) -> bool:
        """Check if authentication is valid"""
        return bool(self.access_token and self.tenant_id)

    def build_invoice_payload(
        self,
        invoice: Dict[str, Any],
        contact_id: str,
    ) -> Dict[str, Any]:
        """
        Build Xero invoice payload from Crafta invoice.

        Xero Invoice Schema:
        {
            "Type": "ACCREC",
            "Contact": {"ContactID": "..."},
            "Date": "2026-01-20",
            "DueDate": "2026-02-19",
            "LineItems": [
                {
                    "Description": "Consulting services",
                    "Quantity": 10,
                    "UnitAmount": 200.00,
                    "AccountCode": "200"
                }
            ],
            "Reference": "Crafta-INV-001"
        }
        """
        line_items = []
        for line in invoice.get("lines", []):
            xero_line = {
                "Description": line.get("description", ""),
                "Quantity": float(line.get("quantity", 0)),
                "UnitAmount": float(line.get("unit_price", 0)),
                "AccountCode": "200",  # Default revenue account
            }
            line_items.append(xero_line)

        payload = {
            "Type": "ACCREC",  # Accounts Receivable Invoice
            "Contact": {"ContactID": contact_id},
            "Date": invoice.get("invoice_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "LineItems": line_items,
            "Reference": f"Crafta-{invoice.get('invoice_id', '')}",
            "Status": "DRAFT",  # Start as draft, approve in Xero
        }

        if invoice.get("due_date"):
            payload["DueDate"] = invoice["due_date"][:10]

        return payload

    async def create_invoice(
        self,
        payload: Dict[str, Any],
        approval_id: str,
    ) -> Dict[str, Any]:
        """
        Create invoice in Xero.

        CRITICAL: This should only be called after human approval.
        """
        if not self.validate_auth():
            raise ValueError("Xero not authenticated")

        # TODO: Implement actual API call
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        xero_invoice_id = f"XERO-{timestamp}"

        logger.info(f"Invoice created in Xero: {xero_invoice_id}")

        return {
            "erp_invoice_id": xero_invoice_id,
            "status": "created",
            "payload": payload,
        }

    async def get_contacts(
        self,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get contact list from Xero"""
        if not self.validate_auth():
            raise ValueError("Xero not authenticated")

        # TODO: Implement actual API call
        contacts = [
            {"id": "xero-1", "name": "Acme Corp", "email": "billing@acme.com"},
            {"id": "xero-2", "name": "BlueCo Inc", "email": "ap@blueco.com"},
        ]

        if search:
            contacts = [c for c in contacts if search.lower() in c["name"].lower()]

        return contacts[:limit]

    async def void_invoice(self, invoice_id: str) -> bool:
        """Void an invoice in Xero"""
        if not self.validate_auth():
            raise ValueError("Xero not authenticated")

        # TODO: Implement actual void operation
        logger.info(f"Invoice voided in Xero: {invoice_id}")
        return True
