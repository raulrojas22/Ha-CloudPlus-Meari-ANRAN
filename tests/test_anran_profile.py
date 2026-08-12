"""Regression tests for the ANRAN application profile.

These tests deliberately inspect the source AST instead of importing the Home
Assistant component, so they can run without a full Home Assistant runtime.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def _assignment_value(path: Path, name: str) -> ast.AST:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return node.value
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return node.value
    raise AssertionError(f"{name} not found in {path}")


def _dict_entry(node: ast.AST, key: str) -> ast.AST:
    assert isinstance(node, ast.Dict)
    for item_key, value in zip(node.keys, node.values):
        if isinstance(item_key, ast.Constant) and item_key.value == key:
            return value
    raise AssertionError(f"{key} not found")


class AnranProfileTests(unittest.TestCase):
    def test_anran_uses_its_ios_wire_identity(self) -> None:
        profiles = _assignment_value(
            ROOT / "custom_components/cloudplus/api.py", "APP_PROFILE_CONFIG"
        )
        anran = _dict_entry(profiles, "anran")
        self.assertIsInstance(anran, ast.Call)
        self.assertEqual(
            [ast.literal_eval(arg) for arg in anran.args[:3]],
            ["84", "6.2.0", "2026071016"],
        )
        keyword_values = {
            keyword.arg: ast.literal_eval(keyword.value)
            for keyword in anran.keywords
        }
        self.assertEqual(keyword_values["phone_type"], "i")
        self.assertEqual(keyword_values["lng_type"], "es")

    def test_anran_is_exposed_in_home_assistant_profile_selector(self) -> None:
        names = _assignment_value(
            ROOT / "custom_components/cloudplus/const.py", "APP_PROFILE_NAMES"
        )
        self.assertEqual(ast.literal_eval(_dict_entry(names, "anran")), "ANRAN")


if __name__ == "__main__":
    unittest.main()
