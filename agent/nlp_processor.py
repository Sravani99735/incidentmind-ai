"""
Natural Language Processing (NLP) and Conversational Engine for IncidentMind AI
Handles intent recognition, entity extraction, sentiment/urgency analysis,
and natural conversational dialogue for on-call engineers.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from data.db import (
    get_all_services,
    get_all_incidents,
    get_incident_by_id,
    get_dashboard_stats
)


class NLPProcessor:
    """
    Intelligent NLP pipeline providing:
    1. Multi-class Intent Classification
    2. SRE Named Entity Recognition (Services, Incidents, Errors, Metrics)
    3. Sentiment & Urgency Assessment
    4. Conversational Dialogue Generator for natural, non-robotic chat.
    """

    INTENT_INCIDENT_INVESTIGATION = "incident_investigation"
    INTENT_INCIDENT_STATUS = "incident_status"
    INTENT_TOOL_EXECUTION = "tool_execution"
    INTENT_POSTMORTEM_INQUIRY = "postmortem_inquiry"
    INTENT_GENERAL_CONVERSATION = "general_conversation"
    INTENT_HINDSIGHT_EXPLANATION = "hindsight_explanation"

    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Complete NLP processing pipeline for an incoming user prompt.
        """
        text = message.strip()
        entities = self.extract_entities(text)
        intent = self.classify_intent(text, entities)
        urgency = self.assess_urgency(text)

        return {
            "raw_text": text,
            "intent": intent,
            "entities": entities,
            "urgency": urgency,
            "is_conversational": intent in (
                self.INTENT_GENERAL_CONVERSATION,
                self.INTENT_HINDSIGHT_EXPLANATION
            )
        }

    def classify_intent(self, text: str, entities: Dict[str, Any]) -> str:
        """Determines the primary user intent."""
        t_low = text.lower()

        # 1. Greetings & General Conversational Phrases
        greetings = ("hi", "hello", "hey", "good morning", "good evening", "how are you", "who are you", "what can you do", "help", "thanks", "thank you", "nice to meet you", "yo", "sup")
        words = re.findall(r"\b\w+\b", t_low)
        if any(w in greetings for w in words) and len(words) <= 5 and not entities.get("incident_id") and not entities.get("error_codes"):
            return self.INTENT_GENERAL_CONVERSATION

        if any(phrase in t_low for phrase in ("how are you doing", "what is your name", "tell me about yourself", "how's your day", "rough on-call", "tired", "stressed")):
            return self.INTENT_GENERAL_CONVERSATION

        # 2. Hindsight / Architectural explanation requests
        if any(phrase in t_low for phrase in ("how does hindsight work", "what is hindsight", "why persistent memory", "explain memory", "how do you remember", "what is mttr")):
            return self.INTENT_HINDSIGHT_EXPLANATION

        # 3. Post-Mortem Inquiry
        if any(phrase in t_low for phrase in ("post-mortem", "postmortem", "lessons learned", "prevention", "what did we learn")):
            return self.INTENT_POSTMORTEM_INQUIRY

        # 4. Explicit Tool Execution Requests
        tool_triggers = ("check logs", "show logs", "get logs", "check status", "metrics", "database metrics", "healthcheck", "probe", "deployment history")
        if any(trig in t_low for trig in tool_triggers) and not any(kw in t_low for kw in ("investigate", "fix", "why is", "root cause")):
            return self.INTENT_TOOL_EXECUTION

        # 5. Incident Status Query
        if any(phrase in t_low for phrase in ("status of", "what is happening with", "list incidents", "active incidents", "any alerts")):
            return self.INTENT_INCIDENT_STATUS

        # 6. Default to Incident Investigation if error signals or incident IDs are present
        if entities.get("incident_id") or entities.get("error_codes") or any(kw in t_low for kw in ("503", "error", "failing", "down", "outage", "timeout", "slow", "incident", "investigate", "triage", "debug", "broken")):
            return self.INTENT_INCIDENT_INVESTIGATION

        return self.INTENT_GENERAL_CONVERSATION

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extracts SRE entities from natural text."""
        entities = {
            "incident_id": None,
            "service": None,
            "error_codes": [],
            "keywords": []
        }

        # Incident ID match (INC-XXXX)
        inc_match = re.search(r"\b(INC-\d{4})\b", text, re.IGNORECASE)
        if inc_match:
            entities["incident_id"] = inc_match.group(1).upper()

        # Service recognition
        services = get_all_services()
        t_low = text.lower()
        for s in services:
            s_name = s["name"]
            if s_name.lower() in t_low or s_name.lower().replace(" service", "").replace(" api", "") in t_low:
                entities["service"] = s_name
                break

        # Fallback service heuristics
        if not entities["service"]:
            if "payment" in t_low or "checkout" in t_low:
                entities["service"] = "Payment API"
            elif "auth" in t_low or "token" in t_low or "login" in t_low:
                entities["service"] = "Authentication Service"
            elif "order" in t_low or "cart" in t_low:
                entities["service"] = "Order Service"
            elif "database" in t_low or "postgres" in t_low or "pgbouncer" in t_low:
                entities["service"] = "Database Service"
            elif "gateway" in t_low or "envoy" in t_low:
                entities["service"] = "API Gateway"
            elif "notification" in t_low or "apns" in t_low or "sms" in t_low:
                entities["service"] = "Notification Service"
            elif "search" in t_low:
                entities["service"] = "Search API"
            elif "inventory" in t_low:
                entities["service"] = "Inventory Service"

        # Error codes
        error_matches = re.findall(r"\b(500|502|503|504|429|401|403|OOMKilled|Timeout|CrashLoopBackOff|Deadlock)\b", text, re.IGNORECASE)
        if error_matches:
            entities["error_codes"] = list(set([e.upper() for e in error_matches]))

        return entities

    def assess_urgency(self, text: str) -> str:
        """Determines urgency level based on text markers."""
        t_low = text.lower()
        if any(w in t_low for w in ("outage", "production down", "critical", "sev1", "p1", "fatal", "emergency", "immediately")):
            return "P1 - Critical"
        if any(w in t_low for w in ("error", "503", "degraded", "failing", "broken", "high", "timeout", "spike")):
            return "P2 - High"
        return "P3 - Normal"

    def generate_conversational_reply(self, message: str, intent: str, entities: Dict[str, Any]) -> str:
        """
        Generates empathetic, natural conversational dialogue for normal chat interactions,
        maintaining the persona of an expert, calm Senior Staff SRE colleague.
        """
        t_low = message.lower()

        # Greetings & Persona Introductions
        if any(g in t_low for g in ("hi", "hello", "hey", "good morning", "good evening", "yo")):
            return (
                "👋 Hello! I'm **IncidentMind AI**, your persistent incident response partner. "
                "I track production health, investigate alerts across our microservices, and remember every past outage, "
                "failed fix, and post-mortem lesson using **Hindsight**.\n\n"
                "How's on-call treating you today? Let me know if you want to triage an active alert, inspect service telemetry, or discuss an incident!"
            )

        if "how are you" in t_low:
            stats = get_dashboard_stats()
            return (
                f"I'm operating at peak telemetry! 🚀\n\n"
                f"Currently tracking **{stats['total_services']} microservices** with **{stats['active_incidents']} active incident** "
                f"and **{stats['total_memories']} persistent organizational memories** retained in Hindsight. "
                f"Our historical memory has reduced MTTR by approximately **{stats['mttr_reduction_pct']}%**.\n\n"
                f"What service or incident would you like to review?"
            )

        if "rough" in t_low or "tired" in t_low or "stress" in t_low or "on-call" in t_low:
            return (
                "On-call shifts during high-traffic surges can be exhausting—I completely hear you. ☕ "
                "The biggest pain point in on-call is having to start troubleshooting from zero when an outage hits. "
                "That's why I remember what fixes worked and what fixes failed in previous incidents so you don't have to guess.\n\n"
                "Take a breath! If an alert is firing, paste the symptoms or logs here and we'll investigate together step by step."
            )

        if "who are you" in t_low or "what can you do" in t_low or "help" in t_low:
            return (
                "I am **IncidentMind AI** — an AI Incident Response Agent designed for SRE and DevOps teams.\n\n"
                "### What I Do Differently:\n"
                "1. **Persistent Incident Memory (Hindsight)**: I don't reset between sessions. I recall past incidents (e.g. INC-0101, INC-0145) to see what fixes worked and which ones failed.\n"
                "2. **Multi-Outcome Learning**: I understand that *Same Symptom != Same Root Cause*. If Payment API throws 503, I evaluate both pool exhaustion AND credential rotation before advising.\n"
                "3. **Telemetry & Diagnostics**: I run safe diagnostic tools (`get_service_status`, `get_recent_logs`, `get_database_metrics`).\n"
                "4. **Human-in-the-Loop Safety**: High-risk actions like pool scaling or pod restarts always require your explicit authorization.\n\n"
                "Try saying: *'Investigate 503 errors on Payment API'* or *'Check database metrics for Payment API'*!"
            )

        if intent == self.INTENT_HINDSIGHT_EXPLANATION:
            return (
                "### How IncidentMind Uses Hindsight 🧠\n\n"
                "Standard AI assistants suffer from **session amnesia**—each time an outage happens, they start from zero and often suggest the same fixes that previously failed.\n\n"
                "IncidentMind connects to **Hindsight** (`incidentmind_org_knowledge` bank) using three core operations:\n"
                "- **`retain()`**: When an incident is resolved or a fix fails, we persist verified facts, root causes, and cautionary lessons.\n"
                "- **`recall()`**: During an active alert, we query the bank with affected service, error codes, and symptoms to retrieve relevant historical precedents with exact *Why-Useful* provenance.\n"
                "- **`reflect()`**: Synthesizes cross-incident mental models (e.g. identifying that Payment API 503s bifurcate into pool saturation vs credential rotation).\n\n"
                "This transforms tribal engineering knowledge into permanent organizational memory."
            )

        if intent == self.INTENT_POSTMORTEM_INQUIRY:
            return (
                "Post-mortems are the lifeblood of continuous engineering reliability! 📋\n\n"
                "Whenever an incident is resolved in IncidentMind, our Post-Mortem Engine automatically drafts:\n"
                "- Executive Impact Summary\n"
                "- Verified Root Cause\n"
                "- Successful Resolution Action\n"
                "- **Failed Fix Attempts** (to prevent repeat mistakes)\n"
                "- Architectural Action Items\n\n"
                "These insights are automatically retained into Hindsight so future on-call engineers benefit immediately."
            )

        # General friendly fallback
        return (
            f"Understood! I'm here to assist with any SRE tasks or engineering questions. "
            f"If there's an active alert, tell me the service or error message (e.g., 'Payment API 503') "
            f"and I'll pull our historical incident memory and diagnostic telemetry right away."
        )


# Singleton
_nlp_instance = None

def get_nlp_processor() -> NLPProcessor:
    global _nlp_instance
    if _nlp_instance is None:
        _nlp_instance = NLPProcessor()
    return _nlp_instance
