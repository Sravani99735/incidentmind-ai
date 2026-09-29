"""
Simulated SRE Telemetry and Diagnostics Tools for IncidentMind AI
Provides realistic production signals for diagnostics and investigation.
All tool outputs are clearly labeled as [DEMO ENVIRONMENT].
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


def get_service_status(service_name: str) -> Dict[str, Any]:
    """
    Retrieves real-time infrastructure state, pod health, and resource metrics.
    """
    s_clean = service_name.lower().strip()

    # Dynamic status based on target service
    if "payment" in s_clean:
        status = "Degraded"
        replicas = {"desired": 8, "ready": 5, "unavailable": 3}
        cpu_usage_pct = 42.5
        memory_usage_pct = 78.2
        restarts = 14
        uptime = "14h 22m"
        events = [
            "Pod payment-service-7f89c-a2b1 CrashLoopBackOff",
            "Readiness probe failed: HTTP 503 on /healthz/ready",
            "HPA scaled replicas from 4 to 8 due to latency spike"
        ]
    elif "auth" in s_clean:
        status = "Healthy"
        replicas = {"desired": 6, "ready": 6, "unavailable": 0}
        cpu_usage_pct = 31.0
        memory_usage_pct = 54.0
        restarts = 0
        uptime = "12d 8h"
        events = ["Cluster steady state, all health probes passing"]
    elif "order" in s_clean:
        status = "Degraded"
        replicas = {"desired": 10, "ready": 8, "unavailable": 2}
        cpu_usage_pct = 68.0
        memory_usage_pct = 82.0
        restarts = 3
        uptime = "2d 4h"
        events = ["Upstream timeout on Payment API /v1/checkout"]
    elif "database" in s_clean:
        status = "Healthy"
        replicas = {"desired": 1, "ready": 1, "unavailable": 0}
        cpu_usage_pct = 28.4
        memory_usage_pct = 61.2
        restarts = 0
        uptime = "48d 11h"
        events = ["Aurora PostgreSQL cluster healthy across 3 AZs"]
    else:
        status = "Healthy"
        replicas = {"desired": 4, "ready": 4, "unavailable": 0}
        cpu_usage_pct = 25.0
        memory_usage_pct = 45.0
        restarts = 0
        uptime = "6d 14h"
        events = ["No abnormal pod churn detected"]

    return {
        "service": service_name,
        "health_status": status,
        "replicas": replicas,
        "cpu_usage_pct": cpu_usage_pct,
        "memory_usage_pct": memory_usage_pct,
        "restart_count_last_1h": restarts,
        "uptime": uptime,
        "cluster": "prod-us-east-1-eks",
        "recent_k8s_events": events,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "is_demo_environment": True,
        "environment_label": "[DEMO ENVIRONMENT: High-Fidelity SRE Telemetry]"
    }


def get_recent_logs(service_name: str, lines: int = 20, severity: str = "ALL") -> Dict[str, Any]:
    """
    Fetches container logs for the specified service with timestamped error signatures.
    """
    s_clean = service_name.lower().strip()
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if "payment" in s_clean:
        log_lines = [
            f"{now_ts}.102 [INFO] payment.server: Listening on port 8080 (gRPC 9090)",
            f"{now_ts}.140 [WARN] payment.http: Ingress spike: 1,840 req/sec on /v1/checkout/process",
            f"{now_ts}.185 [ERROR] payment.db.pool: Connection acquisition timeout after 5000ms. active=98 idle=2 max=100 queue=312",
            f"{now_ts}.210 [ERROR] payment.db.client: Failed to obtain connection from PgBouncer pooler: connection pool exhausted",
            f"{now_ts}.245 [INFO] payment.auth: Token signature validation: JWKS verified (auth=valid, token_age=140s)",
            f"{now_ts}.280 [FATAL] payment.checkout: Database connection pool exhausted. Returning HTTP 503 to ingress NLB",
            f"{now_ts}.310 [ERROR] payment.worker: Worker thread pool saturated: 64/64 workers blocked on DB acquisition",
            f"{now_ts}.340 [WARN] payment.health: Readiness probe degraded: DB query latency > 5000ms"
        ]
    elif "auth" in s_clean:
        log_lines = [
            f"{now_ts}.050 [INFO] auth.token: Issued JWT token for subject user_99482 (claims verified)",
            f"{now_ts}.080 [INFO] auth.jwks: Key rotation check: current key id 'key_2026_q3' valid (expires in 45 days)",
            f"{now_ts}.120 [WARN] auth.rate_limit: Token introspection rate limit warning for client 'order-service' (420/500 rps)",
            f"{now_ts}.150 [INFO] auth.redis: Session cache hit ratio: 98.4%"
        ]
    elif "order" in s_clean:
        log_lines = [
            f"{now_ts}.010 [INFO] order.checkout: Processing checkout order ord_8849204",
            f"{now_ts}.085 [ERROR] order.payment_client: Payment API returned HTTP 503 for checkout transaction tx_7718",
            f"{now_ts}.110 [WARN] order.retry: Retrying payment settlement in 1000ms with exponential jitter (attempt 2/3)",
            f"{now_ts}.210 [ERROR] order.payment_client: Payment API checkout retry failed: 503 Service Unavailable"
        ]
    else:
        log_lines = [
            f"{now_ts}.001 [INFO] service.main: Request handled in 12ms status=200",
            f"{now_ts}.045 [INFO] service.health: Healthcheck OK (database=OK, cache=OK)"
        ]

    return {
        "service": service_name,
        "lines_returned": min(lines, len(log_lines)),
        "logs": "\n".join(log_lines[:lines]),
        "has_error_signatures": any("[ERROR]" in l or "[FATAL]" in l for l in log_lines),
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "is_demo_environment": True,
        "environment_label": "[DEMO ENVIRONMENT: High-Fidelity SRE Telemetry]"
    }


def get_deployment_history(service_name: str) -> Dict[str, Any]:
    """
    Returns deployment history and release tags to establish timeline correlation.
    """
    s_clean = service_name.lower().strip()

    if "payment" in s_clean:
        deployments = [
            {
                "version": "v2.6.2",
                "deployed_at": "3 hours ago (2026-09-28 17:30 UTC)",
                "commit": "a4f89d1",
                "author": "payments-dev@company.com",
                "message": "fix: batch checkout settlement reconciliation logic",
                "status": "Deployed",
                "config_changes": ["PGBOUNCER_MAX_CONNECTIONS=100", "TIMEOUT_MS=5000"]
            },
            {
                "version": "v2.6.0",
                "deployed_at": "26 days ago (2026-09-02 03:00 UTC)",
                "commit": "b8901cc",
                "author": "cicd-runner@company.com",
                "message": "feat: secrets manager rotation update (INC-0145 deploy)",
                "status": "Deployed",
                "config_changes": ["EXTERNAL_SECRETS_REFRESH_INTERVAL=1h"]
            },
            {
                "version": "v2.4.0",
                "deployed_at": "49 days ago (2026-08-10 14:00 UTC)",
                "commit": "f1023aa",
                "author": "payments-dev@company.com",
                "message": "feat: connection pool tuning (INC-0101 deploy)",
                "status": "Deployed",
                "config_changes": ["PGBOUNCER_MAX_CONNECTIONS=100"]
            }
        ]
    else:
        deployments = [
            {
                "version": "v1.4.1",
                "deployed_at": "2 days ago",
                "commit": "c4982a1",
                "author": "sre-team@company.com",
                "message": "chore: dependency security update",
                "status": "Deployed",
                "config_changes": []
            }
        ]

    return {
        "service": service_name,
        "total_deployments_recorded": len(deployments),
        "recent_deployments": deployments,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "is_demo_environment": True,
        "environment_label": "[DEMO ENVIRONMENT: High-Fidelity SRE Telemetry]"
    }


def get_database_metrics(service_name: str) -> Dict[str, Any]:
    """
    Inspects connection pool saturation, active queries, and DB host metrics.
    """
    s_clean = service_name.lower().strip()

    if "payment" in s_clean:
        pool_metrics = {
            "max_connections": 100,
            "active_connections": 98,
            "idle_connections": 2,
            "saturation_pct": 98.0,
            "waiting_connection_queue": 312,
            "connection_acquisition_latency_p99_ms": 5012,
            "database_host_cpu_pct": 26.4,  # Notice: DB host CPU is NOT pegged!
            "active_deadlocks": 0,
            "replication_lag_ms": 0,
            "auth_failures_last_5m": 0  # Notice: Auth is NOT failing! Pool is saturated!
        }
    else:
        pool_metrics = {
            "max_connections": 100,
            "active_connections": 18,
            "idle_connections": 82,
            "saturation_pct": 18.0,
            "waiting_connection_queue": 0,
            "connection_acquisition_latency_p99_ms": 4.2,
            "database_host_cpu_pct": 15.0,
            "active_deadlocks": 0,
            "replication_lag_ms": 2,
            "auth_failures_last_5m": 0
        }

    return {
        "service": service_name,
        "database_type": "Aurora PostgreSQL 16 / PgBouncer",
        "metrics": pool_metrics,
        "diagnostics_summary": (
            "Pool saturation is at 98% with 312 queued requests. "
            "Primary DB CPU is low (26.4%), indicating connection limit saturation rather than database instance overload."
            if pool_metrics["saturation_pct"] > 90 else "Connection pool is healthy with 0 queue depth."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "is_demo_environment": True,
        "environment_label": "[DEMO ENVIRONMENT: High-Fidelity SRE Telemetry]"
    }


def check_health_endpoint(service_name: str, endpoint: str = "/healthz") -> Dict[str, Any]:
    """
    Probes internal service health check endpoint.
    """
    s_clean = service_name.lower().strip()

    if "payment" in s_clean:
        status_code = 503
        latency_ms = 5024
        checks = {
            "live": True,
            "database_pool": False,  # Failing
            "auth_provider": True,  # Passing
            "redis_cache": True
        }
    else:
        status_code = 200
        latency_ms = 8
        checks = {
            "live": True,
            "database_pool": True,
            "auth_provider": True,
            "redis_cache": True
        }

    return {
        "service": service_name,
        "endpoint": endpoint,
        "http_status": status_code,
        "latency_ms": latency_ms,
        "subsystem_checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "is_demo_environment": True,
        "environment_label": "[DEMO ENVIRONMENT: High-Fidelity SRE Telemetry]"
    }
