---
capability: evolve
purpose: >
  Modify the CAPTAIN framework itself — FOUNDATION.md and the skill files
  that implement it. The framework is human-owned; the agent authors,
  the human approves.
---

# `evolve`

**`evolve` is the only capability that modifies the framework.** It writes to
`FOUNDATION.md` and brings the skill files (`SKILL.md`, `capabilities/*.md`) into
consistency with it. It touches nothing else — not artifact code, not workspace intent.

The framework is itself intent, governed by CAPTAIN's own design. Changes go through the
same authorship/ownership split as any intent: the agent may author; the human owns;
review is the gate. **There is no ADR file and no decision log** — intent is stateless
(`FOUNDATION.md` §11). The decision trail is the git history of `FOUNDATION.md`.

## Trigger

```
/captain evolve @prompt
```

- `@prompt` — the change request: what to change, and (where known) why.

## What it does

1. Read `FOUNDATION.md` and the skill files — know the current framework before
   changing it.
2. Propose the change against the foundation. A change must either derive from the
   existing design or argue that the design itself should change. Apply the **minimal-
   burden test**: *what is the meaningful difference if this change does not exist?* A
   change that fails it does not land, even if easy to write — this is the primary
   defense against the framework bloating back into the dense, layered shape CAPTAIN was
   built to escape.
3. Edit `FOUNDATION.md` (the substantive change).
4. **Propagate to the skill files** so `SKILL.md` and `capabilities/*.md` stay
   consistent. Intent is authoritative; the skill follows — propagation happens *after*
   the foundation edit, never before.

## Output

- Edits to `FOUNDATION.md` and any affected skill files.
- A concise change list on stdout (file, what, why). Rationale that needs prose rides on
  stdout — there is no persisted prose file. `evolve` changes the framework, not workspace
  intent, so it writes no `.trace.md` entry; its record is the git history of
  `FOUNDATION.md`.
- The change list is presented for approval **before** `FOUNDATION.md` or any skill
  file is edited (`FOUNDATION.md` §12); apply only once the human approves. Framework
  changes warrant explicit review — do not self-commit unless the human says so.
- **`--dry-run`** prints the change list and exits, writing nothing (`FOUNDATION.md` §12).
  Re-run without the flag to apply.

## Completion

- `FOUNDATION.md` carries the change, and the skill files are consistent with it. A
  foundation edit without skill propagation is *incomplete* — re-invoke to finish it.

## Halt

- The change contradicts the foundation without proposing the foundation itself change
  — surface the contradiction, ask whether the foundation is in scope.
- The change cannot trace a derivation and is not argued as a design change — report
  the missing rationale (minimal-burden test).
- Material uncertainty about the prompt.

## Boundary

- `sync`/`audit`/`refine` operate on workspace intent and artifact; only `evolve` touches
  the framework. A free-form prompt proposing a framework change is redirected here.
