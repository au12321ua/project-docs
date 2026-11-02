# Documentation and branch conventions

## Choose independent levels and branch models

Each level adds a layer; it does not discard the previous level's agreements.
Record `Documentation level: L<n>` near the start of `AGENTS.md`. Level labels
describe a project convention, not a Codex feature.

| Level | Adds | Typical reason | Common branch pairing |
| --- | --- | --- | --- |
| L0 | AGENTS, README, ignored `.local/`, commit convention | Script or prototype | Simple |
| L1 | `docs/HANDOFF.md`, `docs/decisions.md` | Work spans sessions; users set durable constraints | Simple |
| L2 | `docs/architecture/`, `docs/design/` | Important understanding spans many files | Integration |
| L3 | `docs/proposals/` with an index and archive | Parallel plans, design approval, versioned releases | Full Git Flow |

An empty decisions file is valid until the user makes a decision worth retaining.
At L2/L3, write useful initial architecture/design content based on evidence;
do not manufacture facts to fill templates. Propose an upgrade if the selected
level cannot express the requested work adequately.

The common pairing is a starting point. A small project can need release branches,
and a large project can keep a simple branch model if the user chooses it.

| Branch model | Integration branch | Release branch | Working convention |
| --- | --- | --- | --- |
| Simple | Existing `main` or `master` | Same branch | Short task branches; worktrees optional |
| Integration | Existing or selected `develop`/`dev` | Existing `main`/`master` | Code in task worktrees; docs in a docs branch |
| Full Git Flow | Existing or selected `develop`/`dev` | Existing `main`/`master` | Integration model plus release/hotfix branches and version tags |

Record `Integration branch: <actual-name>` and, where distinct,
`Release branch: <actual-name>`. The helper also accepts backticks around values.
Preserve `dev` if it already serves as integration; otherwise propose `develop`.
Never normalize one spelling by creating a second integration branch.

Use `feature/`, `fix/`, `docs/`, `release/`, or `hotfix/` task prefixes. Include a
proposal ID when relevant, such as `feature/P-003-report-export`. Release versions
and tag names come from the project; never infer a release from a documentation
change.

## Place content by lifecycle

| Location | Answers | Maintenance |
| --- | --- | --- |
| `AGENTS.md` | How should an agent work here? | Short entrypoint with map, commands, agreements, and actual branch procedure |
| `README.md` | What is this project and how do I use it? | Human-facing product/use information |
| `docs/HANDOFF.md` | What do I need to take over this code? | Rewrite for this branch's current capabilities, checks, pitfalls, and useful next work |
| `docs/architecture/` | How does the whole system fit together? | Current boundaries, flows, invariants, and dependencies |
| `docs/design/` | Why does this feature work this way now? | Current intent, constraints, tradeoffs, and cross-file behavior |
| `docs/proposals/` | What is planned and what happened to earlier plans? | Status on every proposal; index all proposals; retain terminal history in `archive/` |
| `docs/decisions.md` | What explicit rules did the user decide? | Append-only U entries with sources and supersession annotations |
| Commit bodies | What changed and why in this change? | Implementation summary and relevant P/U references |
| Root `.local/` | How was this work carried out? | Ignored process logs, never the authority for current behavior |

HANDOFF is a takeover checklist, not a chronological journal or an allocation of
parallel tasks. Worktree copies cannot provide a complete live task board. Useful
candidate follow-up work can appear there; developed plans belong in proposals.
Use `git worktree list` and `git branch --no-merged <integration>` as partial
coordination clues, not a complete scheduler.

## Decision records

Use ascending, never-reused U IDs with at least two digits. Preserve existing IDs.
Each entry needs the actual user decision and traceable original words or a
durable conversation link. A migration plan's approval is not approval for
agent-inferred constraints hidden within it.

The bundled template uses `## U-01 — <title>`, `Source:`, `Supersedes:`, and
`Superseded by:` labels. `none` is valid for an absent relationship. For a new
replacement, append its entry with `Supersedes: U-01` and annotate the old entry
with `Superseded by: U-02`; leave the old decision body unchanged. A new decision
can replace multiple old entries. If the project already has an equally clear
format, preserve it and review any helper format warnings manually.

Before allocating P/U numbers, inspect the integrated records and outstanding
branches. For parallel work, reserve the next IDs in a small docs branch and
integrate it immediately when authorized, or use the project's existing allocator.
Never renumber already published records to resolve a collision silently.

## Proposal lifecycle

Use P IDs with at least three digits. The starter format uses
`# P-001 — <title>` and `Status: draft` (or another status below). The helper
recognizes these English labels case-insensitively; adapt manually for an
established format rather than replacing project conventions to satisfy a script.

| Status | Meaning | Placement |
| --- | --- | --- |
| draft | Under discussion | Active proposal directory |
| accepted | Approved plan, possibly in progress | Active proposal directory |
| deferred | Deliberately postponed | Project-selected active or archived location |
| completed | Implemented and conclusions integrated into current-state docs | `archive/` |
| cancelled | Abandoned, with reason | `archive/` |
| superseded | Replaced by a linked proposal | `archive/` |

Use `docs/proposals/README.md` as the default index, or retain an existing
`index.md`. List every proposal's ID, current status, and link, including archived
ones. The helper expects a Markdown table with `ID`, `Status`, and `Document`
columns in any order. Explain deferred placement in the index. Keep the plan's
outcome and rationale when archiving; current-state docs become authoritative for
the implemented behavior.

## Finish a branch without losing work

Write the selected model's procedure directly into `AGENTS.md`, including real
initialization and verification commands. If the project needs no initialization,
say so after inspecting it. Keep the primary checkout on integration when using
worktrees. Docs-only work can temporarily use a docs branch there if clean and
not owned by another session.

Before cleanup, verify the requested merge occurred, inspect the task worktree's
status, and verify the branch tip is reachable from integration. For squash/rebase
integration, examine the actual integration and preserve the original branch if
safe deletion cannot establish it. Never delete a branch with unique work just to
complete a cleanup checklist.

Remove a clean task worktree, delete its integrated local branch with `-d`, delete
its remote branch only within authorization, and run `git worktree prune`. Use
`git worktree remove` without force. A failure is evidence to investigate. Do not
delete another session's worktree or arbitrary old branches. No automatic fetch,
push, main/master merge, release, or tag is implied by applying this skill.
