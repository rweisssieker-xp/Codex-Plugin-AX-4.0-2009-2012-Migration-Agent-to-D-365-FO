import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class QualityControlTests(unittest.TestCase):
    def test_creates_reproducible_quality_and_evidence_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "ax_migration_compiler.py"),
                    str(ROOT / "assets" / "example-ax-export.xpo"),
                    "--out",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "ax_migration_quality.py"),
                    "--decisions",
                    str(output / "decision-compiler.json"),
                    "--out",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            quality = output / "quality-control"
            self.assertTrue((quality / "evidence-ledger.json").exists())
            self.assertTrue((quality / "executive-dashboard.json").exists())
            self.assertTrue((quality / "benchmark-results.json").exists())
