import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceLayoutTests(unittest.TestCase):
    def test_legacy_entrypoint_is_thin(self):
        path = ROOT / "OutlastTrialsAudioEditor.py"
        self.assertLess(len(path.read_text(encoding="utf-8").splitlines()), 30)

    def test_all_python_files_compile(self):
        for path in ROOT.rglob("*.py"):
            if ".git" in path.parts:
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_upstream_classes_are_still_defined(self):
        manifest = json.loads((ROOT / "tests/fixtures/upstream_api.json").read_text(encoding="utf-8"))
        found = {}
        functions = set()
        for path in (ROOT / "outlast_trials_audio_editor").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    found[node.name] = {
                        child.name for child in node.body if isinstance(child, ast.FunctionDef)
                    }
                elif isinstance(node, ast.FunctionDef):
                    functions.add(node.name)
        # WemSubtitleApp methods are intentionally distributed across mixins.
        mixin_methods = set()
        for name, methods in found.items():
            if name.endswith("Mixin"):
                mixin_methods.update(methods)
        for function_name in manifest["functions"]:
            self.assertIn(function_name, functions, f"Missing function: {function_name}")
        for class_name, expected_methods in manifest["classes"].items():
            if class_name == "WemSubtitleApp":
                actual = found.get(class_name, set()) | mixin_methods
            else:
                actual = found.get(class_name, set())
            self.assertIn(class_name, found, f"Missing class: {class_name}")
            self.assertTrue(set(expected_methods).issubset(actual), f"Missing methods on {class_name}: {set(expected_methods)-actual}")


if __name__ == "__main__":
    unittest.main()
