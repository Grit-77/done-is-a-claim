"""Exercise the package verifier with complete valid and deliberately broken trees."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "tools" / "check_package.py"


class PackageCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "package"
        self.root.mkdir()
        identity = {"name": "example-workflow", "version": "2.4.1", "description": "Check evidence.",
                    "author": {"name": "Example"}, "license": "Apache-2.0"}
        interface = {"displayName": "Example Workflow", "shortDescription": "Check the evidence",
                     "longDescription": "Instructions for checking evidence.",
                     "developerName": "Example", "category": "Developer Tools"}
        self.write_json("plugin.json", {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                                      **identity, "extensions": {"com.openai": {"interface": interface}}})
        self.write_json(".claude-plugin/plugin.json", identity)
        self.write_json(".codex-plugin/plugin.json", {**identity, "skills": "./skills/", "hooks": {}, "interface": interface})
        self.write_json(".claude-plugin/marketplace.json", {
            "name": "example-workflow-marketplace", "owner": {"name": "Example"},
            "plugins": [{"name": "example-workflow", "source": "./", "version": "2.4.1"}]})
        self.write_json(".agents/plugins/marketplace.json", {
            "name": "example-workflow-marketplace", "plugins": [{"name": "example-workflow",
                "source": {"source": "local", "path": "./"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools"}]})
        self.write("skills/example/SKILL.md", "---\nname: example\ndescription: Check evidence before reporting.\n---\n\n# Evidence\n")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_json(self, name, data):
        self.write(name, json.dumps(data))

    def mutate(self, name, change):
        data = json.loads((self.root / name).read_text(encoding="utf-8"))
        change(data)
        self.write_json(name, data)

    def run_check(self):
        return subprocess.run([sys.executable, str(CHECKER), "--root", str(self.root)],
                              capture_output=True, text=True, check=False)

    def assert_rejected(self, diagnostic):
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_valid_package_exits_zero_and_states_limits(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Package structure check passed", result.stdout)
        self.assertIn("runtime activation", result.stdout)

    def test_missing_manifest_is_rejected(self):
        (self.root / ".claude-plugin/plugin.json").unlink()
        self.assert_rejected(".claude-plugin/plugin.json")

    def test_invalid_json_and_nonobject_json_are_rejected(self):
        for content in ("{broken", "[]", "null"):
            with self.subTest(content=content):
                self.write("plugin.json", content)
                self.assert_rejected("plugin.json")

    def test_duplicate_json_fields_are_rejected(self):
        self.write("plugin.json", '{"name":"first","name":"second"}')
        self.assert_rejected("duplicate JSON field")

    def test_identity_and_version_drift_are_rejected(self):
        for field, value in (("name", "another-plugin"), ("version", "2.4.2"), ("license", "MIT")):
            with self.subTest(field=field):
                original = (self.root / ".claude-plugin/plugin.json").read_text(encoding="utf-8")
                self.mutate(".claude-plugin/plugin.json", lambda data: data.update({field: value}))
                self.assert_rejected(field)
                self.write(".claude-plugin/plugin.json", original)

    def test_invalid_portable_names_and_versions_are_rejected(self):
        for field, value in (("name", "Invalid_Name"), ("name", "a" * 65), ("version", "1.2"), ("version", "01.2.3")):
            with self.subTest(field=field, value=value):
                original = (self.root / "plugin.json").read_text(encoding="utf-8")
                self.mutate("plugin.json", lambda data: data.update({field: value}))
                self.assert_rejected(field)
                self.write("plugin.json", original)

    def test_portable_component_fields_are_rejected(self):
        for field in ("skills", "interface", "mcpServers", "apps"):
            with self.subTest(field=field):
                original = (self.root / "plugin.json").read_text(encoding="utf-8")
                self.mutate("plugin.json", lambda data: data.update({field: {}}))
                self.assert_rejected(field)
                self.write("plugin.json", original)

    def test_native_catalog_identity_and_version_drift_are_rejected(self):
        self.mutate(".claude-plugin/marketplace.json", lambda data: data["plugins"][0].update({"version": "9.0.0"}))
        self.assert_rejected("version")

    def test_catalog_name_drift_and_multiple_entries_are_rejected(self):
        self.mutate(".agents/plugins/marketplace.json", lambda data: data.update({"name": "wrong-marketplace"}))
        self.assert_rejected("marketplace name")
        self.mutate(".agents/plugins/marketplace.json", lambda data: data.update({"name": "example-workflow-marketplace", "plugins": []}))
        self.assert_rejected("one plugin")

    def test_catalog_sources_must_resolve_to_the_package_root(self):
        for name, source in ((".claude-plugin/marketplace.json", "../outside"),
                             (".agents/plugins/marketplace.json", {"source": "local", "path": "./skills"})):
            with self.subTest(name=name):
                self.mutate(name, lambda data: data["plugins"][0].update({"source": source}))
                self.assert_rejected("source")

    def test_codex_install_policy_cannot_force_installation(self):
        self.mutate(".agents/plugins/marketplace.json", lambda data: data["plugins"][0]["policy"].update({"installation": "INSTALLED"}))
        self.assert_rejected("policy")

    def test_compatibility_skills_path_must_use_the_packaged_directory(self):
        self.mutate(".codex-plugin/plugin.json", lambda data: data.update({"skills": "../outside"}))
        self.assert_rejected("skills")

    def test_presentation_drift_and_long_subtitles_are_rejected(self):
        self.mutate(".codex-plugin/plugin.json", lambda data: data["interface"].update({"displayName": "Wrong"}))
        self.assert_rejected("interface")
        self.mutate("plugin.json", lambda data: data["extensions"]["com.openai"]["interface"].update({"shortDescription": "x" * 31}))
        self.assert_rejected("shortDescription")

    def test_runtime_declarations_are_rejected_even_if_shadowed(self):
        for name, field, value in ((".codex-plugin/plugin.json", "hooks", {"SessionStart": []}),
                                   (".claude-plugin/plugin.json", "mcpServers", {})):
            with self.subTest(name=name):
                self.mutate(name, lambda data: data.update({field: value}))
                self.assert_rejected(field)

    def test_root_extension_cannot_declare_hooks(self):
        self.mutate("plugin.json", lambda data: data["extensions"]["com.openai"].update({"hooks": "./hooks/hooks.json"}))
        self.assert_rejected("hooks")

    def test_shadowed_compatibility_extension_cannot_declare_hooks(self):
        self.mutate(".codex-plugin/plugin.json", lambda data: data.update({
            "extensions": {"com.openai": {"hooks": "./hooks/hooks.json"}}}))
        self.assert_rejected("extensions")

    def test_manifest_cannot_add_background_monitors(self):
        self.mutate(".claude-plugin/plugin.json", lambda data: data.update({
            "experimental": {"monitors": [{"name": "watch", "command": "python watch.py"}]}}))
        self.assert_rejected("experimental")

    def test_discoverable_runtime_files_are_rejected(self):
        for name in ("mcp.json", ".mcp.json", ".app.json", "hooks/hooks.json", ".claude-plugin/hooks.json"):
            with self.subTest(name=name):
                self.write_json(name, {})
                self.assert_rejected("skills-only")
                (self.root / name).unlink()

    def test_no_skill_and_malformed_skill_are_rejected(self):
        (self.root / "skills/example/SKILL.md").unlink()
        self.assert_rejected("SKILL.md")
        self.write("skills/example/SKILL.md", "---\nname: wrong\ndescription: Useful.\n---\n")
        self.assert_rejected("skill name")

    def test_missing_skill_metadata_is_rejected(self):
        self.write("skills/example/SKILL.md", "---\nname: example\n---\n")
        self.assert_rejected("description")

    def test_skill_directory_without_entrypoint_is_rejected(self):
        self.write("skills/incomplete/reference.md", "Missing its entrypoint.\n")
        self.assert_rejected("skills/incomplete/SKILL.md")

    def test_symlinked_skill_directory_outside_package_is_rejected(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (outside / "SKILL.md").write_text("---\nname: shortcut\ndescription: Outside.\n---\n", encoding="utf-8")
        try:
            (self.root / "skills/shortcut").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        self.assert_rejected("outside package")

    def test_missing_root_is_rejected(self):
        self.root = self.root / "absent"
        self.assert_rejected("root is not a directory")


if __name__ == "__main__":
    unittest.main()
