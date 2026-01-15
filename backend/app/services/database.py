"""
Database service - in-memory storage for MVP

In production, replace with PostgreSQL/Supabase.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# In-memory storage (replace with actual DB in production)
_storage = {
    "contracts": {},
    "work_events": {},
    "invoices": {},
    "approvals": {},
    "action_logs": [],
}


async def init_db():
    """Initialize database connection"""
    logger.info("Database initialized (in-memory mode)")


async def close_db():
    """Close database connection"""
    logger.info("Database connection closed")


# =============================================================================
# CONTRACT STORAGE
# =============================================================================

async def save_contract(contract_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Save or update a contract"""
    data["updated_at"] = datetime.utcnow().isoformat()
    _storage["contracts"][contract_id] = data
    return data


async def get_contract_by_id(contract_id: str) -> Optional[Dict[str, Any]]:
    """Get a contract by ID"""
    return _storage["contracts"].get(contract_id)


async def list_all_contracts(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List contracts with optional filtering"""
    contracts = list(_storage["contracts"].values())

    if status:
        contracts = [c for c in contracts if c.get("status") == status]

    # Sort by upload time descending
    contracts.sort(key=lambda x: x.get("upload_time", ""), reverse=True)

    total = len(contracts)
    contracts = contracts[offset:offset + limit]

    return {
        "contracts": contracts,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# =============================================================================
# WORK EVENTS STORAGE
# =============================================================================

async def save_work_events_batch(contract_id: str, events: List[Dict[str, Any]]):
    """Save batch of work events"""
    if contract_id not in _storage["work_events"]:
        _storage["work_events"][contract_id] = []

    _storage["work_events"][contract_id].extend(events)


async def get_work_events_by_contract(
    contract_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get work events for a contract"""
    events = _storage["work_events"].get(contract_id, [])

    # Filter by date range
    if start_date:
        events = [e for e in events if e.get("date", "") >= start_date.isoformat()]
    if end_date:
        events = [e for e in events if e.get("date", "") <= end_date.isoformat()]

    total = len(events)
    events = events[offset:offset + limit]

    return {
        "events": events,
        "total": total,
    }


async def save_single_work_event(contract_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Save a single work event"""
    if contract_id not in _storage["work_events"]:
        _storage["work_events"][contract_id] = []

    _storage["work_events"][contract_id].append(event)
    return event


async def update_work_event_by_id(event_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a work event"""
    for contract_id, events in _storage["work_events"].items():
        for i, event in enumerate(events):
            if event.get("event_id") == event_id:
                events[i].update(update_data)
                return events[i]
    return None


async def delete_work_event_by_id(event_id: str) -> bool:
    """Delete a work event"""
    for contract_id, events in _storage["work_events"].items():
        for i, event in enumerate(events):
            if event.get("event_id") == event_id:
                events.pop(i)
                return True
    return False


# =============================================================================
# INVOICE STORAGE
# =============================================================================

async def save_invoice(invoice_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Save or update an invoice"""
    data["updated_at"] = datetime.utcnow().isoformat()
    _storage["invoices"][invoice_id] = data
    return data


async def get_invoice_by_id(invoice_id: str) -> Optional[Dict[str, Any]]:
    """Get an invoice by ID"""
    return _storage["invoices"].get(invoice_id)


async def list_all_invoices(
    status: Optional[str] = None,
    contract_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List invoices with optional filtering"""
    invoices = list(_storage["invoices"].values())

    if status:
        invoices = [i for i in invoices if i.get("status") == status]
    if contract_id:
        invoices = [i for i in invoices if i.get("contract_id") == contract_id]

    # Sort by created_at descending
    invoices.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    total = len(invoices)
    invoices = invoices[offset:offset + limit]

    return {
        "invoices": invoices,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# =============================================================================
# APPROVAL STORAGE
# =============================================================================

async def save_approval(approval_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Save an approval"""
    _storage["approvals"][approval_id] = data
    return data


async def get_approval_by_id(approval_id: str) -> Optional[Dict[str, Any]]:
    """Get an approval by ID"""
    return _storage["approvals"].get(approval_id)


async def get_approvals_by_invoice(invoice_id: str) -> List[Dict[str, Any]]:
    """Get all approvals for an invoice"""
    return [
        a for a in _storage["approvals"].values()
        if a.get("invoice_id") == invoice_id
    ]


# =============================================================================
# ACTION LOG STORAGE
# =============================================================================

async def save_action_log(log: Dict[str, Any]):
    """Save an action log entry"""
    _storage["action_logs"].append(log)


async def get_action_logs(
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get action logs with optional filtering"""
    logs = _storage["action_logs"]

    if entity_id:
        logs = [l for l in logs if l.get("entity_id") == entity_id]
    if entity_type:
        logs = [l for l in logs if l.get("entity_type") == entity_type]

    # Sort by timestamp descending
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return logs[:limit]


# =============================================================================
# SEED DATA
# =============================================================================

async def seed_sample_data():
    """Seed sample data for development"""
    from backend.schemas.json_schemas import (
        SAMPLE_CONTRACT,
        SAMPLE_WORK_EVENT,
        SAMPLE_INVOICE_DRAFT,
        SAMPLE_APPROVAL_LOG,
    )

    # Seed contract
    await save_contract(SAMPLE_CONTRACT["contract_id"], SAMPLE_CONTRACT)

    # Seed work events
    await save_single_work_event(
        SAMPLE_WORK_EVENT["contract_id"],
        SAMPLE_WORK_EVENT,
    )

    # Seed invoice
    await save_invoice(SAMPLE_INVOICE_DRAFT["invoice_id"], SAMPLE_INVOICE_DRAFT)

    # Seed approval
    await save_approval(SAMPLE_APPROVAL_LOG["approval_id"], SAMPLE_APPROVAL_LOG)

    logger.info("Sample data seeded successfully")
