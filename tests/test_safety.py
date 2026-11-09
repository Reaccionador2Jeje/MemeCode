import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "runtime" / "host_bridge.py"
SPEC = importlib.util.spec_from_file_location("host_bridge", MODULE_PATH)
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)

class WorkspaceSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
    def tearDown(self):
        self.temp.cleanup()
    def test_rejects_parent_traversal(self):
        with self.assertRaises(bridge.WorkspaceError):
            bridge.safe_path(self.root, "../outside.txt")
    def test_rejects_absolute_path(self):
        with self.assertRaises(bridge.WorkspaceError):
            bridge.safe_path(self.root, str(self.root / "file.txt"))
    def test_read_write_inside_workspace(self):
        bridge.write_file(self.root, "src/hello.txt", "hola")
        self.assertEqual(bridge.read_file(self.root, "src/hello.txt"), "hola")
    def test_blocks_env_file(self):
        (self.root / ".env").write_text("TOKEN=secret", encoding="utf-8")
        with self.assertRaises(bridge.WorkspaceError):
            bridge.read_file(self.root, ".env")
    def test_blocks_system_commands(self):
        with self.assertRaises(bridge.WorkspaceError):
            bridge.run_command(self.root, ["sudo", "echo", "no"], 5)

    def test_blocks_shell_wrappers(self):
        with self.assertRaises(bridge.WorkspaceError):
            bridge.run_command(self.root, ["bash", "-c", "echo unsafe"], 5)

if __name__ == "__main__":
    unittest.main()
