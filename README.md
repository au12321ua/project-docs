# Project Docs

An English agent skill for setting up, adopting, upgrading, and auditing project
documentation and branch conventions. The result is a compact project `AGENTS.md`
that other agents can follow without installing this skill.

The repository root is the skill folder. Its structure follows OpenAI's
[skill documentation](https://learn.chatgpt.com/docs/build-skills): a focused
`SKILL.md`, optional UI metadata, references loaded when needed, starter templates,
and a deterministic helper for mechanical checks.

## What it does

- Separates current system facts, proposals and their outcomes, process history,
  and explicit user decisions.
- Offers four cumulative documentation levels, from a small script's working
  agreements to architecture, design, and indexed proposals.
- Keeps documentation levels independent of simple branches, an integration
  branch, or full Git Flow. Preserves actual `dev`/`develop` names.
- Preserves project instructions and decision history during migration.
- Keeps HANDOFF aligned with its branch's code and out of live task scheduling.
- Repairs evidence-backed documentation drift within scope and reports unresolved
  intent, without inventing user decisions or automatically upgrading a project.

## Install for your user

Ask Codex's built-in installer:

```text
Use $skill-installer to install au12321ua/project-docs from repository path ".",
branch "master", named "project-docs", into ~/.agents/skills.
```

Or, after cloning this repository, run from its root:

```bash
mkdir -p "$HOME/.agents/skills"
ln -s "$PWD" "$HOME/.agents/skills/project-docs"
```

The symlink command fails if that name already exists; inspect an existing install
before replacing it. Codex supports symlinked skill folders. The skill is available
on your next turn; restart Codex if it does not appear. For one project, place the
skill folder in that project's `.agents/skills/project-docs/` instead.

The core skill needs no API key or additional skill. Its optional audit helper
requires Python 3.10+ and uses Git for repository checks. It has no Python package
dependencies.

## Use

```text
Use $project-docs to initialize this project at L1 with simple branches on main.
```

```text
Use $project-docs to adopt these conventions in this repository. Inspect the
existing rules and documents, then prepare the migration plan and any proposed
user-decision entries for my review.
```

```text
Use $project-docs to upgrade this project from L1 to L2. Keep our current simple
branch model. The upgrade is approved.
```

```text
Use $project-docs to audit documentation drift. Fix issues supported by the code
and existing decisions, and report contradictions you cannot resolve.
```

Init needs a chosen level and branch model; adopt needs an approved migration and
each proposed U entry; upgrade needs approval. Choices and authorization already
given in the conversation count. Audit allows evidence-backed documentation fixes
within the requested scope. Publication, release operations, and branch deletion
follow the user's existing authorization.

## Mechanical audit

```bash
python3 scripts/audit.py --repo /path/to/project --json
python3 scripts/audit.py --repo /path/to/project --level L2 --integration-branch dev --strict
```

The helper reports broken local Markdown targets, missing inline code paths,
level-specific documents, proposal status/index/archive inconsistencies, decision
supersession errors, ignored-log problems, and local Git cleanup candidates. It
reads Git-tracked and untracked, nonignored Markdown, or scans files if Git is
unavailable. Dependency directories, `.local/`, and starter `templates/` directories
are excluded. It does not edit, fetch, merge, delete, or access the network.

Exit codes are `0` for no errors, `1` for errors (also warnings with `--strict`),
and `2` for invalid arguments or an inspection failure. JSON includes findings,
severity counts, and limitations. Code examples in fenced blocks are ignored.

The expected starter labels are shown in
[conventions](references/conventions.md). Existing project formats can require
manual review. Link fragments, symbol validity, semantic drift, decision provenance,
actual proposal completion, and squash/rebase integration require agent review;
path existence and Git ancestry cannot establish those facts.

## Maintain

```bash
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

Tests use disposable local repositories, including real worktrees, to verify
findings and ensure audits preserve files, Git metadata, branches, and worktrees.
Use the built-in `skill-creator` validator for manifest validation as well.
Behavioral review still needs realistic agent use; static validation and helper
tests do not prove the skill will make every documentation decision correctly.

The original [design](design.md) is retained as the implementation input.
