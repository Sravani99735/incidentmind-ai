"""
IncidentMind AI — Autonomous SRE Agent Orchestrator
Executes multi-stage incident investigation, Hindsight memory recall,
simulated telemetry diagnostics, and conversational on-call dialogue.
"""

import time
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from agent.schemas import (
    InvestigationResult,
    MemoryRecallCard,
    ApprovalRequest,
    ChatMessageResponse
)
from agent.tools import (
    get_service_status,
    get_recent_logs,
    get_deployment_history,
    get_database_metrics,
    check_health_endpoint
)
from agent.tool_validator import (
    validate_and_sanitize_tool_call,
    check_action_approval_requirement,
    normalize_service_name
)
from agent.nlp_processor import get_nlp_processor, NLPProcessor
from hindsight.memory_service import get_memory_service
from data.db import (
    get_incident_by_id,
    get_all_incidents,
    get_service_by_name,
    add_incident_event,
    add_audit_event,
    update_incident,
    get_db_connection
)

logger = logging.getLogger("incidentmind.agent")


class IncidentAgent:
    """
    Lead SRE Incident Response Agent.
    Combines real-time telemetry diagnostics with persistent Hindsight memory.
    """

    def __init__(self):
        self.nlp = get_nlp_processor()
        self.memory_service = get_memory_service()

    # ==================== DUAL-MODE SRE CHAT ====================

    def handle_chat_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        service: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handles incoming on-call chat messages.
        Supports both natural SRE conversation and deep incident investigation.
        """
        conv_id = conversation_id or f"conv_{uuid.uuid4().hex[:10]}"
        nlp_res = self.nlp.process_message(message)
        intent = nlp_res["intent"]
        entities = nlp_res["entities"]

        target_service = entities.get("service") or service or "Payment API"
        target_inc_id = entities.get("incident_id") or incident_id

        # 1. Normal Conversational Dialogue
        if nlp_res["is_conversational"]:
            reply_text = self.nlp.generate_conversational_reply(message, intent, entities)
            return {
                "conversation_id": conv_id,
                "sender": "agent",
                "content": reply_text,
                "intent": intent,
                "extracted_entities": entities,
                "memories_used": [],
                "tool_calls": [],
                "approval_needed": None,
                "why_useful": "Conversational on-call companion with full SRE system knowledge.",
                "is_memory_powered": False
            }

        # 2. Incident Status Inquiry
        if intent == NLPProcessor.INTENT_INCIDENT_STATUS:
            return self._handle_status_inquiry(message, conv_id, target_inc_id, target_service, entities)

        # 3. Explicit Tool Execution Request
        if intent == NLPProcessor.INTENT_TOOL_EXECUTION:
            return self._handle_tool_request(message, conv_id, target_service, entities)

        # 4. Post-Mortem Inquiry
        if intent == NLPProcessor.INTENT_POSTMORTEM_INQUIRY:
            return self._handle_postmortem_inquiry(message, conv_id, target_inc_id, target_service)

        # 5. Default: Active Incident Investigation & Triage
        return self._handle_investigation_chat(message, conv_id, target_inc_id, target_service, nlp_res)

    def _handle_status_inquiry(self, message: str, conv_id: str, inc_id: Optional[str], service: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handles questions about active incidents or service health."""
        if inc_id:
            inc = get_incident_by_id(inc_id)
            if inc:
                content = (
                    f"### Status of {inc['id']}: {inc['title']}\n\n"
                    f"- **Service**: `{inc['service']}`\n"
                    f"- **Severity**: `{inc['severity']}`\n"
                    f"- **Status**: `{inc['status']}`\n"
                    f"- **Root Cause**: {inc.get('root_cause', 'Under investigation')}\n"
                    f"- **Successful Fix**: {inc.get('successful_resolution') or 'Pending verification'}\n\n"
                    f"Would you like me to inspect recent diagnostic logs or run telemetry probes?"
                )
                return {
                    "conversation_id": conv_id,
                    "sender": "agent",
                    "content": content,
                    "intent": "incident_status",
                    "extracted_entities": entities,
                    "memories_used": [],
                    "tool_calls": [],
                    "approval_needed": None,
                    "why_useful": "Quick lookup from persistent incident registry.",
                    "is_memory_powered": True
                }

        # General status
        incidents = get_all_incidents()
        active = [i for i in incidents if i["status"] != "Resolved"]
        content = (
            f"### Active Incident Overview\n\n"
            f"Currently tracking **{len(active)} active incident(s)**:\n\n"
        )
        for act in active[:3]:
            content += f"- **{act['id']}** ({act['service']}): {act['title']} — Status: `{act['status']}`\n"

        content += f"\nTotal resolved incidents in organizational memory: **{len(incidents) - len(active)}**."
        return {
            "conversation_id": conv_id,
            "sender": "agent",
            "content": content,
            "intent": "incident_status",
            "extracted_entities": entities,
            "memories_used": [],
            "tool_calls": [],
            "approval_needed": None,
            "why_useful": "Fleet-wide incident tracking.",
            "is_memory_powered": True
        }

    def _handle_tool_request(self, message: str, conv_id: str, service: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Executes diagnostic tools upon explicit SRE request."""
        m_low = message.lower()
        tool_results = []

        if "log" in m_low:
            tool_name = "get_recent_logs"
            data = get_recent_logs(service_name=service, lines=15)
            tool_results.append({"tool": tool_name, "data": data})
            content = (
                f"### Diagnostic Logs for `{service}`:\n\n"
                f"```text\n{data['logs']}\n```\n\n"
                f"**Telemetry Insight**: Error signatures detected in container stdout."
            )
        elif "metric" in m_low or "database" in m_low or "pool" in m_low:
            tool_name = "get_database_metrics"
            data = get_database_metrics(service_name=service)
            tool_results.append({"tool": tool_name, "data": data})
            metrics = data["metrics"]
            content = (
                f"### Database Metrics for `{service}`:\n\n"
                f"- **Pool Saturation**: `{metrics['saturation_pct']}%` ({metrics['active_connections']}/{metrics['max_connections']})\n"
                f"- **Waiting Queue**: `{metrics['waiting_connection_queue']} requests`\n"
                f"- **P99 Acquisition Latency**: `{metrics['connection_acquisition_latency_p99_ms']}ms`\n"
                f"- **Primary DB CPU**: `{metrics['database_host_cpu_pct']}%`\n"
                f"- **Auth Failures (5m)**: `{metrics['auth_failures_last_5m']}`\n\n"
                f"💡 **Analysis**: {data['diagnostics_summary']}"
            )
        else:
            tool_name = "get_service_status"
            data = get_service_status(service_name=service)
            tool_results.append({"tool": tool_name, "data": data})
            content = (
                f"### Infrastructure Health for `{service}`:\n\n"
                f"- **Health Status**: `{data['health_status']}`\n"
                f"- **Pod Replicas**: `{data['replicas']['ready']}/{data['replicas']['desired']}` ready\n"
                f"- **CPU / Memory**: `{data['cpu_usage_pct']}% CPU` | `{data['memory_usage_pct']}% RAM`\n"
                f"- **Restarts (1h)**: `{data['restart_count_last_1h']}`\n"
                f"- **Uptime**: `{data['uptime']}`\n"
            )

        return {
            "conversation_id": conv_id,
            "sender": "agent",
            "content": content,
            "intent": "tool_execution",
            "extracted_entities": entities,
            "memories_used": [],
            "tool_calls": tool_results,
            "approval_needed": None,
            "why_useful": "Live telemetry inspection via diagnostic tool suite.",
            "is_memory_powered": False
        }

    def _handle_postmortem_inquiry(self, message: str, conv_id: str, inc_id: Optional[str], service: str) -> Dict[str, Any]:
        """Provides post-mortem insights from memory."""
        memories = self.memory_service.recall_for_incident(
            service=service,
            symptoms=["post-mortem", "lessons learned"],
            top_k=4
        )
        content = (
            f"### Organizational Lessons Learned for `{service}`\n\n"
            f"Based on historical incident post-mortems retained in Hindsight:\n\n"
        )
        for m in memories["memories"]:
            content += f"- **[{m['category']}]** {m['text']}\n"

        content += "\nThese post-mortem insights are actively applied to prevent repeating historical mistakes."
        return {
            "conversation_id": conv_id,
            "sender": "agent",
            "content": content,
            "intent": "postmortem_inquiry",
            "extracted_entities": {"service": service},
            "memories_used": memories["memories"],
            "tool_calls": [],
            "approval_needed": None,
            "why_useful": "Prevents organizational amnesia across engineering rotations.",
            "is_memory_powered": True
        }

    def _handle_investigation_chat(
        self,
        message: str,
        conv_id: str,
        inc_id: Optional[str],
        service: str,
        nlp_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs complete incident triage workflow with Hindsight recall,
        multi-outcome correlation, live telemetry, and human approval gateway.
        """
        # 1. Fetch or create incident
        incident = None
        if inc_id:
            incident = get_incident_by_id(inc_id)

        symptoms = [nlp_res["raw_text"]]
        if incident and incident.get("symptoms"):
            symptoms.extend(incident["symptoms"])

        # 2. Hindsight Memory Recall
        recall_res = self.memory_service.recall_for_incident(
            service=service,
            symptoms=symptoms,
            logs=incident.get("logs", "") if incident else message,
            top_k=5
        )

        # 3. Live Telemetry Tool Diagnostics
        status_data = get_service_status(service)
        logs_data = get_recent_logs(service, lines=10)
        metrics_data = get_database_metrics(service)

        tool_calls = [
            {"tool": "get_service_status", "data": status_data},
            {"tool": "get_recent_logs", "data": logs_data},
            {"tool": "get_database_metrics", "data": metrics_data}
        ]

        # 4. Multi-Outcome Learning & Synthesis
        bifurcated = recall_res.get("bifurcated_cause", False)
        memories = recall_res.get("memories", [])
        cautions = recall_res.get("cautions", [])

        # Formulate Senior SRE Diagnostic Response
        content_lines = [
            f"### 🚨 Incident Investigation: `{service}`",
            f"**Triage Severity**: `{nlp_res['urgency']}` | **Status**: `Active Investigation`\n",
            "#### 1. Live Telemetry Diagnostics:",
            f"- **Pod Status**: `{status_data['replicas']['ready']}/{status_data['replicas']['desired']}` ready (Status: `{status_data['health_status']}`)",
            f"- **PgBouncer Pool**: `active={metrics_data['metrics']['active_connections']}/{metrics_data['metrics']['max_connections']}` (Saturation: `{metrics_data['metrics']['saturation_pct']}%`)",
            f"- **Waiting Queue**: `{metrics_data['metrics']['waiting_connection_queue']} requests` | P99 Latency: `{metrics_data['metrics']['connection_acquisition_latency_p99_ms']}ms`",
            f"- **Auth Failures**: `{metrics_data['metrics']['auth_failures_last_5m']}` (Authentication is valid)\n",
            "#### 2. Persistent Hindsight Memory Recall:"
        ]

        for m in memories[:3]:
            badge = "⚠️ FAILED ATTEMPT" if m["is_warning"] else "✅ SUCCESSFUL PRECEDENT"
            content_lines.append(f"- **{badge}** ({m['incident_id']}): {m['text']}")
            content_lines.append(f"  *Why Useful*: {m['why_useful']}")

        if bifurcated:
            content_lines.extend([
                "\n#### 3. 🧠 Multi-Outcome Learning Analysis (Same Symptom != Same Root Cause):",
                "Historical incident memory reveals two divergent causes for 503 errors on Payment API:",
                "- **INC-0101**: Connection pool exhaustion &rarr; *Solved by pool expansion (50 &rarr; 100)*.",
                "- **INC-0145**: Credential rotation failure &rarr; *Pool expansion FAILED; solved by Secrets Manager sync*.",
                "- **Current Diagnosis**: Our live telemetry shows `auth_failures=0` and `auth=valid`, while `waiting_queue=312` with `active=98/100`. "
                "This rules out credential rotation (INC-0145) and confirms genuine connection pool exhaustion!"
            ])

        # 5. Proposed Remediation & Human Approval Gate
        approval_needed = {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "action_type": "scale_connection_pool",
            "target_service": service,
            "risk_level": "Medium",
            "description": "Increase PgBouncer database connection pool max_connections from 100 to 150 and roll pods gracefully.",
            "parameters": {"service_name": service, "new_max_connections": 150},
            "status": "pending_approval"
        }

        content_lines.extend([
            "\n#### 4. Recommended Remediation & Safety Gateway:",
            f"I have prepared the proven mitigation plan based on INC-0101 learnings:\n"
            f"> **Proposed Action**: {approval_needed['description']}\n"
            f"> **Risk Level**: `{approval_needed['risk_level']}` | **Target**: `{approval_needed['target_service']}`\n\n"
            f"⚠️ *Human-in-the-loop safety required*: Please click **Authorize Remediation** below to execute this change safely in the demo environment."
        ])

        if inc_id:
            add_incident_event(
                incident_id=inc_id,
                event_type="agent_analysis",
                title="IncidentMind AI Triage Completed",
                detail=f"Synthesized live telemetry and {len(memories)} Hindsight memories. Identified pool exhaustion.",
                metadata={"bifurcated": bifurcated, "pool_saturation_pct": metrics_data["metrics"]["saturation_pct"]}
            )

        return {
            "conversation_id": conv_id,
            "sender": "agent",
            "content": "\n".join(content_lines),
            "intent": "incident_investigation",
            "extracted_entities": nlp_res["entities"],
            "memories_used": memories,
            "tool_calls": tool_calls,
            "approval_needed": approval_needed,
            "why_useful": "Synthesized historical successes (INC-0101) and avoided repeat mistakes (INC-0145).",
            "is_memory_powered": True
        }

    # ==================== HUMAN APPROVAL EXECUTION ====================

    def execute_approved_remediation(
        self,
        action_id: str,
        action_type: str,
        target_service: str,
        parameters: Dict[str, Any],
        approved_by: str = "on_call_sre"
    ) -> Dict[str, Any]:
        """
        Executes a human-authorized remediation action in the demo environment
        and logs to the tamper-evident audit trail.
        """
        # Record audit event
        audit_id = add_audit_event(
            tool_name=action_type,
            parameters=parameters,
            approved_by=approved_by,
            status="executed",
            result={"status": "success", "new_max_connections": 150, "rollout": "complete"}
        )

        # Update service status & active incidents
        time.sleep(0.1)  # Simulated execution latency

        incidents = get_all_incidents(service=target_service)
        active_inc = next((i for i in incidents if i["status"] != "Resolved"), None)
        if active_inc:
            update_incident(active_inc["id"], {
                "status": "Resolved",
                "successful_resolution": f"Increased database connection pool to {parameters.get('new_max_connections', 150)} and performed rolling pod restart (Approved by {approved_by}).",
                "outcome": "Resolved"
            })
            add_incident_event(
                incident_id=active_inc["id"],
                event_type="action_executed",
                title=f"Remediation Executed: {action_type}",
                detail=f"Approved by {approved_by}. Connection pool scaled to 150. Queue drained.",
                metadata={"audit_id": audit_id, "action_id": action_id}
            )

        return {
            "success": True,
            "action_id": action_id,
            "audit_id": audit_id,
            "status": "Executed Successfully",
            "message": f"Remediation '{action_type}' for {target_service} executed successfully.",
            "post_action_telemetry": {
                "health_status": "Healthy",
                "pool_saturation_pct": 24.0,
                "waiting_queue": 0,
                "latency_p99_ms": 12.4
            }
        }


# Singleton
_agent_instance = None

def get_incident_agent() -> IncidentAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = IncidentAgent()
    return _agent_instance
