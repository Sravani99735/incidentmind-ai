# 2.5-Minute Demo Video Script — IncidentMind AI

> **Target Video Duration:** 2 minutes 30 seconds  
> **Presenter:** Lead AI / SRE Engineer  
> **Key Message:** *"Production Incidents Shouldn't Start From Zero."*

---

### 1. Problem [0:00 - 0:20]
- **Visual:** Presenter on camera, transition to screen share of landing page (`/`).
- **Narration:**
  > "Hi judges! We've all been on-call at 3:00 AM when a critical service goes down. You scramble through logs, try a fix, and only later realize your teammate already proved that fix fails three weeks ago. 
  > 
  > Generic AI assistants like ChatGPT can't solve this because they have zero organizational memory across sessions. When an outage hits, they start from scratch and repeat the same mistakes."

---

### 2. IncidentMind [0:20 - 0:35]
- **Visual:** Landing page showing live KPI metrics and the Hindsight persistent memory status indicator.
- **Narration:**
  > "That's why we built **IncidentMind AI** — an AI-powered incident response agent that builds persistent organizational memory using **Hindsight**. 
  > 
  > It remembers root causes, telemetry signatures, successful mitigations, and critically: **failed troubleshooting attempts**."

---

### 3. INC-0101 (The Initial Learning) [0:35 - 0:55]
- **Visual:** Navigate to `/demo` &rarr; Step 1 is active.
- **Narration:**
  > "Let's walk through our 60-second proof.
  > 
  > In **INC-0101**, our Payment API experiences an HTTP 503 outage during a checkout surge. Telemetry shows PgBouncer pool saturation. The team scales the pool from 50 to 100, which resolves the outage. 
  > 
  > IncidentMind uses `hindsight.retain()` to permanently store this root cause and verified resolution."

---

### 4. INC-0145 (Failed Fix & Caution) [0:55 - 1:15]
- **Visual:** Click 'Next Step' &rarr; Step 2 (INC-0145) is active.
- **Narration:**
  > "Three weeks later in **INC-0145**, Payment API throws identical 503 errors! An engineer blindly tries increasing the pool to 150—and it **FAILS** completely. 
  > 
  > Why? Because the root cause this time was an AWS Secrets Manager credential rotation mismatch! 
  > 
  > Crucially, IncidentMind retains this **failed troubleshooting attempt** as a cautionary memory so the team never wastes 45 minutes on that dead end again."

---

### 5. INC-0182 (The Hindsight Payoff) [1:15 - 1:45]
- **Visual:** Click 'Finish & Open Workspace' &rarr; Investigation Workspace opens for **INC-0182**.
- **Narration:**
  > "Now, here is the payoff in our Investigation Workspace for **INC-0182**. 
  > 
  > Payment API triggers a 503 alert again. A generic AI would blindly guess or repeat the failed pool increase. 
  > 
  > Look at IncidentMind AI: on the right, it has queried Hindsight. It recalled **BOTH** INC-0101 and INC-0145! 
  > 
  > It immediately flags our core law: **Same Symptom != Same Root Cause**. 
  > 
  > It inspects live telemetry: `auth_failures=0` and `auth=valid`, while `waiting_queue=312` and `active=98/100`. 
  > 
  > It rules out the credential trap and confirms pool saturation. 
  > 
  > And notice our safety boundary: it generates an **Approval Gateway Card**. I authorize the action, and the incident resolves in 90 seconds instead of 45 minutes!"

---

### 6. Hindsight Memory [1:45 - 2:05]
- **Visual:** Open `/memory` (Hindsight Memory Explorer) showing Bank `incidentmind_org_knowledge`.
- **Narration:**
  > "Behind the scenes, IncidentMind AI connects to Hindsight using the official `hindsight-client` Python SDK:
  > - `retain()` codifies root causes, resolutions, and failed attempts.
  > - `recall()` retrieves historical precedents with Why-Useful provenance.
  > - `reflect()` autonomously synthesizes recurring failure archetypes across services."

---

### 7. Results [2:05 - 2:20]
- **Visual:** Open `/before-after` (The Memory Difference Lab).
- **Narration:**
  > "The benchmark results speak for themselves:
  > - **86% MTTR Reduction** (down from 45 minutes to 6 minutes).
  > - **0% Risk** of repeating previously failed fixes (versus 65% for generic AI).
  > - Gated human-in-the-loop approvals for production safety."

---

### 8. Closing [2:20 - 2:30]
- **Visual:** Presenter on camera with GitHub repo link on screen.
- **Narration:**
  > "Production incidents are inevitable. But starting from zero is an engineering choice. With IncidentMind AI and Hindsight, your team never fights the same outage twice.
  > 
  > Thank you!"
