"""Portable addon regression smoke checks; synthetic local data only."""
import unittest
import importlib.util
from pathlib import Path

class AddonTests(unittest.TestCase):
    def test_local_contracts(self):
        path=Path(__file__).resolve().parents[1]/'apps/windows/desktop/addon_checks.py'
        spec=importlib.util.spec_from_file_location('addon_smoke',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=module.run_checks()
        self.assertEqual(result['failed'],0,result)
        self.assertEqual(result['passed'],7)
