"""Pruebas de las funciones ligeras: no requieren PyTorch."""
import tempfile
import unittest
from pathlib import Path

from neural.agent import NeuralAgentError, list_project_files, read_project_file, workspace_path
from neural.planner import PlanError, parse_plan, preview_plan, safe_path


class NeuralLightTests(unittest.TestCase):
    def test_plan_accepts_valid_create_operation(self):
        plan = parse_plan(
            '{"version":1,"summary":"Crear nota","operations":'
            '[{"action":"create_file","path":"nota.txt","content":"hola"}]}'
        )
        self.assertEqual(preview_plan(Path.cwd(), plan)[0], "create_file: nota.txt (nuevo)")

    def test_plan_rejects_path_traversal(self):
        with self.assertRaises(PlanError):
            safe_path(Path.cwd(), "../fuera.txt")

    def test_plan_rejects_secret_files(self):
        with self.assertRaises(PlanError):
            safe_path(Path.cwd(), ".env")

    def test_workspace_rejects_absolute_path(self):
        with self.assertRaises(NeuralAgentError):
            workspace_path(Path.cwd(), "/etc/passwd")

    def test_workspace_rejects_secret_files(self):
        with self.assertRaises(NeuralAgentError):
            workspace_path(Path.cwd(), "keys/private.pem")

    def test_list_and_read_project_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "hello.txt").write_text("hola", encoding="utf-8")
            self.assertEqual(list_project_files(root), ["hello.txt"])
            self.assertEqual(read_project_file(root, "hello.txt"), "hola")


if __name__ == "__main__":
    unittest.main()
