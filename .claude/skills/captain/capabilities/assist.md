---
capability: assist
purpose: >
  Act as workspace domain expert on artifacts intent does not govern — project
  config, dotfiles, CLAUDE.md, tooling, scaffolding. The honest home for a
  verb-less change-prompt that targets a file no contract reaches. Mutating:
  gated by the approval gate like sync/refine/evolve.
---

# `assist`

**`assist` is the off-intent expert capability.** It acts on **ungoverned** artifacts —
files no contract names through an `artifact_path` (`FOUNDATION.md` §13): project config,
dotfiles, `CLAUDE.md`, tooling, CI, scaffolding, and **test code** (`FOUNDATION.md` §14 —
tests are artifact, governed by no contract). Intent says nothing about these by
design, so there is no intent to bypass; the agent simply acts as workspace domain
expert, gated like any mutation (§12). **Failing tests** that drifted from the artifact —
e.g. the human edited the code — are the canonical `assist` test task: fix the tests
against the current code.

It is the write-side counterpart of `explain`. `explain` answers a verb-less *question*
from the intent and, when intent is silent, returns "undetermined." `assist` handles a
verb-less *change* to a file intent was never meant to govern — and, when the target
turns out to be governed, refuses and redirects to `sync`. The six intent/framework
capabilities all stop at the intent boundary; `assist` is the residual that picks up
exactly what falls outside it, without loosening their boundaries.

**Not an intent-bypass.** The load-bearing rule is the boundary test (`FOUNDATION.md`
§13): *does an `artifact_path` name this file?* If yes, the change belongs to `sync`
forward and `assist` refuses, redirecting there. `assist` can never reach a governed
artifact — that is what keeps a flexible capability from eroding the framework.

## Trigger

```
/captain assist @prompt
/captain @prompt          # verb-less change to an ungoverned artifact → routes here (SKILL.md router)
```

- `@prompt` — a change request whose target is an ungoverned artifact: edit a config,
  fix a dotfile, update `CLAUDE.md`, adjust tooling or CI, fix failing tests against the
  current code.

## What it does

1. Identify the target file(s) from the prompt.
2. **Run the boundary test** (`FOUNDATION.md` §13): check whether any contract names the
   target via `artifact_path` (resolved through `captain.yaml` `repos:`). If one does,
   **halt and redirect to `sync`** — the change is governed and not `assist`'s to make.
3. For an ungoverned target, act as workspace domain expert: prepare the change.
4. **Propose then apply** (`FOUNDATION.md` §12) — present a concise change list (file,
   what, why) and wait for approval before writing. Longer rationale rides on stdout
   (the session is the prose channel; `assist` touches ungoverned artifacts, not intent,
   so it writes no `.trace.md` entry).

## Output

- Edits to the ungoverned artifact(s), once approved.
- A concise change list on stdout (file, what, why).
- **`--dry-run`** prints the change list and exits, writing nothing (`FOUNDATION.md` §12).
  Re-run without the flag to apply.
- **No edit to intent, governed artifact, framework, or `compliance.yaml`** — those are
  owned by `sync` / `refine` / `evolve` / `audit`.

## Completion

- The ungoverned artifact carries the change and the human has approved it; or the target
  was found governed and the request was redirected to `sync` (a valid, complete outcome
  for `assist`).

## Halt

- **The target is governed** — an `artifact_path` names it. Redirect to `sync` forward and
  stop. This is the primary halt: it is what makes `assist` safe.
- The prompt is a **question**, not a change → `explain` (workspace) or `help` (CAPTAIN).
- The prompt proposes a change to **intent** → `refine` or `sync intent`; to the
  **framework** → `evolve`; to **epoch structure** (`epoch.md`, epoch folders, `explore:` in
  `captain.yaml`) → `explore`. Epoch structure is not an ungoverned artifact — it is
  `explore`'s, and the boundary test does not apply to it.
- Material uncertainty about which file the prompt targets, or whether it is governed —
  ask one disambiguation question, then dispatch.

## Boundary

- **Ungoverned artifacts only, and gated.** `assist` writes only to files no contract
  reaches, and only after approval (§12). The governed artifact is `sync`'s; intent is
  `sync`/`refine`'s; the framework is `evolve`'s; `compliance.yaml` is `audit`'s; epoch
  structure is `explore`'s. Crossing
  into any of those is a router error — and for the governed artifact specifically, the
  boundary test catches it before any write.
