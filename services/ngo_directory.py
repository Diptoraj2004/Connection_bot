"""
services/ngo_directory.py — DEPRECATED COMPATIBILITY SHIM.

All logic has moved to services/ngo_manager.py which has the full
database with financial filtering and email outreach.

This file exists only so legacy imports (chat_session, old routes)
don't break. It delegates to ngo_manager.
"""
from services.ngo_manager import (
    find_affordable_support,
    get_ngo_by_id,
    FULL_NGO_DATABASE as NGO_DATABASE,
)


def find_support(condition_or_test: str = "", online_only: bool = False) -> dict:
    """Compatibility shim — delegates to ngo_manager.find_affordable_support."""
    results = find_affordable_support(
        condition=condition_or_test,
        max_cost_inr=0,          # Default: free only
        prefer_online=online_only or True,
        limit=1,
    )
    if results:
        return results[0]
    # Absolute fallback
    return {
        "id":      "vandrevala",
        "name":    "Vandrevala Foundation",
        "type":    "Emergency / Counseling",
        "contact": "1860-2662-345 (24x7)",
        "cost_tier": "free",
    }


def list_all_ngos() -> list:
    return NGO_DATABASE
