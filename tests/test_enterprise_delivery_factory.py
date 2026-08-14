import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EnterpriseDeliveryFactoryTests(unittest.TestCase):
    def test_generates_all_sixteen_review_gated_capabilities(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "ax_enterprise_delivery_factory.py"),
                    str(ROOT / "assets" / "example-ax-export.xpo"),
                    "--out",
                    temporary,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            suite = Path(temporary) / "enterprise-delivery-suite"
            self.assertIn('"capabilities": 16', result.stdout)
            self.assertTrue((suite / "enterprise-delivery-catalog.json").exists())
            self.assertEqual(len(list(suite.glob("*.md"))), 16)
