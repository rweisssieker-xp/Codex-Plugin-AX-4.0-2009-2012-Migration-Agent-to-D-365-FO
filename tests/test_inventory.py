import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ax_migration_inventory import discover


class InventoryTests(unittest.TestCase):
    def test_example_xpo_discovers_expected_objects_and_risks(self):
        records = discover(ROOT / "assets" / "example-ax-export.xpo")
        by_name = {record["name"]: record for record in records}
        self.assertEqual(
            set(by_name),
            {
                "CustLegacyStaging",
                "CustLegacySync",
                "CustLegacyReconciliation",
                "CustLegacyClerk",
            },
        )
        self.assertIn("direct_sql", by_name["CustLegacySync"]["signals"])
        self.assertEqual(by_name["CustLegacyClerk"]["type"], "SecurityRole")
