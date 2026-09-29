"""
Unit Tests for Incident Dataset, Service Catalog, and Post-Mortem Engine
"""

import unittest
from data.db import (
    get_all_services,
    get_all_incidents,
    get_incident_by_id,
    get_incident_events,
    get_dashboard_stats
)
from services.postmortem_service import get_postmortem_service
from services.learning_service import get_learning_service


class TestIncidentsCatalog(unittest.TestCase):

    def test_01_service_catalog_completeness(self):
        """Verifies all 8 enterprise microservices exist."""
        services = get_all_services()
        self.assertEqual(len(services), 8)
        service_names = [s["name"] for s in services]
        self.assertIn("Payment API", service_names)
        self.assertIn("Authentication Service", service_names)
        self.assertIn("Order Service", service_names)
        self.assertIn("Database Service", service_names)
        print(f" [PASS] test_01_service_catalog_completeness (Found {len(services)} services)")

    def test_02_incident_catalog_enterprise_scale(self):
        """Verifies dataset contains at least 30 realistic production incidents."""
        incidents = get_all_incidents()
        self.assertGreaterEqual(len(incidents), 30)
        print(f" [PASS] test_02_incident_catalog_enterprise_scale (Total incidents: {len(incidents)})")

    def test_03_critical_patterns_present(self):
        """Verifies core architectural failure patterns are present."""
        inc_0101 = get_incident_by_id("INC-0101")
        self.assertIsNotNone(inc_0101)
        self.assertIn("connection pool", inc_0101["root_cause"].lower())

        inc_0145 = get_incident_by_id("INC-0145")
        self.assertIsNotNone(inc_0145)
        self.assertIn("credential", inc_0145["root_cause"].lower())
        self.assertGreater(len(inc_0145["failed_fixes"]), 0)

        inc_0182 = get_incident_by_id("INC-0182")
        self.assertIsNotNone(inc_0182)

        print(" [PASS] test_03_critical_patterns_present (INC-0101, INC-0145, INC-0182 verified)")

    def test_04_postmortem_generation_and_retention(self):
        """Verifies post-mortem engine creates executive report and retains lessons."""
        pm_service = get_postmortem_service()
        pm = pm_service.generate_postmortem("INC-0101")
        self.assertEqual(pm["incident_id"], "INC-0101")
        self.assertIn("prevention_items", pm)
        self.assertGreater(len(pm["prevention_items"]), 0)
        self.assertTrue(pm["retained_in_hindsight"])
        print(" [PASS] test_04_postmortem_generation_and_retention")

    def test_05_learning_service_metrics(self):
        """Verifies learning service extracts fleet-wide recurring failure archetypes."""
        lrn_service = get_learning_service()
        overview = lrn_service.get_learning_overview()
        self.assertIn("patterns", overview)
        self.assertIn("timeline", overview)
        self.assertGreaterEqual(len(overview["patterns"]), 5)
        print(f" [PASS] test_05_learning_service_metrics ({len(overview['patterns'])} failure archetypes codified)")


if __name__ == "__main__":
    unittest.main()
