"""Project installs must preserve existing material and carry verifiable copies."""

import hashlib
import importlib.util
import io
import json
from contextlib import redirect_stderr
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


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
        (self.source / "profiles.json").write_text(json.dumps({"small": ["first"], "both": ["first", "second"]}))
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

    def test_source_empty_directory_refuses_initial_install_before_writes(self):
        (self.source / "skills/first/empty").mkdir()
        before = self.snapshot(self.base)
        result = self.install()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("empty", result.stderr.lower())
        self.assertEqual(self.snapshot(self.base), before)

    def test_later_source_empty_directory_refuses_every_selection_before_writes(self):
        (self.source / "skills/second/nested/empty").mkdir(parents=True)
        before = self.snapshot(self.base)
        result = self.install("--skill", "second", "--agent", "claude-code")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("empty", result.stderr.lower())
        self.assertEqual(self.snapshot(self.base), before)

    def test_list_needs_no_target_and_performs_no_writes(self):
        before = self.snapshot(self.base)
        result = self.run_install("--list")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ("first", "second", "small", "both"):
            self.assertIn(name, result.stdout)
        self.assertEqual(self.snapshot(self.base), before)

    def test_profiles_compose_with_skills_and_deduplicate(self):
        result = self.run_install("--project", self.project, "--agent", "codex",
                                  "--profile", "small", "--profile", "both", "--skill", "first")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("Installed:"), 2)
        self.assertTrue((self.project / ".agents/skills/second/SKILL.md").is_file())

    def test_unknown_profile_and_missing_profile_member_write_nothing(self):
        for profile in ("missing", "broken"):
            (self.source / "profiles.json").write_text(json.dumps({"broken": ["first", "missing"]}))
            result = self.run_install("--project", self.project, "--agent", "codex", "--profile", profile)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.snapshot(), {})

    def test_update_retains_backup_and_installs_new_selection(self):
        self.assertEqual(self.install().returncode, 0)
        old = self.snapshot(self.project / ".agents/skills/first")
        (self.source / "skills/first/SKILL.md").write_bytes(b"new version")
        result = self.install("--update", "--skill", "second")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.project / ".agents/skills/first/SKILL.md").read_bytes(), b"new version")
        self.assertTrue((self.project / ".agents/skills/second/SKILL.md").is_file())
        backups = list((self.project / ".local/done-is-a-claim/backups").glob("*/*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(self.snapshot(backups[0]), old)
        self.assertIn(str(backups[0]), result.stdout)

    def test_repository_profiles_upgrade_eight_evidence_skills_to_thirteen_workflow_skills(self):
        shutil.copytree(ROOT / "skills", self.source / "skills", dirs_exist_ok=True)
        shutil.copyfile(ROOT / "profiles.json", self.source / "profiles.json")
        arguments = ("--project", self.project, "--agent", "codex")
        first = self.run_install(*arguments, "--profile", "evidence")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        installed = self.project / ".agents/skills"
        before = {path.name: self.snapshot(path) for path in installed.iterdir()}
        self.assertEqual(set(before), {"acceptance-design", "reading-measurements", "whose-red",
                                      "evidence-freshness", "public-claims", "checking-delivery",
                                      "collecting-worker-results", "resuming-work"})
        result = self.run_install(*arguments, "--profile", "workflow", "--update")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual({path.name for path in installed.iterdir()}, set(before) | {
            "using-done-is-a-claim", "planning-changes", "executing-plans",
            "debugging-with-evidence", "reviewing-changes"})
        backups = list((self.project / ".local/done-is-a-claim/backups").glob("*/*"))
        self.assertEqual(len(backups), 8)
        for backup in backups:
            self.assertEqual(self.snapshot(backup), before[backup.name[len(".agents-"):]])
        review_project = self.base / "review-project"
        review_project.mkdir()
        review = self.run_install("--project", review_project, "--agent", "claude-code", "--profile", "review")
        self.assertEqual(review.returncode, 0, review.stdout + review.stderr)
        self.assertEqual({path.name for path in (review_project / ".claude/skills").iterdir()}, {
            "using-done-is-a-claim", "reviewing-changes", "reading-measurements", "whose-red",
            "evidence-freshness", "public-claims", "checking-delivery"})

    def test_update_dry_run_checks_existing_and_new_without_writes(self):
        self.assertEqual(self.install().returncode, 0)
        before = self.snapshot(self.base)
        result = self.install("--update", "--dry-run", "--skill", "second")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Would update:", result.stdout)
        self.assertIn("Would install:", result.stdout)
        self.assertEqual(self.snapshot(self.base), before)

    def test_update_rejects_drift_before_any_new_install_or_backup(self):
        for change in ("modified", "missing", "extra", "empty-directory", "provenance"):
            with self.subTest(change=change):
                if (self.project / ".agents").exists():
                    shutil.rmtree(self.project / ".agents")
                self.assertEqual(self.install().returncode, 0)
                destination = self.project / ".agents/skills/first"
                if change == "modified":
                    (destination / "SKILL.md").write_bytes(b"my edits")
                elif change == "missing":
                    (destination / "LICENSE").unlink()
                elif change == "extra":
                    (destination / "my-file").write_bytes(b"keep")
                elif change == "empty-directory":
                    (destination / "my-folder").mkdir()
                else:
                    (destination / "PROVENANCE.json").unlink()
                before = self.snapshot()
                result = self.install("--update", "--skill", "second")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.snapshot(), before)

    def test_update_rejects_unknown_and_malformed_provenance(self):
        self.assertEqual(self.install().returncode, 0)
        provenance = self.project / ".agents/skills/first/PROVENANCE.json"
        original = json.loads(provenance.read_text())
        variants = [[], {}, {**original, "source_repository": "https://other.invalid"},
                    {**original, "skill": "second"}, {**original, "source_revision": 12},
                    {**original, "extra": "unknown"}, {**original, "files_sha256": []},
                    {**original, "files_sha256": {"../escape": "0" * 64}},
                    {**original, "files_sha256": {"SKILL.md": True}}]
        for value in variants:
            with self.subTest(value=value):
                provenance.write_text(json.dumps(value))
                before = self.snapshot()
                result = self.install("--update")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.snapshot(), before)

    def test_update_rejects_links_in_installed_tree(self):
        self.assertEqual(self.install().returncode, 0)
        destination = self.project / ".agents/skills/first"
        original = destination / "references/guide.txt"
        original.unlink()
        self.make_link(original, self.source / "skills/first/references/guide.txt", directory=False)
        result = self.install("--update", "--skill", "second")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(original.is_symlink())
        self.assertFalse((destination.parent / "second").exists())

    def test_update_rejects_unsafe_backup_ancestor_during_preflight(self):
        self.assertEqual(self.install().returncode, 0)
        (self.project / ".local").write_bytes(b"my file")
        before = self.snapshot()
        result = self.install("--update", "--skill", "second")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def load_installer(self):
        spec = importlib.util.spec_from_file_location("installer_fixture", self.source / "tools/install_skills.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_stage_failure_never_publishes_or_moves_originals(self):
        self.assertEqual(self.install().returncode, 0)
        module = self.load_installer()
        project, selections = module.preflight(self.source, self.project, ["codex"], ["first", "second"], True)
        before = self.snapshot()
        copytree = shutil.copytree

        def fail_second(source, destination, *args, **kwargs):
            if Path(source).name == "second":
                raise OSError("injected staging failure")
            return copytree(source, destination, *args, **kwargs)

        with patch.object(module.shutil, "copytree", side_effect=fail_second), redirect_stderr(io.StringIO()):
            result = module.install(self.source, project, selections)
        self.assertEqual(result, 1)
        self.assertEqual(self.snapshot(), before)

    def test_recheck_after_staging_blocks_drift_before_any_publication(self):
        self.assertEqual(self.install().returncode, 0)
        module = self.load_installer()
        project, selections = module.preflight(self.source, self.project, ["codex"], ["first", "second"], True)
        copytree = shutil.copytree
        original = self.project / ".agents/skills/first/SKILL.md"

        def edit_during_stage(source, destination, *args, **kwargs):
            result = copytree(source, destination, *args, **kwargs)
            if Path(source).name == "second":
                original.write_bytes(b"concurrent user edit")
            return result

        with patch.object(module.shutil, "copytree", side_effect=edit_during_stage), redirect_stderr(io.StringIO()):
            result = module.install(self.source, project, selections)
        self.assertEqual(result, 1)
        self.assertEqual(original.read_bytes(), b"concurrent user edit")
        self.assertFalse((original.parent.parent / "second").exists())
        self.assertFalse((self.project / ".local").exists())

    def test_exclusive_publish_rejects_new_empty_destination(self):
        module = self.load_installer()
        project, selections = module.preflight(self.source, self.project, ["codex"], ["first"])
        original_mkdir = Path.mkdir
        destination = self.project / ".agents/skills/first"

        def race_mkdir(path, *args, **kwargs):
            if path == destination:
                original_mkdir(path)
            return original_mkdir(path, *args, **kwargs)

        with patch.object(Path, "mkdir", race_mkdir), redirect_stderr(io.StringIO()):
            result = module.install(self.source, project, selections)
        self.assertEqual(result, 1)
        self.assertEqual(list(destination.iterdir()), [])

    def test_partial_update_failure_retains_original_and_reports_backup(self):
        self.assertEqual(self.install().returncode, 0)
        old = self.snapshot(self.project / ".agents/skills/first")
        module = self.load_installer()
        project, selections = module.preflight(self.source, self.project, ["codex"], ["first"], True)
        rename = Path.rename
        errors = io.StringIO()

        def fail_publish(path, target):
            if ".skill-install-" in str(path):
                raise OSError("injected publication failure")
            return rename(path, target)

        with patch.object(Path, "rename", fail_publish), redirect_stderr(errors):
            result = module.install(self.source, project, selections)
        self.assertEqual(result, 1)
        backups = list((self.project / ".local/done-is-a-claim/backups").glob("*/*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(self.snapshot(backups[0]), old)
        self.assertIn(str(backups[0]), errors.getvalue())
        self.assertIn("Incomplete destination retained:", errors.getvalue())
        self.assertIn("installed destinations: none", errors.getvalue())

    @unittest.skipUnless(sys.platform == "win32", "Windows junction fixture")
    def test_update_rejects_installed_junction_without_symlink_privilege(self):
        import _winapi
        self.assertEqual(self.install().returncode, 0)
        destination = self.project / ".agents/skills/first"
        _winapi.CreateJunction(str(self.source / "skills/first/references"), str(destination / "alias"))
        result = self.install("--update", "--skill", "second")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("junction", result.stderr.lower())
        self.assertFalse((destination.parent / "second").exists())


if __name__ == "__main__":
    unittest.main()
