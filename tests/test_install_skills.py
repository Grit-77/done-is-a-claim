"""Project installs must preserve existing material and carry verifiable copies."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallSkillsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.source = self.base / "source"
        (self.source / "tools").mkdir(parents=True)
        tool = ROOT / "tools" / "install_skills.py"
        if tool.exists():
            shutil.copyfile(tool, self.source / "tools" / tool.name)
        for name in ("first", "second"):
            folder = self.source / "skills" / name
            (folder / "references").mkdir(parents=True)
            (folder / "SKILL.md").write_bytes(f"---\nname: {name}\ndescription: fixture\n---\n".encode())
            (folder / "references" / "guide.txt").write_bytes(b"fixture\x00\xff\n")
        shutil.copyfile(ROOT / "LICENSE", self.source / "LICENSE")
        self.project = self.base / "project"
        self.project.mkdir()

    def run_install(self, *arguments):
        return subprocess.run(
            [sys.executable, str(self.source / "tools" / "install_skills.py"), *map(str, arguments)],
            cwd=self.base, capture_output=True, text=True, check=False,
        )

    def install(self, *arguments):
        return self.run_install("--project", self.project, "--agent", "codex", "--skill", "first", *arguments)

    def snapshot(self, root=None):
        root = root or self.project
        return {str(path.relative_to(root)): ("dir" if path.is_dir() else path.read_bytes())
                for path in root.rglob("*")}

    def make_link(self, link, target, directory=True):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symlinks unavailable: {error}")

    def test_explicit_install_copies_only_selection_for_each_agent(self):
        for agent, folder in (("codex", ".agents"), ("claude-code", ".claude")):
            with self.subTest(agent=agent):
                result = self.run_install("--project", self.project, "--agent", agent, "--skill", "first")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                destination = self.project / folder / "skills" / "first"
                self.assertEqual((destination / "SKILL.md").read_bytes(), (self.source / "skills/first/SKILL.md").read_bytes())
                self.assertEqual((destination / "references/guide.txt").read_bytes(), b"fixture\x00\xff\n")
                self.assertFalse((destination.parent / "second").exists())

    def test_multiple_agents_and_skills_install_all_explicit_selections(self):
        result = self.install("--agent", "claude-code", "--skill", "second")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for folder in (".agents", ".claude"):
            for name in ("first", "second"):
                self.assertTrue((self.project / folder / "skills" / name / "SKILL.md").is_file())

    def test_dry_run_has_zero_writes_and_prints_resolved_destinations(self):
        before = self.snapshot(self.base)
        result = self.install("--dry-run", "--agent", "claude-code")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.snapshot(self.base), before)
        for folder in (".agents", ".claude"):
            self.assertIn(str((self.project / folder / "skills/first").resolve()), result.stdout)

    def test_later_collision_refuses_every_selection_before_any_write(self):
        occupied = self.project / ".claude/skills/second"
        occupied.mkdir(parents=True)
        (occupied / "mine.txt").write_bytes(b"user material")
        before = self.snapshot()
        result = self.install("--agent", "claude-code", "--skill", "second")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exists", result.stderr.lower())
        self.assertEqual(self.snapshot(), before)

    def test_later_missing_selection_refuses_every_selection_before_any_write(self):
        result = self.install("--skill", "missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), {})

    def test_preserves_unrelated_instructions_settings_and_skills(self):
        files = {"AGENTS.md": b"mine\r\n", "CLAUDE.md": b"mine too\xff", ".claude/settings.json": b'{"keep": true}',
                 ".agents/skills/other/SKILL.md": b"existing skill"}
        for name, content in files.items():
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        result = self.install("--agent", "claude-code")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name, content in files.items():
            self.assertEqual((self.project / name).read_bytes(), content)

    def test_license_and_provenance_hash_every_copied_file_without_local_paths(self):
        git = self.source / ".git"
        (git / "refs/heads").mkdir(parents=True)
        revision = "1234567890abcdef1234567890abcdef12345678"
        (git / "HEAD").write_text("ref: refs/heads/test\n", encoding="ascii")
        (git / "refs/heads/test").write_text(revision + "\n", encoding="ascii")
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        destination = self.project / ".agents/skills/first"
        self.assertEqual((destination / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())
        metadata_text = (destination / "PROVENANCE.json").read_text(encoding="utf-8")
        metadata = json.loads(metadata_text)
        self.assertEqual(metadata["source_repository"], "https://github.com/Grit-77/done-is-a-claim")
        self.assertEqual(metadata["source_revision"], revision)
        self.assertEqual(metadata["skill"], "first")
        expected = {name: hashlib.sha256((destination / name).read_bytes()).hexdigest()
                    for name in ("SKILL.md", "references/guide.txt", "LICENSE")}
        self.assertEqual(metadata["files_sha256"], expected)
        self.assertNotIn(str(self.source), metadata_text)
        self.assertNotIn(str(self.project), metadata_text)

    def test_archive_source_reports_unknown_revision(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        metadata = json.loads((self.project / ".agents/skills/first/PROVENANCE.json").read_text())
        self.assertEqual(metadata["source_revision"], "unknown")

    def test_installs_with_python_310_path_api_without_is_junction(self):
        # CI supports 3.10; Path.is_junction was added in 3.12. Exercise the
        # actual installer with that newer API absent, even on a newer runner.
        code = ("from pathlib import Path\nimport runpy, sys\n"
                "if hasattr(Path, 'is_junction'): delattr(Path, 'is_junction')\n"
                "sys.argv = sys.argv[1:]\nrunpy.run_path(sys.argv[0], run_name='__main__')\n")
        result = subprocess.run(
            [sys.executable, "-c", code, str(self.source / "tools/install_skills.py"),
             "--project", str(self.project), "--agent", "codex", "--skill", "first"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.project / ".agents/skills/first/SKILL.md").is_file())

    def test_requires_existing_directory_and_explicit_agent_and_skill(self):
        plain_file = self.base / "file"
        plain_file.write_bytes(b"keep")
        for arguments in (("--project", self.base / "missing", "--agent", "codex", "--skill", "first"),
                          ("--project", plain_file, "--agent", "codex", "--skill", "first"),
                          ("--agent", "codex", "--skill", "first"),
                          ("--project", self.project, "--skill", "first"),
                          ("--project", self.project, "--agent", "codex")):
            with self.subTest(arguments=arguments):
                result = self.run_install(*arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.snapshot(), {})
        self.assertFalse((self.base / "missing").exists())

    def test_invalid_names_and_unknown_agent_cannot_escape_target(self):
        for name in ("../first", "..", "FIRST", "first/second", "first\\second", "C:first", "", "first."):
            with self.subTest(name=name):
                result = self.run_install("--project", self.project, "--agent", "codex", "--skill", name)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.snapshot(), {})
        result = self.install("--agent", "global")
        self.assertNotEqual(result.returncode, 0)

    def test_dangling_destination_is_a_collision(self):
        parent = self.project / ".agents/skills"
        parent.mkdir(parents=True)
        link = parent / "first"
        self.make_link(link, self.base / "missing")
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(link.is_symlink())
        self.assertFalse((self.base / "missing").exists())

    def test_symlinked_destination_ancestor_cannot_write_outside_project(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.make_link(self.project / ".agents", outside)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(outside), {})

    @unittest.skipUnless(sys.platform == "win32", "Windows junction fixture")
    def test_windows_junction_ancestor_is_rejected_without_symlink_privilege(self):
        import _winapi
        outside = self.base / "outside"
        outside.mkdir()
        _winapi.CreateJunction(str(outside), str(self.project / ".agents"))
        result = self.install()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("junction", result.stderr.lower())
        self.assertEqual(self.snapshot(outside), {})

    @unittest.skipUnless(sys.platform == "win32", "Windows junction fixture")
    def test_project_dotdot_cannot_hide_a_junction_ancestor(self):
        import _winapi
        outside = self.base / "outside"
        outside.mkdir()
        (self.project / "child").mkdir()
        _winapi.CreateJunction(str(outside), str(self.project / "alias"))
        target = self.project / "alias" / ".." / "child"
        result = self.run_install("--project", target, "--agent", "codex", "--skill", "first")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.project / "child/.agents").exists())

    def test_symlinked_project_or_ancestor_is_rejected(self):
        alias = self.base / "alias"
        self.make_link(alias, self.project)
        for target in (alias, alias / "child"):
            (self.project / "child").mkdir(exist_ok=True)
            result = self.run_install("--project", target, "--agent", "codex", "--skill", "first")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.project / ".agents").exists())
            self.assertFalse((self.project / "child/.agents").exists())

    def test_symlinked_source_file_is_rejected_before_writes(self):
        self.make_link(self.source / "skills/second/linked", self.source / "LICENSE", directory=False)
        result = self.install("--skill", "second")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), {})


if __name__ == "__main__":
    unittest.main()
