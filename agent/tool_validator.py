"""
Tool Argument Validator and Safety Approval Gate for IncidentMind AI
Ensures parameter safety, canonical service resolution, and Human-In-The-Loop gatekeeping.
"""

from typing import Dict, Any, Tuple, Optional
from data.db import get_all_services

# Allowed Read-Only Diagnostic Tools (Auto-approved)
SAFE_DIAGNOSTIC_TOOLS = {
    "get_service_status",
    "get_recent_logs",
    "get_deployment_history",
    "get_database_metrics",
    "check_health_endpoint"
}

# State-Altering Actions Requiring Human-In-The-Loop Approval
RESTRICTED_REMEDIATION_ACTIONS = {
    "scale_connection_pool": {"risk": "Medium", "desc": "Modify database connection pool max_connections"},
    "restart_pods": {"risk": "High", "desc": "Perform rolling restart of target pods"},
    "rotate_credentials": {"risk": "Critical", "desc": "Trigger secrets rotation in Secrets Manager"},
    "rollback_deployment": {"risk": "High", "desc": "Roll back Kubernetes deployment to previous revision"},
    "flush_cache": {"risk": "Medium", "desc": "Flush distributed Redis cache keys"}
}


def normalize_service_name(raw_name: str) -> str:
    """Resolves arbitrary service nicknames or abbreviations to canonical service catalog name."""
    if not raw_name:
        return "Payment API"

    raw_lower = raw_name.lower().replace("-", " ").replace("_", " ").strip()
    services = get_all_services()

    for s in services:
        s_name = s["name"]
        s_lower = s_name.lower().replace("-", " ")
        if raw_lower in s_lower or s_lower in raw_lower:
            return s_name

    # Keyword heuristics
    if "pay" in raw_lower:
        return "Payment API"
    if "auth" in raw_lower or "token" in raw_lower or "jwt" in raw_lower:
        return "Authentication Service"
    if "order" in raw_lower or "cart" in raw_lower or "checkout" in raw_lower:
        return "Order Service"
    if "notify" in raw_lower or "sms" in raw_lower or "email" in raw_lower:
        return "Notification Service"
    if "inv" in raw_lower or "stock" in raw_lower:
        return "Inventory Service"
    if "search" in raw_lower or "elastic" in raw_lower:
        return "Search API"
    if "db" in raw_lower or "database" in raw_lower or "postgres" in raw_lower:
        return "Database Service"
    if "gate" in raw_lower or "envoy" in raw_lower or "proxy" in raw_lower:
        return "API Gateway"

    return raw_name


def validate_and_sanitize_tool_call(tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates tool name and sanitizes parameters.
    Returns (is_valid, error_or_info_message, sanitized_parameters).
    """
    if tool_name not in SAFE_DIAGNOSTIC_TOOLS and tool_name not in RESTRICTED_REMEDIATION_ACTIONS:
        return False, f"Unknown or unauthorized tool: '{tool_name}'", {}

    sanitized = dict(parameters)

    # Sanitize service parameter if present
    if "service_name" in sanitized:
        sanitized["service_name"] = normalize_service_name(sanitized["service_name"])
    elif "service" in sanitized:
        sanitized["service_name"] = normalize_service_name(sanitized.pop("service"))

    # Sanitize integer lines
    if "lines" in sanitized:
        try:
            sanitized["lines"] = max(1, min(100, int(sanitized["lines"])))
        except (ValueError, TypeError):
            sanitized["lines"] = 20

    return True, "Valid", sanitized


def check_action_approval_requirement(action_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Checks if an action requires explicit human approval before execution.
    Returns (requires_approval, approval_details).
    """
    if action_name in RESTRICTED_REMEDIATION_ACTIONS:
        meta = RESTRICTED_REMEDIATION_ACTIONS[action_name]
        service = parameters.get("service_name") or parameters.get("service") or "Unknown"
        return True, {
            "action_type": action_name,
            "target_service": service,
            "risk_level": meta["risk"],
            "description": f"{meta['desc']} for {service}",
            "parameters": parameters,
            "status": "pending_approval"
        }

    return False, None
