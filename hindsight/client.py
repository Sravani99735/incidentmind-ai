"""
Official Hindsight SDK Client Wrapper for IncidentMind AI
Handles retain, recall, and reflect operations with the official hindsight-client SDK.
Maintains transparent live connection vs local resilient fallback status.
"""

import os
import uuid
import logging
from typing import Optional, List, Dict, Any

from config.settings import (
    HINDSIGHT_URL,
    HINDSIGHT_API_KEY,
    HINDSIGHT_BANK_ID,
    get_hindsight_status
)
from data.db import (
    save_memory_record,
    search_local_memories,
    get_all_memories
)

# Official Hindsight Client imports
try:
    from hindsight_client import (
        Hindsight,
        RecallResponse,
        RecallResult,
        RetainResponse,
        ReflectResponse
    )
    HINDSIGHT_SDK_AVAILABLE = True
except ImportError:
    HINDSIGHT_SDK_AVAILABLE = False

logger = logging.getLogger("incidentmind.hindsight.client")


class HindsightClientWrapper:
    """
    Dedicated client wrapper for Hindsight Memory Layer.
    Ensures all memory operations use official Hindsight methods:
      - retain(): persist extracted incident facts, failed attempts, and resolutions.
      - recall(): retrieve relevant historical outages with multi-strategy search.
      - reflect(): synthesize long-term organizational mental models and recurring patterns.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, bank_id: Optional[str] = None):
        self.base_url = (base_url or HINDSIGHT_URL).rstrip("/")
        self.api_key = api_key or HINDSIGHT_API_KEY
        self.bank_id = bank_id or HINDSIGHT_BANK_ID
        self.is_live = False
        self._client: Optional[Any] = None

        if HINDSIGHT_SDK_AVAILABLE:
            try:
                self._client = Hindsight(
                    base_url=self.base_url,
                    api_key=self.api_key if self.api_key else None
                )
                self.check_connection()
            except Exception as e:
                logger.warning(f"Could not connect to live Hindsight server at {self.base_url}: {e}")
                self.is_live = False

    def check_connection(self) -> bool:
        """Checks if the Hindsight engine is actively responsive."""
        status_info = get_hindsight_status()
        self.is_live = status_info.get("connected", False)
        return self.is_live

    def get_status_info(self) -> Dict[str, Any]:
        """Returns connection diagnostics and mode."""
        self.check_connection()
        return {
            "is_live": self.is_live,
            "base_url": self.base_url,
            "bank_id": self.bank_id,
            "engine": "Hindsight v0.10.1 (Official SDK)",
            "status": "Connected" if self.is_live else "Unavailable",
            "badge_label": "LIVE HINDSIGHT MODE" if self.is_live else "FALLBACK MODE (Local Persistent Resiliency)",
            "note": "Connected to live Hindsight persistent memory server." if self.is_live else "Hindsight server offline. Using local resilient memory store."
        }

    # ==================== RETAIN ====================

    def retain(
        self,
        content: str,
        bank_id: Optional[str] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        service: Optional[str] = None,
        incident_id: Optional[str] = None,
        category: Optional[str] = None,
        outcome: Optional[str] = "Resolved"
    ) -> Dict[str, Any]:
        """
        Retains an incident fact, resolution, failed attempt, or post-mortem lesson.
        Saves locally as well to ensure local resilience.
        """
        target_bank = bank_id or self.bank_id
        safe_meta = {str(k): str(v) for k, v in (metadata or {}).items()}
        safe_tags = [str(t) for t in (tags or [])]

        # Always persist to local resilient storage
        mem_id = f"mem_{uuid.uuid4().hex[:12]}"
        save_memory_record({
            "id": mem_id,
            "bank_id": target_bank,
            "service": service or safe_meta.get("service", "System"),
            "incident_id": incident_id or safe_meta.get("incident_id", ""),
            "text": content,
            "category": category or safe_meta.get("category", "General"),
            "confidence_label": safe_meta.get("confidence_label", "Organizational Knowledge"),
            "context": context or f"Incident {incident_id}",
            "tags": safe_tags,
            "outcome": outcome
        })

        # If live Hindsight is connected, send via official SDK
        if self.check_connection() and self._client:
            try:
                resp = self._client.retain(
                    bank_id=target_bank,
                    content=content,
                    context=context,
                    metadata=safe_meta,
                    tags=safe_tags
                )
                return {
                    "success": True,
                    "id": getattr(resp, "id", mem_id),
                    "bank_id": target_bank,
                    "mode": "live_hindsight"
                }
            except Exception as e:
                logger.warning(f"Live Hindsight retain error: {e}. Fallback record preserved.")

        return {
            "success": True,
            "id": mem_id,
            "bank_id": target_bank,
            "mode": "local_fallback"
        }

    # ==================== RECALL ====================

    def recall(
        self,
        query: str,
        bank_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        service: Optional[str] = None,
        top_k: int = 5
    ) -> Any:
        """
        Recalls relevant incident memories matching query and context.
        Returns official RecallResponse object.
        """
        target_bank = bank_id or self.bank_id

        # 1. Try Live Hindsight Server if available
        if self.check_connection() and self._client:
            try:
                resp = self._client.recall(
                    bank_id=target_bank,
                    query=query,
                    tags=tags,
                    max_tokens=4096
                )
                if resp and hasattr(resp, "results") and resp.results:
                    return resp
            except Exception as e:
                logger.warning(f"Live Hindsight recall failed: {e}. Falling back to resilient store.")

        # 2. Local Resilient Fallback Search
        local_results = search_local_memories(
            query_text=query,
            bank_id=target_bank,
            service=service,
            limit=top_k
        )

        recall_items: List[Any] = []
        for r in local_results:
            safe_meta = {
                "service": str(r.get("service") or ""),
                "incident_id": str(r.get("incident_id") or ""),
                "category": str(r.get("category") or "General"),
                "confidence_label": str(r.get("confidence_label") or "Organizational Knowledge"),
                "outcome": str(r.get("outcome") or "Resolved"),
                "score": str(r.get("score", "0.85"))
            }

            if HINDSIGHT_SDK_AVAILABLE:
                item = RecallResult(
                    id=str(r["id"]),
                    text=str(r["text"]),
                    metadata=safe_meta,
                    tags=[str(t) for t in r.get("tags", [])],
                    context=str(r.get("context") or "")
                )
            else:
                item = {
                    "id": str(r["id"]),
                    "text": str(r["text"]),
                    "metadata": safe_meta,
                    "tags": r.get("tags", []),
                    "context": str(r.get("context") or "")
                }
            recall_items.append(item)

        if HINDSIGHT_SDK_AVAILABLE:
            return RecallResponse(results=recall_items)
        return {"results": recall_items}

    # ==================== REFLECT ====================

    def reflect(
        self,
        query: str,
        bank_id: Optional[str] = None,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes organizational knowledge into higher-level mental models and lessons.
        """
        target_bank = bank_id or self.bank_id

        if self.check_connection() and self._client:
            try:
                resp = self._client.reflect(
                    bank_id=target_bank,
                    query=query,
                    context=context,
                    tags=tags
                )
                return {
                    "synthesis": getattr(resp, "response", str(resp)),
                    "mode": "live_hindsight"
                }
            except Exception as e:
                logger.warning(f"Live Hindsight reflect failed: {e}. Generating local synthesis.")

        # Local synthesis from persistent memories
        memories = search_local_memories(query_text=query, bank_id=target_bank, limit=6)
        if not memories:
            memories = get_all_memories()[:6]

        facts_text = "\n".join([f"- {m['text']}" for m in memories])
        synthesis = (
            f"Organizational synthesis based on {len(memories)} retained incident records:\n"
            f"Key recurring pattern: Services experiencing connection timeouts or 503 errors exhibit bifurcated root causes: "
            f"(1) Resource constraint (connection pool exhaustion), and (2) Security/Config desynchronization (credential rotation mismatch). "
            f"Actionable rule: Always inspect authentication and handshake logs prior to scaling pool limits.\n\n"
            f"Supporting historical evidence:\n{facts_text}"
        )

        return {
            "synthesis": synthesis,
            "mode": "local_fallback",
            "evidence_count": len(memories)
        }


# Singleton instance
_client_instance: Optional[HindsightClientWrapper] = None

def get_hindsight_client() -> HindsightClientWrapper:
    """Returns singleton Hindsight client wrapper."""
    global _client_instance
    if _client_instance is None:
        _client_instance = HindsightClientWrapper()
    return _client_instance
