import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "assets" / "example-ax-export.xpo"


class GeneratorSmokeTests(unittest.TestCase):
    def test_primary_delivery_generators_run(self):
        generators = [
            "ax_migration_innovation.py",
            "ax_migration_project_lead.py",
            "ax_data_migration_factory.py",
            "ax_commerce_integration_factory.py",
            "ax_commerce_scale_unit.py",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            for script in generators:
                with self.subTest(script=script):
                    subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "scripts" / script),
                            str(INPUT),
                            "--out",
                            temporary,
                        ],
                        cwd=ROOT,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
