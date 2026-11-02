"""Observable behavior checks using disposable repositories; no network access."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from audit import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="project-docs-test-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "project"
        self.repo.mkdir()
        self.environment = patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.write("AGENTS.md", "# Agreements\nDocumentation level: L1\nIntegration branch: main\n")
        self.write("README.md", "# A project\n")
        self.write("docs/HANDOFF.md", "# Current handoff\n")
        self.write("docs/decisions.md", "# User decisions\n")
        self.write(".gitignore", "/.local/\n")

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def codes(self, **kwargs):
        return {finding["code"] for finding in audit(self.repo, **kwargs)["findings"]}

    def decisions(self, text):
        self.write("docs/decisions.md", text)

    def proposals(self, status="draft", archived=False, index_status=None):
        name = ("archive/" if archived else "") + "P-001-export.md"
        self.write("docs/proposals/" + name, f"# P-001 — Export\n\nStatus: {status}\n")
        self.write("docs/proposals/README.md",
                   "# Proposals\n\n| ID | Status | Document |\n| --- | --- | --- |\n"
                   f"| P-001 | {index_status or status} | [Export]({name}) |\n")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout

    def initialize_git(self):
        if not shutil.which("git"):
            self.skipTest("Git is not installed")
        self.git("-c", "init.templateDir=", "init", "-q", "-b", "main")
        self.git("add", ".")
        self.commit("Initial fixture")

    def commit(self, message):
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}",
                 "commit", "-q", "-m", message)

    def snapshot(self):
        root = Path(self.temporary.name)
        return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob("*") if path.is_file()}

    def test_valid_minimal_project_has_no_actionable_findings(self):
        result = audit(self.repo)
        self.assertEqual(result["counts"]["error"], 0)
        self.assertEqual(result["counts"]["warning"], 0)
        self.assertEqual(result["level"], "L1")

    def test_selected_level_checks_its_own_required_documents(self):
        (self.repo / "docs/HANDOFF.md").unlink()
        self.assertIn("LEVEL_FILE_MISSING", self.codes())
        self.assertNotIn("LEVEL_FILE_MISSING", self.codes(level="L0"))
        self.assertIn("LEVEL_CONTENT_MISSING", self.codes(level="L2"))

    def test_local_links_support_encoded_paths_titles_and_fragments(self):
        self.write("docs/with space.md", "# Target\n")
        self.write("README.md", '[Target](docs/with%20space.md#target "title")\n'
                   '[Target](<docs/with space.md>)\n[Here](#get-started)\n')
        self.assertNotIn("LINK_MISSING", self.codes())

    def test_missing_links_images_and_reference_definitions(self):
        self.write("README.md", "[Guide](docs/missing.md)\n![Diagram](docs/missing.png)\n"
                   "[Reference][guide]\n[guide]: docs/also-missing.md\n")
        findings = [f for f in audit(self.repo)["findings"] if f["code"] == "LINK_MISSING"]
        self.assertEqual(len(findings), 3)
        self.assertEqual({f["line"] for f in findings}, {1, 2, 4})

    def test_fenced_and_inline_link_examples_are_not_live_links(self):
        self.write("README.md", "```markdown\n[example](missing.md)\n```\n"
                   "~~~text\n`docs/missing.py`\n~~~\n`[literal](missing.md)`\n")
        self.assertNotIn("LINK_MISSING", self.codes())
        self.assertNotIn("CODE_PATH_MISSING", self.codes())

    def test_external_and_outside_repository_links_are_not_read(self):
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("PRIVATE FIXTURE CONTENT", encoding="utf-8")
        self.write("README.md", "[Outside](../outside.md)\n[Web](https://example.invalid/page)\n")
        report = audit(self.repo)
        self.assertIn("LINK_OUTSIDE_REPO", {f["code"] for f in report["findings"]})
        self.assertNotIn("PRIVATE FIXTURE CONTENT", json.dumps(report))

    def test_symbolic_link_cannot_expand_markdown_scan_outside_repository(self):
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("[Should never be inspected](missing.md)", encoding="utf-8")
        (self.repo / "docs/external.md").symlink_to(outside)
        self.assertNotIn("LINK_MISSING", self.codes())

    def test_code_path_checks_accept_root_paths_and_line_numbers(self):
        self.write("src/service.py", "pass\n")
        self.write("docs/HANDOFF.md", "See `src/service.py:1` and `src/moved.py`.\n")
        findings = [f for f in audit(self.repo)["findings"] if f["code"] == "CODE_PATH_MISSING"]
        self.assertEqual(len(findings), 1)
        self.assertIn("src/moved.py", findings[0]["message"])

    def test_starter_templates_are_not_audited_as_current_records(self):
        self.write("assets/templates/example.md", "[Future](missing.md)\n")
        self.assertNotIn("LINK_MISSING", self.codes())

    def test_valid_sourced_replacement_preserves_records(self):
        self.decisions("## U-01 — First\nSource: User message 2026-01-01\n"
                       "Superseded by: U-02\n\nOriginal immutable decision.\n\n"
                       "## U-02 — Replacement\nSource: User message 2026-02-01\n"
                       "Supersedes: U-01\n\nNew explicit decision.\n")
        before = self.snapshot()
        self.assertEqual(audit(self.repo)["counts"]["error"], 0)
        self.assertEqual(before, self.snapshot())

    def test_missing_decision_source_is_a_review_warning(self):
        self.decisions("## U-01 — First\nAn unsupported decision.\n")
        self.assertIn("DECISION_SOURCE_MISSING", self.codes())

    def test_missing_reciprocal_supersession_is_an_error(self):
        self.decisions("## U-01 — First\nSource: message A\n\n"
                       "## U-02 — Second\nSource: message B\nSupersedes: U-01\n")
        self.assertIn("DECISION_RECIPROCAL_MISSING", self.codes())

    def test_missing_supersession_target_is_an_error(self):
        self.decisions("## U-01 — First\nSource: message A\nSuperseded by: U-99\n")
        self.assertIn("DECISION_TARGET_MISSING", self.codes())

    def test_decision_cycles_are_rejected_even_when_reciprocal(self):
        self.decisions("## U-01 — First\nSource: message A\nSupersedes: U-02\nSuperseded by: U-02\n"
                       "## U-02 — Second\nSource: message B\nSupersedes: U-01\nSuperseded by: U-01\n")
        self.assertIn("DECISION_CYCLE", self.codes())

    def test_duplicate_decision_ids_are_rejected(self):
        self.decisions("## U-01 — First\nSource: A\n## U-01 — Another\nSource: B\n")
        self.assertIn("DECISION_DUPLICATE", self.codes())

    def test_completed_archived_proposal_with_matching_index_passes(self):
        self.proposals("completed", archived=True)
        self.assertEqual(audit(self.repo)["counts"]["error"], 0)

    def test_terminal_proposal_must_be_archived(self):
        for status in ("completed", "cancelled", "superseded"):
            with self.subTest(status=status):
                self.proposals(status)
                self.assertIn("PROPOSAL_NOT_ARCHIVED", self.codes())

    def test_active_proposal_cannot_be_archived(self):
        self.proposals("accepted", archived=True)
        self.assertIn("PROPOSAL_ACTIVE_ARCHIVED", self.codes())

    def test_deferred_proposal_can_use_either_location(self):
        for archived in (True, False):
            with self.subTest(archived=archived):
                if (self.repo / "docs/proposals").exists():
                    shutil.rmtree(self.repo / "docs/proposals")
                self.proposals("deferred", archived=archived)
                self.assertEqual(audit(self.repo)["counts"]["error"], 0)

    def test_proposal_status_must_match_index(self):
        self.proposals("accepted", index_status="draft")
        self.assertIn("PROPOSAL_INDEX_STATUS", self.codes())

    def test_missing_index_and_missing_rows_are_distinguished(self):
        self.proposals()
        (self.repo / "docs/proposals/README.md").unlink()
        self.assertIn("PROPOSAL_INDEX_MISSING", self.codes())
        self.write("docs/proposals/README.md", "| ID | Status | Document |\n| --- | --- | --- |\n")
        self.assertIn("PROPOSAL_NOT_INDEXED", self.codes())

    def test_index_link_must_point_to_the_matching_proposal(self):
        self.proposals()
        self.write("docs/proposals/other.md", "# P-002 — Another\nStatus: draft\n")
        self.write("docs/proposals/README.md", "| ID | Status | Document |\n| --- | --- | --- |\n"
                   "| P-001 | draft | [Wrong](other.md) |\n| P-002 | draft | [Other](other.md) |\n")
        self.assertIn("PROPOSAL_INDEX_TARGET", self.codes())

    def test_duplicate_proposals_and_index_entries_are_rejected(self):
        self.proposals()
        self.write("docs/proposals/duplicate.md", "# P-001 — Duplicate\nStatus: draft\n")
        path = self.repo / "docs/proposals/README.md"
        path.write_text(path.read_text() + "| P-001 | draft | [Again](duplicate.md) |\n")
        codes = self.codes()
        self.assertIn("PROPOSAL_DUPLICATE", codes)
        self.assertIn("PROPOSAL_INDEX_DUPLICATE", codes)

    def test_malformed_index_url_reports_findings_instead_of_crashing(self):
        self.proposals()
        self.write("docs/proposals/README.md", "| ID | Status | Document |\n| --- | --- | --- |\n"
                   "| P-001 | draft | [Invalid](http://[) |\n")
        self.assertIn("PROPOSAL_INDEX_TARGET", self.codes())

    def test_proposals_require_a_recognized_status(self):
        self.proposals("finished-maybe")
        self.assertIn("PROPOSAL_STATUS", self.codes())

    def test_local_logs_must_be_ignored_and_not_tracked(self):
        self.initialize_git()
        self.assertNotIn("LOCAL_NOT_IGNORED", self.codes())
        self.write(".gitignore", "")
        self.write(".local/session.txt", "process data\n")
        self.git("add", ".local/session.txt")
        codes = self.codes()
        self.assertIn("LOCAL_NOT_IGNORED", codes)
        self.assertIn("LOCAL_TRACKED", codes)

    def test_git_audit_preserves_dirty_worktree_branches_and_git_metadata(self):
        self.initialize_git()
        worktree = Path(self.temporary.name) / "task-worktree"
        self.git("worktree", "add", "-q", "-b", "docs/integrated", str(worktree), "main")
        (worktree / "untracked.txt").write_text("unsaved collaboration work\n")
        before = self.snapshot()
        refs = self.git("show-ref")
        trees = self.git("worktree", "list", "--porcelain")
        report = audit(self.repo)
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("MERGED_BRANCH", codes)
        self.assertIn("MERGED_WORKTREE", codes)
        self.assertTrue(any("dirty" in f["message"] for f in report["findings"] if f["code"] == "MERGED_WORKTREE"))
        self.assertEqual(before, self.snapshot())
        self.assertEqual(refs, self.git("show-ref"))
        self.assertEqual(trees, self.git("worktree", "list", "--porcelain"))

    def test_unintegrated_branch_is_not_a_cleanup_candidate(self):
        self.initialize_git()
        self.git("switch", "-q", "-c", "fix/unfinished")
        self.write("unfinished.txt", "unique work\n")
        self.git("add", "unfinished.txt")
        self.commit("Unique unfinished work")
        self.git("switch", "-q", "main")
        self.assertNotIn("MERGED_BRANCH", self.codes())

    def test_git_ignored_documents_are_not_scanned(self):
        self.initialize_git()
        self.write(".gitignore", "/.local/\n/generated/\n")
        self.write("generated/output.md", "[Ignored](missing.md)\n")
        self.assertNotIn("LINK_MISSING", self.codes())

    def test_prunable_worktree_is_reported_without_pruning(self):
        self.initialize_git()
        worktree = Path(self.temporary.name) / "removed-worktree"
        self.git("worktree", "add", "-q", "-b", "docs/old", str(worktree), "main")
        shutil.rmtree(worktree)
        before = self.snapshot()
        self.assertIn("STALE_WORKTREE", self.codes())
        self.assertEqual(before, self.snapshot())

    def test_existing_dev_branch_is_preserved_and_detected(self):
        self.initialize_git()
        self.git("branch", "-m", "dev")
        self.write("AGENTS.md", "Documentation level: L1\nIntegration branch: `dev`\n")
        branches = self.git("branch", "--format=%(refname:short)")
        report = audit(self.repo)
        self.assertEqual(report["integration_branch"], "dev")
        self.assertNotIn("INTEGRATION_MISSING", {f["code"] for f in report["findings"]})
        self.assertEqual(branches, self.git("branch", "--format=%(refname:short)"))

    def test_cli_json_exit_codes_and_argument_errors(self):
        command = [sys.executable, str(Path(__file__).with_name("audit.py")), "--repo", str(self.repo), "--json"]
        self.write("docs/HANDOFF.md", "See `src/missing.py`.\n")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["counts"]["warning"], 1)
        strict = subprocess.run([*command, "--strict"], capture_output=True, text=True)
        self.assertEqual(strict.returncode, 1)
        self.write("README.md", "[Broken](missing.md)\n")
        failed = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(failed.returncode, 1)
        invalid = subprocess.run([*command, "--level", "L9"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)


if __name__ == "__main__":
    unittest.main()
