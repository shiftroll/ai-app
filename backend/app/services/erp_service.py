"""
ERP Integration Service

Handles connections and invoice pushing to:
- QuickBooks
- Xero
- NetSuite

All operations require prior human approval.
No auto-posting without explicit approval flag.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from app.config import settings
from app.services.database import save_invoice, get_invoice_by_id

logger = logging.getLogger(__name__)

# In-memory ERP connection state (replace with proper storage in production)
_erp_connections = {}


# =============================================================================
# ERP STATUS
# =============================================================================

async def get_erp_status(erp_type: str) -> Dict[str, Any]:
    """Get connection status for an ERP"""
    connection = _erp_connections.get(erp_type, {})

    if not connection:
        # Check if configured
        configured = False
        if erp_type == "quickbooks":
            configured = bool(settings.quickbooks_client_id)
        elif erp_type == "xero":
            configured = bool(settings.xero_client_id)
        elif erp_type == "netsuite":
            configured = bool(settings.netsuite_account_id)

        if not configured:
            return {
                "connected": False,
                "error": "Not configured"
            }

        return {
            "connected": False,
            "error": "Not authenticated"
        }

    return {
        "connected": connection.get("connected", False),
        "last_sync": connection.get("last_sync"),
        "expires_at": connection.get("expires_at"),
        "company_name": connection.get("company_name"),
    }


# =============================================================================
# OAUTH FLOW
# =============================================================================

async def initiate_oauth_flow(erp_type: str) -> Dict[str, Any]:
    """
    Initiate OAuth flow for ERP connection.

    Design Note:
    - In production, implement proper OAuth 2.0 flow
    - Store tokens securely with encryption
    - Implement token refresh logic
    """
    import secrets
    state = secrets.token_urlsafe(32)

    # Store state for verification
    _erp_connections[f"{erp_type}_state"] = state

    # Build auth URL based on ERP type
    if erp_type == "quickbooks":
        auth_url = (
            f"https://appcenter.intuit.com/connect/oauth2"
            f"?client_id={settings.quickbooks_client_id}"
            f"&response_type=code"
            f"&scope=com.intuit.quickbooks.accounting"
            f"&redirect_uri={settings.quickbooks_redirect_uri}"
            f"&state={state}"
        )
    elif erp_type == "xero":
        auth_url = (
            f"https://login.xero.com/identity/connect/authorize"
            f"?response_type=code"
            f"&client_id={settings.xero_client_id}"
            f"&redirect_uri={settings.xero_redirect_uri}"
            f"&scope=openid profile email accounting.transactions"
            f"&state={state}"
        )
    elif erp_type == "netsuite":
        # NetSuite uses Token Based Authentication
        auth_url = (
            f"https://{settings.netsuite_account_id}.app.netsuite.com/app/login/oauth2/authorize.nl"
            f"?response_type=code"
            f"&client_id={settings.netsuite_consumer_key}"
            f"&state={state}"
        )
    else:
        raise ValueError(f"Unknown ERP type: {erp_type}")

    return {
        "auth_url": auth_url,
        "state": state,
    }


async def handle_oauth_callback(
    erp_type: str,
    code: str,
    state: str,
    realm_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Handle OAuth callback and exchange code for tokens.

    Design Note:
    - Verify state parameter to prevent CSRF
    - Exchange code for access token
    - Store tokens securely
    """
    # Verify state
    stored_state = _erp_connections.get(f"{erp_type}_state")
    if state != stored_state:
        raise ValueError("Invalid state parameter")

    # In production, exchange code for tokens via HTTP
    # For MVP, simulate successful connection
    _erp_connections[erp_type] = {
        "connected": True,
        "access_token": f"mock_token_{code[:8]}",
        "refresh_token": f"mock_refresh_{code[:8]}",
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "last_sync": datetime.utcnow().isoformat(),
        "realm_id": realm_id,  # QuickBooks company ID
        "company_name": f"Demo Company ({erp_type.title()})",
    }

    logger.info(f"ERP connected: {erp_type}")

    return _erp_connections[erp_type]


async def validate_erp_credentials(
    erp_type: str,
    credentials: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate ERP credentials without saving.

    Design Note:
    - Make test API call to verify credentials
    - Check permissions/scopes
    """
    # In production, make actual API call to validate
    # For MVP, simulate validation
    if credentials.get("access_token"):
        return {
            "valid": True,
            "message": "Credentials validated successfully",
            "company_name": "Demo Company",
        }

    return {
        "valid": False,
        "message": "Invalid or missing credentials",
    }


# =============================================================================
# CUSTOMER MANAGEMENT
# =============================================================================

async def list_erp_customers(
    erp_type: str,
    search: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    List customers from connected ERP.

    Design Note:
    - Implement pagination for large customer lists
    - Cache results for performance
    """
    # Check connection
    connection = _erp_connections.get(erp_type)
    if not connection or not connection.get("connected"):
        raise ValueError(f"{erp_type} not connected")

    # In production, fetch from ERP API
    # For MVP, return sample data
    sample_customers = [
        {"id": "BLUE-900", "name": "BlueCo Inc.", "email": "billing@blueco.com"},
        {"id": "ACME-001", "name": "ACME Services", "email": "ap@acme.com"},
        {"id": "TECH-123", "name": "TechCorp Ltd.", "email": "finance@techcorp.com"},
    ]

    if search:
        sample_customers = [
            c for c in sample_customers
            if search.lower() in c["name"].lower() or search.lower() in c["id"].lower()
        ]

    return sample_customers[:limit]


# =============================================================================
# FIELD MAPPING
# =============================================================================

async def get_field_mapping(erp_type: str) -> Dict[str, Any]:
    """Get field mapping for ERP invoice schema"""
    mappings = {
        "quickbooks": {
            "customer_ref": {"erp_field": "CustomerRef.value", "required": True},
            "invoice_date": {"erp_field": "TxnDate", "format": "YYYY-MM-DD"},
            "due_date": {"erp_field": "DueDate", "format": "YYYY-MM-DD"},
            "line.description": {"erp_field": "Line[].Description"},
            "line.quantity": {"erp_field": "Line[].SalesItemLineDetail.Qty"},
            "line.unit_price": {"erp_field": "Line[].SalesItemLineDetail.UnitPrice"},
            "line.amount": {"erp_field": "Line[].Amount"},
            "memo": {"erp_field": "PrivateNote"},
        },
        "xero": {
            "customer_ref": {"erp_field": "Contact.ContactID", "required": True},
            "invoice_date": {"erp_field": "Date", "format": "YYYY-MM-DD"},
            "due_date": {"erp_field": "DueDate", "format": "YYYY-MM-DD"},
            "line.description": {"erp_field": "LineItems[].Description"},
            "line.quantity": {"erp_field": "LineItems[].Quantity"},
            "line.unit_price": {"erp_field": "LineItems[].UnitAmount"},
            "line.amount": {"erp_field": "LineItems[].LineAmount"},
            "reference": {"erp_field": "Reference"},
        },
        "netsuite": {
            "customer_ref": {"erp_field": "entity", "required": True},
            "invoice_date": {"erp_field": "tranDate", "format": "YYYY-MM-DD"},
            "due_date": {"erp_field": "dueDate", "format": "YYYY-MM-DD"},
            "line.description": {"erp_field": "item[].description"},
            "line.quantity": {"erp_field": "item[].quantity"},
            "line.unit_price": {"erp_field": "item[].rate"},
            "line.amount": {"erp_field": "item[].amount"},
            "memo": {"erp_field": "memo"},
        },
    }

    return mappings.get(erp_type, {})


# =============================================================================
# INVOICE PUSH
# =============================================================================

async def push_invoice_to_erp(
    invoice: Dict[str, Any],
    erp_type: str,
    customer_ref: str,
) -> Dict[str, Any]:
    """
    Push approved invoice to ERP system.

    CRITICAL: This function should only be called for approved invoices.
    The calling code must verify approval status before calling.

    Design Note:
    - In production, implement actual ERP API calls
    - Handle errors and implement retry logic
    - Create credit memos for corrections
    """
    # Verify ERP is connected
    connection = _erp_connections.get(erp_type)
    if not connection or not connection.get("connected"):
        raise ValueError(f"{erp_type} not connected")

    # Build ERP payload based on type
    erp_payload = await _build_erp_payload(invoice, erp_type, customer_ref)

    # In production, make actual API call
    # For MVP, simulate successful push
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    erp_invoice_id = f"{erp_type.upper()}-{timestamp}"

    logger.info(f"Invoice {invoice['invoice_id']} pushed to {erp_type} as {erp_invoice_id}")

    # Update invoice with ERP reference
    invoice["erp_invoice_id"] = erp_invoice_id
    invoice["erp_type"] = erp_type
    invoice["pushed_at"] = datetime.utcnow().isoformat()
    invoice["status"] = "pushed"

    await save_invoice(invoice["invoice_id"], invoice)

    return {
        "erp_invoice_id": erp_invoice_id,
        "erp_type": erp_type,
        "pushed_at": invoice["pushed_at"],
        "payload": erp_payload,
    }


async def _build_erp_payload(
    invoice: Dict[str, Any],
    erp_type: str,
    customer_ref: str,
) -> Dict[str, Any]:
    """Build ERP-specific invoice payload"""
    lines = []
    for line in invoice.get("lines", []):
        lines.append({
            "description": line.get("description", ""),
            "quantity": float(line.get("quantity", 0)),
            "unit_price": float(line.get("unit_price", 0)),
            "amount": float(line.get("amount", 0)),
            "taxable": False,
        })

    base_payload = {
        "customer_ref": customer_ref,
        "lines": lines,
        "invoice_date": invoice.get("invoice_date", datetime.utcnow().isoformat())[:10],
        "due_date": invoice.get("due_date", "")[:10] if invoice.get("due_date") else None,
        "subtotal": float(invoice.get("subtotal", 0)),
        "tax_total": float(invoice.get("tax", 0)),
        "total": float(invoice.get("total", 0)),
        "memo": f"Generated by Crafta Control Room; invoice_id={invoice.get('invoice_id')}",
        "crafta_invoice_id": invoice.get("invoice_id"),
        "crafta_approval_id": invoice.get("approval_id"),
    }

    return base_payload
