---
capability: refine
purpose: >
  Bring the intent at an IRN into clean, sync-ready shape — clarity,
  notation, and structure — without changing what it means.
---

# `refine`

**`refine` polishes intent at an IRN so `sync` and `audit` can consume it.** It is the
only capability whose job is intent *quality*. It does not produce artifact (`sync`),
does not record verdicts (`audit`), does not touch the framework (`evolve`). It changes
how intent reads, never what it commits to — meaning is preserved, the human owns it.

## Trigger

```
/captain refine @irn
```

- `@irn` — the scope to refine: an entity, a component, or a single contract.
  (`FOUNDATION.md` §4.) Refining a parent refines its children.

## What it does

Run on the intent at `@irn`:

1. **IRN integrity.** Every entity/component/contract name conforms to
   `FOUNDATION.md` §2, §9, R11 — entity Capitalized, component lowercase, contract
   PascalCase + `Contract`, version `.v<major>_<minor>`. Contract names are unique
   *within their component* and name a **commitment, not a location** (flag and propose
   shorter names that re-encode entity/component/method — §9).

   **A rename carries its references.** When refine renames an entity, component, or
   contract, grep the workspace for the old name *before applying* — other entities' prose
   may cite it by IRN, and `compliance.yaml` verdicts are keyed to it. Update every
   in-prose reference; flag (do not edit) stale `compliance.yaml` keys — those clear on the
   next `audit`, not by hand (§11). A rename that strands a reference is incomplete.

2. **No floating nouns** (`FOUNDATION.md` §10–§11). Scan prose for nouns it leans on.
   Every such noun must resolve to an IRN (entity/component/contract) or be plain
   English. Flag an unresolved noun; propose either anchoring it to an IRN or rewording
   to plain prose. This is a *clarity* check, not a dependency check — it builds no graph.

   **Scan prose only — never the contract bodies.** Do **not** flag tokens that appear:
   - inside a fenced block (```` ``` ````) or its comments — that is artifact shape,
     not intent prose (e.g. `Capability`, `STATUS_FAILED`, a key name in a `shape` body);
   - inside a path or URN expression (contains `/`, `://`, `{}`);
   - as an `e.g.` example value.

   A capitalized noun in *prose* that names no entity (e.g. "the appropriate Parser",
   "a manifest Schema") is the target: propose lowercasing to plain prose, or anchoring
   to the real IRN (`Manifest.parser`) if a reference is meant.

3. **`lit:` honesty** (`FOUNDATION.md` §4). Flag `lit:` on tokens whose exact spelling
   is *not* load-bearing (propose dropping it) and bare tokens that must be verbatim
   artifact strings (propose adding it).

   **No backticks** (`FOUNDATION.md` §4). A workspace intent file contains no single
   backtick. Run the invariant — `grep -rn '`' <intent>/<Entity>/*.md | grep -v '```'`
   must be empty — and route every hit:
   - a verbatim artifact symbol → `lit:`;
   - an enumerated surface (signatures, a `shape`/`literal` body) → a fenced block;
   - a concept noun that pins no exact string → plain prose.
   Signature/surface lists are the dominant source — they belong in a fence, never inline
   backticks. This is refine's work to fix, not a halt.

4. **Binding completeness** (`FOUNDATION.md` §7). Every contract declares a `binding`
   (one of `name`/`shape`/`literal`/`semantic`) and an `artifact_path`. Flag a missing
   one — it is a hard gap, not a style note. For `semantic`, check the body is
   **ordered numbered steps**, not a paragraph; propose the restructure.

5. **Granularity echo** (`FOUNDATION.md` §6). Read the G floor off each contract's depth
   (G0/G1/G2) and echo it back. Absence is agent-free, not an error — but echo it so a
   genuine forget surfaces.

6. **Prose tightening.** Concise, structured, bare-metal. Dense sequential prose →
   numbered/bulleted lists. No re-encoding what the artifact's own shape already says
   (`FOUNDATION.md` §8).

## Output

- A concise change list (one line per change: file, what, why) for the intent files
  under `@irn`, presented for approval **before** any edit is applied
  (`FOUNDATION.md` §12).
- Anything needing prose discussion rides on stdout — the session is the prose channel;
  there is no persisted prose file.
- Apply only once the human approves. On apply, append one `.trace.md` entry per mutated
  IRN (`TYPE | IRN | message`, `SKILL.md` *Communication*) — `refine` changes intent, so
  it traces.
- **`--dry-run`** prints the change list and exits, writing nothing (`FOUNDATION.md` §12).
  Re-run without the flag to apply.

## Halt

- `@irn` does not resolve to an existing entity/component/contract — report it.
- A missing `binding` or `artifact_path` that the human must supply — `refine` flags it;
  it does not invent one.
- Material uncertainty about meaning that context cannot resolve — ask, on stdout,
  before writing.

`refine` does not halt on the things it exists to fix (loose prose, missing IRN polish,
`lit:` drift) — those are its work, not blockers.

## Boundary

- A precondition for `sync` (forward) and `audit`: both expect refined intent and may
  halt asking for `refine` if a binding is missing or a name is malformed.
- `refine` never writes artifact and never writes `compliance.yaml`.
- **Never `epoch.md`.** Under exploration `refine` polishes the intent inside the current
  epoch and does not touch epoch structure — `epoch.md` is not intent, no IRN addresses it,
  and it is exempt from the no-backticks invariant (`FOUNDATION.md` §16). Keep the grep in
  step 3 scoped to the entity folders.
