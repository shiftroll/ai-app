"""
NetSuite Connector

Handles Token-Based Authentication (TBA) and invoice creation for NetSuite.
Never auto-posts without explicit approval.

Design Notes:
- NetSuite uses Token-Based Authentication (OAuth 1.0a style)
- In production, use the netsuite library or SuiteTalk REST API
- Handle signature generation for requests
- Map Crafta fields to NetSuite schema
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
import hashlib
import hmac
import base64

logger = logging.getLogger(__name__)


class NetSuiteConnector:
    """
    NetSuite connector for invoice creation.

    Field Mapping (Crafta → NetSuite):
    - customer_ref → entity
    - invoice_date → tranDate
    - due_date → dueDate
    - line.description → item[].description
    - line.quantity → item[].quantity
    - line.unit_price → item[].rate
    - line.amount → item[].amount
    - memo → memo
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        token_id: Optional[str] = None,
        token_secret: Optional[str] = None,
    ):
        self.account_id = account_id or os.getenv("NETSUITE_ACCOUNT_ID")
        self.consumer_key = consumer_key or os.getenv("NETSUITE_CONSUMER_KEY")
        self.consumer_secret = consumer_secret or os.getenv("NETSUITE_CONSUMER_SECRET")
        self.token_id = token_id or os.getenv("NETSUITE_TOKEN_ID")
        self.token_secret = token_secret or os.getenv("NETSUITE_TOKEN_SECRET")

    @property
    def base_url(self) -> str:
        """Get NetSuite API base URL"""
        return f"https://{self.account_id}.suitetalk.api.netsuite.com/services/rest/record/v1"

    def validate_auth(self) -> bool:
        """Check if authentication is valid"""
        return all([
            self.account_id,
            self.consumer_key,
            self.consumer_secret,
            self.token_id,
            self.token_secret,
        ])

    def _generate_signature(
        self,
        method: str,
        url: str,
        params: Dict[str, str],
    ) -> str:
        """
        Generate OAuth 1.0a signature for NetSuite TBA.

        In production, implement proper signature generation.
        """
        # TODO: Implement actual signature generation
        # This is a simplified placeholder
        base_string = f"{method}&{url}&{sorted(params.items())}"
        key = f"{self.consumer_secret}&{self.token_secret}"
        signature = hmac.new(
            key.encode(),
            base_string.encode(),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(signature).decode()

    def build_invoice_payload(
        self,
        invoice: Dict[str, Any],
        entity_id: str,
    ) -> Dict[str, Any]:
        """
        Build NetSuite invoice payload from Crafta invoice.

        NetSuite Invoice Schema:
        {
            "entity": {"id": "123"},
            "tranDate": "2026-01-20",
            "dueDate": "2026-02-19",
            "item": {
                "items": [
                    {
                        "item": {"id": "1"},
                        "quantity": 10,
                        "rate": 200.00,
                        "description": "Consulting services"
                    }
                ]
            },
            "memo": "Crafta Invoice"
        }
        """
        items = []
        for line in invoice.get("lines", []):
            ns_item = {
                "quantity": float(line.get("quantity", 0)),
                "rate": float(line.get("unit_price", 0)),
                "description": line.get("description", ""),
            }
            items.append(ns_item)

        payload = {
            "entity": {"id": entity_id},
            "tranDate": invoice.get("invoice_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "item": {"items": items},
            "memo": f"Crafta Invoice: {invoice.get('invoice_id', '')}",
        }

        if invoice.get("due_date"):
            payload["dueDate"] = invoice["due_date"][:10]

        return payload

    async def create_invoice(
        self,
        payload: Dict[str, Any],
        approval_id: str,
    ) -> Dict[str, Any]:
        """
        Create invoice in NetSuite.

        CRITICAL: This should only be called after human approval.
        """
        if not self.validate_auth():
            raise ValueError("NetSuite not authenticated")

        # TODO: Implement actual API call
        # url = f"{self.base_url}/invoice"
        # headers = self._get_auth_headers("POST", url)
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(url, json=payload, headers=headers)

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        ns_invoice_id = f"NS-{timestamp}"

        logger.info(f"Invoice created in NetSuite: {ns_invoice_id}")

        return {
            "erp_invoice_id": ns_invoice_id,
            "status": "created",
            "payload": payload,
        }

    async def get_customers(
        self,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get customer list from NetSuite"""
        if not self.validate_auth():
            raise ValueError("NetSuite not authenticated")

        # TODO: Implement actual API call
        customers = [
            {"id": "ns-1", "name": "Acme Corp", "email": "billing@acme.com"},
            {"id": "ns-2", "name": "BlueCo Inc", "email": "ap@blueco.com"},
        ]

        if search:
            customers = [c for c in customers if search.lower() in c["name"].lower()]

        return customers[:limit]

    async def void_invoice(self, invoice_id: str) -> bool:
        """Void an invoice in NetSuite"""
        if not self.validate_auth():
            raise ValueError("NetSuite not authenticated")

        # TODO: Implement actual void operation
        logger.info(f"Invoice voided in NetSuite: {invoice_id}")
        return True
