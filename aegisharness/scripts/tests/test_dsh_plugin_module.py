"""Run the dsh bundle smoke test from the unified test entry point.

`run_tests.py` only discovers `test_*.py`, so this wrapper keeps the Node smoke
test reachable from the same command. It is skipped when Node is not available,
matching how the dsh installer treats an absent runtime dependency.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
TEST_FILE = PLUGIN_ROOT / "tests" / "dsh-plugin.test.mjs"
MANIFEST = PLUGIN_ROOT / "package.json"


class DshPluginModuleTest(unittest.TestCase):
    def test_bundle_manifest_declares_the_shipped_patch(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "@elierncn/aegisharness-dsh")
        self.assertEqual(payload["dsh"]["bundle"]["patch"], "./cordis.patch.yml")
        self.assertEqual(payload["exports"]["."], "./lib/index.js")
        self.assertTrue((PLUGIN_ROOT / "cordis.patch.yml").is_file())
        self.assertIn("cordis.patch.yml", payload["files"])
        self.assertIn("tests/dsh-plugin.test.mjs", payload["files"])

    def test_plugin_registers_every_public_command(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is not available")
        self.assertTrue(TEST_FILE.is_file(), f"smoke test is missing: {TEST_FILE}")
        result = subprocess.run(
            [node, str(TEST_FILE)],
            cwd=str(PLUGIN_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("9 skills", result.stdout)


if __name__ == "__main__":
    unittest.main()
