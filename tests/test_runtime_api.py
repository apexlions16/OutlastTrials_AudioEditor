import importlib
import inspect
import json
import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]


class RuntimeApiTests(unittest.TestCase):
    def test_all_package_modules_import(self):
        modules = []
        for path in (ROOT / "outlast_trials_audio_editor").rglob("*.py"):
            module = path.relative_to(ROOT).with_suffix("").as_posix().replace("/", ".")
            if module.endswith(".__init__"):
                module = module[: -len(".__init__")]
            modules.append(module)

        for module in sorted(set(modules)):
            with self.subTest(module=module):
                importlib.import_module(module)

    def test_public_classes_and_effective_methods_are_available(self):
        legacy = importlib.import_module("OutlastTrialsAudioEditor")
        manifest = json.loads(
            (ROOT / "tests/fixtures/upstream_api.json").read_text(encoding="utf-8")
        )

        for class_name, method_names in manifest["classes"].items():
            with self.subTest(class_name=class_name):
                cls = getattr(legacy, class_name)
                self.assertTrue(inspect.isclass(cls))
                for method_name in method_names:
                    self.assertIsNotNone(
                        inspect.getattr_static(cls, method_name, None),
                        f"Missing runtime member: {class_name}.{method_name}",
                    )


if __name__ == "__main__":
    unittest.main()
