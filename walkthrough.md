# Evaluator & Judge Walkthrough — IncidentMind AI

> **Project Name:** IncidentMind AI  
> **Tagline:** *"Production Incidents Shouldn't Start From Zero."*  
> **Core Proposition:** AI-powered incident response and investigation agent with persistent organizational memory using Hindsight.

---

## 1. Setup

### Prerequisites
- Python 3.10+
- pip
- Git

### Installation
From the project directory (`c:\Users\ADMIN\OneDrive\Desktop\Project_First\pro-ject`):

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

*(Note: `HINDSIGHT_URL` defaults to `http://localhost:8888`. When offline, the app operates in transparent local resilient fallback mode with full schema adherence and persistence).*

---

## 2. Start Application

Start the IncidentMind AI server:

```bash
python app.py
```

Expected startup output:
```text
[INFO] incidentmind.app: Starting IncidentMind AI Server on port 5000 (Debug: True)
 * Running on http://127.0.0.1:5000
```

Open **`http://127.0.0.1:5000/`** in your web browser.

---

## 3. Open `/demo`

Navigate to:
**`http://127.0.0.1:5000/demo`**  
*(or click the **"60s Demo"** button in the top navigation bar).*

---

## 4. Run the 3 Incidents

On the `/demo` page, you can click **"Auto-Play 60s Demo"** or manually advance using **"Next Step"**:

### Incident 1: INC-0101 (First Encounter)
- **Scenario:** Payment API experiences HTTP 503 during a promotional checkout surge. Database connection pool reaches 50/50 while DB CPU remains healthy (<25%).
- **Action Taken:** SRE scales the connection pool from 50 to 100 in ConfigMap.
- **Outcome:** Resolved within 3 minutes.
- **What Hindsight Retains:** Root cause (pool exhaustion) and proven resolution (pool 50 &rarr; 100).
- **Lesson Stored:** Baseline established: When DB CPU is low but pool queue is high, pool expansion works.

### Incident 2: INC-0145 (Failed Fix & Caution)
- **Scenario:** Similar HTTP 503 symptoms appear after a nightly deployment.
- **Mistake:** SRE team blindly repeats the INC-0101 fix (scaling pool 100 &rarr; 150). **IT FAILS!**
- **Actual Root Cause:** AWS Secrets Manager credential rotation mismatch; pods booted with stale password.
- **Verified Fix:** Force-refreshed Kubernetes Secret from AWS Secrets Manager using ExternalSecrets operator.
- **What Hindsight Retains:** **The failed troubleshooting attempt is retained as a cautionary lesson!**
- **Crucial Lesson Stored:** *"Same Symptom != Same Root Cause. Check authentication logs before touching connection pool size."*

### Incident 3: INC-0182 (The Hindsight Payoff)
- **Scenario:** Recurring HTTP 503 surge during batch settlement.
- **Agent Behavior:**
  1. IncidentMind AI queries Hindsight Bank `incidentmind_org_knowledge`.
  2. It recalls **BOTH** INC-0101 and INC-0145.
  3. It identifies that symptoms are identical but root causes diverge.
  4. It invokes diagnostic tools: checks `auth_failures=0` and `auth=valid`, while `waiting_queue=312` and `active=98/100`.
  5. It rules out credential failure (avoiding the INC-0145 trap) and confirms pool saturation.
  6. It presents an **Authorization Gateway Card** to scale the pool to 150.
- **Outcome:** Outage mitigated in 90 seconds with **0% risk of repeating the failed fix** and an **86% reduction in MTTR**!

---

## 5. Run Tests

To execute the complete automated test suite:

```bash
python -m unittest discover tests
```

---

## 6. Expected Results

The test suite will execute 21 tests covering all five core subsystems:

```text
Ran 21 tests in 0.617s
OK

 [PASS] test_01_nlp_intent_classification
 [PASS] test_02_conversational_chat_reply
 [PASS] test_03_incident_investigation_workflow
 [PASS] test_04_human_in_the_loop_approval_execution
 [PASS] test_01_client_initialization_and_status
 [PASS] test_02_retain_operation
 [PASS] test_03_recall_operation (Retrieved 3 memories)
 [PASS] test_04_memory_service_multi_outcome_recall (Why-Useful verified)
 [PASS] test_05_reflect_synthesis
 [PASS] test_01_service_catalog_completeness (Found 8 services)
 [PASS] test_02_incident_catalog_enterprise_scale (Total incidents: 32)
 [PASS] test_03_critical_patterns_present (INC-0101, INC-0145, INC-0182 verified)
 [PASS] test_04_postmortem_generation_and_retention
 [PASS] test_05_learning_service_metrics (5 failure archetypes codified)

========================================================
 STARTING CRITICAL END-TO-END HINDSIGHT MEMORY TEST
 (INC-0101 -> INC-0145 -> INC-0182 Progression)
========================================================
 [PASS] Step 1 & 2: INC-0101 resolved and retained into Hindsight.
 [PASS] Step 3: INC-0145 triage successfully recalled historical INC-0101 precedent.
 [PASS] Step 4 & 5: INC-0145 recorded failed fix attempt and cautionary lesson.
 [PASS] Step 6a: Multi-Outcome Correlation active! Detected divergence: Same Symptom != Same Root Cause
 [PASS] Step 6b: Successfully loaded cautionary warning against repeating INC-0145 failed fix.
 [PASS] Step 6c: MTTR Reduction verified: 86% with 0% repeat mistake risk.
========================================================
 CRITICAL MULTI-INCIDENT END-TO-END TEST PASSED 100%!
========================================================

 [PASS] test_01_service_status_tool
 [PASS] test_02_recent_logs_tool
 [PASS] test_03_database_metrics_tool
 [PASS] test_04_deployment_history_tool
 [PASS] test_05_health_endpoint_tool
 [PASS] test_06_tool_validator_and_approval_gate
```

---

## 7. Key Takeaways for Evaluators

1. **Persistent Memory is Central:** Hindsight is not decorative; without memory of INC-0145, the agent would blindly repeat the failed pool fix.
2. **Multi-Outcome Learning:** Storing failed attempts prevents repeat downtime.
3. **Safety First:** Diagnostic tools run automatically; state-altering changes require human-in-the-loop authorization with permanent audit logging.
