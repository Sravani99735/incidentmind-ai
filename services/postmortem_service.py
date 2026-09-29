"""
Post-Mortem Generation and Knowledge Retention Service for IncidentMind AI
Automates blameless post-mortem drafting and syncs organizational takeaways to Hindsight.
"""

import uuid
from typing import Dict, Any, List, Optional
from data.db import (
    get_incident_by_id,
    save_postmortem,
    get_postmortem_by_incident_id,
    get_all_postmortems,
    add_incident_event
)
from hindsight.memory_service import get_memory_service


class PostMortemService:
    """Drafts post-mortems and retains preventative lessons into Hindsight memory."""

    def __init__(self):
        self.memory_service = get_memory_service()

    def generate_postmortem(self, incident_id: str) -> Dict[str, Any]:
        """
        Drafts a comprehensive blameless SRE post-mortem for the incident,
        persists it in SQLite, and retains its insights into Hindsight.
        """
        incident = get_incident_by_id(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        service = incident.get("service", "System")
        title = incident.get("title", f"Incident on {service}")
        symptoms = incident.get("symptoms", [])
        sym_str = ", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms)
        root_cause = incident.get("root_cause") or f"Resource exhaustion or configuration mismatch in {service} dependencies."
        successful_fix = incident.get("successful_resolution") or f"Executed verified remediation for {service}."
        failed_fixes = incident.get("failed_fixes", [])

        # Construct Actionable Prevention Roadmap
        prevention_items = [
            f"[P0] Enforce automated pre-flight health validation for {service} deployment pipelines.",
            f"[P1] Add Datadog / Prometheus alert thresholds for connection pool queue depth > 50.",
            f"[P2] Document cross-service failure signatures in runbook and sync to Hindsight."
        ]

        lessons = (
            f"Incident {incident_id} on {service} demonstrated that symptoms ({sym_str}) "
            f"require immediate cross-referencing with past outages. "
            f"Fix '{successful_fix}' successfully restored SLO. "
            f"Organizational memory must be consulted to prevent repeating dead-end fix attempts."
        )

        pm_data = {
            "id": f"PM-{incident_id}",
            "incident_id": incident_id,
            "title": f"Post-Mortem: {title}",
            "service": service,
            "root_cause": root_cause,
            "impact_summary": f"Service degradation on {service}. Customer transactions delayed during peak window.",
            "successful_fix": successful_fix,
            "failed_attempts": failed_fixes,
            "prevention_items": prevention_items,
            "lessons_learned": lessons,
            "retained_in_hindsight": True
        }

        # Save to DB
        pm_id = save_postmortem(pm_data)

        # Retain into Hindsight Memory Bank
        self.memory_service.retain_postmortem_insights(pm_data)

        # Log timeline event
        add_incident_event(
            incident_id=incident_id,
            event_type="postmortem_published",
            title="Post-Mortem Published & Retained",
            detail=f"Post-Mortem {pm_id} published. Preventative lessons retained in Hindsight memory bank."
        )

        return pm_data

    def get_postmortem(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return get_postmortem_by_incident_id(incident_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return get_all_postmortems()


_postmortem_instance = None

def get_postmortem_service() -> PostMortemService:
    global _postmortem_instance
    if _postmortem_instance is None:
        _postmortem_instance = PostMortemService()
    return _postmortem_instance
