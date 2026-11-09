"""Pruebas del planificador de MemeCode Neural."""
import json
import tempfile
import unittest
from pathlib import Path

from neural.planner import PlanError, apply_plan, parse_plan, preview_plan


class NeuralPlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make_plan(self, operations):
        return {"version": 1, "summary": "Prueba", "operations": operations}

    def test_parse_valid_plan(self):
        raw = json.dumps(self.make_plan([{
            "action": "create_file", "path": "src/main.py", "content": "print('ok')"
        }]))
        self.assertEqual(len(parse_plan(raw)["operations"]), 1)

    def test_rejects_invalid_json_and_unknown_actions(self):
        with self.assertRaises(PlanError):
            parse_plan("esto no es json")
        with self.assertRaises(PlanError):
            parse_plan(json.dumps(self.make_plan([{
                "action": "run_shell", "path": "x", "content": "echo hi"
            }])))

    def test_rejects_path_traversal_and_secret_files(self):
        plan = self.make_plan([{
            "action": "create_file", "path": "../outside", "content": "x"
        }])
        with self.assertRaises(PlanError):
            preview_plan(self.root, plan)
        plan["operations"][0]["path"] = ".env"
        with self.assertRaises(PlanError):
            preview_plan(self.root, plan)

    def test_requires_approval(self):
        plan = self.make_plan([{
            "action": "create_file", "path": "new.txt", "content": "hola"
        }])
        with self.assertRaises(PlanError):
            apply_plan(self.root, plan)
        self.assertFalse((self.root / "new.txt").exists())

    def test_creates_file_after_approval(self):
        plan = self.make_plan([{
            "action": "create_file", "path": "src/new.py", "content": "print('hola')"
        }])
        apply_plan(self.root, plan, approve=True)
        self.assertEqual((self.root / "src/new.py").read_text(), "print('hola')")

    def test_replace_requires_existing_file_and_preserves_backup(self):
        target = self.root / "old.txt"
        target.write_text("antes")
        plan = self.make_plan([{
            "action": "replace_file", "path": "old.txt", "content": "después"
        }])
        apply_plan(self.root, plan, approve=True)
        self.assertEqual(target.read_text(), "después")

    def test_rejects_duplicate_paths_and_too_many_operations(self):
        operation = {"action": "create_file", "path": "a.txt", "content": "a"}
        with self.assertRaises(PlanError):
            parse_plan(json.dumps(self.make_plan([operation, operation])))
        with self.assertRaises(PlanError):
            parse_plan(json.dumps(self.make_plan([operation] * 9)))


if __name__ == "__main__":
    unittest.main()
