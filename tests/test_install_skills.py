"""Project installs must preserve existing material and carry verifiable copies."""

import hashlib
import importlib.util
import io
import json
from contextlib import redirect_stderr, redirect_stdout
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
        # tempfile may return a Windows 8.3 alias. Preflight resolves the
        # project, so use the same canonical root for paths and race injection.
        self.base = Path(temporary.name).resolve()
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

    def test_json_list_is_one_object_and_does_not_write(self):
        before = self.snapshot(self.base)
        result = self.run_install("--list", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["state"], "listed")
        self.assertEqual(report["available_skills"], ["first", "second"])
        self.assertEqual(report["available_profiles"], {"small": ["first"], "both": ["first", "second"]})
        self.assertIsNone(report["source"]["version"])
        self.assertIsNone(report["source"]["revision"])
        self.assertEqual(report["installed_paths"], [])
        self.assertEqual(self.snapshot(self.base), before)

    def test_json_dry_run_deduplicates_multi_agent_profile_and_writes_nothing(self):
        before = self.snapshot(self.base)
        result = self.run_install("--project", self.project, "--agent", "codex", "--agent", "claude-code",
                                  "--profile", "both", "--skill", "first", "--dry-run", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["state"], "planned")
        self.assertEqual(len(report["planned"]), 4)
        self.assertEqual({item["action"] for item in report["planned"]}, {"install"})
        self.assertEqual(report["copied_count"], 0)
        self.assertEqual(report["updated_count"], 0)
        self.assertEqual(report["installed_paths"], [])
        self.assertIsNone(report["next_step"])
        self.assertEqual(self.snapshot(self.base), before)

    def test_json_install_reports_actual_paths_source_and_keeps_instructions(self):
        (self.project / "AGENTS.md").write_bytes(b"owner instructions")
        (self.source / "plugin.json").write_text('{"version":"1.4.0"}')
        git = self.source / ".git"
        git.mkdir()
        revision = "1234567890abcdef1234567890abcdef12345678"
        (git / "HEAD").write_text(revision + "\n")
        result = self.install("--agent", "claude-code", "--profile", "both", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["state"], "installed")
        self.assertEqual(report["copied_count"], 4)
        self.assertEqual(report["updated_count"], 0)
        self.assertEqual(report["source"]["version"], "1.4.0")
        self.assertEqual(report["source"]["revision"], revision)
        self.assertEqual(len(report["installed_paths"]), 4)
        for path in report["installed_paths"]:
            self.assertTrue((Path(path) / "SKILL.md").is_file())
        self.assertFalse(report["instructions_changed"])
        self.assertFalse(report["activated"])
        self.assertEqual((self.project / "AGENTS.md").read_bytes(), b"owner instructions")
        self.assertIn("first", report["next_step"])
        self.assertNotIn("using-done-is-a-claim", report["next_step"])

    def test_json_update_counts_replacements_separately_and_reports_retained_backup(self):
        self.assertEqual(self.install().returncode, 0)
        old = self.snapshot(self.project / ".agents/skills/first")
        (self.source / "skills/first/SKILL.md").write_bytes(b"new version")
        before = self.snapshot(self.base)
        dry_run = self.install("--update", "--skill", "second", "--dry-run", "--json")
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        planned = json.loads(dry_run.stdout)
        self.assertEqual([item["action"] for item in planned["planned"]], ["update", "install"])
        self.assertEqual(self.snapshot(self.base), before)
        result = self.install("--update", "--skill", "second", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["copied_count"], 1)
        self.assertEqual(report["updated_count"], 1)
        self.assertEqual(len(report["installed_paths"]), 2)
        self.assertEqual(len(report["backups"]), 1)
        self.assertEqual(report["backups"][0]["destination"], str(self.project / ".agents/skills/first"))
        self.assertEqual(self.snapshot(Path(report["backups"][0]["path"])), old)

    def test_json_preflight_errors_are_parseable_and_write_nothing(self):
        self.assertEqual(self.install().returncode, 0)
        for arguments in (("--skill", "missing"), ("--profile", "missing"), (), ("--update",)):
            with self.subTest(arguments=arguments):
                if "--update" in arguments:
                    (self.project / ".agents/skills/first/SKILL.md").write_bytes(b"owner edit")
                before = self.snapshot(self.base)
                result = self.install(*arguments, "--json")
                self.assertEqual(result.returncode, 1, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["state"], "failed")
                self.assertTrue(report["error"])
                self.assertEqual(report["installed_paths"], [])
                self.assertEqual(report["copied_count"], 0)
                self.assertEqual(report["updated_count"], 0)
                self.assertIsNone(report["next_step"])
                self.assertEqual(self.snapshot(self.base), before)

    def test_plain_summary_selects_only_an_installed_entry_and_preserves_installed_lines(self):
        shutil.copytree(ROOT / "skills", self.source / "skills", dirs_exist_ok=True)
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Installed: " + str(self.project / ".agents/skills/first"), result.stdout)
        self.assertIn("Next step:", result.stdout)
        self.assertIn("fresh", result.stdout.lower())
        self.assertNotIn("using-done-is-a-claim", result.stdout)
        result = self.run_install("--project", self.project, "--agent", "codex", "--skill", "using-done-is-a-claim")
        self.assertEqual(result.returncode, 0, result.stderr)
        next_step = result.stdout.split("Next step:", 1)[1]
        self.assertIn("using-done-is-a-claim", next_step)
        self.assertIn("AGENTS.md", result.stdout)
        self.assertIn("CLAUDE.md", result.stdout)
        self.assertIn("activation", result.stdout.lower())
        self.assertIn("What you can use:", result.stdout)

    def test_json_partial_publish_reports_only_completed_paths_and_retained_original(self):
        self.assertEqual(self.install("--skill", "second").returncode, 0)
        old_second = self.snapshot(self.project / ".agents/skills/second")
        module = self.load_installer()
        rename = Path.rename
        output = io.StringIO()
        errors = io.StringIO()
        argv = [str(self.source / "tools/install_skills.py"), "--project", str(self.project),
                "--agent", "codex", "--skill", "first", "--skill", "second", "--update", "--json"]

        def fail_second_publish(path, target):
            if ".skill-install-" in str(path) and Path(target).parent.name == "second":
                raise OSError("injected second publication failure")
            return rename(path, target)

        with patch.object(sys, "argv", argv), patch.object(Path, "rename", fail_second_publish), \
                redirect_stdout(output), redirect_stderr(errors):
            result = module.main()
        self.assertEqual(result, 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["state"], "failed")
        self.assertEqual(report["installed_paths"], [str(self.project / ".agents/skills/first")])
        self.assertEqual(report["copied_count"], 0)
        self.assertEqual(report["updated_count"], 1)
        self.assertEqual(report["incomplete_path"], str(self.project / ".agents/skills/second"))
        self.assertEqual(len(report["backups"]), 2)
        self.assertEqual(self.snapshot(Path(report["backups"][1]["path"])), old_second)
        self.assertIsNone(report["next_step"])
        self.assertIn("injected second publication failure", report["error"])
        self.assertEqual([item["skill"] for item in report["capabilities"]], ["first"])

    def test_json_stage_failure_has_no_completed_or_incomplete_destinations(self):
        module = self.load_installer()
        output = io.StringIO()
        before = self.snapshot(self.base)
        argv = [str(self.source / "tools/install_skills.py"), "--project", str(self.project),
                "--agent", "codex", "--skill", "first", "--json"]
        with patch.object(sys, "argv", argv), patch.object(module.shutil, "copytree", side_effect=OSError("stage failed")), \
                redirect_stdout(output), redirect_stderr(io.StringIO()):
            result = module.main()
        self.assertEqual(result, 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["state"], "failed")
        self.assertEqual(report["installed_paths"], [])
        self.assertEqual(report["backups"], [])
        self.assertIsNone(report["incomplete_path"])
        self.assertEqual(report["capabilities"], [])
        self.assertEqual(self.snapshot(self.base), before)

    def test_single_repository_skill_reports_only_its_capability_and_next_step(self):
        shutil.copytree(ROOT / "skills/reading-measurements", self.source / "skills/reading-measurements")
        result = self.run_install("--project", self.project, "--agent", "codex",
                                  "--skill", "reading-measurements", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["skills"], ["reading-measurements"])
        self.assertEqual([item["skill"] for item in report["capabilities"]], ["reading-measurements"])
        self.assertIn("reading-measurements", report["next_step"])
        self.assertNotIn("using-done-is-a-claim", report["next_step"])

    def test_json_report_revision_matches_the_revision_used_for_published_provenance(self):
        module = self.load_installer()
        argv = [str(self.source / "tools/install_skills.py"), "--project", str(self.project),
                "--agent", "codex", "--skill", "first", "--json"]
        output = io.StringIO()
        revision = "1234567890abcdef1234567890abcdef12345678"
        with patch.object(sys, "argv", argv), patch.object(module, "source_revision", side_effect=["unknown", revision]), \
                redirect_stdout(output):
            result = module.main()
        self.assertEqual(result, 0)
        report = json.loads(output.getvalue())
        provenance = json.loads((self.project / ".agents/skills/first/PROVENANCE.json").read_text())
        self.assertEqual(provenance["source_revision"], revision)
        self.assertEqual(report["source"]["revision"], revision)

    def invoke_json_main(self, module, *arguments):
        output = io.StringIO()
        errors = io.StringIO()
        argv = [str(self.source / "tools/install_skills.py"), "--project", str(self.project),
                "--agent", "codex", "--skill", "first", "--json", *arguments]
        with patch.object(sys, "argv", argv), redirect_stdout(output), redirect_stderr(errors):
            code = module.main()
        return code, json.loads(output.getvalue()), errors.getvalue()

    def test_staging_uses_inherited_permissions_and_child_can_use_copied_files(self):
        module = self.load_installer()
        mkdir = module.os.mkdir
        copytree = module.shutil.copytree

        def normal_permissions(path, mode=0o777, *args, **kwargs):
            if Path(path).name.startswith(".skill-install-") and mode == 0o700:
                raise ValueError("native session cannot use restrictive staging permissions")
            return mkdir(path, mode, *args, **kwargs)

        def child_access(source, destination, *args, **kwargs):
            result = copytree(source, destination, *args, **kwargs)
            if Path(source).name == "first":
                child = subprocess.run([sys.executable, "-c",
                    "import pathlib,sys; p=pathlib.Path(sys.argv[1]); data=p.read_bytes(); p.write_bytes(data)",
                    str(Path(destination) / "SKILL.md")], capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, child.stderr)
            return result

        with patch.object(module.os, "mkdir", normal_permissions), patch.object(module.shutil, "copytree", child_access):
            code, report, _ = self.invoke_json_main(module)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["copied_count"], 1)
        self.assertTrue(report["staging"]["removed"])
        self.assertIsNone(report["staging"]["retained_path"])
        self.assertFalse(Path(report["staging"]["path"]).exists())

    def test_unexpected_staging_material_is_retained_and_invalidates_completed_install(self):
        module = self.load_installer()
        copytree = module.shutil.copytree

        def insert_user_material(source, destination, *args, **kwargs):
            result = copytree(source, destination, *args, **kwargs)
            if Path(source).name == "first":
                (Path(destination).parent / "owner-file.txt").write_bytes(b"retain owner material")
            return result

        with patch.object(module.shutil, "copytree", insert_user_material):
            code, report, errors = self.invoke_json_main(module)
        self.assertEqual(code, 1)
        self.assertEqual(report["state"], "failed")
        self.assertEqual(report["copied_count"], 1)
        self.assertEqual(report["installed_paths"], [str(self.project / ".agents/skills/first")])
        self.assertIsNone(report["next_step"])
        staging = Path(report["staging"]["retained_path"])
        self.assertEqual((staging / "owner-file.txt").read_bytes(), b"retain owner material")
        self.assertFalse(report["staging"]["removed"])
        self.assertTrue(report["staging"]["error"])
        self.assertIn(str(staging), errors)

    def test_partial_staging_failure_removes_only_known_copied_material(self):
        module = self.load_installer()
        copytree = module.shutil.copytree
        before = self.snapshot()

        def fail_after_copy(source, destination, *args, **kwargs):
            result = copytree(source, destination, *args, **kwargs)
            if Path(source).name == "first":
                raise OSError("failure after source copy")
            return result

        with patch.object(module.shutil, "copytree", fail_after_copy):
            code, report, _ = self.invoke_json_main(module)
        self.assertEqual(code, 1)
        self.assertEqual(report["installed_paths"], [])
        self.assertTrue(report["staging"]["removed"])
        self.assertEqual(self.snapshot(), before)

    def test_partial_staging_failure_retains_modified_known_filename(self):
        module = self.load_installer()
        copytree = module.shutil.copytree

        def corrupt_then_fail(source, destination, *args, **kwargs):
            result = copytree(source, destination, *args, **kwargs)
            if Path(source).name == "first":
                (Path(destination) / "SKILL.md").write_bytes(b"changed concurrently")
                raise OSError("failure with changed stage")
            return result

        with patch.object(module.shutil, "copytree", corrupt_then_fail):
            code, report, _ = self.invoke_json_main(module)
        self.assertEqual(code, 1)
        self.assertEqual(report["installed_paths"], [])
        staging = Path(report["staging"]["retained_path"])
        self.assertEqual((staging / "0/SKILL.md").read_bytes(), b"changed concurrently")
        self.assertTrue((staging / "0/references/guide.txt").exists())

    def test_cleanup_error_keeps_published_counts_and_reports_retained_staging(self):
        module = self.load_installer()
        rmdir = Path.rmdir

        def fail_cleanup(path):
            if path.name.startswith(".skill-install-"):
                raise PermissionError("cleanup refused")
            return rmdir(path)

        with patch.object(Path, "rmdir", fail_cleanup):
            code, report, _ = self.invoke_json_main(module)
        self.assertEqual(code, 1)
        self.assertEqual(report["state"], "failed")
        self.assertEqual(report["copied_count"], 1)
        self.assertTrue((self.project / ".agents/skills/first/SKILL.md").exists())
        self.assertFalse(report["staging"]["removed"])
        self.assertIn("cleanup refused", report["staging"]["error"])
        self.assertIsNone(report["next_step"])

    @unittest.skipUnless(sys.platform == "win32", "Windows junction fixture")
    def test_staging_replaced_by_junction_retains_external_sentinel(self):
        import _winapi
        module = self.load_installer()
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "sentinel.txt").write_bytes(b"external owner material")
        rename = Path.rename
        replaced = []

        def replace_after_publish(path, target):
            result = rename(path, target)
            if ".skill-install-" in str(path) and not any(path.parent.iterdir()):
                staging = path.parent.parent
                rename(staging, staging.with_name(staging.name + "-original"))
                _winapi.CreateJunction(str(outside), str(staging))
                replaced.append(staging)
            return result

        with patch.object(Path, "rename", replace_after_publish):
            code, report, _ = self.invoke_json_main(module)
        self.assertEqual(code, 1)
        self.assertEqual(report["copied_count"], 1)
        self.assertEqual((outside / "sentinel.txt").read_bytes(), b"external owner material")
        self.assertEqual(len(list(outside.iterdir())), 1)
        self.assertFalse(report["staging"]["removed"])
        self.assertEqual(report["staging"]["retained_path"], str(replaced[0]))
        replaced[0].rmdir()  # remove the test junction only, preserving its target

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
        race_injected = False

        def race_mkdir(path, *args, **kwargs):
            nonlocal race_injected
            if path == destination:
                original_mkdir(path)
                race_injected = True
            return original_mkdir(path, *args, **kwargs)

        with patch.object(Path, "mkdir", race_mkdir), redirect_stderr(io.StringIO()):
            result = module.install(self.source, project, selections)
        self.assertTrue(race_injected, "the concurrent destination must actually be created")
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
