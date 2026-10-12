---
capability: explain
purpose: >
  Answer a free-form question about the workspace from the intent — and only the
  intent. It reads the entity/component/contract files, never the artifact
  repos. Read-only: it produces an answer, never a change.
---

# `explain`

**`explain` is the read-only capability.** It answers a question about the workspace and
mutates nothing — not artifact, not intent, not framework, not `compliance.yaml`
(`FOUNDATION.md` §12). Its only output is the answer on stdout. It is the honest home
for a verb-less `/captain @prompt`, which the router (`SKILL.md`) defaults here.

The other capabilities — `help` aside — all produce or reconcile intent and artifact. `explain`
produces understanding **from the intent alone**. That is the whole of its job; the
moment an answer would require a change, it stops and names the capability that owns
the change (§Halt).

**Intent is the only source.** `explain` answers from the workspace's own account —
the entity, component, and contract files (`FOUNDATION.md` §1: intent is authoritative).
It does **not** read the artifact repos, and it does **not** invoke the `mda-cross-repo`
skill or any other cross-repo/artifact-navigation tool. An answer the intent does not
support is "undetermined," not a reason to fall back to the code (§Halt).

## Trigger

```
/captain explain @prompt
/captain @prompt          # verb-less free-form → defaults here (SKILL.md router)
```

- `@prompt` — a question about the workspace: what something is, where it lives, how two things
  relate, which artifact satisfies a contract, etc.

## What it does

1. Read the workspace through `captain.yaml` — `intent_path`, the entity/component
   files, and `compliance.yaml` when conformance is in question. Under exploration, also
   `epoch.md` — **any** epoch, not only the current one, since lineage and past findings are
   workspace facts and `explain` is the read path for them (`FOUNDATION.md` §16). **This is
   the only source.** Do not read the artifact repos; do not invoke `mda-cross-repo`.
2. Answer concisely on stdout, grounded in the intent. Cite the IRNs the answer rests
   on so the human can verify it against the source files. Longer prose stays on stdout
   — `explain` is read-only and persists nothing.

## Output

- A concise answer on stdout, grounded in named intent (IRN) — from the intent files,
  not the artifact.
- **No writes.** No edit to intent, artifact, framework, or `compliance.yaml`.

## Completion

- The question is answered from the intent, or the answer is "undetermined" with the
  gap named — the intent does not yet say (a missing entity, an unwritten contract, a
  detail the intent leaves to the agent). An honest non-answer is a valid completion;
  reaching into the artifact to fill the gap is not.

## Halt

- The prompt is a **change request**, not a question — redirect to the owning
  capability (`sync` for intent⇄artifact, `refine` for intent shape, `evolve` for the
  framework, `assist` for ungoverned artifacts, `explore` for epoch structure) and stop.
  `explain` never performs the change.
- The answer cannot be grounded in the intent — report what the intent is missing
  rather than inventing it or reaching into the code (no floating claims, mirroring
  `FOUNDATION.md` §10–§11).

## Boundary

- **Intent-only and read-only.** It reads the workspace intent files, `compliance.yaml`, and
  `epoch.md` — not the artifact repos, not `mda-cross-repo` — and writes nothing. Mutation is
  the exclusive province of `sync`/`refine`/`audit`/`evolve`/`assist`/`explore`; the artifact
  is the province of `sync` (governed) and `assist` (ungoverned); epoch structure is
  `explore`'s, and `explain` only reads it.
