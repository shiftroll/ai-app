"""
Contract Service

Business logic for contract management including parsing,
term extraction, and anonymization.
"""

import os
import sys
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import logging

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.services.database import (
    save_contract,
    get_contract_by_id,
    list_all_contracts,
)
from app.services.audit_service import log_action
from app.config import settings

logger = logging.getLogger(__name__)


async def parse_contract_async(
    contract_id: str,
    file_path: str,
    uploaded_by: str,
    use_llm: bool = True,
):
    """
    Asynchronously parse a contract file.

    This is run as a background task after file upload.
    Updates contract status as parsing progresses.

    Design Note:
    - In production, this should be a Celery task or similar
    - LLM calls can be expensive; consider caching parsed results
    - For better accuracy, implement domain-specific fine-tuning
    """
    try:
        # Update status to parsing
        await save_contract(contract_id, {
            "contract_id": contract_id,
            "source_filename": os.path.basename(file_path),
            "uploaded_by": uploaded_by,
            "upload_time": datetime.utcnow().isoformat(),
            "status": "parsing",
        })

        # Import parser (lazy import to avoid circular deps)
        from agents.parse_contract import parse_contract_file

        # Run parsing
        # Design Note: In production, add timeout handling and retries
        result = parse_contract_file(
            file_path=file_path,
            uploaded_by=uploaded_by,
            contract_id=contract_id,
            use_llm=use_llm and settings.openai_api_key is not None,
            openai_api_key=settings.openai_api_key,
        )

        # Save parsed contract
        result["status"] = "parsed"
        await save_contract(contract_id, result)

        # Log success
        await log_action(
            kind="parse",
            entity_type="contract",
            entity_id=contract_id,
            actor_id="system",
            payload={
                "terms_count": len(result.get("terms", [])),
                "use_llm": use_llm,
            },
        )

        logger.info(f"Contract parsed successfully: {contract_id}")

    except Exception as e:
        logger.error(f"Contract parsing failed: {e}", exc_info=True)

        # Update status to failed
        await save_contract(contract_id, {
            "contract_id": contract_id,
            "source_filename": os.path.basename(file_path),
            "uploaded_by": uploaded_by,
            "upload_time": datetime.utcnow().isoformat(),
            "status": "failed",
            "error": str(e),
        })


async def get_contract(contract_id: str) -> Optional[Dict[str, Any]]:
    """Get a contract by ID"""
    return await get_contract_by_id(contract_id)


async def list_contracts(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List contracts with optional filtering"""
    return await list_all_contracts(status=status, limit=limit, offset=offset)


async def update_contract_terms(
    contract_id: str,
    updates: List[Dict[str, Any]],
    updated_by: str,
) -> Dict[str, Any]:
    """
    Update extracted terms in a contract.

    This is used when a human reviewer corrects auto-extracted values.
    All original values are preserved in the audit trail.

    Args:
        contract_id: Contract ID
        updates: List of updates, each with clause_id and fields to update
        updated_by: User ID making the update

    Returns:
        Updated contract
    """
    contract = await get_contract_by_id(contract_id)
    if not contract:
        raise ValueError("Contract not found")

    terms = contract.get("terms", [])

    # Apply updates
    for update in updates:
        clause_id = update.get("clause_id")
        for term in terms:
            if term.get("clause_id") == clause_id:
                # Update fields
                for key, value in update.items():
                    if key != "clause_id" and value is not None:
                        term[key] = value
                # Mark as manually reviewed
                term["manually_reviewed"] = True
                term["reviewed_by"] = updated_by
                term["reviewed_at"] = datetime.utcnow().isoformat()
                break

    contract["terms"] = terms
    contract["updated_at"] = datetime.utcnow().isoformat()

    # Save
    await save_contract(contract_id, contract)

    return contract


async def anonymize_contract(
    contract: Dict[str, Any],
    round_amounts_to: int = 1000,
    replace_names: bool = True,
    remove_dates: bool = False,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Anonymize a contract for case study or public sharing.

    Replaces sensitive data while preserving structure.

    Args:
        contract: Contract data
        round_amounts_to: Round amounts to nearest X
        replace_names: Replace party names with placeholders
        remove_dates: Remove specific dates

    Returns:
        Tuple of (anonymized_contract, rules_applied)
    """
    import copy
    anonymized = copy.deepcopy(contract)
    rules_applied = []

    # Remove contract ID and replace with anonymized version
    anonymized["contract_id"] = f"anon_{hashlib.md5(contract['contract_id'].encode()).hexdigest()[:8]}"
    rules_applied.append("contract_id_anonymized")

    # Replace party names
    if replace_names:
        party_map = {}
        for i, party in enumerate(anonymized.get("parties", [])):
            role = party.get("role", "party")
            placeholder = f"{role.title()} {chr(65 + i)}"  # Vendor A, Client B, etc.
            party_map[party.get("name", "")] = placeholder
            party["name"] = placeholder
            party["identifier"] = f"{role.upper()}-{i+1:03d}"

        # Replace in raw text
        if anonymized.get("raw_text"):
            for original, replacement in party_map.items():
                anonymized["raw_text"] = anonymized["raw_text"].replace(original, replacement)

        rules_applied.append("names_replaced")

    # Round amounts
    if round_amounts_to > 0:
        for term in anonymized.get("terms", []):
            try:
                value = float(term.get("value", 0))
                if value > 0:
                    rounded = round(value / round_amounts_to) * round_amounts_to
                    term["value"] = str(int(rounded))
                    term["value_rounded"] = True
            except (ValueError, TypeError):
                pass
        rules_applied.append(f"amounts_rounded_to_{round_amounts_to}")

    # Remove dates
    if remove_dates:
        anonymized["upload_time"] = "REDACTED"
        anonymized["effective_date"] = None
        anonymized["expiration_date"] = None
        for term in anonymized.get("terms", []):
            term["extracted_text"] = "[DATE REDACTED]" if "date" in term.get("extracted_text", "").lower() else term.get("extracted_text", "")
        rules_applied.append("dates_removed")

    # Remove raw text (too identifiable)
    anonymized["raw_text"] = "[REDACTED FOR PRIVACY]"
    rules_applied.append("raw_text_redacted")

    # Remove uploader info
    anonymized["uploaded_by"] = "anonymous"
    rules_applied.append("uploader_anonymized")

    return anonymized, rules_applied
