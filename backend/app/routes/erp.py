"""
ERP Integration API Routes

Endpoints:
- GET /api/erp/status - Get ERP connection status
- POST /api/erp/{erp_type}/connect - Initiate OAuth flow
- GET /api/erp/{erp_type}/callback - OAuth callback
- POST /api/erp/{erp_type}/validate - Validate credentials
- GET /api/erp/{erp_type}/customers - List customers in ERP
- GET /api/erp/field-mapping/{erp_type} - Get field mapping for ERP
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import settings
from app.services.erp_service import (
    get_erp_status,
    initiate_oauth_flow,
    handle_oauth_callback,
    validate_erp_credentials,
    list_erp_customers,
    get_field_mapping,
)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ERPCredentials(BaseModel):
    """ERP credentials for validation"""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    realm_id: Optional[str] = None  # QuickBooks
    tenant_id: Optional[str] = None  # Xero


class ERPStatusResponse(BaseModel):
    """ERP connection status"""
    erp_type: str
    connected: bool
    last_sync: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_all_erp_status() -> Dict[str, Any]:
    """
    Get connection status for all configured ERPs.

    **Example Response:**
    ```json
    {
      "quickbooks": {
        "connected": true,
        "last_sync": "2026-01-20T08:00:00Z",
        "expires_at": "2026-02-19T08:00:00Z"
      },
      "xero": {
        "connected": false,
        "error": "Not configured"
      },
      "netsuite": {
        "connected": false,
        "error": "Not configured"
      }
    }
    ```
    """
    status = {}
    for erp in ["quickbooks", "xero", "netsuite"]:
        status[erp] = await get_erp_status(erp)
    return status


@router.get("/status/{erp_type}")
async def get_single_erp_status(erp_type: str) -> ERPStatusResponse:
    """Get connection status for a specific ERP"""
    if erp_type not in ["quickbooks", "xero", "netsuite"]:
        raise HTTPException(status_code=400, detail="Invalid ERP type")

    status = await get_erp_status(erp_type)
    return ERPStatusResponse(erp_type=erp_type, **status)


@router.post("/{erp_type}/connect")
async def connect_erp(
    erp_type: str,
    request: Request,
) -> Dict[str, Any]:
    """
    Initiate OAuth connection flow for an ERP.

    Returns the authorization URL to redirect the user to.

    **Supported ERPs:**
    - quickbooks
    - xero
    - netsuite

    **Example Response:**
    ```json
    {
      "erp_type": "quickbooks",
      "auth_url": "https://appcenter.intuit.com/connect/oauth2?...",
      "state": "random-state-string"
    }
    ```
    """
    if erp_type not in ["quickbooks", "xero", "netsuite"]:
        raise HTTPException(status_code=400, detail="Invalid ERP type")

    result = await initiate_oauth_flow(erp_type)

    return {
        "erp_type": erp_type,
        "auth_url": result["auth_url"],
        "state": result["state"],
    }


@router.get("/{erp_type}/callback")
async def erp_oauth_callback(
    erp_type: str,
    code: str = Query(...),
    state: str = Query(...),
    realm_id: Optional[str] = Query(default=None),  # QuickBooks
) -> RedirectResponse:
    """
    OAuth callback endpoint.

    This is called by the ERP after user authorization.
    Exchanges the code for access tokens.
    """
    if erp_type not in ["quickbooks", "xero", "netsuite"]:
        raise HTTPException(status_code=400, detail="Invalid ERP type")

    try:
        await handle_oauth_callback(
            erp_type=erp_type,
            code=code,
            state=state,
            realm_id=realm_id,
        )
        # Redirect to success page
        return RedirectResponse(url=f"/settings/erp?connected={erp_type}&success=true")
    except Exception as e:
        # Redirect to error page
        return RedirectResponse(url=f"/settings/erp?error={str(e)}")


@router.post("/{erp_type}/validate")
async def validate_credentials(
    erp_type: str,
    credentials: ERPCredentials,
) -> Dict[str, Any]:
    """
    Validate ERP credentials without saving.

    Tests the connection and returns validation result.
    """
    if erp_type not in ["quickbooks", "xero", "netsuite"]:
        raise HTTPException(status_code=400, detail="Invalid ERP type")

    result = await validate_erp_credentials(erp_type, credentials.dict())

    return {
        "erp_type": erp_type,
        "valid": result["valid"],
        "message": result.get("message", ""),
        "company_name": result.get("company_name"),
    }


@router.get("/{erp_type}/customers")
async def list_customers(
    erp_type: str,
    search: Optional[str] = Query(default=None, description="Search term"),
    limit: int = Query(default=50, le=200),
) -> Dict[str, Any]:
    """
    List customers from the connected ERP.

    Used to map Crafta contracts to ERP customer records.

    **Example Response:**
    ```json
    {
      "customers": [
        {
          "id": "BLUE-900",
          "name": "BlueCo Inc.",
          "email": "billing@blueco.com"
        }
      ],
      "total": 1
    }
    ```
    """
    if erp_type not in ["quickbooks", "xero", "netsuite"]:
        raise HTTPException(status_code=400, detail="Invalid ERP type")

    customers = await list_erp_customers(erp_type, search=search, limit=limit)

    return {
        "erp_type": erp_type,
        "customers": customers,
        "total": len(customers),
    }


@router.get("/field-mapping/{erp_type}")
async def get_erp_field_mapping(erp_type: str) -> Dict[str, Any]:
    """
    Get field mapping between Crafta InvoiceDraft and ERP invoice schema.

    Used to understand how data maps to each ERP.

    **Example Response (QuickBooks):**
    ```json
    {
      "erp_type": "quickbooks",
      "mapping": {
        "customer_ref": {
          "erp_field": "CustomerRef.value",
          "required": true
        },
        "invoice_date": {
          "erp_field": "TxnDate",
          "format": "YYYY-MM-DD"
        },
        "line.description": {
          "erp_field": "Line[].Description"
        },
        "line.amount": {
          "erp_field": "Line[].Amount"
        }
      }
    }
    ```
    """
    if erp_type not in ["quickbooks", "xero", "netsuite"]:
        raise HTTPException(status_code=400, detail="Invalid ERP type")

    mapping = await get_field_mapping(erp_type)

    return {
        "erp_type": erp_type,
        "mapping": mapping,
    }
