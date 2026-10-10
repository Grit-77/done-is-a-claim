#!/usr/bin/env python3
"""Check this skills-only distribution's manifests, catalogs and contained skills."""

import argparse
import json
import os
from pathlib import Path
import re


MANIFESTS = ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
CATALOGS = (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json")
IDENTITY = ("name", "version", "description", "author", "license", "homepage", "repository")
RUNTIME_FIELDS = ("mcpServers", "apps", "commands", "agents", "outputStyles", "workflows",
                  "lspServers", "experimental", "channels", "dependencies", "userConfig")
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SEMVER = re.compile(
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|[\dA-Za-z-]*[A-Za-z-][\dA-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|[\dA-Za-z-]*[A-Za-z-][\dA-Za-z-]*))*)?"
    r"(?:\+[\dA-Za-z-]+(?:\.[\dA-Za-z-]+)*)?"
)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def check_package(root):
    root = root.resolve()
    errors = []
    if not root.is_dir():
        return [f"root is not a directory: {root}"]

    def report(path, message):
        errors.append(f"{path}: {message}")

    def contained(path):
        if not path.resolve().is_relative_to(root):
            report(path.relative_to(root).as_posix(), "outside package")
            return False
        return True

    def read_object(name):
        path = root / name
        if not contained(path):
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        except (OSError, UnicodeError, ValueError) as error:
            report(name, f"cannot read JSON object: {error}")
            return None
        if not isinstance(data, dict):
            report(name, "JSON must be an object")
            return None
        return data

    documents = {name: read_object(name) for name in MANIFESTS + CATALOGS}
    portable = documents["plugin.json"]
    if portable is None:
        return errors
    name = portable.get("name")
    if not isinstance(name, str) or len(name) > 64 or not NAME.fullmatch(name):
        report("plugin.json", "name must be lowercase kebab-case, at most 64 characters")
    version = portable.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        report("plugin.json", "version must be strict semantic versioning")
    for field in ("description", "license"):
        if not isinstance(portable.get(field), str) or not portable[field].strip():
            report("plugin.json", f"{field} must be a nonempty string")
    author = portable.get("author")
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        report("plugin.json", "author must have a nonempty name")
    if portable.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        report("plugin.json", "expected Agent Plugins 1.0 schema")
    for field in ("skills", "interface", "hooks"):
        if field in portable:
            report("plugin.json", f"portable manifest must not declare top-level {field}")
    extension = portable.get("extensions", {})
    openai = extension.get("com.openai") if isinstance(extension, dict) else None
    interface = openai.get("interface") if isinstance(openai, dict) else None
    if not isinstance(interface, dict):
        report("plugin.json", "extensions.com.openai.interface must be an object")
    else:
        for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
            if not isinstance(interface.get(field), str) or not interface[field].strip():
                report("plugin.json", f"interface.{field} must be a nonempty string")
        subtitle = interface.get("shortDescription")
        if isinstance(subtitle, str) and len(subtitle) > 30:
            report("plugin.json", "interface.shortDescription exceeds 30 characters")
    if isinstance(openai, dict):
        for field in openai:
            if field != "interface":
                report("plugin.json", f"skills-only extension must not declare {field}")

    for manifest_name in MANIFESTS:
        manifest = documents[manifest_name]
        if manifest is None:
            continue
        for field in RUNTIME_FIELDS:
            if field in manifest:
                report(manifest_name, f"skills-only manifest must not declare {field}")
        if manifest_name != "plugin.json":
            if "extensions" in manifest:
                report(manifest_name, "skills-only compatibility manifest must not declare extra extensions")
            for field in IDENTITY:
                if manifest.get(field) != portable.get(field):
                    report(manifest_name, f"{field} differs from portable manifest")
        if manifest_name == ".codex-plugin/plugin.json":
            if manifest.get("skills") != "./skills/":
                report(manifest_name, "skills must reference ./skills/ from the package root")
            if manifest.get("hooks") != {}:
                report(manifest_name, "skills-only compatibility hooks must be an empty object")
            if manifest.get("interface") != interface:
                report(manifest_name, "interface differs from portable presentation")
        elif "hooks" in manifest:
            report(manifest_name, "skills-only manifest must not declare hooks")
        if manifest_name == ".claude-plugin/plugin.json" and "skills" in manifest:
            report(manifest_name, "use default root skills/ discovery without extra skills paths")

    for catalog_name in CATALOGS:
        catalog = documents[catalog_name]
        if catalog is None:
            continue
        if catalog.get("name") != f"{name}-marketplace":
            report(catalog_name, "marketplace name must match the plugin name plus -marketplace")
        entries = catalog.get("plugins")
        if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
            report(catalog_name, "catalog must contain exactly one plugin object")
            continue
        entry = entries[0]
        if entry.get("name") != name:
            report(catalog_name, "plugin name differs from portable manifest")
        if "version" in entry and entry["version"] != version:
            report(catalog_name, "plugin version differs from portable manifest")
        for field in ("skills", "hooks") + RUNTIME_FIELDS:
            if field in entry:
                report(catalog_name, f"skills-only catalog must not declare {field}")
        if catalog_name == ".claude-plugin/marketplace.json":
            owner = catalog.get("owner")
            if not isinstance(owner, dict) or not isinstance(owner.get("name"), str) or not owner["name"].strip():
                report(catalog_name, "owner must have a nonempty name")
            if entry.get("source") != "./":
                report(catalog_name, "source must be ./ (the complete package root)")
        else:
            if entry.get("source") != {"source": "local", "path": "./"}:
                report(catalog_name, "source must reference local ./ (the complete package root)")
            if entry.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
                report(catalog_name, "policy must keep installation AVAILABLE and authentication ON_INSTALL")
            if entry.get("category") != "Developer Tools":
                report(catalog_name, "category must be Developer Tools")

    for filename in ("mcp.json", ".mcp.json", ".app.json", ".lsp.json", "hooks/hooks.json", ".claude-plugin/hooks.json"):
        path = root / filename
        if path.exists() or path.is_symlink():
            report(filename, "skills-only package must not provide discoverable runtime configuration")
    for folder in ("hooks", "commands", "agents", "outputStyles", "workflows"):
        if (root / folder).is_dir() and any((root / folder).iterdir()):
            report(folder, "skills-only package must not provide other runtime components")

    skills = root / "skills"
    if contained(skills) and skills.is_dir():
        for child in skills.iterdir():
            if child.is_dir() and not (child / "SKILL.md").is_file():
                report((child / "SKILL.md").relative_to(root).as_posix(), "missing skill entrypoint")
        for directory, folders, files in os.walk(skills):
            for child in folders + files:
                contained(Path(directory) / child)
        skill_files = sorted(skills.glob("*/SKILL.md"))
    else:
        skill_files = []
    if not skill_files:
        report("skills", "at least one packaged skills/<name>/SKILL.md is required")
    for path in skill_files:
        if not contained(path):
            continue
        locator = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            report(locator, f"cannot read SKILL.md: {error}")
            continue
        lines = text.splitlines()
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            report(locator, "SKILL.md requires closed frontmatter with name and description")
            continue
        header = "\n".join(lines[1:lines.index("---", 1)])
        for field in ("name", "description"):
            values = re.findall(rf"^{field}:[ \t]*(.*)$", header, re.MULTILINE)
            if len(values) != 1 or not values[0].strip().strip("\"'"):
                report(locator, f"SKILL.md requires one nonempty {field}")
            elif field == "name":
                skill_name = values[0].strip().strip("\"'")
                if skill_name != path.parent.name or not NAME.fullmatch(skill_name):
                    report(locator, "skill name must match its lowercase kebab-case directory")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check_package(args.root)
    print("Structure only: manifests, identity/version agreement, local catalogs, contained skills and skills-only components.")
    print("Does not prove native installation, runtime activation, agent compliance or tool availability. Run native validators separately.")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Package structure check failed: {len(errors)} error(s).")
        return 1
    print("Package structure check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
