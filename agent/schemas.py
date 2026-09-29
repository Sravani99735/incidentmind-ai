"""
Data Schemas and Pydantic Models for IncidentMind AI
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    id: str
    name: str
    tier: str
    owner_team: str
    language: str
    runtime: str
    current_version: str
    dependencies: List[str] = []
    health_status: str = "Healthy"
    description: str = ""


class IncidentSchema(BaseModel):
    id: str
    title: str
    service: str
    severity: str = "High"
    environment: str = "AWS + Kubernetes"
    version: Optional[str] = "v1.0"
    detected_at: Optional[str] = None
    status: str = "Investigating"
    symptoms: List[str] = []
    logs: Optional[str] = ""
    root_cause: Optional[str] = ""
    attempted_fixes: List[str] = []
    successful_resolution: Optional[str] = ""
    failed_fixes: List[str] = []
    outcome: Optional[str] = "Investigating"
    pattern_type: Optional[str] = ""
    post_mortem_summary: Optional[str] = ""
    lessons_learned: Optional[str] = ""
    hindsight_memories: List[str] = []


class ToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    reasoning: str
    requires_approval: bool = False


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any
    executed_at: str
    is_simulation: bool = True


class ApprovalRequest(BaseModel):
    action_id: str
    action_type: str
    description: str
    target_service: str
    parameters: Dict[str, Any]
    risk_level: str = "Medium"  # Low, Medium, High, Critical
    status: str = "pending"  # pending, approved, rejected


class MemoryRecallCard(BaseModel):
    incident_id: str
    service: str
    text: str
    category: str
    outcome: str
    why_useful: str
    is_warning: bool = False
    confidence_label: str = "High Relevance"


class InvestigationResult(BaseModel):
    incident_id: str
    service: str
    severity: str
    status: str
    symptoms: List[str]
    root_cause_hypothesis: str
    evidence_gathered: List[Dict[str, Any]]
    memories_recalled: List[MemoryRecallCard]
    cautions_and_warnings: List[str]
    recommended_actions: List[str]
    approval_required_actions: List[ApprovalRequest]
    bifurcated_symptom_analysis: Optional[Dict[str, Any]] = None
    execution_time_ms: int = 42


class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    incident_id: Optional[str] = None
    service: Optional[str] = None


class ChatMessageResponse(BaseModel):
    conversation_id: str
    sender: str = "agent"
    content: str
    intent: str
    extracted_entities: Dict[str, Any] = {}
    memories_used: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []
    approval_needed: Optional[Dict[str, Any]] = None
    why_useful: Optional[str] = None
    is_memory_powered: bool = True


class PostMortemCreate(BaseModel):
    incident_id: str
    title: str
    service: str
    root_cause: str
    impact_summary: str
    successful_fix: str
    failed_attempts: List[str] = []
    prevention_items: List[str] = []
    lessons_learned: str
