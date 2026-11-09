"""Pruebas del agente local Neural."""
import tempfile
import unittest
from pathlib import Path

from neural.agent import (
    NeuralAgentError, create_project_file, list_project_files,
    read_project_file, run_project_tests, workspace_path,
)


class NeuralAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_lists_and_reads_workspace_files(self):
        (self.root / "hello.py").write_text("print('hola')", encoding="utf-8")
        self.assertIn("hello.py", list_project_files(self.root))
        self.assertEqual(read_project_file(self.root, "hello.py"), "print('hola')")

    def test_blocks_path_traversal(self):
        with self.assertRaises(NeuralAgentError):
            workspace_path(self.root, "../outside.txt")

    def test_blocks_secret_files(self):
        with self.assertRaises(NeuralAgentError):
            read_project_file(self.root, ".env")

    def test_create_requires_approval_and_never_overwrites(self):
        with self.assertRaises(NeuralAgentError):
            create_project_file(self.root, "new.txt", "hola")
        create_project_file(self.root, "new.txt", "hola", approve=True)
        with self.assertRaises(NeuralAgentError):
            create_project_file(self.root, "new.txt", "reemplazo", approve=True)
        self.assertEqual((self.root / "new.txt").read_text(encoding="utf-8"), "hola")

    def test_tests_require_approval(self):
        with self.assertRaises(NeuralAgentError):
            run_project_tests(self.root)


if __name__ == "__main__":
    unittest.main()
