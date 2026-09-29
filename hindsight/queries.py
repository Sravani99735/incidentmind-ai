"""
Query Formulation and Keyword Extraction for Hindsight Memory Recall
Transforms raw incident alerts, logs, and stack traces into optimized retrieval queries.
"""

import re
from typing import List, Dict, Any, Optional


def extract_error_codes(logs: str) -> List[str]:
    """Extracts HTTP status codes, gRPC status codes, and error exceptions from log snippets."""
    if not logs:
        return []

    codes = []
    # HTTP codes like 500, 502, 503, 504, 429
    http_matches = re.findall(r"\b(50[0-4]|429|401|403)\b", logs)
    codes.extend(http_matches)

    # Common exception tokens
    exceptions = re.findall(
        r"\b([A-Za-z]+(?:Exception|Timeout|Error|Crash|Deadlock|Exhausted|OOMKilled))\b",
        logs
    )
    codes.extend(exceptions)

    # Postgres / DB codes
    db_matches = re.findall(r"(?:code\s*=\s*['\"]?([A-Z0-9]{5})['\"]?|password authentication failed|connection pool exhausted)", logs, re.IGNORECASE)
    for m in db_matches:
        if isinstance(m, str) and m:
            codes.append(m)

    return list(dict.fromkeys(codes))  # Deduplicate maintaining order


def build_incident_search_query(
    service: str,
    symptoms: Optional[List[str]] = None,
    logs: Optional[str] = None,
    environment: Optional[str] = None
) -> str:
    """
    Constructs an information-dense query string designed to maximize semantic and
    keyword match in Hindsight memory banks.
    """
    parts = []
    if service:
        parts.append(f"Service: {service}")

    if symptoms:
        cleaned_symptoms = [s.strip() for s in symptoms if s.strip()]
        if cleaned_symptoms:
            parts.append(f"Symptoms: {', '.join(cleaned_symptoms)}")

    if logs:
        error_tokens = extract_error_codes(logs)
        if error_tokens:
            parts.append(f"Signatures: {' '.join(error_tokens[:6])}")
        
        # Take key log line with ERROR or FATAL
        error_lines = [
            line.strip() for line in logs.splitlines()
            if any(term in line.upper() for term in ("ERROR", "FATAL", "PANIC", "CRITICAL", "TIMEOUT"))
        ]
        if error_lines:
            parts.append(f"Log excerpt: {error_lines[0][:150]}")

    if environment:
        parts.append(f"Environment: {environment}")

    return " | ".join(parts)


def generate_contrastive_queries(incident: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generates alternative queries to catch divergent root causes for identical symptoms.
    e.g. When experiencing 503 on Payment API, search for:
    - Connection pool saturation
    - Credential / secret rotation failure
    - Upstream gateway timeout
    """
    service = incident.get("service", "")
    symptoms = incident.get("symptoms", [])
    sym_str = " ".join(symptoms)

    queries = [
        {
            "focus": "Exact Symptom & Service",
            "query": f"{service} {sym_str}"
        }
    ]

    if "503" in sym_str or "timeout" in sym_str.lower() or "connection" in sym_str.lower():
        queries.append({
            "focus": "Resource Contention Pattern",
            "query": f"{service} database connection pool saturation exhausted PgBouncer active max"
        })
        queries.append({
            "focus": "Authentication / Configuration Pattern",
            "query": f"{service} credential rotation password authentication failed SecretManager ExternalSecrets"
        })

    if "cpu" in sym_str.lower() or "memory" in sym_str.lower() or "oom" in sym_str.lower():
        queries.append({
            "focus": "Memory Leak & Garbage Collection",
            "query": f"{service} memory leak OOMKilled heap heapdump garbage collection"
        })

    return queries
