# Modes

Read only the section relevant to the current request. Existing explicit user
choices and approvals remain valid; a mode does not add another approval round.

## Init

Inspect the project before calling it empty. Explain a suitable documentation
level and branch model using [conventions.md](conventions.md). Obtain the user's
choices if the request did not already provide them; a proposed default is not
approval. Documentation level and branch model can be selected independently.

Create only the selected layer's useful documents, adapting the starter assets.
An architecture or design entry needs real content, not an empty directory or a
filled-out speculative template. Keep README focused on understanding and using
the product. Put agent workflow, commands, and the document map in `AGENTS.md`.
Ignore root `.local/` without replacing existing ignore patterns; use `/.local/`
and verify with `git check-ignore`. If local logs are already tracked, propose
removing them from version control without deleting the local files.

Record the actual integration and release branch names. Create branches only as
needed by the selected model, preserving existing branches and commits. A separate
integration branch normally keeps the primary checkout. In a project without Git,
prepare the documents and explain the remaining setup; initialize Git only when
the requested setup includes it. Do not invent runtime commands or user decisions.

## Adopt

Inventory the existing README, handoff and architecture/design documents, proposal
and decision records, and agent-specific instruction files. Read relevant code
and verification evidence. Look for distinct content in `CLAUDE.md`, nested
`AGENTS.md`, and similar files before proposing changes.

Prepare a concrete migration map with source, destination, retained content,
removals, and unresolved questions. Include the proposed documentation level and
branch model if not already selected. Present the complete text and source of
each new U entry for approval; do not turn every technical choice into a user
decision. Existing approved U records can be migrated verbatim under an approved
plan without asking the user to decide them again. Keep identifiers, history, and
links intact.

Once approved, perform the migration in one `docs/` branch. Move content into the
selected structure and update incoming links. Keep existing project-specific
instructions in `AGENTS.md`. Reduce an agent-specific entrypoint to `@AGENTS.md`
only if its unique rules have been preserved and that tool supports the directive;
otherwise use its supported forwarding mechanism. Preserve nested scope rules.

Label architecture reconstructed from code **Pending confirmation**, cite the
observations behind it, and distinguish it from accepted design intent. Request
confirmation of consequential uncertain claims. Do not fabricate rationale from
the code. Remove the label only when evidence or user confirmation resolves it.

Reorganizing documents does not authorize application changes. If implementation
work becomes necessary, prepare the corresponding branch/worktree and keep the
work within existing authorization or request the missing scope.

## Upgrade

Explain the concrete pressure for the next level: repeated handoff needs, hidden
cross-file structure, or proposal/release coordination. Obtain approval for the
upgrade and any independent branch-model change before implementing them.

Add the next layer while preserving existing agreements. Move useful content
instead of rewriting its history: a system overview in HANDOFF can move into
architecture, leaving a link and the current takeover notes. Split current-state
designs from proposals only where their lifecycle differs. Update `AGENTS.md`,
document links, and the selected-level label together. Do not silently downgrade
or remove existing material.

## Audit

Run the read-only audit helper, then inspect the relevant files and code. The
helper's warnings are review candidates, not permission to change Git history or
proof of stale semantics. Check:

- Broken local links, code paths, and symbol references; verify moved targets.
- Current-state claims against relevant implementation, runtime evidence, and
  recent changes. Use `git log -- <paths>` and document history where useful.
- Terminal proposals left outside `archive/`, missing or stale index entries,
  and completed proposals whose conclusions never reached current-state docs.
- Duplicate IDs, missing decision sources, inconsistent supersession links, and
  cycles. Do not rewrite user-decision bodies to reconcile them.
- Integrated branch/worktree candidates, outstanding edits, and remote branch
  state when it is available locally. An ancestor check misses squash/rebase
  integration; inspect those cases before drawing conclusions. Do not fetch or
  delete based on a read-only audit request alone.
- Whether `AGENTS.md` can guide an agent without this skill and whether root
  `.local/` is ignored. Keep secrets out of logs.

Repair evidence-backed documentation drift within the authorized scope on a docs
branch. Preserve append-only decisions; request clarification for unresolved
intent. Archive an actually completed/cancelled/superseded proposal and update its
index only after confirming its outcome. Do not mark a proposal completed merely
to satisfy the checker. Propose needed upgrades without making them.

For multi-person or multi-machine coordination, optionally suggest a separate
private repository for collaboration logs with secret filtering. Do not create or
push that repository as part of a routine audit. A shared live work board, when
useful, belongs with the human or scheduling agent; an absolute path under the
primary checkout's ignored `.local/` is one possible location.

Conclude with what was fixed, what evidence was used, what remains uncertain, and
which actions need a decision. Keep historical proposals and process logs from
being presented as current system facts.
