"""
Work Events API Routes

Endpoints:
- POST /api/workevents/{contract_id}/upload - Upload work events CSV
- GET /api/workevents/{contract_id} - List work events for a contract
- POST /api/workevents/{contract_id} - Add single work event
- PUT /api/workevents/{event_id} - Update work event
- DELETE /api/workevents/{event_id} - Delete work event
"""

import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.audit_service import log_action
from app.services.workevent_service import (
    save_work_events,
    get_work_events,
    create_work_event,
    update_work_event,
    delete_work_event,
)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class WorkEventCreate(BaseModel):
    """Request to create a work event"""
    event_id: Optional[str] = None
    date: datetime
    description: str
    units: float
    unit_type: str
    amount: Optional[float] = None
    external_ref: Optional[str] = None


class WorkEventUpdate(BaseModel):
    """Request to update a work event"""
    date: Optional[datetime] = None
    description: Optional[str] = None
    units: Optional[float] = None
    unit_type: Optional[str] = None
    amount: Optional[float] = None
    external_ref: Optional[str] = None


class WorkEventResponse(BaseModel):
    """Work event response"""
    event_id: str
    contract_id: str
    date: datetime
    description: str
    units: float
    unit_type: str
    amount: Optional[float]
    external_ref: Optional[str]
    uploaded_at: datetime


class UploadWorkEventsResponse(BaseModel):
    """Response for work events upload"""
    contract_id: str
    events_uploaded: int
    events_failed: int
    errors: List[str]
    message: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/{contract_id}/upload", response_model=UploadWorkEventsResponse)
async def upload_work_events(
    contract_id: str,
    file: UploadFile = File(...),
    uploaded_by: str = Query(..., description="User ID uploading events"),
) -> UploadWorkEventsResponse:
    """
    Upload work events from CSV file.

    **Expected CSV columns:**
    - event_id (optional, auto-generated if missing)
    - date (required, format: YYYY-MM-DD)
    - description (required)
    - units (required, numeric)
    - unit_type (required, e.g., "hour", "day", "item")
    - amount (optional, pre-calculated amount)
    - external_ref (optional, e.g., PO number)

    **Example CSV:**
    ```csv
    event_id,date,description,units,unit_type,amount,external_ref
    we_001,2025-12-12,Consulting hours for Dec,10,hour,2000,PO-778
    we_002,2025-12-15,Additional support,5,hour,1000,PO-779
    ```

    **Example Response:**
    ```json
    {
      "contract_id": "ctr_20260115_001",
      "events_uploaded": 10,
      "events_failed": 0,
      "errors": [],
      "message": "Successfully uploaded 10 work events"
    }
    ```
    """
    # Read and parse CSV
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    # Parse CSV
    events = []
    errors = []
    reader = csv.DictReader(io.StringIO(text))

    for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
        try:
            event = {
                "event_id": row.get("event_id") or f"we_{contract_id}_{row_num}",
                "contract_id": contract_id,
                "date": row.get("date"),
                "description": row.get("description", ""),
                "units": float(row.get("units", 0)),
                "unit_type": row.get("unit_type", "unit"),
                "amount": float(row["amount"]) if row.get("amount") else None,
                "external_ref": row.get("external_ref"),
                "uploaded_by": uploaded_by,
                "uploaded_at": datetime.utcnow().isoformat(),
            }
            events.append(event)
        except (ValueError, KeyError) as e:
            errors.append(f"Row {row_num}: {str(e)}")

    # Save events
    if events:
        await save_work_events(contract_id, events)

    # Log action
    await log_action(
        kind="upload",
        entity_type="work_events",
        entity_id=contract_id,
        actor_id=uploaded_by,
        payload={
            "filename": file.filename,
            "events_count": len(events),
            "errors_count": len(errors),
        },
    )

    return UploadWorkEventsResponse(
        contract_id=contract_id,
        events_uploaded=len(events),
        events_failed=len(errors),
        errors=errors[:10],  # Limit error messages
        message=f"Successfully uploaded {len(events)} work events"
        if events
        else "No valid events found",
    )


@router.get("/{contract_id}", response_model=Dict[str, Any])
async def list_work_events(
    contract_id: str,
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """
    List work events for a contract.

    **Query Parameters:**
    - `start_date`: Filter events on or after this date
    - `end_date`: Filter events on or before this date
    - `limit`: Maximum results (default 100, max 500)
    - `offset`: Pagination offset

    **Example Response:**
    ```json
    {
      "events": [
        {
          "event_id": "we_001",
          "date": "2025-12-12",
          "description": "Consulting hours for Dec",
          "units": 10,
          "unit_type": "hour",
          "amount": 2000,
          "external_ref": "PO-778"
        }
      ],
      "total": 15,
      "contract_id": "ctr_20260115_001"
    }
    ```
    """
    events = await get_work_events(
        contract_id=contract_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return {
        "events": events.get("events", []),
        "total": events.get("total", 0),
        "contract_id": contract_id,
    }


@router.post("/{contract_id}", response_model=WorkEventResponse)
async def add_work_event(
    contract_id: str,
    event: WorkEventCreate,
    created_by: str = Query(..., description="User ID creating the event"),
) -> WorkEventResponse:
    """
    Add a single work event to a contract.

    **Example Request:**
    ```json
    {
      "date": "2025-12-20",
      "description": "Additional consulting work",
      "units": 8,
      "unit_type": "hour",
      "amount": 1600,
      "external_ref": "PO-780"
    }
    ```
    """
    result = await create_work_event(
        contract_id=contract_id,
        event_data=event.dict(),
        created_by=created_by,
    )

    # Log action
    await log_action(
        kind="upload",
        entity_type="work_event",
        entity_id=result["event_id"],
        actor_id=created_by,
        payload=event.dict(),
    )

    return WorkEventResponse(**result)


@router.put("/{event_id}", response_model=WorkEventResponse)
async def update_event(
    event_id: str,
    update: WorkEventUpdate,
    updated_by: str = Query(..., description="User ID updating the event"),
) -> WorkEventResponse:
    """
    Update an existing work event.
    """
    result = await update_work_event(
        event_id=event_id,
        update_data=update.dict(exclude_none=True),
        updated_by=updated_by,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Work event not found")

    # Log action
    await log_action(
        kind="edit",
        entity_type="work_event",
        entity_id=event_id,
        actor_id=updated_by,
        payload=update.dict(exclude_none=True),
    )

    return WorkEventResponse(**result)


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    deleted_by: str = Query(..., description="User ID deleting the event"),
) -> Dict[str, Any]:
    """
    Delete a work event.
    """
    success = await delete_work_event(event_id, deleted_by)

    if not success:
        raise HTTPException(status_code=404, detail="Work event not found")

    # Log action
    await log_action(
        kind="edit",
        entity_type="work_event",
        entity_id=event_id,
        actor_id=deleted_by,
        payload={"action": "delete"},
    )

    return {
        "message": "Work event deleted",
        "event_id": event_id,
    }
