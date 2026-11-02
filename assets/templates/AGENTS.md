# Project working agreements

Documentation level: {{level}}
Branch model: {{simple, integration, or full Git Flow}}
Integration branch: {{actual branch}}
Release branch: {{actual branch; omit when the same as integration}}

## Start and verify

Read the documents relevant to the task: {{short reading order and document map}}.
Current behavior is documented in {{applicable HANDOFF, architecture, and design
paths}}. Proposals record plans and historical outcomes.

Run: {{verified setup/run commands}}
Check: {{verified verification commands}}

## Documentation

Complete implementation and its documentation together within the authorized
task. Resolve conflicts using effective explicit user decisions, then code and
runtime evidence, then other documents. Distinguish intended constraints from
implemented behavior. Correct resolvable drift; ask about unresolved intent.
Document rationale, hidden constraints, and cross-file understanding using code
paths or symbols instead of duplicating obvious code details.

Keep current-state documents aligned with this branch. Rewrite HANDOFF as a
takeover checklist; use commits and ignored root `.local/` for process history.
Keep live parallel assignments out of HANDOFF. Propose documentation-level
upgrades with reasons and obtain approval; do not upgrade automatically.

{{Keep the next two paragraphs only at applicable levels.}}
Record only explicit user decisions in `docs/decisions.md` as sourced U IDs. Append
new entries without changing old bodies or reusing IDs. A replacement links both
ways; the only edit to the old entry is its supersession annotation. Record a
clear user replacement directly; clarify ambiguous conflicts or inferred intent.

Give each proposal a P ID, a status, and an entry in {{proposal index}}. Use draft,
accepted, deferred, completed, cancelled, or superseded. Archive terminal proposals;
{{deferred placement rule}}. On completion, put implemented conclusions in the
current-state design or architecture docs and retain the proposal as history.
Coordinate ID allocation with {{project practice}} before parallel work.

## Branch procedure

Create a short task branch from {{integration}}, using feature/, fix/, or docs/
and a relevant P ID. {{Full Git Flow only: release/ starts at integration; hotfix/
starts at the release branch.}}
{{State whether code work requires a worktree. If it does: use
../<repo>-<description>/ and initialize with the verified commands below; leave
the primary checkout on integration. Docs-only work uses one docs/ branch without
a worktree unless requested. Move to a suitable branch/worktree if code changes
become necessary.}}
Worktree initialization: {{verified commands, or no setup required}}

Commit code and affected docs on the same branch; summarize implementation and
reference related P/U IDs in commit bodies. {{Separate integration model: merge
into integration with --no-ff when authorized; summarize the branch in the merge
commit.}}
Main/master merges, pushes, tags, and remote branch deletions need authorization;
honor authorization already given. {{Full Git Flow only: integrate approved
release/hotfix branches into the release branch, tag the approved version, and
merge back into integration.}}

After the authorized merge, verify integration and clean worktree status, return
the primary checkout to integration, remove the task worktree without force,
delete its local branch with `git branch -d`, delete its remote branch if
authorized, then run `git worktree prune`. Investigate failed safe deletion; never
substitute `-D` or discard another session's work. Keep process logs in the primary
checkout's ignored `.local/`, so removing a worktree cannot lose them.
