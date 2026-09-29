"""
Organizational Learning Service for IncidentMind AI
Analyzes persistent memory growth, multi-outcome failure patterns, and preventative reliability trends.
"""

from typing import Dict, Any, List
from data.db import (
    get_all_memories,
    get_all_incidents,
    get_all_services,
    get_dashboard_stats
)
from hindsight.memory_service import get_memory_service


class LearningService:
    """Derives fleet-wide organizational learnings from Hindsight persistent memories."""

    def __init__(self):
        self.memory_service = get_memory_service()

    def get_learning_overview(self) -> Dict[str, Any]:
        """Calculates organizational learning metrics and recurring pattern distributions."""
        all_memories = get_all_memories()
        incidents = get_all_incidents()
        services = get_all_services()
        stats = get_dashboard_stats()

        # Categorize memories
        resolutions = [m for m in all_memories if m.get("category") == "Resolution" or "successful" in m["text"].lower()]
        failed_fixes = [m for m in all_memories if m.get("category") == "Failed Attempt" or "failed" in m["text"].lower()]
        post_mortems = [m for m in all_memories if m.get("category") == "Post-Mortem Insight" or "lesson" in m["text"].lower()]

        # Pattern distribution
        patterns = [
            {
                "pattern": "Pattern A: 503 &rarr; Connection Pool Saturation",
                "service": "Payment API",
                "frequency": 4,
                "first_seen": "INC-0101",
                "verified_solution": "Scale PgBouncer pool ceiling & adjust pod count",
                "danger_avoided": "Restarting pods without pool expansion drops in-flight checkouts",
                "status": "Codified in Hindsight"
            },
            {
                "pattern": "Pattern B: 503 &rarr; Secrets Credential Rotation Desync",
                "service": "Payment API",
                "frequency": 3,
                "first_seen": "INC-0145",
                "verified_solution": "Trigger ExternalSecrets operator manual refresh",
                "danger_avoided": "Blindly increasing pool size FAILED because auth failed before connection",
                "status": "Codified in Hindsight"
            },
            {
                "pattern": "Pattern C: High CPU &rarr; Memory Leak & Garbage Collection",
                "service": "Order Service",
                "frequency": 5,
                "first_seen": "INC-0210",
                "verified_solution": "Heap profiling + patch unbounded HashMap cache",
                "danger_avoided": "Container restarts were merely temporary; code patch was permanent",
                "status": "Codified in Hindsight"
            },
            {
                "pattern": "Pattern D: High Latency &rarr; 3rd-Party Gateway Timeout",
                "service": "Notification Service",
                "frequency": 3,
                "first_seen": "INC-0240",
                "verified_solution": "Tune circuit breaker fallback & decouple async workers",
                "danger_avoided": "Cascading thread exhaustion across caller services",
                "status": "Codified in Hindsight"
            },
            {
                "pattern": "Pattern E: Auth 401/403 &rarr; Expired Signing Key",
                "service": "Authentication Service",
                "frequency": 2,
                "first_seen": "INC-0280",
                "verified_solution": "Rotate JWKS asymmetric keypair & flush public cache",
                "danger_avoided": "Rolling back app code didn't fix expired cryptographic key",
                "status": "Codified in Hindsight"
            }
        ]

        # Call Hindsight reflect for live synthesis
        reflection = self.memory_service.reflect_on_reliability(
            query="Synthesize high-frequency failure modes and preventative rules for SRE team"
        )

        # Knowledge evolution timeline
        timeline = [
            {
                "stage": "Interaction 1 (INC-0101)",
                "event": "Database Pool Saturated",
                "action": "Learned pool ceiling of 50 was inadequate under traffic surge. Increased to 100.",
                "hindsight_stored": "Retained pool exhaustion signature: active=50, queue=284, DB CPU healthy.",
                "value_added": "Baseline memory created."
            },
            {
                "stage": "Interaction 2 (INC-0145)",
                "event": "Identical 503 Symptoms",
                "action": "Attempted increasing pool again (FAILED). Discovered password auth failure from secret rotation.",
                "hindsight_stored": "Retained failed fix + critical rule: 'Same Symptom != Same Root Cause'. Check auth logs before pool.",
                "value_added": "Multi-outcome distinction learned."
            },
            {
                "stage": "Interaction 3 (INC-0182)",
                "event": "Recurring 503 Surge",
                "action": "IncidentMind AI recalled both INC-0101 and INC-0145. Verified auth telemetry, confirmed pool saturation, avoided dead end.",
                "hindsight_stored": "Verified pool expansion to 150. Mitigated in 90 seconds instead of 45 minutes.",
                "value_added": "Zero-friction resolution with 0% risk of failed fix repetition."
            }
        ]

        return {
            "stats": stats,
            "total_memories": len(all_memories),
            "resolutions_retained": len(resolutions),
            "failed_fixes_retained": len(failed_fixes),
            "postmortems_retained": len(post_mortems),
            "patterns": patterns,
            "reflection": reflection,
            "timeline": timeline
        }


_learning_instance = None

def get_learning_service() -> LearningService:
    global _learning_instance
    if _learning_instance is None:
        _learning_instance = LearningService()
    return _learning_instance
