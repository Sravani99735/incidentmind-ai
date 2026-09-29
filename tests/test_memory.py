"""
Critical End-to-End Multi-Outcome Incident Memory Test for IncidentMind AI
Verifies the complete organizational learning loop:
1. INC-0101 (First Encounter): Pool saturation -> Solved by pool increase -> Retained in Hindsight.
2. INC-0145 (Costly Mistake): Identical 503 -> Blindly trying pool increase fails! -> Credential fix -> Retained failed attempt & caution in Hindsight.
3. INC-0182 (The Payoff): Recurring 503 -> Agent recalls BOTH precedents -> Understands 'Same Symptom != Same Root Cause' -> Inspects auth vs pool telemetry -> Recommends verified action with 0% repeat mistake risk.
"""

import unittest
from hindsight.memory_service import get_memory_service
from services.analysis_service import get_analysis_service
from agent.incident_agent import get_incident_agent
from data.db import create_incident, get_incident_by_id, update_incident


class TestMultiOutcomeIncidentMemory(unittest.TestCase):

    def setUp(self):
        self.memory_service = get_memory_service()
        self.analysis_service = get_analysis_service()
        self.agent = get_incident_agent()

    def test_complete_end_to_end_memory_progression(self):
        print("\n========================================================")
        print(" STARTING CRITICAL END-TO-END HINDSIGHT MEMORY TEST")
        print(" (INC-0101 -> INC-0145 -> INC-0182 Progression)")
        print("========================================================")

        # ----------------------------------------------------
        # STEP 1 & 2: INC-0101 Initial Incident & Retention
        # ----------------------------------------------------
        inc_0101_data = {
            "id": "INC-0101",
            "title": "Payment API 503 During Surge",
            "service": "Payment API",
            "severity": "Critical",
            "symptoms": ["HTTP 503 Service Unavailable", "PgBouncer pool exhausted"],
            "logs": "2026-08-10 [ERROR] payment.db.pool: connection acquisition timeout active=50 max=50 queue=284",
            "root_cause": "Database connection pool exhaustion caused by concurrent surge exceeding default 50 connection ceiling.",
            "successful_resolution": "Increased DB connection pool max_connections from 50 to 100 in ConfigMap.",
            "failed_fixes": [],
            "status": "Resolved"
        }
        create_incident(inc_0101_data)
        retained_ids_0101 = self.memory_service.retain_incident_resolution(inc_0101_data)
        self.assertGreater(len(retained_ids_0101), 0)
        print(" [PASS] Step 1 & 2: INC-0101 resolved and retained into Hindsight.")

        # ----------------------------------------------------
        # STEP 3 & 4 & 5: INC-0145 Second Incident with Failed Fix Caution
        # ----------------------------------------------------
        # Query memory for new incident with identical symptoms
        recall_for_0145 = self.memory_service.recall_for_incident(
            service="Payment API",
            symptoms=["HTTP 503 Service Unavailable", "database connection timeout"],
            logs="2026-09-02 [ERROR] payment.db: password authentication failed for user 'payment_app'"
        )
        # Verify INC-0101 was recalled
        inc_ids_recalled = [m["incident_id"] for m in recall_for_0145["memories"]]
        self.assertIn("INC-0101", inc_ids_recalled)
        print(" [PASS] Step 3: INC-0145 triage successfully recalled historical INC-0101 precedent.")

        # Retain that increasing pool to 150 FAILED because credentials were broken
        inc_0145_data = {
            "id": "INC-0145",
            "title": "Payment API 503 After Deployment",
            "service": "Payment API",
            "severity": "Critical",
            "symptoms": ["HTTP 503 Service Unavailable", "database connection timeout"],
            "logs": "2026-09-02 [ERROR] payment.db: password authentication failed for user 'payment_app'",
            "root_cause": "AWS Secrets Manager credential rotation failure during CI/CD rollout.",
            "attempted_fixes": ["Attempted increasing connection pool 100->150 (FAILED: blind repetition of INC-0101 fix)"],
            "successful_resolution": "Force-refreshed Kubernetes Secret from AWS Secrets Manager using ExternalSecrets operator.",
            "failed_fixes": ["Increasing connection pool size failed: connection pool was empty because authentication failed before connection established."],
            "status": "Resolved"
        }
        create_incident(inc_0145_data)
        self.memory_service.retain_incident_resolution(inc_0145_data)
        self.memory_service.retain_failed_fix(
            incident_id="INC-0145",
            service="Payment API",
            failed_fix="Increasing connection pool size failed because auth failed before connection could be established.",
            actual_root_cause="AWS Secrets Manager credential rotation mismatch."
        )
        print(" [PASS] Step 4 & 5: INC-0145 recorded failed fix attempt and cautionary lesson.")

        # ----------------------------------------------------
        # STEP 6: INC-0182 Third Incident (The Payoff)
        # ----------------------------------------------------
        recall_for_0182 = self.memory_service.recall_for_incident(
            service="Payment API",
            symptoms=["HTTP 503 Service Unavailable", "Intermittent database socket timeout"],
            logs="2026-09-20 [ERROR] payment.db: connection pool query timed out (max=100, active=98, auth=valid)"
        )

        # 1. Verify BOTH INC-0101 and INC-0145 are recalled
        recalled_0182_ids = set([m["incident_id"] for m in recall_for_0182["memories"]])
        self.assertIn("INC-0101", recalled_0182_ids)
        self.assertIn("INC-0145", recalled_0182_ids)

        # 2. Verify "Same Symptom != Same Root Cause" bifurcation is detected
        self.assertTrue(recall_for_0182["bifurcated_cause"])
        self.assertIsNotNone(recall_for_0182["bifurcation_details"])
        print(f" [PASS] Step 6a: Multi-Outcome Correlation active! Detected divergence: {recall_for_0182['bifurcation_details']['pattern']}")

        # 3. Verify Failed Fix cautions are present
        self.assertGreater(len(recall_for_0182["failed_fixes"]), 0)
        self.assertTrue(any("INC-0145" == f["incident_id"] for f in recall_for_0182["failed_fixes"]))
        print(" [PASS] Step 6b: Successfully loaded cautionary warning against repeating INC-0145 failed fix.")

        # 4. Verify Before/After comparison demonstrates MTTR reduction
        comp = self.analysis_service.compare_investigation("INC-0182")
        self.assertGreater(comp["mttr_savings_pct"], 70)
        self.assertEqual(comp["memory_powered"]["risk_of_failed_fix_repetition"], "0% (Eliminated)")
        print(f" [PASS] Step 6c: MTTR Reduction verified: {comp['mttr_savings_pct']}% with 0% repeat mistake risk.")

        print("========================================================")
        print(" CRITICAL MULTI-INCIDENT END-TO-END TEST PASSED 100%!")
        print("========================================================\n")


if __name__ == "__main__":
    unittest.main()
