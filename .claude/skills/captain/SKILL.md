---
name: captain
argument-hint: "[refine|sync|audit|evolve|explain|help|assist|explore] <irn|prompt> [--dry-run]"
description: >
  Intent Framework. Use when the user invokes `/captain …` or asks to refine, sync,
  audit, evolve, explain, assist, explore, or get help on an intent-driven workspace — a
  directory containing `captain.yaml` and Entity folders of component `.md` files, or an
  exploratory workspace of numbered intent epochs. Artifacts may be code or ideas. The
  framework is defined in FOUNDATION.md; this file routes invocations to a capability.
---

# CAPTAIN

**CAPTAIN is an intent framework: the human authors structured intent (entities,
components, contracts at a chosen granularity); the agent implements artifacts to
match — code or ideas, settled or still under exploration.** This file routes `/captain`
invocations to one of eight capabilities. The
framework itself — ontology, IRN, granularity, binding — lives in `FOUNDATION.md`.
Read it to justify or evaluate a decision. This file is operational.

## Capabilities

Eight. Closed list.

- **`refine`** — bring intent at an IRN into clean, sync-ready shape. Specified in `capabilities/refine.md`.
- **`sync`** — bring intent and artifact into agreement, either direction. Specified in `capabilities/sync.md`.
- **`audit`** — report whether contracts are honored, into `compliance.yaml`. Specified in `capabilities/audit.md`.
- **`evolve`** — modify the framework itself. Specified in `capabilities/evolve.md`.
- **`explain`** — answer a question about the workspace from the intent alone, read-only. Specified in `capabilities/explain.md`.
- **`help`** — describe CAPTAIN itself: its capabilities and core framework concepts, read-only. Specified in `capabilities/help.md`.
- **`assist`** — act as workspace domain expert on artifacts intent does not govern (config, dotfiles, `CLAUDE.md`, tooling). Specified in `capabilities/assist.md`.
- **`explore`** — run the exploratory phase: epochs of intent, each artifact's result informing the next. Specified in `capabilities/explore.md`.

## Router

1. Strip any `--flag` token (e.g. `--dry-run`) from the argument stream — it applies to
   whichever capability is dispatched. Then read the first remaining token after `/captain`.
2. If it matches `{refine, sync, audit, evolve, explain, help, assist, explore}` → load `capabilities/<verb>.md`, dispatch with remaining tokens.
3. Otherwise → treat the whole string as a free-form prompt.
   - If it **asks a question** (the default for a verb-less prompt) — about the
     workspace → `explain`; about CAPTAIN itself → `help`.
   - If it **proposes a change**, classify by **target**:
     - the framework (`FOUNDATION.md`, the skill files) → `evolve`;
     - intent files → `refine` (shape/clarity) or `sync intent` (author from artifact);
     - **epoch structure** — `epoch.md`, an epoch folder, `explore:` in `captain.yaml`, or a
       request to iterate the intent itself (branch a parallel option, advance to a next
       version, assess what an artifact revealed, adopt a winner) → `explore`
       (`FOUNDATION.md` §16);
     - a **governed** artifact (an `artifact_path` names it, `FOUNDATION.md` §13) →
       `sync` forward — never `refine`/`evolve`;
     - an **ungoverned** artifact (no `artifact_path` names it — config, dotfiles,
       `CLAUDE.md`, tooling) → `assist`. This is the residual: `assist` owns off-intent
       changes the other capabilities cannot, without loosening their boundaries.
4. If unsure → ask one disambiguation question, then dispatch.

## Parameters

- **`@irn`** — an Intent Resource Name (`FOUNDATION.md` §4):
  `<entity>[.<component>[.<contract>[.v<major>_<minor>]]]`. Resolves to an entity
  folder, a component file, or a contract within it.
- **`@artifact_path`** — a repo-relative path to artifact, resolved through
  `captain.yaml` `repos:`.
- **`@what`** ∈ `{code, docs, intent}` — `sync` direction selector. `code` includes tests.
  `code` names the *governed artifact*, whatever its kind: for `artifact_kind: idea`
  (`FOUNDATION.md` §15) it writes prose and generates no tests.
- **`@action`** ∈ `{start, branch, advance, assess, adopt}` — `explore`'s selector
  (`FOUNDATION.md` §16).
- **`@epoch`** — an epoch folder name (`0002-intent-b`); defaults to `explore.current`.
- **`@prompt`** — free-form user text (for `evolve` and the free-form router path).
- **`--dry-run`** — on a mutating capability (`sync`, `refine`, `evolve`, `assist`,
  `explore`): run
  the propose step, print the change list, and **exit without mutating** (`FOUNDATION.md`
  §12). No approve branch; re-run without the flag to apply. `sync intent --dry-run` is the
  **"missing intent"** report — the intent reverse-sync would author for artifact regions
  no contract covers.

No `@mode` — no behavioral selector beyond `@what` and `explore`'s `@action`, both of which
choose *which* operation runs, not how one behaves. The mutating
capabilities (`sync`, `refine`, `evolve`, `assist`, `explore`) propose a concise change list and
**wait for human approval before applying** (`FOUNDATION.md` §12); `--dry-run` stops them
at the proposal (it is a terminate-after-propose switch, not a mode). `audit` is exempt and
writes `compliance.yaml` directly. Committing is the human's act unless they say otherwise.

## Workspace

CAPTAIN operates on a workspace whose location is declared in `captain.yaml`:

```
<intent_path>/
  captain.yaml      # config: repo map + intent_path
  compliance.yaml    # generated by audit; all contract verdicts
  .trace.md          # intent change trace — disposable, auto-generated (see below)
  Entity/            # one folder per entity
    Entity.md        # entity doc: description, artifact_repo, prose
    component.md     # component doc: contracts
    ...
  ...
```

### Locating the workspace

**`captain.yaml` is the entry point.** Find it, read `intent_path`, and resolve the
workspace root from it before any other read:

1. Search for `captain.yaml` from the current working directory downward (and at the
   repo root). It lives *inside* the intent workspace.
2. Read its `intent_path` — the workspace root, **relative to the repo root** where this
   skill lives. The entity folders sit directly under it.

```yaml
intent_path: intent                # workspace root, relative to the repo root
code_path: src                     # default root for governed source, repo-relative
tests_path: tests                  # default root for tests, repo-relative
repos:
  repo-a: /abs/path/to/repo-a      # optional; defaults to ../repo-a (sibling of repo root)
  repo-b: /abs/path/to/...         # optional; defaults to ../repo-b
```

- **`intent_path`** — relative path, from the repo root, to the directory holding the
  entity folders, `compliance.yaml`, and `.trace.md`. Required. Do **not** assume a
  top-level `intent/`; always read it.
- **`repos`** — maps each repo name (an entity's `artifact_repo`) to a local path. A repo
  with no entry defaults to a sibling of the repo root (`../<repo-name>`).
- **`code_path` / `tests_path`** — repo-relative roots for governed source and tests
  (defaults `src` / `tests`). Test location is **read from here, never inferred** from a
  folder on disk; tests mirror `code_path` → `tests_path` (`FOUNDATION.md` §14). For
  artifacts outside `code_path`, `tests_path` is overridden — by a component in its
  frontmatter, or by a single contract alongside its `binding`/`artifact_path` when one
  component's contracts sit in separate trees. Most specific wins: contract, then
  component, then the default mirror.
- **`compliance.yaml`** — the single conformance file for all contracts. Generated by
  `audit`, never hand-edited. History lives in git. Written at `<intent_path>/compliance.yaml`.

### Exploratory workspaces

When `captain.yaml` declares `explore:`, `intent_path` holds **epochs** rather than entity
folders, and each epoch is a complete intent workspace (`FOUNDATION.md` §16):

```
<intent_path>/
  captain.yaml
  0001-intent/
    epoch.md         # parent + question (frontmatter), finding (body)
    compliance.yaml
    .trace.md
    Entity/
  0002-intent-a/     # sibling A
  0002-intent-b/     # sibling B
<artifacts_path>/
  0001-artifact/
  0002-artifact-a/
  0002-artifact-b/
```

```yaml
intent_path: intents
explore:
  current: 0002-intent-b     # exactly one epoch is authoritative
  artifacts_path: artifacts
```

**The resolution rule** — the only exploration-awareness any capability but `explore` needs:

> When `explore:` is declared, the effective intent root is
> `<intent_path>/<explore.current>`, and the artifact root is `<artifacts_path>/` + the
> current epoch's derived artifact folder (`0002-intent-b` → `0002-artifact-b`). Otherwise
> the effective intent root is `<intent_path>` and artifacts resolve through `repos:`
> (`FOUNDATION.md` §7).

Read `<intent_path>` everywhere above — `compliance.yaml`, `.trace.md`, the entity folders —
as the **effective** intent root. With this rule in place `refine`, `sync`, `audit`, and
`assist` operate inside the current epoch without knowing epochs exist; only `explore` reads
or writes epoch structure, and only `explain` additionally reads `epoch.md` (read-only, any
epoch). Frozen epochs are never a source of truth. During exploration `repos:`, `code_path`,
and `tests_path` do not govern epoch artifacts — exploration is single-repo (§16).

Entity- and component-file structure follows `FOUNDATION.md` §2–§9. No `index` file,
no `decisions`/ADR file, no logs — intent is stateless (`FOUNDATION.md` §11), with the one
bounded exception of `epoch.md` under exploration (§11 *The exploration exemption*, §16).

## Communication

**stdout is the only prose channel: concise, non-verbose, no narration.** Capabilities
work quietly and emit a short change list when a decision is needed. Every prose
exchange — a question, a rationale, a propose summary, a reverse-sync anchor — rides on
stdout, in-session. There is **no persisted prose file** (intent is stateless,
`FOUNDATION.md` §11); prose the session does not keep is not kept.

**`intent/.trace.md` is the intent change trace** — the one disposable sidecar
(`FOUNDATION.md` §11). It records intent changes; it is never authoritative and nothing
in intent references it. It may be deleted, in part or whole, at any time.

- **Written automatically, on apply**, by the capabilities that mutate **intent** —
  `refine` and `sync intent`. `sync code`/`sync docs` change the artifact, not the
  intent, and write nothing here; `audit` writes `compliance.yaml`; `evolve` changes the
  framework, whose record is the git history of `FOUNDATION.md`; `explore` writes epoch
  structure, whose record is the epoch tree itself. Under exploration `.trace.md` is
  **per-epoch** — it traces that epoch's intent (`FOUNDATION.md` §16). Appending an entry needs
  no separate approval — it records a change the human already approved (`FOUNDATION.md`
  §12).
- **Format.** `## YYYY-MM-DD` date headers, **reverse-chronological by date**; within a
  date, entries appear in the order they were generated (first to last). One entry per
  line:

  ```
  - TYPE | IRN | message
  ```

  - **TYPE** — one of `ADDED`, `REMOVED`, `MODIFIED`, `RENAMED`, `FIXED`, `DEPRECATED`.
  - **IRN** — the affected entity / component / contract (`FOUNDATION.md` §4).
  - **message** — concise, bare-metal; what changed, not why.

## Out of scope

`/captain` modifies **governed** code only via `sync` forward; modifies intent only via
`sync` reverse and `refine`; modifies the framework only via `evolve`; modifies **epoch
structure** only via `explore`. `explain` reads the intent alone (never the artifact, never
`mda-cross-repo`) and modifies nothing.
Crossing those boundaries — e.g. editing a governed artifact outside `sync` — is a
router error.

An **ungoverned** artifact (no `artifact_path` names it — config, dotfiles, `CLAUDE.md`,
tooling, `FOUNDATION.md` §13) is **not out of scope**: it is `assist`'s province. `assist`
acts on it as workspace domain expert and refuses the moment the target turns out to be
governed, redirecting to `sync`. That boundary is what keeps `assist` from becoming an
intent-bypass.
