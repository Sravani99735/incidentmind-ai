"""
Unit Tests for Simulated SRE Diagnostic Tools & Safety Validator
"""

import unittest
from agent.tools import (
    get_service_status,
    get_recent_logs,
    get_deployment_history,
    get_database_metrics,
    check_health_endpoint
)
from agent.tool_validator import (
    validate_and_sanitize_tool_call,
    normalize_service_name,
    check_action_approval_requirement
)


class TestSRETools(unittest.TestCase):

    def test_01_service_status_tool(self):
        """Verifies get_service_status returns structured telemetry with demo labels."""
        data = get_service_status("Payment API")
        self.assertIn("health_status", data)
        self.assertIn("replicas", data)
        self.assertTrue(data.get("is_demo_environment"))
        self.assertIn("DEMO ENVIRONMENT", data.get("environment_label", ""))
        print(" [PASS] test_01_service_status_tool")

    def test_02_recent_logs_tool(self):
        """Verifies get_recent_logs returns formatted logs and error markers."""
        data = get_recent_logs("Payment API", lines=10)
        self.assertIn("logs", data)
        self.assertIn("has_error_signatures", data)
        self.assertTrue(data.get("is_demo_environment"))
        print(" [PASS] test_02_recent_logs_tool")

    def test_03_database_metrics_tool(self):
        """Verifies get_database_metrics returns connection pool saturation and queue depth."""
        data = get_database_metrics("Payment API")
        metrics = data["metrics"]
        self.assertIn("max_connections", metrics)
        self.assertIn("active_connections", metrics)
        self.assertIn("waiting_connection_queue", metrics)
        self.assertIn("saturation_pct", metrics)
        print(" [PASS] test_03_database_metrics_tool")

    def test_04_deployment_history_tool(self):
        """Verifies get_deployment_history tracks historical release commits."""
        data = get_deployment_history("Payment API")
        self.assertIn("recent_deployments", data)
        self.assertGreater(len(data["recent_deployments"]), 0)
        print(" [PASS] test_04_deployment_history_tool")

    def test_05_health_endpoint_tool(self):
        """Verifies check_health_endpoint probes subsystem dependencies."""
        data = check_health_endpoint("Payment API")
        self.assertIn("http_status", data)
        self.assertIn("subsystem_checks", data)
        print(" [PASS] test_05_health_endpoint_tool")

    def test_06_tool_validator_and_approval_gate(self):
        """Verifies read-only tools are allowed and state-altering actions require approval."""
        # Read-only tool
        valid, msg, clean_params = validate_and_sanitize_tool_call(
            "get_service_status", {"service": "payment"}
        )
        self.assertTrue(valid)
        self.assertEqual(clean_params["service_name"], "Payment API")

        # State-altering remediation action
        needs_approval, approval_meta = check_action_approval_requirement(
            "scale_connection_pool", {"service_name": "Payment API", "new_max_connections": 150}
        )
        self.assertTrue(needs_approval)
        self.assertEqual(approval_meta["risk_level"], "Medium")
        print(" [PASS] test_06_tool_validator_and_approval_gate")


if __name__ == "__main__":
    unittest.main()
