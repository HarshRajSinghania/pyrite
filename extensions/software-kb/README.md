# software-kb extension

The software-kb extension adds the types, commands, and workflows for managing a software project's knowledge base with Pyrite. It is used with the `software` template (`pyrite init --template software`).

## Install

From a clone of the Pyrite repository:

```bash
pip install -e extensions/software-kb
```

See also the note in [docs/getting-started.md](../../docs/getting-started.md).

## Types the software template declares

- **adr** — Architecture Decision Record (with status and adr_number).
- **design_doc** — Design document or specification.
- **standard** — Coding standard or convention.
- **programmatic_validation** — Programmatic check with pass/fail criteria.
- **development_convention** — Judgment-based development guidance.
- **component** — Module or service documentation.
- **backlog_item** — Work item with status and priority (the main workflow type). Epic is a backlog_item with `kind: epic`.
- **runbook** — Operational procedure.
- **milestone** — Project milestone.
- **work_log** — Record of work done on an item.

## Backlog lifecycle

Backlog items start as `proposed`. Valid transitions (via `pyrite sw transition <id> <to> -k <kb>` or the dedicated claim/submit/review commands). Transitions marked *reason* require `--reason`:

| From          | To           | Command / note                                      |
|---------------|--------------|-----------------------------------------------------|
| proposed      | planned      | `sw transition`                                     |
| proposed      | accepted     | `sw transition`                                     |
| planned       | accepted     | `sw transition`                                     |
| accepted      | in_progress  | `sw claim --assignee/-a <name>`                     |
| in_progress   | review       | `sw submit`                                         |
| in_progress   | done         | `sw transition`                                     |
| review        | done         | `sw review <id> -o approved --reviewer <name>`      |
| review        | in_progress  | `sw review <id> -o changes_requested --reviewer <name> --feedback <text>` *reason* |
| done          | retired      | `sw transition`                                     |
| proposed      | deferred     | `sw transition`                                     |
| planned       | deferred     | `sw transition`                                     |
| deferred      | proposed     | `sw transition`                                     |
| proposed      | wont_do      | `sw transition` *reason*                            |
| accepted      | wont_do      | `sw transition` *reason*                            |
| accepted      | proposed     | `sw transition` *reason*                            |
| accepted      | deferred     | `sw transition`                                     |
| done          | accepted     | `sw transition` *reason* (reopen)                   |
| in_progress   | accepted     | `sw transition` *reason* (unclaim)                  |

## Dependencies (blocked_by / blocks)

An item can be blocked by another via a link:

```bash
pyrite link <item> <blocker> -r blocked_by -k <kb>
```

The inverse relation is `blocks`.

- `sw pull-next` skips blocked items and lists them under `blocked_items`.
- today the CLI `sw claim` does not refuse a blocked item; see #1288. MCP `sw_claim` refuses a blocked item.
- `sw context-for-item` includes the dependency information in the context bundle.

## `sw` commands

Run `pyrite sw --help` for the full list. One-line summaries:

- `sw adrs` — List Architecture Decision Records.
- `sw new-adr` — Create a new ADR.
- `sw backlog` — List backlog items (filter by status, etc.).
- `sw epics` — List epics (backlog items with kind: epic).
- `sw epic` — Show details of an epic.
- `sw prioritize` — Adjust priorities.
- `sw standards` — List standards (validations + conventions).
- `sw validations` — List programmatic validations.
- `sw conventions` — List development conventions.
- `sw migrate-standards` — Migrate older standards format.
- `sw milestones` — List milestones with stats.
- `sw board` — Show the kanban board.
- `sw review-queue` — Items waiting for review.
- `sw claim` — Claim an accepted item (moves to in_progress; requires --assignee).
- `sw submit` — Submit an in_progress item for review.
- `sw transition` — Transition an item to a new status.
- `sw pull-next` — Recommend the next unblocked accepted item.
- `sw review` — Record a review outcome (requires --reviewer; changes_requested needs --feedback).
- `sw log` — Log a work session against an item.
- `sw components` — List component docs.
- `sw check-ready` — Check Definition of Ready for an item.
- `sw refine` — Scan backlog for DoR gaps.
- `sw context-for-item` — Full context bundle for an item (ADRs, components, deps, etc.).
