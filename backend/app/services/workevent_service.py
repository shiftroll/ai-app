"""
Work Event Service

Business logic for work event management.
"""

import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from app.services.database import (
    save_work_events_batch,
    get_work_events_by_contract,
    save_single_work_event,
    update_work_event_by_id,
    delete_work_event_by_id,
)

logger = logging.getLogger(__name__)


async def save_work_events(contract_id: str, events: List[Dict[str, Any]]):
    """Save batch of work events for a contract"""
    await save_work_events_batch(contract_id, events)
    logger.info(f"Saved {len(events)} work events for contract {contract_id}")


async def get_work_events(
    contract_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get work events for a contract with optional filtering"""
    return await get_work_events_by_contract(
        contract_id=contract_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


async def create_work_event(
    contract_id: str,
    event_data: Dict[str, Any],
    created_by: str,
) -> Dict[str, Any]:
    """Create a single work event"""
    # Generate event ID if not provided
    if not event_data.get("event_id"):
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        hash_suffix = hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:4]
        event_data["event_id"] = f"we_{timestamp}_{hash_suffix}"

    event_data["contract_id"] = contract_id
    event_data["uploaded_by"] = created_by
    event_data["uploaded_at"] = datetime.utcnow().isoformat()

    await save_single_work_event(contract_id, event_data)
    logger.info(f"Created work event {event_data['event_id']} for contract {contract_id}")

    return event_data


async def update_work_event(
    event_id: str,
    update_data: Dict[str, Any],
    updated_by: str,
) -> Optional[Dict[str, Any]]:
    """Update a work event"""
    update_data["updated_by"] = updated_by
    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = await update_work_event_by_id(event_id, update_data)
    if result:
        logger.info(f"Updated work event {event_id}")
    return result


async def delete_work_event(event_id: str, deleted_by: str) -> bool:
    """Delete a work event"""
    result = await delete_work_event_by_id(event_id)
    if result:
        logger.info(f"Deleted work event {event_id} by {deleted_by}")
    return result
