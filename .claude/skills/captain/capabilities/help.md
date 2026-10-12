---
capability: help
purpose: >
  Describe CAPTAIN itself — what the framework is, the capabilities it offers,
  and the core concepts of FOUNDATION.md. Read-only: it orients, never changes
  anything. Its subject is the framework, not the workspace.
---

# `help`

**`help` is the self-describing capability.** It answers "what is CAPTAIN and what can
it do" from the framework files alone, and mutates nothing — not artifact, not intent,
not framework, not `compliance.yaml` (`FOUNDATION.md` §12). Its only output is the
description on stdout.

It is the sibling of `explain`, split by subject: `explain` describes **the workspace**
(its intent); `help` describes **CAPTAIN** (the framework — `SKILL.md` and
`FOUNDATION.md`). Neither reads the artifact repos.

## Trigger

```
/captain help
```

- Takes no parameters. Any trailing tokens are ignored.

## What it does

Emit, on stdout, in this order:

1. **One sentence** stating what CAPTAIN is — the human authors structured intent;
   the agent implements artifacts to match.
2. **A table of all capabilities** (`SKILL.md` — the closed list), one row each, with a
   short description:

   | Capability | What it does |
   |------------|--------------|
   | `refine`  | Bring intent at an IRN into clean, sync-ready shape. |
   | `sync`    | Bring intent and artifact into agreement, either direction. |
   | `audit`   | Report whether contracts are honored, into `compliance.yaml`. |
   | `evolve`  | Modify the framework itself. |
   | `explain` | Answer a question about the workspace from the intent alone, read-only. |
   | `help`    | Describe CAPTAIN itself, read-only. |
   | `assist`  | Act as workspace domain expert on artifacts intent does not govern. |
   | `explore` | Run the exploratory phase: epochs of intent, each artifact informing the next. |

3. **A bullet list of the core framework concepts** (from `FOUNDATION.md`):

   - **Ontology** — two nouns: Entity and Component; Contract is a handle, not a third noun.
   - **The Containment Law** — the entity is the maximal concept; every same-named form is a subset.
   - **IRN** — Intent Resource Name: `<entity>.<component>.<contract>.v<major>_<minor>`.
   - **`lit:`** — pins a verbatim artifact symbol; bare tokens are agent-named prose.
   - **Contract names + versioning** — PascalCase + `Contract`, unique per component; version only on a break.
   - **Contract binding types** — `name` / `shape` / `literal` / `semantic`; `semantic` is last resort for code, native for ideas.
   - **Artifact kinds** — `code` (deterministic, tested) or `idea` (prose, judged by reading); declared, never inferred.
   - **Exploration** — an opt-in phase of numbered epochs (successors and siblings), each artifact's finding feeding the next, ending at `adopt`.

Read the current `SKILL.md` and `FOUNDATION.md` before emitting, so the capability list
and concept glosses reflect the framework as it actually stands, not this file's copy.

## Output

- The description on stdout: one sentence, the capability table, the concept list.
- **No writes.** No edit to intent, artifact, framework, or `compliance.yaml`.

## Completion

- CAPTAIN is described from the framework files. There is no "undetermined" case — the
  subject is the framework itself, always present.

## Halt

- The prompt is a **change request**, not a request to be oriented — redirect to the
  owning capability (`evolve` for the framework, `sync`/`refine` for intent⇄artifact,
  `assist` for ungoverned artifacts) and stop. `help` never performs the change.
- The prompt is a **question about the workspace**, not about CAPTAIN — that is
  `explain`'s subject; redirect there.

## Boundary

- **Framework-only and read-only.** It reads `SKILL.md` and `FOUNDATION.md` and writes
  nothing. The workspace intent is `explain`'s subject; the artifact is `sync`'s;
  mutation belongs to `sync`/`refine`/`audit`/`evolve`.
