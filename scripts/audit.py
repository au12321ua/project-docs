#!/usr/bin/env python3
"""Read-only mechanical checks for project-docs conventions (Python 3.10+)."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


STATUSES = {"draft", "accepted", "deferred", "completed", "cancelled", "superseded"}
TERMINAL = {"completed", "cancelled", "superseded"}
SKIP_DIRS = {".git", ".local", ".venv", "venv", "node_modules", "vendor", "__pycache__"}
LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[^)\n]*)?\)")
IMAGE = re.compile(r"!\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[^)\n]*)?\)")
DEFINITION = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>\n]+>|\S+)", re.MULTILINE)
CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml",
    ".md", ".rs", ".go", ".c", ".h", ".cpp", ".sh", ".sql", ".css", ".html",
    ".vue", ".svelte", ".java", ".kt", ".swift", ".rb", ".xml", ".ini", ".cfg",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    line: int
    message: str


def git(repo: Path, *args: str) -> str | None:
    """Disable optional Git writes, including index refreshes during status."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True,
            timeout=15, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def unfenced(text: str) -> str:
    """Remove code examples while keeping line offsets for findings."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if match and fence is None:
            fence = match[1]
            lines.append("\n")
        elif fence is not None:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            lines.append("\n")
        else:
            lines.append(line)
    return "".join(lines)


def field(text: str, label: str) -> str | None:
    match = re.search(
        rf"^\s*(?:[-*]\s+)?(?:\*\*)?{re.escape(label)}(?:\*\*)?:\s*(.*?)\s*$",
        text, re.MULTILINE | re.IGNORECASE,
    )
    return match[1].strip().strip("`*") if match else None


def records(text: str, prefix: str) -> list[tuple[str, int, str]]:
    headings = list(re.finditer(rf"^#{{1,6}}\s+({prefix}-\d+)\b[^\n]*", text, re.MULTILINE))
    return [
        (match[1], text.count("\n", 0, match.start()) + 1,
         text[match.start():headings[i + 1].start() if i + 1 < len(headings) else len(text)])
        for i, match in enumerate(headings)
    ]


def markdown_files(repo: Path) -> list[Path]:
    listing = git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if listing is not None:
        candidates = (repo / name for name in set(listing.split("\0")) if name)
    else:
        found = []
        for directory, names, files in os.walk(repo, followlinks=False):
            names[:] = [n for n in names if n not in SKIP_DIRS and not (Path(directory) / n).is_symlink()]
            found.extend(Path(directory) / name for name in files)
        candidates = iter(found)
    result = []
    for path in candidates:
        relative = path.relative_to(repo)
        if path.suffix.lower() != ".md" or any(part in SKIP_DIRS for part in relative.parts):
            continue
        if "templates" in relative.parts:
            continue  # Starter files describe future projects, not this repository.
        if path.is_file() and path.resolve().is_relative_to(repo):
            result.append(path)
    return sorted(result)


class Audit:
    def __init__(self, repo: Path):
        self.repo = repo.resolve()
        self.findings: list[Finding] = []
        self.documents: dict[Path, str] = {}

    def add(self, severity: str, code: str, path: Path | str, message: str, line: int = 0) -> None:
        if isinstance(path, Path):
            path = str(path.relative_to(self.repo))
        self.findings.append(Finding(severity, code, path, line, message))

    def check_target(self, source: Path, target: str, line: int) -> None:
        target = target.strip("<>")
        try:
            url = urlsplit(target)
        except ValueError:
            self.add("warning", "LINK_FORMAT", source, "Cannot parse a local link target.", line)
            return
        if url.scheme or url.netloc or not url.path:
            return
        decoded = unquote(url.path)
        path = self.repo / decoded.lstrip("/") if decoded.startswith("/") else source.parent / decoded
        resolved = path.resolve()
        if not resolved.is_relative_to(self.repo):
            self.add("info", "LINK_OUTSIDE_REPO", source, "A local link leaves the repository; check it manually.", line)
        elif not resolved.exists():
            self.add("error", "LINK_MISSING", source, f"Missing local target: {decoded}", line)

    def check_links(self) -> None:
        for path, text in self.documents.items():
            # Inline code may contain literal link syntax; it is not a Markdown link.
            prose = re.sub(r"`+[^`\n]+`+", lambda m: " " * len(m[0]), text)
            for pattern in (LINK, IMAGE, DEFINITION):
                for match in pattern.finditer(prose):
                    self.check_target(path, match[1], prose.count("\n", 0, match.start()) + 1)
            for match in re.finditer(r"(?<!`)`([^`\n]+)`(?!`)", text):
                reference = match[1]
                if "/" not in reference or re.search(r"[\s<>{}*?]|://", reference):
                    continue
                reference = re.sub(r":\d+(?::\d+)?$", "", reference.split("#", 1)[0])
                if Path(reference).suffix.lower() not in CODE_SUFFIXES:
                    continue
                candidates = [(path.parent / reference).resolve(), (self.repo / reference).resolve()]
                inside = [candidate for candidate in candidates if candidate.is_relative_to(self.repo)]
                if inside and not any(candidate.exists() for candidate in inside):
                    self.add("warning", "CODE_PATH_MISSING", path,
                             f"Code/document path may have moved: {reference}", text.count("\n", 0, match.start()) + 1)

    def check_level(self, level: str | None) -> None:
        if level is None:
            self.add("info", "LEVEL_UNSET", "AGENTS.md", "Documentation level not detected; use --level if needed.")
            return
        required = ["AGENTS.md", "README.md"]
        if int(level[1]) >= 1:
            required += ["docs/HANDOFF.md", "docs/decisions.md"]
        for name in required:
            if self.repo / name not in self.documents:
                self.add("error", "LEVEL_FILE_MISSING", name, f"Required {level} document is missing or unreadable.")
        if int(level[1]) >= 2:
            for name in ("architecture", "design"):
                root = self.repo / "docs" / name
                if not any(path.is_relative_to(root) for path in self.documents):
                    self.add("warning", "LEVEL_CONTENT_MISSING", root, f"{level} needs useful current-state content here.")
        if int(level[1]) >= 3 and not any(
            self.repo / "docs/proposals" / name in self.documents for name in ("README.md", "index.md")
        ):
            self.add("error", "PROPOSAL_INDEX_MISSING", "docs/proposals", "No proposal index found.")

    def check_decisions(self) -> None:
        path = self.repo / "docs/decisions.md"
        entries = records(self.documents.get(path, ""), "U")
        seen = {}
        for identifier, line, body in entries:
            if identifier in seen:
                self.add("error", "DECISION_DUPLICATE", path, f"Duplicate decision ID: {identifier}", line)
            seen[identifier] = (line, body)
            if not re.fullmatch(r"U-\d{2,}", identifier):
                self.add("warning", "DECISION_ID_FORMAT", path, f"Expected at least two digits: {identifier}", line)
            if not field(body, "Source"):
                self.add("warning", "DECISION_SOURCE_MISSING", path, f"No traceable source recorded for {identifier}.", line)
        edges: dict[str, set[str]] = {identifier: set() for identifier in seen}
        for identifier, (line, body) in seen.items():
            for label, reverse in (("Supersedes", "Superseded by"), ("Superseded by", "Supersedes")):
                targets = set(re.findall(r"\bU-\d+\b", field(body, label) or ""))
                for target in targets:
                    if target not in seen:
                        self.add("error", "DECISION_TARGET_MISSING", path,
                                 f"{identifier} refers to missing {target} in {label}.", line)
                    else:
                        other = set(re.findall(r"\bU-\d+\b", field(seen[target][1], reverse) or ""))
                        if identifier not in other:
                            self.add("error", "DECISION_RECIPROCAL_MISSING", path,
                                     f"{identifier} and {target} lack matching supersession annotations.", line)
                    if label == "Superseded by":
                        edges[identifier].add(target)
        # Iterative traversal avoids a recursion limit on long decision histories.
        for start in sorted(edges):
            pending = list(edges[start])
            visited = set()
            while pending:
                target = pending.pop()
                if target == start:
                    self.add("error", "DECISION_CYCLE", path, "Decision supersession contains a cycle.")
                    return
                if target not in visited:
                    visited.add(target)
                    pending.extend(edges.get(target, set()))

    def check_proposals(self) -> None:
        root = self.repo / "docs/proposals"
        paths = [path for path in self.documents if path.is_relative_to(root)]
        if not paths:
            return
        indices = [root / name for name in ("README.md", "index.md") if root / name in self.documents]
        if len(indices) > 1:
            self.add("warning", "PROPOSAL_INDEX_AMBIGUOUS", root, "Both README.md and index.md exist; choose one authority.")
        index = indices[0] if indices else None
        if index is None:
            self.add("error", "PROPOSAL_INDEX_MISSING", root, "Proposals exist without an index.")
        proposals = {}
        for path in paths:
            if path.name.lower() in {"readme.md", "index.md"}:
                continue
            entries = records(self.documents[path], "P")
            if len(entries) != 1:
                self.add("warning", "PROPOSAL_FORMAT", path, "Expected one P-ID heading; inspect the established format manually.")
                continue
            identifier, line, body = entries[0]
            if identifier in proposals:
                self.add("error", "PROPOSAL_DUPLICATE", path, f"Duplicate proposal ID: {identifier}", line)
            status = (field(body, "Status") or "").lower()
            proposals[identifier] = (path, status)
            if not re.fullmatch(r"P-\d{3,}", identifier):
                self.add("warning", "PROPOSAL_ID_FORMAT", path, f"Expected at least three digits: {identifier}", line)
            if status not in STATUSES:
                self.add("error", "PROPOSAL_STATUS", path, f"Missing or unsupported status for {identifier}.", line)
            archived = "archive" in path.relative_to(root).parts[:-1]
            if status in TERMINAL and not archived:
                self.add("error", "PROPOSAL_NOT_ARCHIVED", path, f"{identifier} is {status} but not archived.", line)
            if archived and status in {"draft", "accepted"}:
                self.add("error", "PROPOSAL_ACTIVE_ARCHIVED", path, f"Active {identifier} is in archive/.", line)
        if index is None:
            return
        indexed = set()
        columns = None
        for line_number, row in enumerate(self.documents[index].splitlines(), 1):
            if not row.strip().startswith("|"):
                continue
            cells = [cell.strip().strip("`") for cell in row.strip().strip("|").split("|")]
            labels = [cell.lower() for cell in cells]
            if {"id", "status", "document"}.issubset(labels):
                columns = {label: labels.index(label) for label in ("id", "status", "document")}
                continue
            if columns is None or len(cells) <= max(columns.values()):
                continue
            identifier = cells[columns["id"]]
            if not re.fullmatch(r"P-\d+", identifier):
                continue
            if identifier in indexed:
                self.add("error", "PROPOSAL_INDEX_DUPLICATE", index, f"Duplicate index row: {identifier}", line_number)
            indexed.add(identifier)
            if identifier not in proposals:
                self.add("error", "PROPOSAL_INDEX_UNKNOWN", index, f"Index refers to missing/unrecognized {identifier}.", line_number)
                continue
            path, status = proposals[identifier]
            if cells[columns["status"]].lower() != status:
                self.add("error", "PROPOSAL_INDEX_STATUS", index, f"Index status differs from {identifier}.", line_number)
            link = LINK.search(cells[columns["document"]])
            try:
                url = urlsplit(link[1].strip("<>")) if link else None
                target = unquote(url.path) if url and not url.scheme and not url.netloc else ""
            except ValueError:
                target = ""
            if not target or (index.parent / target).resolve() != path.resolve():
                self.add("error", "PROPOSAL_INDEX_TARGET", index, f"Index must link to {identifier}'s actual document.", line_number)
        if proposals and columns is None:
            self.add("warning", "PROPOSAL_INDEX_FORMAT", index, "Expected an ID/Status/Document table; check the index manually.")
        for identifier, (path, _) in proposals.items():
            if identifier not in indexed:
                self.add("error", "PROPOSAL_NOT_INDEXED", path, f"{identifier} has no recognized index row.")

    def check_git(self, integration: str | None, release: str | None) -> None:
        if git(self.repo, "rev-parse", "--git-dir") is None:
            self.add("info", "GIT_UNAVAILABLE", ".", "Git checks unavailable; no repository or Git executable.")
            return
        if git(self.repo, "check-ignore", "--no-index", "--", ".local/project-docs-audit-probe") is None:
            self.add("warning", "LOCAL_NOT_IGNORED", ".gitignore", "Root .local/ logs are not ignored.")
        tracked = git(self.repo, "ls-files", "--", ".local")
        if tracked:
            self.add("warning", "LOCAL_TRACKED", ".local", "Local process files are already tracked; ignoring does not untrack them.")
        if not integration:
            self.add("info", "INTEGRATION_UNSET", "AGENTS.md", "Integration branch not detected; use --integration-branch for cleanup candidates.")
            return
        branches = git(self.repo, "for-each-ref", "--format=%(refname:short)", "refs/heads") or ""
        if integration not in branches.splitlines():
            self.add("warning", "INTEGRATION_MISSING", "AGENTS.md", f"No local integration branch: {integration}")
            return
        merged = set((git(self.repo, "for-each-ref", f"--merged=refs/heads/{integration}",
                          "--format=%(refname:short)", "refs/heads") or "").splitlines())
        protected = {integration, release, "main", "master", "dev", "develop"}
        candidates = merged - protected
        for branch in sorted(candidates):
            self.add("warning", "MERGED_BRANCH", ".git", f"Local branch is integrated; review cleanup: {branch}")
        worktrees = git(self.repo, "worktree", "list", "--porcelain", "-z") or ""
        for block in worktrees.split("\0\0"):
            values = dict(item.split(" ", 1) if " " in item else (item, "") for item in block.split("\0") if item)
            location = values.get("worktree")
            if not location or Path(location).resolve() == self.repo:
                continue
            if "prunable" in values:
                self.add("warning", "STALE_WORKTREE", ".git", "A worktree registration is prunable; review before pruning.")
            branch = values.get("branch", "").removeprefix("refs/heads/")
            if branch in candidates:
                status = git(Path(location), "status", "--porcelain", "--untracked-files=normal")
                state = "unavailable" if status is None else "dirty" if status else "clean"
                locked = "; locked" if "locked" in values else ""
                self.add("warning", "MERGED_WORKTREE", ".git",
                         f"Integrated worktree for {branch}: {state}{locked}. Inspect ownership before cleanup.")

    def run(self, level: str | None = None, integration_branch: str | None = None) -> dict:
        for path in markdown_files(self.repo):
            try:
                self.documents[path] = unfenced(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError):
                self.add("warning", "DOCUMENT_UNREADABLE", path, "Cannot read Markdown as UTF-8.")
        agents = self.documents.get(self.repo / "AGENTS.md", "")
        level = level or field(agents, "Documentation level")
        if level is not None and level not in {"L0", "L1", "L2", "L3"}:
            self.add("warning", "LEVEL_FORMAT", "AGENTS.md", "Unrecognized level label; use --level.")
            level = None
        integration = integration_branch or field(agents, "Integration branch")
        self.check_links()
        self.check_level(level)
        self.check_decisions()
        self.check_proposals()
        self.check_git(integration, field(agents, "Release branch"))
        self.findings.sort(key=lambda finding: (finding.path, finding.line, finding.code))
        return {
            "repository": str(self.repo), "level": level, "integration_branch": integration,
            "documents_checked": len(self.documents),
            "counts": {severity: sum(f.severity == severity for f in self.findings)
                       for severity in ("error", "warning", "info")},
            "findings": [asdict(finding) for finding in self.findings],
            "limitations": [
                "Local links and path existence only; fragments, symbols, and semantic drift require review.",
                "Decision provenance and proposal completion require human/agent evidence review.",
                "Git candidates use local ancestry; squash/rebase integration and remote state require review.",
            ],
        }


def audit(repo: Path, level: str | None = None, integration_branch: str | None = None) -> dict:
    return Audit(repo).run(level, integration_branch)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root (default: current directory)")
    parser.add_argument("--level", choices=("L0", "L1", "L2", "L3"))
    parser.add_argument("--integration-branch", help="Local branch used to identify integrated cleanup candidates")
    parser.add_argument("--json", action="store_true", help="Print structured findings")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    args = parser.parse_args(argv)
    if not args.repo.is_dir():
        parser.error("--repo must be an existing directory")
    try:
        report = audit(args.repo, args.level, args.integration_branch)
    except OSError as error:
        print(f"Cannot inspect repository: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for item in report["findings"]:
            where = item["path"] + (f':{item["line"]}' if item["line"] else "")
            print(f'{item["severity"].upper()} {item["code"]} {where}: {item["message"]}')
        counts = report["counts"]
        print(f'{report["documents_checked"]} documents; {counts["error"]} errors, {counts["warning"]} warnings.')
        print("Read-only mechanical audit; semantic claims and Git ownership still need review.")
    return int(bool(report["counts"]["error"] or (args.strict and report["counts"]["warning"])))


if __name__ == "__main__":
    sys.exit(main())
