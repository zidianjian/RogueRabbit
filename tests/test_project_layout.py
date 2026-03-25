import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class ProjectLayoutTestCase(unittest.TestCase):
    def test_expected_paths_exist(self) -> None:
        expected_paths = [
            ROOT / "README.md",
            ROOT / "AGENTS.md",
            ROOT / "pyproject.toml",
            ROOT / "docs" / "index.md",
            ROOT / "docs" / "01-overview" / "vision.md",
            ROOT / "docs" / "01-overview" / "roadmap.md",
            ROOT / "docs" / "02-architecture" / "principles.md",
            ROOT / "docs" / "02-architecture" / "layers.md",
            ROOT / "docs" / "02-architecture" / "module-map.md",
            ROOT / "docs" / "03-harness" / "agent-rules.md",
            ROOT / "docs" / "03-harness" / "verification-policy.md",
            ROOT / "docs" / "04-phases" / "phase-1-learning.md",
            ROOT / "docs" / "04-phases" / "phase-2-usable.md",
            ROOT / "docs" / "04-phases" / "phase-3-production.md",
            ROOT / "docs" / "05-capabilities" / "index.md",
            ROOT / "docs" / "06-specs" / "README.md",
            ROOT / "docs" / "07-guides" / "local-dev.md",
            ROOT / "docs" / "07-guides" / "add-capability.md",
            ROOT / "docs" / "templates" / "capability-spec.md",
            ROOT / "docs" / "templates" / "adr.md",
            ROOT / "docs" / "templates" / "iteration-checklist.md",
            ROOT / "src" / "rogue_rabbit" / "__init__.py",
            ROOT / "src" / "rogue_rabbit" / "apps" / "cli.py",
            ROOT / "src" / "rogue_rabbit" / "contracts" / "__init__.py",
            ROOT / "src" / "rogue_rabbit" / "config" / "__init__.py",
            ROOT / "src" / "rogue_rabbit" / "core" / "__init__.py",
            ROOT / "src" / "rogue_rabbit" / "adapters" / "__init__.py",
            ROOT / "src" / "rogue_rabbit" / "runtime" / "__init__.py",
            ROOT / "src" / "rogue_rabbit" / "experiments" / "__init__.py",
        ]
        for path in expected_paths:
            self.assertTrue(path.exists(), str(path))

    def test_package_imports(self) -> None:
        self.assertTrue(SRC.exists(), str(SRC))
        command = [
            sys.executable,
            "-c",
            "import pathlib, sys; sys.path.insert(0, str(pathlib.Path(r'"
            + str(SRC)
            + "'))); import rogue_rabbit; print(rogue_rabbit.__version__)",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "0.1.0")

    def test_cli_runs(self) -> None:
        command = [sys.executable, "-m", "rogue_rabbit.apps.cli"]
        env = dict()
        env.update(PATH=str(Path(sys.executable).parent))
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env={**env, **dict(PYTHONPATH=str(SRC))},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("RogueRabbit", completed.stdout)
        self.assertIn("phase-1", completed.stdout)


if __name__ == "__main__":
    unittest.main()
