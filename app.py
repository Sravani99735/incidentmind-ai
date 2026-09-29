"""
IncidentMind AI — Persistent Organizational Incident Memory for SRE Teams
Main Flask Application Server
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for

from config.settings import (
    PORT,
    DEBUG,
    SECRET_KEY,
    get_hindsight_status,
    get_llm_status
)
from data.db import (
    init_db,
    get_all_services,
    get_all_incidents,
    get_incident_by_id,
    get_incident_events,
    get_all_memories,
    get_all_postmortems,
    get_postmortem_by_incident_id,
    get_dashboard_stats,
    create_incident,
    update_incident,
    add_incident_event,
    get_db_connection
)
from hindsight.memory_service import get_memory_service
from agent.incident_agent import get_incident_agent
from agent.nlp_processor import get_nlp_processor
from agent.tools import (
    get_service_status,
    get_recent_logs,
    get_deployment_history,
    get_database_metrics,
    check_health_endpoint
)
from agent.tool_validator import validate_and_sanitize_tool_call
from services.incident_service import get_incident_service
from services.analysis_service import get_analysis_service
from services.postmortem_service import get_postmortem_service
from services.learning_service import get_learning_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("incidentmind.app")

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize database schema and synthetic dataset on boot
init_db(reset=False)


@app.context_processor
def inject_global_status():
    """Injects system status indicators across all HTML templates."""
    return {
        "hindsight_status": get_hindsight_status(),
        "llm_status": get_llm_status()
    }


# ==================== WEB VIEWS (10 ROUTES) ====================

@app.route("/")
def index():
    """Landing page with hero, live metrics, visual memory loop, and demo jump."""
    stats = get_dashboard_stats()
    services = get_all_services()
    recent_incidents = get_all_incidents()[:5]
    return render_template("index.html", stats=stats, services=services, recent_incidents=recent_incidents)


@app.route("/dashboard")
def dashboard():
    """SRE Operations Dashboard with active incident feed and microservices health."""
    stats = get_dashboard_stats()
    services = get_all_services()
    incidents = get_all_incidents()
    active_incidents = [i for i in incidents if i["status"] != "Resolved"]
    recent_resolved = [i for i in incidents if i["status"] == "Resolved"][:6]
    return render_template(
        "dashboard.html",
        stats=stats,
        services=services,
        active_incidents=active_incidents,
        recent_resolved=recent_resolved
    )


@app.route("/incidents")
def incidents_catalog():
    """Enterprise Incident Catalog with filtering by service, severity, status."""
    service_filter = request.args.get("service")
    severity_filter = request.args.get("severity")
    status_filter = request.args.get("status")

    incidents = get_all_incidents(service=service_filter, severity=severity_filter, status=status_filter)
    services = get_all_services()

    return render_template(
        "incidents.html",
        incidents=incidents,
        services=services,
        selected_service=service_filter,
        selected_severity=severity_filter,
        selected_status=status_filter
    )


@app.route("/incident/<incident_id>")
def incident_detail(incident_id):
    """Detailed Incident Timeline, root cause, symptoms, and post-mortem viewer."""
    incident = get_incident_by_id(incident_id)
    if not incident:
        return redirect(url_for("incidents_catalog"))

    timeline = get_incident_events(incident_id)
    postmortem = get_postmortem_by_incident_id(incident_id)
    all_services = get_all_services()

    return render_template(
        "incident.html",
        incident=incident,
        timeline=timeline,
        postmortem=postmortem,
        services=all_services
    )


@app.route("/analyzer")
def analyzer_workspace():
    """
    Primary SRE Incident Investigation Workspace.
    Features interactive agent chat (handling normal conversation + deep triage),
    live telemetry panels, Hindsight recall cards, and human-in-the-loop approval.
    """
    incident_id = request.args.get("incident_id")
    incident = get_incident_by_id(incident_id) if incident_id else None
    services = get_all_services()
    all_incidents = get_all_incidents()

    # Default to INC-0182 if none selected
    if not incident and all_incidents:
        for inc in all_incidents:
            if inc["id"] == "INC-0182":
                incident = inc
                break
        if not incident:
            incident = all_incidents[0]

    return render_template(
        "analyzer.html",
        incident=incident,
        services=services,
        all_incidents=all_incidents
    )


@app.route("/memory")
def memory_explorer():
    """Hindsight Memory Explorer: filter by service, category, outcome, plus reflection."""
    service_filter = request.args.get("service")
    category_filter = request.args.get("category")

    memories = get_all_memories(service=service_filter, category=category_filter)
    services = get_all_services()
    memory_service = get_memory_service()
    reflection = memory_service.reflect_on_reliability()

    return render_template(
        "memory.html",
        memories=memories,
        services=services,
        reflection=reflection,
        selected_service=service_filter,
        selected_category=category_filter
    )


@app.route("/learning")
def learning_engine():
    """Organizational Learning Engine: multi-outcome insights and memory evolution."""
    learning_service = get_learning_service()
    data = learning_service.get_learning_overview()
    return render_template("learning.html", data=data)


@app.route("/before-after")
def before_after_lab():
    """The Memory Difference Lab: side-by-side run of standard AI vs IncidentMind AI."""
    incident_id = request.args.get("incident_id", "INC-0182")
    analysis_service = get_analysis_service()
    comparison = analysis_service.compare_investigation(incident_id)
    all_incidents = get_all_incidents()
    return render_template(
        "before_after.html",
        comparison=comparison,
        all_incidents=all_incidents,
        selected_id=incident_id
    )


@app.route("/demo")
def demo_walkthrough():
    """60-Second Guided Demo Mode for hackathon judges."""
    return render_template("demo.html")


@app.route("/documentation")
def documentation():
    """System Architecture, API Documentation, SRE Runbooks, and Hindsight Guide."""
    return render_template("documentation.html")


# ==================== API ENDPOINTS ====================

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Dual-mode conversational + incident triage agent chat."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    conv_id = data.get("conversation_id")
    incident_id = data.get("incident_id")
    service = data.get("service")

    agent = get_incident_agent()
    response = agent.handle_chat_message(
        message=message,
        conversation_id=conv_id,
        incident_id=incident_id,
        service=service
    )
    return jsonify(response)


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Deep incident analysis with Hindsight recall."""
    data = request.get_json() or {}
    service = data.get("service", "Payment API")
    symptoms = data.get("symptoms", [])
    logs = data.get("logs", "")
    incident_id = data.get("incident_id")

    memory_service = get_memory_service()
    recall_res = memory_service.recall_for_incident(
        service=service,
        symptoms=symptoms if isinstance(symptoms, list) else [symptoms],
        logs=logs,
        top_k=6
    )

    db_metrics = get_database_metrics(service)
    status_data = get_service_status(service)
    recent_logs = get_recent_logs(service, lines=15)

    return jsonify({
        "service": service,
        "incident_id": incident_id,
        "recall": recall_res,
        "telemetry": {
            "status": status_data,
            "metrics": db_metrics,
            "logs": recent_logs
        }
    })


@app.route("/api/compare", methods=["GET"])
def api_compare():
    """Side-by-side Before/After execution."""
    incident_id = request.args.get("incident_id", "INC-0182")
    analysis_service = get_analysis_service()
    comparison = analysis_service.compare_investigation(incident_id)
    return jsonify(comparison)


@app.route("/api/tools/execute", methods=["POST"])
def api_execute_tool():
    """Simulated SRE tool execution with parameter validation."""
    data = request.get_json() or {}
    tool_name = data.get("tool_name", "")
    parameters = data.get("parameters", {})

    is_valid, msg, clean_params = validate_and_sanitize_tool_call(tool_name, parameters)
    if not is_valid:
        return jsonify({"success": False, "error": msg}), 400

    service = clean_params.get("service_name", "Payment API")

    if tool_name == "get_service_status":
        result = get_service_status(service)
    elif tool_name == "get_recent_logs":
        result = get_recent_logs(service, lines=clean_params.get("lines", 20))
    elif tool_name == "get_deployment_history":
        result = get_deployment_history(service)
    elif tool_name == "get_database_metrics":
        result = get_database_metrics(service)
    elif tool_name == "check_health_endpoint":
        result = check_health_endpoint(service, clean_params.get("endpoint", "/healthz"))
    else:
        return jsonify({"success": False, "error": "Action requires human approval gateway"}), 403

    return jsonify({"success": True, "tool_name": tool_name, "data": result})


@app.route("/api/tools/approve", methods=["POST"])
def api_approve_action():
    """Human-in-the-loop remediation action authorization."""
    data = request.get_json() or {}
    action_id = data.get("action_id", "act_default")
    action_type = data.get("action_type", "scale_connection_pool")
    target_service = data.get("target_service", "Payment API")
    parameters = data.get("parameters", {})
    approved_by = data.get("approved_by", "On-Call SRE Engineer")

    agent = get_incident_agent()
    result = agent.execute_approved_remediation(
        action_id=action_id,
        action_type=action_type,
        target_service=target_service,
        parameters=parameters,
        approved_by=approved_by
    )
    return jsonify(result)


@app.route("/api/postmortem/generate", methods=["POST"])
def api_generate_postmortem():
    """Generates post-mortem and retains into Hindsight memory."""
    data = request.get_json() or {}
    incident_id = data.get("incident_id")
    if not incident_id:
        return jsonify({"error": "incident_id is required"}), 400

    pm_service = get_postmortem_service()
    try:
        pm = pm_service.generate_postmortem(incident_id)
        return jsonify({"success": True, "postmortem": pm})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hindsight/status", methods=["GET"])
def api_hindsight_status():
    """Returns live connection status of Hindsight engine."""
    return jsonify(get_hindsight_status())


# ==================== 60-SECOND DEMO API ====================

DEMO_STEPS = [
    {
        "step": 1,
        "title": "Incident 1: INC-0101 (The Initial Learning)",
        "badge": "First Encounter",
        "description": "Payment API experiences HTTP 503 during promotional checkout surge. Database connection pool exhausts at 50 connections.",
        "incident_id": "INC-0101",
        "service": "Payment API",
        "symptoms": ["HTTP 503 Service Unavailable", "PgBouncer pool exhausted (50/50)"],
        "telemetry": "active=50, idle=0, queue=284, Aurora DB host CPU=24% (healthy)",
        "action_taken": "Scaled connection pool from 50 to 100 in ConfigMap and restarted pods gracefully.",
        "outcome": "Resolved. Checkout restored within 3 minutes.",
        "hindsight_stored": [
            "INC-0101: Payment API 503 caused by database connection pool exhaustion on Kubernetes.",
            "INC-0101: Pool saturation showed active=50, idle=0, queue=284 with DB CPU healthy.",
            "INC-0101: Increasing connection pool from 50 to 100 successfully resolved the outage."
        ],
        "lesson": "Retained baseline: When DB CPU is low but pool queue is high, pool expansion works."
    },
    {
        "step": 2,
        "title": "Incident 2: INC-0145 (The Costly Mistake & Cautionary Retain)",
        "badge": "Same Symptom != Same Root Cause",
        "description": "Payment API fails again with identical HTTP 503 errors! SRE team blindly repeats INC-0101 fix (increasing pool 100->150). IT FAILS COMPLETELY!",
        "incident_id": "INC-0145",
        "service": "Payment API",
        "symptoms": ["HTTP 503 Service Unavailable", "Database connection timeout"],
        "failed_action": "Increasing connection pool to 150 FAILED: Pods crashed because root cause was password authentication failure from secret rotation mismatch.",
        "actual_fix": "Force-refreshed Kubernetes Secret from AWS Secrets Manager using ExternalSecrets operator.",
        "outcome": "Resolved. But 45 minutes of downtime wasted repeating the wrong fix.",
        "hindsight_stored": [
            "INC-0145: Increasing connection pool FAILED because root cause was credential rotation mismatch.",
            "INC-0145: CRITICAL LESSON: HTTP 503 on Payment API can be caused by pool exhaustion OR auth failure; check auth logs before touching pool size!"
        ],
        "lesson": "Crucial: Hindsight retains the FAILED attempt and caution so the team never repeats it."
    },
    {
        "step": 3,
        "title": "Incident 3: INC-0182 (The Hindsight Payoff)",
        "badge": "Zero Repeat Mistakes",
        "description": "Payment API triggers HTTP 503 alerts again during batch settlement. Traditional AI would blindly guess. IncidentMind AI recalls BOTH INC-0101 and INC-0145.",
        "incident_id": "INC-0182",
        "service": "Payment API",
        "symptoms": ["HTTP 503 Service Unavailable", "Intermittent database socket timeout"],
        "agent_behavior": (
            "1. Recalls INC-0101 (Pool Saturation) AND INC-0145 (Credential Failure).\n"
            "2. Flags 'Same Symptom != Same Root Cause' warning.\n"
            "3. Probes live telemetry: verifies `auth_failures=0` and `auth=valid`. Rules out INC-0145!\n"
            "4. Observes `active=98/100` and `queue=312`. Confirms INC-0101 pool saturation!\n"
            "5. Recommends verified pool expansion to 150 with human approval gateway."
        ),
        "outcome": "Mitigated in 90 seconds. 0% chance of repeating failed fix. 86% MTTR reduction.",
        "hindsight_stored": [
            "INC-0182: Confirmed pool saturation via live auth telemetry, avoiding INC-0145 credential trap.",
            "INC-0182: Scaled PgBouncer pool to 150 with human authorization."
        ],
        "lesson": "Demonstrates clear value: Agent learned from failure and succeeded where stateless AI fails."
    }
]


@app.route("/api/demo/state", methods=["GET"])
def api_demo_state():
    """Returns the full 3-step demo walkthrough script."""
    step = int(request.args.get("step", 1))
    step = max(1, min(len(DEMO_STEPS), step))
    return jsonify({
        "current_step": step,
        "total_steps": len(DEMO_STEPS),
        "step_data": DEMO_STEPS[step - 1],
        "all_steps": DEMO_STEPS
    })


@app.route("/api/demo/step", methods=["POST"])
def api_demo_step():
    """Advances or sets demo step."""
    data = request.get_json() or {}
    step = int(data.get("step", 1))
    step = max(1, min(len(DEMO_STEPS), step))
    return jsonify({
        "success": True,
        "current_step": step,
        "step_data": DEMO_STEPS[step - 1]
    })


@app.route("/api/demo/reset", methods=["POST"])
def api_demo_reset():
    """Resets the demo state back to step 1."""
    init_db(reset=False)
    return jsonify({"success": True, "current_step": 1, "message": "Demo state reset successfully."})


if __name__ == "__main__":
    logger.info(f"Starting IncidentMind AI Server on port {PORT} (Debug: {DEBUG})")
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
