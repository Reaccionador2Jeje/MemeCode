import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from runtime.agent import AgentError, build_system_prompt, dispatch_tool, load_memingo_core, run_agent

class AgentToolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()
    def tearDown(self):
        self.temp.cleanup()
    def test_read_file(self):
        (self.root/"hello.txt").write_text("hola",encoding="utf-8")
        self.assertEqual(dispatch_tool(self.root,"read_file",{"path":"hello.txt"}),"hola")
    def test_secret_read_is_blocked(self):
        (self.root/".env").write_text("TOKEN=secret",encoding="utf-8")
        self.assertIn("blocked",dispatch_tool(self.root,"read_file",{"path":".env"}))
    def test_write_requires_approval(self):
        with patch("builtins.input",return_value="n"):
            result=dispatch_tool(self.root,"write_file",{"path":"new.txt","content":"hello"})
        self.assertIn("declined",result)
        self.assertFalse((self.root/"new.txt").exists())
    def test_write_after_approval(self):
        with patch("builtins.input",return_value="y"):
            result=dispatch_tool(self.root,"write_file",{"path":"new.txt","content":"hello"})
        self.assertIn("Saved",result)
        self.assertEqual((self.root/"new.txt").read_text(encoding="utf-8"),"hello")
    def test_final_response(self):
        def fake(messages,**kwargs):
            return {"role":"assistant","content":"Project inspected."}
        self.assertEqual(run_agent("inspect",self.root,api_key="test",model="test",request_fn=fake),"Project inspected.")
    def test_tool_call_round_trip(self):
        count={"n":0}
        def fake(messages,**kwargs):
            count["n"]+=1
            if count["n"]==1:
                return {"role":"assistant","content":None,"tool_calls":[{"id":"c1","type":"function","function":{"name":"list_files","arguments":"{}"}}]}
            self.assertEqual(messages[-1]["role"],"tool")
            return {"role":"assistant","content":"Done."}
        self.assertEqual(run_agent("list files",self.root,api_key="test",model="test",request_fn=fake),"Done.")
    def test_step_limit(self):
        def fake(messages,**kwargs):
            return {"role":"assistant","content":None,"tool_calls":[{"id":"loop","type":"function","function":{"name":"list_files","arguments":"{}"}}]}
        with self.assertRaises(AgentError):
            run_agent("loop",self.root,api_key="test",model="test",max_steps=1,request_fn=fake)


    def test_builds_system_prompt_from_memingo_policy(self):
        config = {"name": "MemeCode", "role": "coding agent",
                  "policy": ["Inspect first.", "Ask before writes."],
                  "workflow": ["inspect", "plan", "test"]}
        prompt = build_system_prompt(config)
        self.assertIn("Inspect first.", prompt)
        self.assertIn("inspect -> plan -> test", prompt)

    def test_loads_policy_from_memingo_runtime(self):
        import json
        from unittest.mock import Mock, patch
        (self.root / "src").mkdir()
        (self.root / "src" / "agent_core.mgo").write_text('spill "{}"', encoding="utf-8")
        config = {"name": "MemeCode", "policy": ["Inspect first."]}
        completed = Mock(returncode=0, stdout=json.dumps(config), stderr="")
        with patch("runtime.agent.shutil.which", return_value="/usr/bin/memingo"), \
             patch("runtime.agent.subprocess.run", return_value=completed) as run:
            loaded = load_memingo_core(self.root)
        self.assertEqual(loaded["name"], "MemeCode")
        self.assertEqual(run.call_args.args[0][1:3], ["run", str(self.root / "src" / "agent_core.mgo")])

    def test_rejects_missing_memingo_core(self):
        with self.assertRaises(AgentError):
            load_memingo_core(self.root)

if __name__=="__main__":
    unittest.main()
