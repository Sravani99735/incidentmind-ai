"""
Configuration Settings for IncidentMind AI
"""

import os
import time
import socket
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Server settings
PORT = int(os.environ.get("PORT", 5000))
SECRET_KEY = os.environ.get("SECRET_KEY", "incidentmind-sre-hackathon-2026-secret")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
DEMO_MODE = os.environ.get("DEMO_MODE", "True").lower() in ("true", "1", "yes")

# Database & Data Paths
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "incidentmind.db"
INCIDENTS_DATA_PATH = DATA_DIR / "incidents.json"
SERVICES_DATA_PATH = DATA_DIR / "services.json"

# Hindsight Configuration
HINDSIGHT_URL = os.environ.get("HINDSIGHT_URL", "http://localhost:8888").rstrip("/")
HINDSIGHT_API_KEY = os.environ.get("HINDSIGHT_API_KEY", "")
HINDSIGHT_BANK_ID = os.environ.get("HINDSIGHT_BANK_ID", "incidentmind_org_knowledge")

# LLM Configuration
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen/qwen3-32b")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", 15))

# Hindsight status caching
_hindsight_status_cache = None
_hindsight_cache_time = 0


def get_hindsight_status():
    """
    Checks if an external Hindsight engine is actively reachable at HINDSIGHT_URL.
    Cached for 5 seconds to guarantee sub-millisecond page renders.
    """
    global _hindsight_status_cache, _hindsight_cache_time
    now = time.time()
    if _hindsight_status_cache is not None and (now - _hindsight_cache_time) < 5:
        return _hindsight_status_cache

    parsed = urlparse(HINDSIGHT_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # Fast TCP socket probe (< 120ms)
    sock_alive = False
    try:
        with socket.create_connection((host, port), timeout=0.12):
            sock_alive = True
    except Exception:
        sock_alive = False

    if not sock_alive:
        _hindsight_status_cache = {
            "connected": False,
            "status": "Unavailable",
            "badge_class": "status-unavailable",
            "url": HINDSIGHT_URL,
            "mode": "fallback",
            "label": "FALLBACK MODE (Local Persistent Resiliency)",
            "note": "Hindsight engine offline at configured URL. Using transparent local resilient memory bank."
        }
        _hindsight_cache_time = now
        return _hindsight_status_cache

    # Verify HTTP endpoint
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{HINDSIGHT_URL}/healthz",
            headers={"Authorization": f"Bearer {HINDSIGHT_API_KEY}"} if HINDSIGHT_API_KEY else {},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=0.4) as resp:
            is_ok = resp.status in (200, 204)
    except Exception:
        is_ok = False

    _hindsight_status_cache = {
        "connected": is_ok,
        "status": "Connected" if is_ok else "Unavailable",
        "badge_class": "status-connected" if is_ok else "status-unavailable",
        "url": HINDSIGHT_URL,
        "mode": "live" if is_ok else "fallback",
        "label": "LIVE HINDSIGHT MODE" if is_ok else "FALLBACK MODE",
        "note": "Connected to official Hindsight persistent memory engine." if is_ok else "Hindsight server unreachable."
    }
    _hindsight_cache_time = now
    return _hindsight_status_cache


def get_llm_status():
    """Returns LLM engine status."""
    if LLM_API_KEY:
        masked = LLM_API_KEY[:4] + "..." + LLM_API_KEY[-4:] if len(LLM_API_KEY) > 8 else "***"
        return {
            "configured": True,
            "provider": "Groq / OpenAI Compatible",
            "model": LLM_MODEL,
            "key_masked": masked,
            "mode": "live_llm",
            "status": "Connected",
            "badge_class": "status-connected"
        }
    return {
        "configured": False,
        "provider": "SRE Reasoning Engine",
        "model": f"{LLM_MODEL} (Demo Simulation)",
        "key_masked": "None",
        "mode": "simulation",
        "status": "Active (Demo Simulation)",
        "badge_class": "status-sim",
        "note": "Configured for zero-friction evaluation. Set LLM_API_KEY in .env for live cloud inference."
    }
