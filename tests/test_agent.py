"""
Unit and Integration Tests for SRE Incident Agent & NLP Engine
Verifies conversational dialogue, incident investigation, tool calling, and human approval gateway.
"""

import unittest
from agent.nlp_processor import get_nlp_processor, NLPProcessor
from agent.incident_agent import get_incident_agent


class TestIncidentAgent(unittest.TestCase):

    def setUp(self):
        self.nlp = get_nlp_processor()
        self.agent = get_incident_agent()

    def test_01_nlp_intent_classification(self):
        """Verifies NLP classifies both normal conversation and technical triage correctly."""
        res_conv = self.nlp.process_message("hello, how are you doing today?")
        self.assertEqual(res_conv["intent"], NLPProcessor.INTENT_GENERAL_CONVERSATION)
        self.assertTrue(res_conv["is_conversational"])

        res_triage = self.nlp.process_message("Payment API is throwing 503 errors during checkout")
        self.assertEqual(res_triage["intent"], NLPProcessor.INTENT_INCIDENT_INVESTIGATION)
        self.assertEqual(res_triage["entities"]["service"], "Payment API")
        self.assertIn("503", res_triage["entities"]["error_codes"])

        res_tool = self.nlp.process_message("check logs for payment service")
        self.assertEqual(res_tool["intent"], NLPProcessor.INTENT_TOOL_EXECUTION)

        print(" [PASS] test_01_nlp_intent_classification")

    def test_02_conversational_chat_reply(self):
        """Verifies agent handles casual on-call chat gracefully."""
        reply = self.agent.handle_chat_message("rough on-call shift, lots of alerts")
        self.assertEqual(reply["sender"], "agent")
        self.assertIn("content", reply)
        self.assertTrue(len(reply["content"]) > 50)
        self.assertFalse(reply["is_memory_powered"])
        print(" [PASS] test_02_conversational_chat_reply")

    def test_03_incident_investigation_workflow(self):
        """Verifies investigation workflow recalls memories, runs tools, and sets approval gateway."""
        reply = self.agent.handle_chat_message("Investigate 503 service unavailable on Payment API")
        self.assertEqual(reply["sender"], "agent")
        self.assertEqual(reply["intent"], "incident_investigation")
        self.assertGreater(len(reply["memories_used"]), 0)
        self.assertGreater(len(reply["tool_calls"]), 0)
        self.assertIsNotNone(reply["approval_needed"])
        self.assertEqual(reply["approval_needed"]["action_type"], "scale_connection_pool")
        print(" [PASS] test_03_incident_investigation_workflow")

    def test_04_human_in_the_loop_approval_execution(self):
        """Verifies authorized remediation executes safely and logs to audit trail."""
        res = self.agent.execute_approved_remediation(
            action_id="act_test_01",
            action_type="scale_connection_pool",
            target_service="Payment API",
            parameters={"service_name": "Payment API", "new_max_connections": 150},
            approved_by="test_sre"
        )
        self.assertTrue(res["success"])
        self.assertIn("audit_id", res)
        self.assertEqual(res["post_action_telemetry"]["health_status"], "Healthy")
        print(" [PASS] test_04_human_in_the_loop_approval_execution")


if __name__ == "__main__":
    unittest.main()
