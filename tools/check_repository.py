#!/usr/bin/env python3
"""Dependency-free structure checks, not a Markdown renderer or YAML parser.

Checks inline Markdown destinations, HTML src/href attributes, single-line
skill frontmatter, and standalone CLAUDE @imports. Does not validate anchors,
reference-style links, remote URLs, prose, or agent/runtime behavior.
"""

import argparse
from html.parser import HTMLParser
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


EXCLUDED_DIRECTORIES = {".local", ".git", ".hg", ".svn", ".bzr"}


def without_code(text):
    """Mask fenced blocks and matching backtick spans, preserving line numbers."""
    lines = text.splitlines(keepends=True)
    fence = None
    for index, line in enumerate(lines):
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            closing = re.match(r"^ {0,3}(" + re.escape(fence[0]) + r"{" + str(fence[1]) + r",})\s*$", line)
            lines[index] = re.sub(r"[^\r\n]", " ", line)
            if closing:
                fence = None
        elif opening:
            fence = (opening[1][0], len(opening[1]))
            lines[index] = re.sub(r"[^\r\n]", " ", line)
    text = "".join(lines)
    span = re.compile(r"(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)", re.DOTALL)
    return span.sub(lambda match: re.sub(r"[^\r\n]", " ", match[0]), text)


def markdown_targets(text):
    """Read inline destinations, including nested labels and parentheses."""
    for match in re.finditer(r"(?<!\\)\[", text):
        position = match.end()
        depth = 1
        while position < len(text) and depth:
            char = text[position]
            if char == "\\":
                position += 2
                continue
            depth += (char == "[") - (char == "]")
            position += 1
        if depth or position >= len(text) or text[position] != "(":
            continue
        position += 1
        while position < len(text) and text[position].isspace():
            position += 1
        if position >= len(text):
            continue
        start = position
        if text[position] == "<":
            end = text.find(">", position + 1)
            if end != -1:
                yield text[position + 1:end], match.start()
            continue
        depth = 0
        while position < len(text):
            char = text[position]
            if char == "\\":
                position += 2
                continue
            if char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char == "(":
                depth += 1
            elif char.isspace() and depth == 0:
                break
            position += 1
        if position < len(text):
            yield text[start:position], match.start()


class HtmlTargets(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("src", "href") and value is not None:
                self.targets.append((value, self.getpos()[0]))


def check_repository(root):
    errors = []
    if not root.is_dir():
        return [f"root is not a directory: {root}"]

    def report(source, message, line=None):
        locator = str(source.relative_to(root)).replace("\\", "/")
        if line is not None:
            locator += f":{line}"
        errors.append(f"{locator}: {message}")

    def check_target(source, target, line=None, require_file=False):
        target = re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])", r"\1", target.strip())
        # A Windows drive is a local path, not a URI scheme, on every OS.
        drive_path = bool(re.match(r"^[A-Za-z]:[\\/]", target))
        try:
            parts = urlsplit(target)
        except ValueError:
            report(source, f"invalid target: {target}", line)
            return
        if parts.scheme == "file":
            if parts.netloc:
                report(source, f"target outside repository: {target}", line)
                return
            local = unquote(parts.path)
            if Path("C:/").is_absolute() and re.match(r"^/[A-Za-z]:/", local):
                local = local[1:]
        elif not drive_path and (parts.scheme or parts.netloc):
            return
        else:
            local = unquote(parts.path)
        if not local:
            return
        if drive_path:
            report(source, f"target outside repository: {target}", line)
            return
        resolved = (source.parent / local.replace("\\", "/")).resolve()
        if not resolved.is_relative_to(root):
            report(source, f"target outside repository: {target}", line)
        elif not resolved.exists():
            report(source, f"missing local target: {target}", line)
        elif require_file and not resolved.is_file():
            report(source, f"CLAUDE import target must be a file: {target}", line)

    documents = {}
    sources = []
    for directory, folders, files in os.walk(root):
        folders[:] = [folder for folder in folders if folder not in EXCLUDED_DIRECTORIES]
        sources.extend(Path(directory) / name for name in files if name.endswith(".md"))
    for source in sorted(sources):
        if not source.resolve().is_relative_to(root):
            report(source, "document outside repository")
            continue
        try:
            text = source.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            report(source, f"cannot read document: {error}")
            continue
        documents[source] = text
        prose = without_code(text)
        for target, offset in markdown_targets(prose):
            check_target(source, target, prose.count("\n", 0, offset) + 1)
        html = HtmlTargets()
        html.feed(prose)
        for target, line in html.targets:
            check_target(source, target, line)

    for source in sorted(root.glob("skills/*/SKILL.md")):
        text = documents.get(source)
        if text is None:
            continue
        lines = text.splitlines()
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            report(source, "frontmatter must open and close with ---")
            continue
        end = lines.index("---", 1)
        fields = {}
        malformed = False
        for line in lines[1:end]:
            if not line.strip():
                continue
            match = re.fullmatch(r"([A-Za-z][\w-]*):[ \t]*(.*)", line)
            if not match or match[1] in fields:
                malformed = True
                continue
            value = match[2].strip()
            if value.startswith(("|", ">")):
                malformed = True
            if value.startswith(("'", '"')):
                if len(value) < 2 or value[-1] != value[0]:
                    malformed = True
                else:
                    value = value[1:-1].strip()
            else:
                # Deliberately support simple strings only, not YAML types,
                # collections, aliases, tags or comments standing in for text.
                value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
                reserved = {"null", "~", "true", "false", "yes", "no", "on", "off", ".nan", ".inf", "-.inf", "+.inf"}
                numeric = re.fullmatch(r"[-+]?(?:\d[\d_]*(?:\.[\d_]*)?|\.[\d_]+)(?:[eE][-+]?\d+)?", value)
                if (value.startswith(("[", "{", "#", "&", "*", "!", "|", ">", "@", "`"))
                        or value.lower() in reserved or numeric or ": " in value):
                    malformed = True
            fields[match[1]] = value
        if malformed or not fields.get("name") or not fields.get("description"):
            report(source, "frontmatter requires unique single-line name and description fields with nonempty simple strings")
        elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]) or fields["name"] != source.parent.name:
            report(source, "skill name must use lowercase letters, digits and hyphens and match its folder")

    claude = root / "CLAUDE.md"
    if claude not in documents:
        report(claude, "missing readable CLAUDE.md")
    else:
        imports = list(re.finditer(r"^[ \t]*@(\S+)[ \t]*$", without_code(documents[claude]), re.MULTILINE))
        if not imports:
            report(claude, "missing standalone local @ import")
        for match in imports:
            target = match[1]
            try:
                parts = urlsplit(target)
            except ValueError:
                report(claude, "invalid CLAUDE import")
                continue
            if parts.scheme or parts.netloc or not parts.path:
                report(claude, "CLAUDE import must specify a local file")
            else:
                check_target(claude, target, require_file=True)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root (defaults to this script's repository)")
    args = parser.parse_args()
    errors = check_repository(args.root.resolve())
    print("Structure only: local inline Markdown links/images, HTML src/href, skill frontmatter and CLAUDE imports.")
    print("Scans repository .md files; excludes directories: " + ", ".join(sorted(EXCLUDED_DIRECTORIES)) + ".")
    print("Does not validate remote URLs, anchors, reference links, prose, or runtime/agent behavior.")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Structure check failed: {len(errors)} error(s).")
        return 1
    print("Structure check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
