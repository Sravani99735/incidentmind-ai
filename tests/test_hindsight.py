"""
Unit and Integration Tests for Hindsight Memory Layer
Verifies retain, recall, reflect, and transparent fallback behavior.
"""

import unittest
from hindsight.client import get_hindsight_client
from hindsight.memory_service import get_memory_service


class TestHindsightLayer(unittest.TestCase):

    def setUp(self):
        self.client = get_hindsight_client()
        self.service = get_memory_service()

    def test_01_client_initialization_and_status(self):
        """Verifies Hindsight wrapper initializes and returns valid diagnostics."""
        status = self.client.get_status_info()
        self.assertIn("is_live", status)
        self.assertIn("base_url", status)
        self.assertIn("bank_id", status)
        self.assertEqual(status["bank_id"], "incidentmind_org_knowledge")
        print(" [PASS] test_01_client_initialization_and_status")

    def test_02_retain_operation(self):
        """Verifies retain saves facts and resolutions cleanly."""
        res = self.client.retain(
            content="INC-TEST: Test memory fact regarding Postgres connection pooling.",
            context="Unit Test Context",
            metadata={"service": "Payment API", "test": "true"},
            tags=["unit_test", "database"],
            service="Payment API",
            incident_id="INC-TEST"
        )
        self.assertTrue(res.get("success"))
        self.assertIn("id", res)
        print(" [PASS] test_02_retain_operation")

    def test_03_recall_operation(self):
        """Verifies recall retrieves relevant memories."""
        resp = self.client.recall(
            query="database connection pool exhaustion PgBouncer",
            service="Payment API",
            top_k=3
        )
        self.assertTrue(hasattr(resp, "results"))
        self.assertGreater(len(resp.results), 0)
        first_mem = resp.results[0]
        self.assertTrue(hasattr(first_mem, "text"))
        self.assertTrue(len(first_mem.text) > 0)
        print(f" [PASS] test_03_recall_operation (Retrieved {len(resp.results)} memories)")

    def test_04_memory_service_multi_outcome_recall(self):
        """Verifies memory service adds Why-Useful attribution and identifies cautions."""
        recall_data = self.service.recall_for_incident(
            service="Payment API",
            symptoms=["HTTP 503", "database connection timeout"],
            top_k=5
        )
        self.assertIn("memories", recall_data)
        self.assertIn("bifurcated_cause", recall_data)
        self.assertGreater(len(recall_data["memories"]), 0)

        # Check why-useful attribution
        for m in recall_data["memories"]:
            self.assertIn("why_useful", m)
            self.assertTrue(len(m["why_useful"]) > 0)

        print(f" [PASS] test_04_memory_service_multi_outcome_recall (Why-Useful verified)")

    def test_05_reflect_synthesis(self):
        """Verifies reflection produces actionable organizational synthesis."""
        reflection = self.service.reflect_on_reliability(query="Synthesize recurring database pool failures")
        self.assertIn("synthesis", reflection)
        self.assertTrue(len(reflection["synthesis"]) > 0)
        print(" [PASS] test_05_reflect_synthesis")


if __name__ == "__main__":
    unittest.main()
