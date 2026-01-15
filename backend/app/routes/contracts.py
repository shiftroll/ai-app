"""
Contract Management API Routes

Endpoints:
- POST /api/contracts/upload - Upload contract file(s)
- GET /api/contracts/{id} - Get parsed contract
- GET /api/contracts - List all contracts
- PUT /api/contracts/{id}/terms - Update extracted terms
- POST /api/contracts/{id}/reparse - Re-run parsing
- POST /api/anonize/{contract_id} - Anonymize contract for case study
"""

import os
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.config import settings
from app.services.storage import save_uploaded_file, get_file_path
from app.services.audit_service import log_action
from app.services.contract_service import (
    parse_contract_async,
    get_contract,
    list_contracts,
    update_contract_terms,
    anonymize_contract,
)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ContractUploadResponse(BaseModel):
    """Response for contract upload"""
    contract_id: str
    filename: str
    status: str
    message: str


class ContractTermUpdate(BaseModel):
    """Request to update contract terms"""
    clause_id: str
    description: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    confidence: Optional[float] = None


class AnonymizeRequest(BaseModel):
    """Request to anonymize a contract"""
    round_amounts_to: int = Field(default=1000, description="Round amounts to nearest X")
    replace_names: bool = Field(default=True, description="Replace party names with placeholders")
    remove_dates: bool = Field(default=False, description="Remove specific dates")


class AnonymizeResponse(BaseModel):
    """Response with anonymized contract"""
    contract_id: str
    anonymized_data: Dict[str, Any]
    original_hash: str
    anonymization_rules_applied: List[str]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    uploaded_by: str = Query(..., description="User ID uploading the contract"),
) -> ContractUploadResponse:
    """
    Upload a contract file (PDF or DOCX) for parsing.

    The file will be stored and parsing will begin asynchronously.
    Check the contract status via GET /api/contracts/{id}.

    **Example Request:**
    ```
    curl -X POST "/api/contracts/upload" \
      -H "Content-Type: multipart/form-data" \
      -F "file=@contract.pdf" \
      -F "uploaded_by=u:user@example.com"
    ```

    **Example Response:**
    ```json
    {
      "contract_id": "ctr_20260115_abc123",
      "filename": "contract.pdf",
      "status": "parsing",
      "message": "Contract uploaded successfully. Parsing in progress."
    }
    ```
    """
    # Validate file type
    allowed_extensions = [".pdf", ".docx", ".doc"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Validate file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )

    # Generate contract ID
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_hash = hashlib.md5(content).hexdigest()[:6]
    contract_id = f"ctr_{timestamp}_{file_hash}"

    # Save file
    file_path = await save_uploaded_file(content, file.filename, contract_id)

    # Log action
    await log_action(
        kind="upload",
        entity_type="contract",
        entity_id=contract_id,
        actor_id=uploaded_by,
        payload={"filename": file.filename, "size": len(content)},
    )

    # Start async parsing
    background_tasks.add_task(
        parse_contract_async,
        contract_id=contract_id,
        file_path=file_path,
        uploaded_by=uploaded_by,
    )

    return ContractUploadResponse(
        contract_id=contract_id,
        filename=file.filename,
        status="parsing",
        message="Contract uploaded successfully. Parsing in progress.",
    )


@router.get("/{contract_id}")
async def get_contract_by_id(
    contract_id: str,
    include_raw_text: bool = Query(default=False, description="Include full raw text"),
) -> Dict[str, Any]:
    """
    Retrieve a parsed contract by ID.

    **Example Response:**
    ```json
    {
      "contract_id": "ctr_20260115_001",
      "source_filename": "MSA-ACME.pdf",
      "uploaded_by": "u:ridho@example.com",
      "upload_time": "2026-01-15T10:12:00Z",
      "parties": [...],
      "currency": "USD",
      "terms": [...],
      "status": "parsed"
    }
    ```
    """
    contract = await get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not include_raw_text and "raw_text" in contract:
        # Truncate raw text
        if contract["raw_text"]:
            contract["raw_text"] = contract["raw_text"][:500] + "..."

    return contract


@router.get("")
async def list_all_contracts(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """
    List all contracts with optional filtering.

    **Query Parameters:**
    - `status`: Filter by contract status (uploaded, parsing, parsed, failed)
    - `limit`: Maximum number of results (default 50, max 100)
    - `offset`: Pagination offset

    **Example Response:**
    ```json
    {
      "contracts": [...],
      "total": 25,
      "limit": 50,
      "offset": 0
    }
    ```
    """
    result = await list_contracts(status=status, limit=limit, offset=offset)
    return result


@router.put("/{contract_id}/terms")
async def update_terms(
    contract_id: str,
    updates: List[ContractTermUpdate],
    updated_by: str = Query(..., description="User ID making the update"),
) -> Dict[str, Any]:
    """
    Update extracted terms in a contract.

    Used when a human reviewer corrects auto-extracted values.
    All changes are logged to the audit trail.

    **Example Request:**
    ```json
    [
      {
        "clause_id": "c1",
        "value": "250",
        "confidence": 1.0
      }
    ]
    ```
    """
    contract = await get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    updated_contract = await update_contract_terms(
        contract_id=contract_id,
        updates=[u.dict(exclude_none=True) for u in updates],
        updated_by=updated_by,
    )

    # Log action
    await log_action(
        kind="edit",
        entity_type="contract",
        entity_id=contract_id,
        actor_id=updated_by,
        payload={"updates": [u.dict() for u in updates]},
    )

    return {
        "message": "Terms updated successfully",
        "contract_id": contract_id,
        "updated_clauses": [u.clause_id for u in updates],
    }


@router.post("/{contract_id}/reparse")
async def reparse_contract(
    contract_id: str,
    background_tasks: BackgroundTasks,
    requested_by: str = Query(..., description="User ID requesting reparse"),
    use_llm: bool = Query(default=True, description="Use LLM for parsing"),
) -> Dict[str, Any]:
    """
    Re-run parsing on an existing contract.

    Useful when parsing parameters are updated or OCR needs improvement.
    """
    contract = await get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    file_path = get_file_path(contract_id, contract.get("source_filename", ""))

    # Start async parsing
    background_tasks.add_task(
        parse_contract_async,
        contract_id=contract_id,
        file_path=file_path,
        uploaded_by=requested_by,
        use_llm=use_llm,
    )

    # Log action
    await log_action(
        kind="parse",
        entity_type="contract",
        entity_id=contract_id,
        actor_id=requested_by,
        payload={"use_llm": use_llm, "action": "reparse"},
    )

    return {
        "message": "Re-parsing initiated",
        "contract_id": contract_id,
        "status": "parsing",
    }


@router.post("/anonize/{contract_id}", response_model=AnonymizeResponse)
async def anonymize_contract_endpoint(
    contract_id: str,
    request: AnonymizeRequest,
    requested_by: str = Query(..., description="User ID requesting anonymization"),
) -> AnonymizeResponse:
    """
    Anonymize a contract for case study or public sharing.

    Replaces sensitive data while preserving structure and aggregated values.

    **Anonymization Rules:**
    - Party names replaced with generic placeholders (e.g., "Vendor A", "Client B")
    - Amounts rounded to nearest specified value
    - Specific dates optionally removed
    - Contract structure and clause types preserved
    """
    contract = await get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Calculate original hash
    import json
    original_hash = hashlib.sha256(
        json.dumps(contract, sort_keys=True, default=str).encode()
    ).hexdigest()

    # Anonymize
    anonymized, rules_applied = await anonymize_contract(
        contract=contract,
        round_amounts_to=request.round_amounts_to,
        replace_names=request.replace_names,
        remove_dates=request.remove_dates,
    )

    # Log action
    await log_action(
        kind="anonymize",
        entity_type="contract",
        entity_id=contract_id,
        actor_id=requested_by,
        payload={"rules": request.dict()},
    )

    return AnonymizeResponse(
        contract_id=contract_id,
        anonymized_data=anonymized,
        original_hash=original_hash,
        anonymization_rules_applied=rules_applied,
    )
