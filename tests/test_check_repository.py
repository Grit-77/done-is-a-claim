"""Exercise the structural checker through its public CLI, using real fixtures."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "tools" / "check_repository.py"


class RepositoryCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.write("README.md", "[Rules](AGENTS.md#rules)\n![Card](assets/card.svg)\n")
        self.write("AGENTS.md", "# Rules\n")
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("assets/card.svg", "<svg xmlns='http://www.w3.org/2000/svg'/>\n")
        self.write("skills/example/SKILL.md", "---\nname: example\ndescription: A useful skill.\n---\n\n# Example\n")

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_check(self):
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(self.root)],
            capture_output=True, text=True, check=False,
        )

    def assert_rejected(self, diagnostic):
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stdout + result.stderr)

    def test_valid_tree_exits_zero_and_describes_scope(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("structure", result.stdout.lower())
        self.assertIn("remote", result.stdout.lower())
        self.assertIn("behavior", result.stdout.lower())

    def test_missing_markdown_link_is_rejected(self):
        self.write("README.md", "[Gone](missing.md)\n")
        self.assert_rejected("missing.md")

    def test_missing_image_is_rejected(self):
        self.write("README.md", "![Gone](assets/missing.svg)\n")
        self.assert_rejected("assets/missing.svg")

    def test_nested_documents_resolve_links_from_their_own_folder(self):
        self.write("docs/guide.md", "[Rules](../AGENTS.md)\n[Missing](missing.md)\n")
        self.assert_rejected("docs/guide.md")

    def test_existing_target_outside_root_is_rejected(self):
        (self.root.parent / "outside.md").write_text("outside", encoding="utf-8")
        self.write("README.md", "[Outside](../outside.md)\n")
        self.assert_rejected("outside repository")

    def test_file_url_outside_root_is_rejected(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        self.write("README.md", f"[Outside]({outside.as_uri()})\n")
        self.assert_rejected("outside repository")

    def test_symlink_target_outside_root_is_rejected(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            (self.root / "shortcut.md").symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        self.write("README.md", "[Outside](shortcut.md)\n")
        self.assert_rejected("outside repository")

    def test_html_local_src_and_href_are_checked(self):
        for attribute in ("src", "href"):
            with self.subTest(attribute=attribute):
                self.write("README.md", f'<img {attribute}="assets/missing.svg">\n')
                self.assert_rejected("assets/missing.svg")

    def test_html_existing_links_and_encoded_markdown_paths_are_valid(self):
        self.write("assets/a card.svg", "<svg/>\n")
        self.write("README.md", '<a href="AGENTS.md#rules">Rules</a>\n<img src="assets/card.svg">\n![Card](assets/a%20card.svg "Caption")\n')
        self.assertEqual(self.run_check().returncode, 0)

    def test_angle_paths_and_balanced_parentheses_are_valid(self):
        self.write("assets/card (new).svg", "<svg/>\n")
        self.write("README.md", '![Card](<assets/card (new).svg>)\n[Card](assets/card%20(new).svg)\n')
        self.assertEqual(self.run_check().returncode, 0)

    def test_external_urls_and_fragment_links_are_ignored(self):
        self.write("README.md", '[Web](https://invalid.example/missing)\n[Mail](mailto:nobody@example.com)\n[Anchor](#missing)\n<img src="//invalid.example/missing">\n')
        self.assertEqual(self.run_check().returncode, 0)

    def test_fenced_and_inline_code_examples_are_ignored(self):
        self.write("README.md", '```md\n[Example](missing.md)\n<img src="missing.svg">\n```\n~~~html\n<a href="gone.md">Example</a>\n~~~\n`[Example](missing.md)`\n``<img src="missing.svg"> `example` ``\n')
        self.assertEqual(self.run_check().returncode, 0)

    def test_mismatched_skill_name_is_rejected(self):
        self.write("skills/example/SKILL.md", "---\nname: another\ndescription: Useful.\n---\n")
        self.assert_rejected("name")

    def test_invalid_skill_name_matching_folder_is_rejected(self):
        self.write("skills/Invalid_Name/SKILL.md", "---\nname: Invalid_Name\ndescription: Useful.\n---\n")
        self.assert_rejected("skill name")

    def test_missing_or_empty_required_skill_fields_are_rejected(self):
        for fields in ("name: example\n", "description: Useful.\n", "name: example\ndescription: \n", 'name: example\ndescription: ""\n'):
            with self.subTest(fields=fields):
                self.write("skills/example/SKILL.md", "---\n" + fields + "---\n")
                self.assert_rejected("frontmatter")

    def test_missing_unclosed_or_multiline_frontmatter_is_rejected(self):
        for content in ("# Example\n", "---\nname: example\ndescription: Useful.\n", "---\nname: example\ndescription: |\n  Multiline.\n---\n"):
            with self.subTest(content=content):
                self.write("skills/example/SKILL.md", content)
                self.assert_rejected("frontmatter")

    def test_duplicate_frontmatter_field_is_rejected(self):
        self.write("skills/example/SKILL.md", "---\nname: example\nname: another\ndescription: Useful.\n---\n")
        self.assert_rejected("frontmatter")

    def test_quoted_single_line_frontmatter_is_valid(self):
        self.write("skills/example/SKILL.md", '---\nname: "example"\ndescription: "Useful: has a colon."\n---\n')
        self.assertEqual(self.run_check().returncode, 0)

    def test_nonstring_or_comment_only_frontmatter_is_rejected(self):
        for value in ("null", "~", "[]", "{}", "# empty", "null # empty", "true", "17", "&alias Useful"):
            with self.subTest(value=value):
                self.write("skills/example/SKILL.md", f"---\nname: example\ndescription: {value}\n---\n")
                self.assert_rejected("frontmatter")

    def test_quoted_yaml_like_description_is_a_valid_string(self):
        self.write("skills/example/SKILL.md", '---\nname: example\ndescription: "null"\n---\n')
        self.assertEqual(self.run_check().returncode, 0)

    def test_local_evidence_and_vcs_documents_are_excluded(self):
        for directory in (".local", ".git", ".hg", ".svn", ".bzr"):
            self.write(f"{directory}/notes.md", "[Private](missing.md)\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(".local", result.stdout)
        self.assertIn(".hg", result.stdout)

    def test_github_markdown_is_still_checked(self):
        self.write(".github/CONTRIBUTING.md", "[Missing](missing.md)\n")
        self.assert_rejected(".github/CONTRIBUTING.md")

    def test_missing_claude_import_target_is_rejected(self):
        self.write("CLAUDE.md", "@missing.md\n")
        self.assert_rejected("missing.md")

    def test_claude_directory_import_is_rejected(self):
        self.write("CLAUDE.md", "@assets\n")
        self.assert_rejected("import")

    def test_claude_without_an_import_is_rejected(self):
        self.write("CLAUDE.md", "Use the rules.\n`@AGENTS.md`\n")
        self.assert_rejected("import")

    def test_claude_fragment_only_import_is_rejected(self):
        self.write("CLAUDE.md", "@#rules\n")
        self.assert_rejected("import")

    def test_malformed_claude_import_exits_cleanly(self):
        self.write("CLAUDE.md", "@https://[broken\n")
        self.assert_rejected("import")
        self.assertNotIn("Traceback", self.run_check().stdout + self.run_check().stderr)

    def test_missing_claude_file_is_rejected(self):
        (self.root / "CLAUDE.md").unlink()
        self.assert_rejected("CLAUDE.md")

    def test_missing_root_exits_nonzero(self):
        result = subprocess.run([sys.executable, str(CHECKER), "--root", str(self.root / "absent")], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("root", (result.stdout + result.stderr).lower())


if __name__ == "__main__":
    unittest.main()
