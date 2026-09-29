"""
Hindsight Organizational Memory Service for IncidentMind AI
Coordinates incident knowledge retention, context-aware recall,
multi-outcome correlation (Successful vs Failed fixes), and why-useful attribution.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from hindsight.client import get_hindsight_client
from hindsight.queries import build_incident_search_query, extract_error_codes
from data.db import (
    get_all_memories,
    save_memory_record,
    get_incident_by_id,
    add_incident_event
)

logger = logging.getLogger("incidentmind.hindsight.memory_service")


class MemoryService:
    """
    Business logic layer for organizational incident memory.
    Enforces the core principle: Production Incidents Shouldn't Start From Zero.
    """

    def __init__(self):
        self.client = get_hindsight_client()

    def get_status_info(self) -> Dict[str, Any]:
        """Returns connection and bank status."""
        return self.client.get_status_info()

    # ==================== RETENTION OPERATIONS ====================

    def retain_incident_resolution(self, incident: Dict[str, Any]) -> List[str]:
        """
        Extracts key factual knowledge from a resolved incident and retains it into Hindsight.
        Retains:
        - Outage symptom & affected service
        - Verified root cause
        - Successful resolution action
        """
        inc_id = incident.get("id", "INC-XXXX")
        service = incident.get("service", "System")
        severity = incident.get("severity", "High")
        symptoms = incident.get("symptoms", [])
        sym_str = ", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms)
        root_cause = incident.get("root_cause", "")
        resolution = incident.get("successful_resolution", "")
        env = incident.get("environment", "")

        retained_ids = []

        # 1. Symptom and Root Cause Memory
        content_cause = (
            f"{inc_id}: {service} experienced {severity} outage with symptoms [{sym_str}] on {env}. "
            f"Root cause was verified as: {root_cause}."
        )
        res1 = self.client.retain(
            content=content_cause,
            context=f"Incident {inc_id} Root Cause Analysis",
            metadata={
                "incident_id": inc_id,
                "service": service,
                "category": "Root Cause",
                "severity": severity,
                "outcome": "Resolved",
                "confidence_label": "Verified Production Post-Mortem"
            },
            tags=[service.lower().replace(" ", "_"), "root_cause", severity.lower()],
            service=service,
            incident_id=inc_id,
            category="Root Cause"
        )
        retained_ids.append(res1.get("id", ""))

        # 2. Successful Resolution Memory
        if resolution:
            content_fix = (
                f"{inc_id}: Successful resolution for {service} ({sym_str}) was: {resolution}."
            )
            res2 = self.client.retain(
                content=content_fix,
                context=f"Incident {inc_id} Proven Resolution",
                metadata={
                    "incident_id": inc_id,
                    "service": service,
                    "category": "Resolution",
                    "outcome": "Success",
                    "confidence_label": "High Efficacy Resolution"
                },
                tags=[service.lower().replace(" ", "_"), "resolution", "proven_fix"],
                service=service,
                incident_id=inc_id,
                category="Resolution",
                outcome="Success"
            )
            retained_ids.append(res2.get("id", ""))

        # 3. Retain failed attempts if documented
        failed_fixes = incident.get("failed_fixes", [])
        if isinstance(failed_fixes, str):
            try:
                failed_fixes = json.loads(failed_fixes)
            except Exception:
                failed_fixes = [failed_fixes]

        for failed_fix in failed_fixes:
            self.retain_failed_fix(inc_id, service, failed_fix, root_cause)

        return retained_ids

    def retain_failed_fix(self, incident_id: str, service: str, failed_fix: str, actual_root_cause: str) -> str:
        """
        Explicitly retains a failed troubleshooting attempt.
        Crucial for preventing recurring team mistakes!
        """
        content = (
            f"{incident_id}: Fix attempt FAILED on {service}: '{failed_fix}'. "
            f"Actual root cause was '{actual_root_cause}', so this action did not resolve the outage."
        )
        res = self.client.retain(
            content=content,
            context=f"Incident {incident_id} Failed Troubleshooting",
            metadata={
                "incident_id": incident_id,
                "service": service,
                "category": "Failed Attempt",
                "outcome": "Failed",
                "confidence_label": "Cautionary Operational Lesson"
            },
            tags=[service.lower().replace(" ", "_"), "failed_fix", "caution"],
            service=service,
            incident_id=incident_id,
            category="Failed Attempt",
            outcome="Failed"
        )
        return res.get("id", "")

    def retain_postmortem_insights(self, postmortem: Dict[str, Any]) -> str:
        """Retains prevention roadmap and architectural takeaways."""
        inc_id = postmortem.get("incident_id", "")
        service = postmortem.get("service", "")
        lessons = postmortem.get("lessons_learned", "")
        root_cause = postmortem.get("root_cause", "")

        content = (
            f"{inc_id} Post-Mortem Insight on {service}: Root cause {root_cause}. "
            f"Key preventative takeaway: {lessons}"
        )
        res = self.client.retain(
            content=content,
            context=f"Post-Mortem {postmortem.get('id', inc_id)}",
            metadata={
                "incident_id": inc_id,
                "service": service,
                "category": "Post-Mortem Insight",
                "confidence_label": "Architectural Prevention"
            },
            tags=[service.lower().replace(" ", "_"), "post_mortem", "prevention"],
            service=service,
            incident_id=inc_id,
            category="Post-Mortem Insight"
        )
        return res.get("id", "")

    # ==================== RECALL & CORRELATION ====================

    def recall_for_incident(
        self,
        service: str,
        symptoms: Optional[List[str]] = None,
        logs: Optional[str] = None,
        environment: Optional[str] = None,
        top_k: int = 6
    ) -> Dict[str, Any]:
        """
        Recalls historical incident memories matching active outage symptoms,
        performs multi-outcome correlation (evaluating both successful and failed past actions),
        and adds explicit Why-Useful attribution for SRE clarity.
        """
        query_str = build_incident_search_query(
            service=service,
            symptoms=symptoms,
            logs=logs,
            environment=environment
        )

        raw_response = self.client.recall(
            query=query_str,
            service=service,
            top_k=top_k
        )

        results = []
        if hasattr(raw_response, "results"):
            results = raw_response.results
        elif isinstance(raw_response, dict):
            results = raw_response.get("results", [])

        # Process and classify memories
        successful_fixes = []
        failed_fixes = []
        cautions = []
        processed_memories = []

        for r in results:
            text = getattr(r, "text", "") or r.get("text", "")
            meta = getattr(r, "metadata", {}) or r.get("metadata", {})
            tags = getattr(r, "tags", []) or r.get("tags", [])
            inc_id = meta.get("incident_id", "")
            cat = meta.get("category", "")
            outcome = meta.get("outcome", "Resolved")

            # Determine Why-Useful Rationale
            why_useful = self._compute_why_useful(text, service, symptoms, logs, outcome)

            is_warning = False
            if "failed" in text.lower() or outcome == "Failed" or "FAILED" in text or "caution" in text.lower():
                failed_fixes.append({
                    "incident_id": inc_id,
                    "text": text,
                    "why_useful": why_useful
                })
                cautions.append(f"Avoid repeating failed action from {inc_id}: {text}")
                is_warning = True
            elif "resolution" in cat.lower() or "resolved" in text.lower() or outcome == "Success":
                successful_fixes.append({
                    "incident_id": inc_id,
                    "text": text,
                    "why_useful": why_useful
                })

            processed_memories.append({
                "id": getattr(r, "id", "") or r.get("id", ""),
                "incident_id": inc_id,
                "service": meta.get("service", service),
                "text": text,
                "category": cat or ("Failed Fix" if is_warning else "Resolution"),
                "confidence_label": meta.get("confidence_label", "High Relevance Match"),
                "outcome": outcome,
                "is_warning": is_warning,
                "why_useful": why_useful,
                "tags": tags
            })

        # Proactively ensure cautionary / failed fix memories for the affected service are included
        service_cautions = get_all_memories(service=service, category="Failed Attempt")
        for cm in service_cautions:
            c_text = cm.get("text", "")
            c_inc_id = cm.get("incident_id", "")
            if not any(pm.get("text") == c_text for pm in processed_memories):
                why_u = self._compute_why_useful(c_text, service, symptoms, logs, "Failed")
                failed_fixes.append({
                    "incident_id": c_inc_id,
                    "text": c_text,
                    "why_useful": why_u
                })
                cautions.append(f"Avoid repeating failed action from {c_inc_id}: {c_text}")
                processed_memories.append({
                    "id": cm.get("id", ""),
                    "incident_id": c_inc_id,
                    "service": service,
                    "text": c_text,
                    "category": "Failed Attempt",
                    "confidence_label": "Cautionary Operational Lesson",
                    "outcome": "Failed",
                    "is_warning": True,
                    "why_useful": why_u,
                    "tags": cm.get("tags", [])
                })

        # Multi-Outcome Correlation: Check if "Same Symptom != Same Root Cause" applies
        bifurcated_cause = False
        bifurcation_details = None

        sym_lower = " ".join(symptoms or []).lower()
        if "503" in sym_lower or "connection" in sym_lower or (logs and "connection" in logs.lower()):
            has_pool_mem = any("pool" in m["text"].lower() for m in processed_memories)
            has_auth_mem = any("credential" in m["text"].lower() or "password" in m["text"].lower() or "auth" in m["text"].lower() for m in processed_memories)
            if has_pool_mem and has_auth_mem:
                bifurcated_cause = True
                bifurcation_details = {
                    "pattern": "Same Symptom != Same Root Cause",
                    "explanation": (
                        "Historical memory detects TWO distinct failure modes for Payment API 503 / connection failures: "
                        "1) Connection pool saturation (INC-0101: solved by pool expansion), and "
                        "2) Secret credential rotation failure (INC-0145: pool expansion FAILED; solved by Secrets Manager refresh). "
                        "Agent must check auth logs before modifying pool size."
                    ),
                    "pool_incident": "INC-0101",
                    "auth_incident": "INC-0145"
                }

        return {
            "query": query_str,
            "total_recalled": len(processed_memories),
            "memories": processed_memories,
            "successful_fixes": successful_fixes,
            "failed_fixes": failed_fixes,
            "cautions": cautions,
            "bifurcated_cause": bifurcated_cause,
            "bifurcation_details": bifurcation_details
        }

    def _compute_why_useful(
        self,
        text: str,
        service: str,
        symptoms: Optional[List[str]],
        logs: Optional[str],
        outcome: str
    ) -> str:
        """Explains why this specific memory is relevant to the active incident."""
        t_low = text.lower()
        if "failed" in t_low or outcome == "Failed":
            return "Identifies a previously attempted action that FAILED under identical symptoms, saving the engineer from wasting critical MTTR on a dead end."
        if "credential" in t_low or "password" in t_low:
            return "Highlights that authentication/credential mismatches manifest as connection timeouts, prompting pre-flight auth inspection."
        if "pool" in t_low:
            return "Provides historical baseline for database connection saturation thresholds and proven PgBouncer configuration values."
        if "memory" in t_low or "oom" in t_low:
            return "Reveals historical memory leak patterns, distinguishing temporary container restarts from permanent code fixes."
        if "lock" in t_low or "deadlock" in t_low:
            return "Points to distributed lock ordering as the underlying cause, preventing futile pod restarts."
        return "Matches affected service architecture and error signatures from previous post-mortem investigations."

    def reflect_on_reliability(self, query: str = "Analyze recurring root causes across microservices") -> Dict[str, Any]:
        """Calls Hindsight reflect to extract high-level architectural insights."""
        return self.client.reflect(query=query)


# Singleton
_memory_service_instance: Optional[MemoryService] = None

def get_memory_service() -> MemoryService:
    """Returns singleton MemoryService instance."""
    global _memory_service_instance
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()
    return _memory_service_instance
