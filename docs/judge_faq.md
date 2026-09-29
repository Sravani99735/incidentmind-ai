# Judge & Evaluator FAQ — IncidentMind AI

---

### Q1: What problem is solved?
**Answer:** Modern engineering organizations suffer from **Organizational Incident Amnesia**. Production outages happen repeatedly, but because past post-mortems live in static documents, on-call engineers start troubleshooting from zero each time. They waste critical Mean Time to Resolution (MTTR) repeating previously failed troubleshooting attempts. IncidentMind AI solves this by embedding **Hindsight** as persistent organizational incident memory.

---

### Q2: What makes it different from a chatbot?
**Answer:** A generic chatbot is a passive text generator with **session amnesia**; it analyzes an outage in total isolation and forgets everything when the session ends. 
IncidentMind AI is an **autonomous SRE incident investigation workspace**:
1. It maintains persistent organizational memory across microservices and engineering rotations.
2. It executes active diagnostic tools (`get_service_status`, `get_recent_logs`, `get_database_metrics`).
3. It understands **multi-outcome learning** (remembering what failed in the past).
4. It is gated by a **Human-in-the-Loop Approval Gateway** for state-altering actions with tamper-evident audit logging.

---

### Q3: What is Hindsight?
**Answer:** [Hindsight](https://hindsight.vectorize.io/) is an intelligent persistent memory layer for AI agents. Unlike simple vector databases that only do one-off cosine similarity search, Hindsight builds structured, persistent knowledge banks that retain complex facts, multi-outcome relationships, and high-level mental models across agent sessions.

---

### Q4: How does persistent memory work?
**Answer:** When an incident is investigated and resolved:
1. Incident facts, symptoms, logs, and root causes are structured and sent to Hindsight memory bank `incidentmind_org_knowledge`.
2. Proven remediations are tagged as verified solutions.
3. Crucially, **failed troubleshooting attempts are retained as cautionary directives**.
4. During future outages, these memories are recalled with exact **Why-Useful** rationale, steering engineers away from repeating dead ends.

---

### Q5: What are Retain / Recall / Reflect?
**Answer:** The three fundamental operations of the Hindsight SDK:
- **`retain(content, metadata, tags, context)`**: Persists newly verified incident facts, root causes, successful resolutions, and failed attempts.
- **`recall(query, tags, top_k)`**: Recalls relevant historical incident precedents matching the active incident's symptoms, error signatures, and affected service.
- **`reflect(query)`**: Autonomously synthesizes cross-incident mental models and identifies recurring failure archetypes across microservices without human prompting.

---

### Q6: How does investigation work?
**Answer:** The agent follows an automated 8-stage pipeline:
1. **NLP Parsing:** Identifies affected microservice, error codes, and symptoms.
2. **Hindsight Recall:** Queries organizational memory bank for historical precedents.
3. **Multi-Outcome Correlation:** Checks whether identical symptoms previously had divergent root causes (**Same Symptom != Same Root Cause**).
4. **Live Tool Execution:** Gathers live telemetry (pod health, error logs, connection pool queue, auth status).
5. **Evidence Synthesis:** Compares live telemetry against historical patterns to confirm or rule out hypotheses.
6. **Remediation Planning:** Proposes targeted action.
7. **Human Approval Gateway:** Gated execution for any state-altering changes.
8. **Post-Mortem & Retention:** Updates incident timeline, drafts post-mortem, and retains new learnings.

---

### Q7: What tools are used?
**Answer:** A suite of 5 simulated diagnostic tools (clearly labeled `[DEMO ENVIRONMENT]`):
- **`get_service_status`**: Returns replica ready counts, CPU/RAM usage %, restart count, uptime.
- **`get_recent_logs`**: Fetches container logs with timestamped error signatures.
- **`get_deployment_history`**: Returns recent git commits, release tags, and ConfigMap changes.
- **`get_database_metrics`**: Inspects PgBouncer pool saturation, waiting queue depth, and DB host CPU.
- **`check_health_endpoint`**: Probes HTTP readiness and dependency subsystem checks.

---

### Q8: Why human approval?
**Answer:** In production SRE, autonomous agents must never blindly modify infrastructure. Gating state-altering actions (e.g., scaling database connection pools, restarting pods, rotating credentials) behind human authorization ensures the engineer maintains executive control, prevents catastrophic hallucinated actions, and fulfills SOC2/compliance requirements.

---

### Q9: How is safety handled?
**Answer:** Safety is handled via three strict boundaries:
1. **Tool Segmentation:** Diagnostic tools are read-only and auto-approved; remediation tools require explicit human authorization.
2. **Audit Logging:** Every approved action is logged permanently to the `audit_events` database table with approver identity, timestamps, parameters, and post-action verification.
3. **Environment Transparency:** All telemetry is explicitly marked as `[DEMO ENVIRONMENT: High-Fidelity SRE Telemetry]`.

---

### Q10: How is MTTR calculated?
**Answer:** In our side-by-side benchmark (`/before-after` and `tests/test_memory.py`):
- **Stateless AI baseline (45 minutes):** The assistant blindly recommends restarting pods and increasing pool size without checking auth logs. In production, this causes prolonged queue timeouts, failed handshakes, and manual rollbacks.
- **IncidentMind AI (6 minutes):** With Hindsight, the agent immediately checks auth telemetry (`auth_failures=0`), rules out credential rotation, verifies queue saturation (`active=98/100`), and scales the pool with human authorization, achieving an **86% reduction in MTTR**.

---

### Q11: How are failed fixes avoided?
**Answer:** When a troubleshooting fix fails (e.g., in INC-0145, increasing the pool failed because the root cause was credential rotation), IncidentMind AI explicitly retains the failed attempt with category `Failed Attempt` and outcome `Failed`. During subsequent triage, the memory service surfaces these records as **⚠️ CAUTION: FAILED FIX** badges with explicit instructions not to repeat that action.

---

### Q12: What happens if Hindsight is unavailable?
**Answer:** The application implements graceful local resilience. If the external Hindsight server is offline, the client wrapper automatically switches to our local resilient storage (SQLite-backed `memory_records` with identical schema and search scoring).

---

### Q13: What is fallback mode?
**Answer:** When the external Hindsight server at `HINDSIGHT_URL` is unreachable, the application displays:  
`● Hindsight Unavailable (FALLBACK MODE: Local Persistent Resiliency)`  
The agent continues operating with full memory persistence using the local resilient store. **Crucial Hackathon Rule:** We never fake Hindsight calls or display simulated live checkmarks when offline.

---

### Q14: How is it tested?
**Answer:** A comprehensive 21-test automated suite (`python -m unittest discover tests`) passing in under 1 second:
- `tests/test_hindsight.py`: Client wrapper, retain, recall, reflect, and diagnostics.
- `tests/test_agent.py`: NLP classification, conversational chat, triage, and human approval gateway.
- `tests/test_memory.py`: **Critical End-to-End Test (INC-0101 &rarr; INC-0145 &rarr; INC-0182)**.
- `tests/test_tools.py`: 5 diagnostic tools, argument validation, and demo tags.
- `tests/test_incidents.py`: 8 microservices, 32 enterprise incidents, post-mortems, and learning engine.

---

### Q15: What is the architecture?
**Answer:**
```text
User 
 → IncidentMind AI Agent 
 → Intent / Reasoning 
 → Investigation Tools 
 → Hindsight Memory (Retain / Recall / Reflect) 
 → Human Approval Gate 
 → Safe Action Execution 
 → Learning / Post-Mortem
```
Built on Python 3.10+, Flask, SQLite, and the official `hindsight-client` Python SDK.

---

### Q16: Future scope?
**Answer:**
1. Native Slack and PagerDuty bot integrations for real-time incident war rooms.
2. Multi-cluster, cross-region Hindsight memory federation across AWS, GCP, and Azure.
3. Automated canary verification and rolling rollback orchestration.
4. OpenTelemetry eBPF trace ingestion into Hindsight memory banks.
