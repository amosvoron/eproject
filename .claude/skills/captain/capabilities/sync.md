---
capability: sync
purpose: >
  Bring intent and artifact into agreement, in the direction the human
  chooses. Forward: intent → code/tests/docs. Reverse: code → intent.
---

# `sync`

**`sync` is the only capability that writes one side from the other** — artifact from
intent (forward) or intent from artifact (reverse). `audit` reports; `refine` polishes;
`evolve` changes the framework. Only `sync` performs the transformation.

## Trigger

```
/captain sync @what @irn | @artifact_path
```

- `@what` ∈ `{code, docs, intent}`:
  - `code` — forward, intent → code **and tests**.
  - `docs` — forward, intent → documentation slice.
  - `intent` — reverse, artifact → intent.
- Target:
  - Forward (`code`/`docs`) — an `@irn` (entity / component / contract).
  - Reverse (`intent`) — an `@irn` (the entity to populate) plus the `@artifact_path` to
    read from, e.g. `/captain sync intent Manifest src/manifest`.

## Resolving artifact location

1. Read `captain.yaml` (located per `SKILL.md` → *Locating the workspace*): `intent_path`
   for the workspace root, `repos:` to map a repo name to a local path (default: sibling
   `../<repo>`). If `explore:` is declared, the **effective** intent root is
   `<intent_path>/<explore.current>` and the artifact root is the current epoch's artifact
   folder — `repos:` does not apply (`SKILL.md` → *Exploratory workspaces*,
   `FOUNDATION.md` §16). `sync` is otherwise exploration-blind.
2. Each contract's `artifact_path` is **repo-relative**, resolved against the owning
   entity's `artifact_repo` (or the contract's own override). `FOUNDATION.md` §7.
3. For test paths, also read `code_path` / `tests_path` (defaults `src` / `tests`); tests
   mirror from `code_path` into `tests_path` in the artifact's repo (`FOUNDATION.md` §14).

## Forward (`code` / `docs`) — intent → artifact

Read the intent at `@irn`; write artifact at the resolved paths so every contract is
honored per its `binding`:

- **`name`** — the named classes/methods/functions exist; bodies are the agent's.
- **`shape`** — the artifact matches the block's structure; slots filled, shape kept.
- **`literal`** — the artifact equals the block verbatim.
- **`semantic`** — the artifact implements the numbered steps faithfully; any embedded
  fenced block is honored exactly.

Discipline:

- **Respect the G floor** (`FOUNDATION.md` §6). At and above the floor, match intent.
  Below it, the agent is free — do not invent commitments the contract did not pin.
- **Tests are part of `code`** — generated from the artifact, not the contracts (§14); see
  *Forward (`code`) — generating tests* below. **Not for `artifact_kind: idea`**
  (`FOUNDATION.md` §15): an idea artifact is prose, `code` writes that prose, and **no tests
  are generated** — its completion rule is the contracts being honored, nothing more. This
  is the declared kind, not §14's "mechanically impossible" exemption.
- **Styling is artifact-side.** Conform to the repo's own config (`pyproject.toml`,
  `ruff.toml`, etc.); never read styling from intent.
- **Stay in scope.** Write only what the contracts at `@irn` cover.

### Forward (`code`) — generating tests

Tests are part of `code` — code without tests is incomplete — but they are **not read off
the contracts** (`FOUNDATION.md` §14). Generate them from the artifact you just wrote:

- **Per component.** Scope tests to the component at `@irn`; the component is the
  organizational unit, not the contract. One component may carry more than one test module
  or class — split by what the code warrants, never one-per-component by rule.
- **Name tests to their component.** Use test class/module names that map plainly to the
  component under test, so the relationship needs no lookup.
- **From the code, not the contract.** Derive cases from the component's own artifact
  surface — public API, branches, error and boundary paths. Do not enumerate tests from
  contract bodies; a contract is verified by `audit` (mostly `code-trace`), not by being
  turned into a test.
- **Policy is CAPTAIN's, tooling is the repo's.** What to cover and how to organize is
  fixed here; the framework, runner, and fixtures come from the repo's own config — read
  tooling from the repo, never from intent (as with styling).
- **Tests as evidence.** A test that asserts a contract may back its `evidence: test`
  verdict in `audit`; that is incidental, not a binding — no contract requires a test.
- **Where they live.** Read `code_path` / `tests_path` from `captain.yaml` (defaults
  `src` / `tests`) — never infer a location from an existing folder. Tests go in the same
  repo as the artifact, mirrored from `code_path` into `tests_path`
  (`src/…/foo.py` → `tests/…/test_foo.py`). An artifact outside `code_path` is placed by a
  `tests_path` override — the contract's own if it declares one, else the component's
  frontmatter (§14, most specific wins). If neither declares one and the component is not
  untestable, **do not generate — notify the human** that the missing `tests_path` is the
  cause. Never the intent workspace.

### Forward (`docs`) — the documentation projection

`docs` projects intent into **human-facing documentation**. It is uniform across every
repo and is read-only on intent — it reads the entity/component files and writes only doc
artifacts, never editing intent. Documentation and intent are **different artifacts for
different readers**, and the projection must hold that line:

- **Intent instructs the agent** — what the artifact is and which contracts it must
  satisfy.
- **Documentation orients a human** — what the artifact is about and its main
  components, held at the conceptual level.

They look similar; their purpose is opposite. Two rules follow and are not optional:

- **Docs reproduce no contracts** — not enumerated, not verbatim. A contract restated
  as-is is intent leaking into docs. Take an explanatory angle that keeps the conceptual
  level; reveal implementation detail only where it genuinely matters (guides and
  examples — how to install, run, or implement an interface), never as a contract dump.
- **Docs never route the reader to the intent.** The README stands on its own. It does
  not defer to the intent workspace for "the real contracts."

The projection is **README files only** — no `docs/` tree, no per-contract pages:

- **One `README.md` per repo**, at the repo root — the repo's purpose and the entities
  it hosts.
- **One `README.md` per entity artifact folder** — the entity's purpose and its main
  components, conceptual, no contracts.
- **1:1 collapse.** When a repo hosts exactly one entity whose artifact folder is the
  repo root, the repo-root README is the entity README — one file, no duplicate. A
  distinct entity README appears only when the entity's artifact folder is a separate
  sub-path, or the repo hosts more than one entity (then the repo README names the
  entities and each entity folder carries its own).

**Precondition — the artifact folder must exist.** An entity README is written only into
an artifact folder that exists on disk. If it does not, **halt** — do not create the
folder, do not document an artifact that isn't there.

Rendering rule — **docs are for humans**:

- Render every `lit:X` as a backtick code-span `` `X` `` (strip the `lit:` prefix). The
  `lit:` notation is an intent-authoring device (`FOUNDATION.md` §4); the reader sees the
  verbatim symbol in code font.
- Fenced blocks (`shape`/`literal` bodies, signatures) carry through as-is.
- Bare prose nouns stay plain prose — they pin no symbol, so they get no backticks.

This is the **only** place backticks are legitimate downstream of intent: the human-facing
projection, never the intent files themselves.

## Reverse (`intent`) — artifact → intent

Read the artifact under `@artifact_path`; write/extend the entity at `@irn`. This is the
fabrication-prone direction — the guards are not optional:

1. **Enumerate the real tree on disk first.** Never read from memory, a README, or an
   inferred layout. The on-disk enumeration is the ground truth.
2. **A failed read is a hard stop.** "File does not exist" means the assumption is wrong
   — do not author from it. More than one in a session means the mental model is wrong;
   re-ground from the enumeration.
3. **Anchor every contract to a real code location** while authoring (a `file:line`, a
   quoted signature, a test name). An unanchored contract is a fabricated contract.
4. **Anchor on stdout, abstract in intent.** The anchor is evidence — it rides on stdout
   (the session prose channel; nothing prose is persisted), not into the contract prose.
   The contract states the commitment in entity/concept terms (`FOUNDATION.md` §8–§9), at
   the G floor you choose — not a verbatim copy of the signature.
5. **Pick a binding honestly** (`FOUNDATION.md` §7): a real symbol → `name`; a structural
   document → `shape`; a verbatim artifact → `literal`; a behavior with no symbol/shape →
   `semantic` (numbered steps). Every authored contract gets a `binding` and
   `artifact_path`.

6. **Name without collision.** Before authoring an entity/component/contract name, grep
   the workspace for it — a name already taken by another entity or component is a
   collision, not a coincidence; resolve it before writing. And confirm the name reflects
   the *intent concept*, not an artifact symbol that merely happens to be capitalized: the
   artifact class `lit:Foo` does not force the entity name `Foo` (§3 — the entity is the
   maximal concept, the class a projection). Pick the entity name for the concept; pin the
   class as `lit:`.

7. **Author backtick-free** (`FOUNDATION.md` §4). Reverse `sync` is where intent is first
   written, so it is where backticks first leak in. Route every verbatim symbol to `lit:`,
   every enumerated surface to a fenced block, every concept noun to prose — do not emit a
   single backtick. (Refine enforces the invariant; sync should not create work for it.)

Reverse `sync` may create the component files it discovers under the entity. Propose the
component set first (one line each) and let the human confirm the shape before authoring
contract bodies.

## Output

- Forward: artifact (code+tests, or docs) at the resolved paths.
- Reverse: entity/component `.md` files under `<intent_path>/<Entity>/`.
- A concise change list (one line per file: action + summary), presented for approval
  **before** any artifact or intent is written (`FOUNDATION.md` §12). Prose discussion
  rides on stdout. Apply only once the human approves. On apply, **reverse** `sync intent`
  appends one `.trace.md` entry per mutated IRN (`TYPE | IRN | message`, `SKILL.md`
  *Communication*); **forward** `sync code`/`sync docs` change the artifact, not the
  intent, and write no trace entry.
- **`--dry-run`** prints the change list and exits, writing nothing (`FOUNDATION.md` §12).
  Forward, it is the artifact diff sync would write; reverse (`sync intent --dry-run`), it
  is the **"missing intent"** — the contracts sync would author for the artifact regions no
  current contract covers. Re-run without the flag to apply.

## Completion

- Forward: every contract at `@irn` honored; for `artifact_kind: code`, the component's test
  code exists and **all its tests pass** (`FOUNDATION.md` §14) — unless testing it is
  mechanically impossible, which must be stated. For `artifact_kind: idea` the honored
  contracts *are* completion; no test clause applies (§15). Absent or failing tests mean the component is **not** complete. An
  out-of-`code_path` component with no `tests_path` at either level — contract or component
  — is **blocked, not complete**: report the missing `tests_path` rather than skipping
  silently.
- Reverse: every authored contract anchored to real code; the human confirmed the
  component shape before bodies were authored.

A test failure forward is not itself a halt — diagnose and fix it. Halt only when the
failure exposes an uncertainty the agent cannot resolve (the test contradicts the
intent and the agent cannot tell which is right).

## Halt

- The IRN does not resolve, or a contract lacks a `binding`/`artifact_path` → report;
  suggest `refine`.
- Reverse: a failed read (guard 2), or material uncertainty about meaning.
- A floating noun in the read-side intent that blocks understanding (`FOUNDATION.md` §11).

## Boundary

- `audit` reports; `sync` reconciles. `sync` does not write `compliance.yaml`.
- `sync` never invents forward topology — it produces artifact from intent that exists.
  Topology discovery is reverse-only.
- `sync` never touches `FOUNDATION.md` or skill files — that is `evolve`, nor epoch
  structure (`epoch.md`, epoch folders, `explore:`) — that is `explore`. Under exploration
  `sync` works **inside** the current epoch, resolved for it and otherwise unaware of it.
