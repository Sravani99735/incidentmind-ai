"""
Incident Management Service for IncidentMind AI
Handles incident lifecycles, state transitions, and timeline tracking.
"""

from typing import List, Dict, Any, Optional
from data.db import (
    get_all_incidents,
    get_incident_by_id,
    create_incident,
    update_incident,
    add_incident_event,
    get_incident_events,
    get_all_services,
    get_service_by_name
)


class IncidentService:
    """Manages incident lifecycles and state transitions."""

    VALID_STATUSES = ["Investigating", "Identified", "Mitigating", "Mitigated", "Resolved"]

    def list_incidents(self, service: Optional[str] = None, severity: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return get_all_incidents(service=service, severity=severity, status=status)

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return get_incident_by_id(incident_id)

    def create_incident(self, incident_data: Dict[str, Any]) -> str:
        inc_id = create_incident(incident_data)
        add_incident_event(
            incident_id=inc_id,
            event_type="status_change",
            title="Incident Opened",
            detail=f"Incident opened with status: {incident_data.get('status', 'Investigating')}"
        )
        return inc_id

    def update_status(self, incident_id: str, new_status: str, note: Optional[str] = None) -> bool:
        if new_status not in self.VALID_STATUSES:
            return False

        update_incident(incident_id, {"status": new_status})
        add_incident_event(
            incident_id=incident_id,
            event_type="status_change",
            title=f"Status Changed to {new_status}",
            detail=note or f"Incident transitioned to {new_status} state."
        )
        return True

    def get_incident_timeline(self, incident_id: str) -> List[Dict[str, Any]]:
        return get_incident_events(incident_id)

    def get_services(self) -> List[Dict[str, Any]]:
        return get_all_services()


_service_instance = None

def get_incident_service() -> IncidentService:
    global _service_instance
    if _service_instance is None:
        _service_instance = IncidentService()
    return _service_instance
