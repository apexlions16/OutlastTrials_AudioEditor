import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from outlast_trials_audio_editor.services.audio import WavToWemConverter


class WwiseProjectCreationTests(unittest.TestCase):
    def make_converter(self, root: Path):
        wwise_root = root / "Wwise 2019"
        cli = wwise_root / "Authoring" / "x64" / "Release" / "bin" / "WwiseCLI.exe"
        cli.parent.mkdir(parents=True)
        cli.touch()

        converter = WavToWemConverter()
        converter.wwise_path = str(wwise_root)
        converter.project_path = str(root / "Project With Spaces")
        return converter, cli

    def test_project_command_uses_unquoted_argument_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            converter, cli = self.make_converter(root)
            project_dir = Path(converter.project_path)
            project_dir.mkdir()

            completed = SimpleNamespace(returncode=0, stderr="")
            with patch(
                "outlast_trials_audio_editor.services.audio.subprocess.run",
                return_value=completed,
            ) as run, patch.object(converter, "create_default_work_unit") as create_work_unit:
                result = converter.ensure_project_exists()

            expected_project = project_dir / f"{project_dir.name}.wproj"
            command = run.call_args.args[0]
            self.assertEqual(command[0], str(cli))
            self.assertEqual(command[1], str(expected_project))
            self.assertFalse(command[1].startswith('"'))
            self.assertFalse(command[1].endswith('"'))
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual(result, str(expected_project))
            create_work_unit.assert_called_once_with(str(project_dir))

    def test_nonempty_project_directory_is_never_deleted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            converter, _ = self.make_converter(root)
            project_dir = Path(converter.project_path)
            project_dir.mkdir()
            marker = project_dir / "keep-me.txt"
            marker.write_text("important", encoding="utf-8")

            with patch("outlast_trials_audio_editor.services.audio.subprocess.run") as run:
                with self.assertRaisesRegex(Exception, "is not empty"):
                    converter.ensure_project_exists()

            run.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"), "important")

    def test_existing_project_skips_cli_creation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            converter, _ = self.make_converter(root)
            project_dir = Path(converter.project_path)
            project_dir.mkdir()
            project_file = project_dir / f"{project_dir.name}.wproj"
            project_file.touch()

            with patch(
                "outlast_trials_audio_editor.services.audio.subprocess.run"
            ) as run, patch.object(converter, "create_default_work_unit") as create_work_unit:
                result = converter.ensure_project_exists()

            run.assert_not_called()
            self.assertEqual(result, str(project_file))
            create_work_unit.assert_called_once_with(str(project_dir))


if __name__ == "__main__":
    unittest.main()
