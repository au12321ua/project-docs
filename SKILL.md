---
name: project-docs
description: >-
  Initialize, adopt, upgrade, or audit a repository's project documentation and
  branch conventions. Use for documentation-system setup, handoff and decision
  records, or documentation drift checks; not routine prose edits or design
  proposals alone.
---

# Project Docs

Make a repository understandable across sessions and agents. The durable result
is a short, project-specific `AGENTS.md`: an agent without this skill must be able
to maintain the documentation and finish the chosen branch workflow from it.

## Establish the mode and scope

Read the applicable repository instructions, relevant documents, Git status,
branches, and worktrees. Inspect enough code and verification evidence to ground
claims about the current system. Preserve unrelated edits and project-specific
instructions. Follow the user's requested language; the starter templates are
English.

| Mode | Use when | Decision needed before changing the project |
| --- | --- | --- |
| init | Establishing conventions in a new project | Documentation level and branch model |
| adopt | Bringing an existing project into these conventions | Concrete migration plan, including removals, and each proposed user-decision entry |
| upgrade | Adding the next documentation layer | The upgrade and any branch-model change |
| audit | Checking existing documentation and collaboration conventions | None for evidence-backed fixes within the authorized task |

Read [references/modes.md](references/modes.md) for the selected mode. An explicit
choice or approval already present in the conversation satisfies the matching
decision requirement; do not ask again. Prepare a concrete plan or proposed
decision text before requesting a missing approval. Continue independent
inspection while awaiting it, but do not make dependent changes.

## Apply the shared rules

- Resolve contradictions using effective, explicit user decisions first, then
  code and runtime evidence, then other documents. A decision can prescribe a
  future state: record an implementation gap rather than describe it as deployed.
  Correct stale documentation directly within scope. Ask only when the available
  decisions, task, and evidence cannot resolve a consequential contradiction.
- Separate current state, plans and their outcomes, process history, and user
  constraints. Document rationale, rejected alternatives, hidden constraints, and
  cross-file understanding. Prefer code paths or symbols to duplicated signatures
  and configuration inventories.
- Record only explicit user decisions as `U-01`, `U-02`, and so on, with a source
  quote or durable conversation reference. Confirm inferred intent before recording
  it. Never promote agent choices or approvals of an unrelated task into user
  constraints. Preserve existing entry bodies and numbers; append new decisions.
  The one permitted edit to an old entry is its supersession annotation. Link both
  directions. When the user clearly replaces a decision, append the replacement
  directly and report it; ask about an ambiguous conflict before acting on it.
- Give every proposal a unique `P-001`-style ID, a status, and an index entry.
  Distinguish draft, accepted, deferred, completed, cancelled, and superseded.
  Archive completed, cancelled, and superseded proposals; document where deferred
  proposals live. Before completing a proposal, put its implemented conclusions
  into the relevant current-state design or architecture documents. Keep historical
  rationale in the archived proposal.
- Commit documentation and the changes it describes on the same branch and merge
  them together. Rewrite HANDOFF to describe the code on that branch; keep process
  history in commits and ignored `.local/` logs. HANDOFF is never a live assignment
  board for parallel branches.
- Add only the documentation layer the user selected. Propose a justified upgrade
  when needed; do not upgrade on the user's behalf. Preserve the existing content
  when moving it, using links in place of duplicate authorities.

Read [references/conventions.md](references/conventions.md) when choosing levels,
placing content, or configuring branches. Start from only the applicable files in
[assets/templates/](assets/templates/). Adapt them to the repository; template
headings, lengths, and example identifiers are not mandatory project structure.

## Leave self-sufficient repository instructions

Preserve the project's own `AGENTS.md` sections. Add a compact convention block
covering the selected level and actual branch names, task-relevant reading order,
documentation map, verified run/check commands, decision and proposal rules,
documentation synchronization, approval boundaries, and branch cleanup. Include
worktree location and initialization commands when worktrees are used. Inline the
rules an uninstalled agent needs; do not make it fetch this skill.

Use a single integration-branch name consistently. `dev` and `develop` are spelling
choices, not two branches that must both exist. Preserve an established name;
otherwise propose `develop` when a separate integration branch is selected.

Work in a short-lived branch. In the chosen worktree model, create a separate
worktree for code changes, normally at `../<repo>-<description>/`; keep a docs-only
adoption in one `docs/` branch without a worktree unless requested. If that work
requires code changes, move the work to an appropriate branch and worktree.
Use the chosen integration branch as the base, except hotfixes start at the release
branch. Do not switch a dirty primary checkout or move another session's work.

Merge into a separate integration branch with `--no-ff` when authorized. Merging
into `main`/`master`, pushing, tagging, and deleting remote branches require the
user's authorization, which may already cover the task. Describe the whole branch
in the merge commit; reference relevant P/U IDs in commit bodies. For full Git
Flow, merge releases and hotfixes into the release branch, tag the approved
version, and merge back into the integration branch.

After an authorized merge, verify the branch is integrated and its worktree is
clean. Return the primary checkout to the integration branch when applicable,
then remove the task worktree, delete the local branch with `git branch -d`, delete
its remote branch if authorized, and prune stale worktree registrations. Inspect
a failed safe deletion; never substitute `-D`. Keep logs in the primary checkout's
`.local/` so worktree removal cannot discard them. Audit findings alone do not
authorize deletion of someone else's branch or worktree.

## Verify the result

For a mechanical check, run the bundled read-only helper:

```bash
python3 <skill-dir>/scripts/audit.py --repo <repository> --json
```

The helper checks local Markdown targets and code-path references, selected-level
files, proposal lifecycle/index consistency, decision supersession links, and
Git cleanup candidates. Use `--integration-branch <name>` or `--level L0` through
`L3` when the corresponding `AGENTS.md` labels cannot be detected. `--strict`
makes warnings fail as well as errors. It never edits files, fetches, merges, or
deletes branches. Re-run it after related fixes.

Complete the semantic review yourself: a path that still exists can describe
substantially changed code, an indexed proposal may be unfinished, and a sourced
decision still needs to match the user's words. Review history where helpful;
do not claim the script establishes semantic correctness.

Report the selected mode and level, material changes, validation performed,
unresolved conflicts or approvals, and the actual branch/worktree state. For an
audit, separate repaired issues from findings that need a user decision. Do not
claim integration, publication, or cleanup that did not occur.
