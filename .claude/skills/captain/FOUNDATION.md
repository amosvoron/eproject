# CAPTAIN — Foundation

> Bare-metal foundation. Intent precedes artifact. The human owns the intent and
> writes it in a structured language; the agent implements the artifact to match.

---

## 1. The two sides

| Side | What it is | Who owns it |
|------|-----------|-------------|
| **Intent** | The concepts, components, and contracts that say *what must be true*. | The human (architect). |
| **Artifact** | The code, documents, and data that implement the intent. | The agent. |

Intent is authored first. When intent and artifact disagree, intent wins.

**Within an epoch** (§16) this is absolute: the artifact is built to match, and a
disagreement is an artifact defect. **Between epochs** the artifact produces evidence the
human uses to author the next intent — it informs, it never overrides. Authority never
flips; the artifact is read as a *result*, never promoted to a source of truth.

---

## 2. The ontology — two nouns

Exactly two nouns: **Entity** and **Component**.

- **Entity** — a *concept* on the intent side. A first-level folder under `intent/`.
  Capitalized, singular (`Manifest`, `Executor`, `Registry`). Owns components,
  governs artifacts. Not a document or data structure. **Stateless and
  unversioned** — a concept does not break (§8). Declares an `artifact_repo` and an
  `artifact_kind` (§15).
- **Component** — an implementable aspect of an entity. Addressed `Entity.lowercase`
  (`Manifest.parser`). Belongs to exactly one entity, contains no other components,
  may reference components of other entities.

A **Contract** is a *named, addressable region of a component's body* — verifiable
conditions the artifact must satisfy. **Not a third noun**; a *handle* placed where
the shape becomes solid and imperative (§8–§9).

An entity may span repositories. Its `artifact_repo` is the default; a contract
whose artifact lives elsewhere overrides with its own (§7). `artifact_kind` follows the
same locality rule — the entity declares it, a contract may override it (§15).

---

## 3. The Containment Law

> **The entity is the maximal concept. Every same-named form is a proper subset of it.**

For an entity `X`, every other surface form bearing its name — the English homonym
`x`, the artifact document `x`, the artifact class `lit:X`, any facet — satisfies
`f ⊊ X`. Each `f` is a strict **projection** of `X` onto one facet; `X` always
exceeds every `f` and the relation never closes upward.

- **One anchor.** Define only entities (and components). Every same-named form
  inherits meaning by containment — no separate definition for word, document, class.
- **Disambiguation is directional and terminates.** To read any form, look *up* to
  its entity; the entity is guaranteed richer, so lookup resolves.
- **Surface form is a projection selector, not a meaning switch.** The notation (§4)
  selects which facet of `X` is meant; it never points at something unrelated.

English nouns are never defined by the framework — `manifest` is anchored by the
entity `Manifest`, not by a rule about the word.

---

## 4. Addressing — the IRN and `lit:`

Two orthogonal axes. The **IRN** addresses *intent nouns*; **`lit:`** marks
*artifact literals*. `lit:` is not an IRN segment.

### The Intent Resource Name (IRN)

One grammar, descending the containment tree, one dot per level:

    <entity>[.<component>[.<contract>[.v<major>_<minor>]]]

| IRN | Names |
|-----|-------|
| `Executor` | the entity |
| `Executor.manifest_executor` | a component |
| `Executor.manifest_executor.WorkflowContract` | a contract |
| `Executor.manifest_executor.WorkflowContract.v1_0` | a contract version |

Each segment requires its parent. The version segment is meaningful **only at the
contract leaf** — the one place intent touches the artifact and can break (§8).
Casing: entity Capitalized, component lowercase, contract PascalCase + `Contract`.

### `lit:` — granularity on the name

A token is **English prose by default** (names a concept; agent picks the spelling).
`lit:` pins it:

- bare `header` — "a header must exist; the agent names it" (unpinned).
- `lit:header` — "the artifact must contain a thing spelled exactly `header`" (bound).

`lit:` marks any verbatim artifact-side string — key, class, branch, controlled
value, concurrency group — not only structural keys. Use it only where exact spelling
is load-bearing; ordinary prose nouns stay bare. Over-use re-creates the noise it
prevents.

**Backticks are retired in workspace intent.** A single backtick is the old notation
`lit:` replaces — a workspace intent file (`<intent_path>/<Entity>/*.md`) **contains no
single backtick**. The invariant: `grep` for `` ` `` over the intent files, excluding the
` ``` ` fence delimiter, is empty. Every would-be backtick routes to one of three forms:

- **`lit:`** — a verbatim artifact symbol whose spelling is load-bearing (class, method,
  key, controlled value);
- **a fenced block** — an enumerated artifact surface (signatures, a `shape`/`literal`
  body), which is artifact shape, not prose (§8);
- **plain prose** — a concept noun that pins no exact string.

This binds intent files only. Framework docs (`FOUNDATION.md`, the skill files) keep
backticks for IRN code-spans — they describe the notation, they are not authored in it.
The **human-facing documentation projection** is the other exception: `sync docs`
deliberately renders each `lit:X` back to `` `X` `` for readers (see `capabilities/sync.md`,
*Forward (`docs`)* — a README-only projection that orients humans and reproduces no
contracts). The retirement governs how intent is *authored*, not how it is *read* —
pinning happens in `lit:`, presentation happens in the projection.

---

## 5. Rules

- **R1** — What counts as an entity is an arbitrary design decision.
- **R2** — An entity is capitalized and singular.
- **R2a** — An entity is an intent-side concept, never a document. By §3, lowercase
  `manifest` is the artifact document — a subset of the entity `Manifest`.
- **R3** — Entities are first-level directories under `intent/`, non-hierarchical.
- **R4** — Inter-entity relationships are declared through intent, not directory
  structure.
- **R5** — No sub-entities.
- **R6** — A component is `Entity.lowercase`, singular, with a backing `<component>.md`.
- **R7** — A component belongs to one entity but may reference components of others (§10).
- **R8** — Components do not contain other components.
- **R9** — A contract's granularity is a **declared floor** (the minimum the artifact
  must honor), read off contract depth (§6). The floor must be verifiable.
- **R10** — An entity may have no components.
- **R11** — A contract name is **unique within its component**, not workspace-global.
  Its full handle is its IRN.

---

## 6. Granularity (G) — the central axis

When you code, granularity is fixed at maximum. Intent is different — **you choose
how far to pin each contract**, and that choice *is* the architecture.

G is a **floor**, not a fixed level:

- **G0 — Named:** the thing exists, by name, on its owner.
- **G1 — Shaped:** + conceptual role / member names (no signatures).
- **G2 — Bound:** + exact public signature. The ceiling — one rung short of code.

G is **read off the depth** of the contract, not declared. **Absence means
agent-free**: what the contract does not pin, the agent decides.

---

## 7. Binding — how a contract meets its artifact

Every contract declares a `binding` and an `artifact_path`. The binding is
**required** (no default) and governs both generation and verification:

- **`name`** — match by symbol name. *(Machine-verifiable.)*
- **`shape`** — the artifact conforms to the block's shape; slots are wildcards,
  surrounding structure is mandatory. *(Machine-verifiable.)*
- **`literal`** — the artifact equals the block, verbatim. *(Machine-verifiable.)*
- **`semantic`** — the artifact faithfully implements a prose-described behavior.
  *(Not machine-verifiable — judged.)*

### `semantic` is the binding of last resort

The other three are mechanically checkable; `semantic` requires judgment, which is
the ambiguity the framework exists to push out of intent. So:

- Use it **only** when no `name`/`shape`/`literal` binding fits (e.g. a workflow).
- Write the body as **ordered, numbered, atomic steps** — a checklist `audit` can
  verify step-by-step, not a paragraph.
- A semantic body **may embed a fenced block** to pin one structural detail; it is
  verified within the semantic judgment, not as a separate binding.

**For `artifact_kind: idea` (§15), `semantic` is the native binding, not a fallback.** An
idea artifact has no symbol to match and no bytes to equal, so no other binding *can* fit —
the rule above is unchanged, but its reason is spent: there is nothing to fall back from.
`shape` and `literal` stay available where an idea artifact genuinely pins a structure (a
required section layout, a fixed framing); `name` almost never applies.

### artifact location

`artifact_path` is **repo-relative**, resolved against the entity's `artifact_repo`
(§2). The repo is declared once on the entity; paths do not repeat it. A contract in
a different repo overrides with its own `artifact_repo`. A contract may list multiple
`artifact_path`s when its commitment spans files.

`binding` and `artifact_path` are **per-contract**; a contract may likewise carry its own
`tests_path` when its artifact's tests sit apart from its siblings' (§14). A
`shape`/`literal` body rides in a fenced block with its format tag (```` ```yaml ````,
```` ```python ````) — a delimiter, not a fragile discriminator.

---

## 8. Contracts are prose-first, and version only when artifacts break

CAPTAIN governs **only the noun notation** — the IRN and `lit:` (§4). Everything else is
**concise prose with clear structure**: the artifact's own shape, annotated. Resort
to notation only to remove ontological/semantic ambiguity, never to re-encode what
plain structure already says. **Strict ≠ verbose** — strictness comes from the
`binding`, not from ceremony.

### Versioning exists for one reason: surviving a breaking change

Not a generic "things have revisions" feature.

- **Only contracts version.** A contract is the point of maximum proximity to the
  artifact (§9) — the only place a breaking change can be felt. Entities and
  components are stateless concepts; concepts don't break. So the version segment is
  meaningful only at the contract leaf of the IRN.
- **An unversioned contract is the *stronger* commitment** — it declares *no breaking
  change will ever be permitted* (a fixed interface). `.v1_0` says "expect a v2";
  no version says "there is no version axis."

A versioned contract's name carries inheritance. A **minor/patch** bump (`.v1_1`)
inherits its predecessor (`.v1_0`) by the meaning of semver — the body declares only
the **delta**; no `inherits:` keyword. Form: `.v<major>_<minor>` (underscore — the dot
is the IRN separator). Delta forms: replacement block, or inline `lit:` changes
(`lit:schema: lit:standard/1.0 -> lit:standard/1.1`). A **major** bump (`.v2_0`) is a
full restatement; old and new may coexist while backwards compatibility is owed.

**An epoch is not a version** (§16). A contract version survives a breaking change to a
*live* artifact, where backwards compatibility is owed. An epoch explores an alternative
*before* anything is committed: nothing is live, nothing is owed, and a superseded epoch is
**frozen, not deprecated**. The two axes are independent — epochs do not inherit contract
versions, and advancing an epoch bumps no version.

---

## 9. Contracts are named, and unique within their component

A component's body solidifies into one or more **named contracts** — handles placed
where intent becomes imperative and G is smallest.

- **Form** — PascalCase + `Contract` suffix (`WorkflowContract`, `FailureSchemaContract`).
- **Names a commitment, not a location.** Never re-encode entity/component/method into
  the name (the IRN already supplies them). Handle length is the anti-sprawl tripwire.
- **Unique within the component** (R11) — like a function name within a module. The
  full handle is the IRN. (Global uniqueness was the pressure that inflated names.)
- **Cardinality** — one or more per component.
- **Readers** — `audit` cites it, contracts may reference one another.

Not an ontological noun — a handle into a component, like a function name into a module.

---

## 10. The framework owns no dependency graph

There is **no `depends_on` field**, and CAPTAIN **derives no dependency graph** —
neither persisted nor on-demand.

A dependency is not an input to intent; it is a **consequence of intent being clear
enough to implement**. Intent states what each component *is* (purpose) and what must
be true of its artifact (contracts). If that is clear, dependencies resolve themselves
at implementation time, in the artifact. If the agent *cannot* resolve how components
connect, the cause is never a missing edge — it is that **the intent is not good
enough**. The fix is always clearer intent.

Mentioning a foreign IRN in prose is **information** — a fact one component states —
not a tracked edge. The discipline that holds is narrower and about clarity: **every
noun the prose leans on must resolve to an IRN or be plain English** — no floating
nouns. That keeps intent unambiguous; it does not build a dependency set.

---

## 11. No index, no persisted state

The component files are the sole source of truth. There is **no index file** and no
persisted graph. Whatever `sync`/`audit` need, they assemble in memory from the
component files, use, and discard. Nothing persisted ⇒ nothing can drift.

The surviving checks are **intent-clarity checks**, not graph checks (the framework
owns no dependency graph — §10):

- **Reference resolution** — every IRN named in prose resolves to a real
  entity / component / contract.
- **No floating nouns** — every leaned-on noun resolves to an IRN or is plain English.

There is deliberately **no acyclicity or orphan check** — a cycle or orphan exists
only once an edge set is reified, and the framework reifies none.

Intent is **stateless**: no ADRs, no logs, no history. Conformance is the single
`intent/compliance.yaml`, fully regenerated by `audit`. History lives in git.

The one **disposable** sidecar is `intent/.trace.md` — an auto-generated change trace
of the **intent** (not the artifact). It is **never a source of truth**: no intent part
may reference it, and it may be deleted in part or whole at any time without loss. It
records what already happened; it does not state what must be true. Its format and the
capabilities that write it are operational detail (`SKILL.md`, *Communication*).

### The exploration exemption

Exploration (§16) is the **one** amendment to statelessness, and it is bounded. An
exploratory workspace persists one `epoch.md` per epoch, holding the epoch's question and
the finding its artifact produced — state that is **not** disposable, because the learning
signal is its whole purpose: epoch N is authored from what epochs 1..N-1 revealed, and a
lost finding is re-derived by hand or not at all.

What keeps it from becoming the decision log this section bans:

- **It is not intent.** `epoch.md` lives in the epoch root, not under an entity. It holds no
  contract, no IRN addresses it, and **intent inside an epoch may never cite it.**
  Statelessness therefore still holds exactly where it earns its keep — *within* an epoch.
- **One finding per epoch, replaced and never appended.** An ADR file grows; a finding is
  overwritten. This cap is load-bearing — loosen it and the ban is void.
- **Nothing aggregates findings.** `explore` assembles the prior findings in memory when
  authoring the next epoch, uses them, and discards them — the same treatment `sync` and
  `audit` give the component files.

`explore.current` in `captain.yaml` is **not** state of this kind: it is a *selector*. This
section forbids **derived** state — an index over the component files, a dependency graph —
because derived state can contradict its source. A selector has no source to contradict.

---

## 12. The approval gate

The **mutating** capabilities — `sync`, `refine`, `evolve`, `assist`, `explore` — never
apply changes to artifact, intent, framework, or epoch structure without human approval.
The gate is **propose-then-apply**:

1. The agent prepares a concise summary of the intended changes (file, what, why) and
   **waits**. The summary rides on stdout — the session is the prose channel; there is
   no persisted prose file.
2. The agent applies nothing until the human approves. Approval is an explicit
   in-session act, not the later commit.

### `--dry-run` — propose and exit

Any mutating capability accepts `--dry-run`: run the propose step, **print the change
list, and exit — mutating nothing.** It is the standard dry-run: it never changes the
state of the system, and there is **no approve branch** (approving would mutate, which a
dry-run must not). To apply, the human re-runs the same invocation **without** `--dry-run`.

The change list a `--dry-run` prints is the answer to *"what would this do?"* — and for
`sync intent` specifically, the printed diff is the **"missing intent"**: the contracts
reverse-sync would author for the parts of the artifact no current contract covers. A
plain run following a `--dry-run` applies the change list **already in context** — it does
not re-derive it (nothing is persisted, §11; the diff lives in the conversation, not on
disk).

`--dry-run` is **not a behavioral `@mode`** — it does not change *what* a capability does,
only whether it stops at propose. The `@mode`-free principle (`SKILL.md`) is intact.

`audit` is **exempt** — it mutates only `compliance.yaml` (the generated conformance
record, §11), never artifact, intent, or framework, so it writes directly. `explain`
is exempt for the stronger reason that it mutates **nothing at all** — not even
`compliance.yaml` — its only output is the answer on stdout. `help` is exempt for
the same reason: it only describes the framework on stdout and writes nothing.

Appending a `.trace.md` entry (§11) is likewise **not** a separately-gated act: the
entry is a record of an intent mutation the human **already approved**, written when
that mutation is applied (`refine`, `sync intent`). The gated thing is the change; the
trace just records it.

The gate is *before* the write, not at the commit.

---

## 13. The intent boundary — governed and ungoverned artifacts

Intent does not govern every file in a repo. A contract reaches an artifact through an
`artifact_path` (§7); a file no `artifact_path` names is **ungoverned** — project
config, dotfiles, `CLAUDE.md`, tooling, scaffolding. These are real work, and a request
to do them is not a request to bypass intent — there is no intent to bypass.

- **Governed artifact** — some contract names it via `artifact_path`. Changes to it are
  the exclusive province of `sync` forward (§7, §12). Touching it any other way is a
  router error.
- **Ungoverned artifact** — no `artifact_path` names it. Intent says nothing about it;
  the agent acts on it as **workspace domain expert**, gated like any mutation (§12).

The boundary is **decidable by a single test**: *does an `artifact_path` name this
file?* If yes, it is `sync`'s and the request routes there. If no, it is ungoverned and
the expert path may act. This test is what keeps the expert path from becoming an
intent-bypass — it can never reach a file a contract governs without being redirected.

This is the same shape as the read side: `explain` answers questions from intent, and
when intent is silent the answer is "undetermined," not a reach into the artifact.
Here, on the write side, when intent is silent the artifact may still be edited — but
only because intent was *never meant* to govern it, and only after the boundary test
confirms it.

---

## 14. Tests are artifact, generated from the code

**This section governs `artifact_kind: code` only** (§15). An `idea` artifact has no test
surface: its verification is `audit` reading the artifact against the contract, and the
completion rule below does not apply to it.

A contract is a **verifiable condition**, but *verifiable* is not *tested*. Verification
runs through the evidence modes `audit` records — `code-trace`, `reasoning`, `test` — and
for most contracts it is **inspection (`code-trace`)**, not a test. A test is one kind of
evidence, never the definition of a contract.

Tests are **artifact**, owned by the agent (§1), and are **not derived from contracts**.
Forward `sync code` generates them **after** the artifact exists, from the **code's own
surface** — public API, branches, error paths — never from a contract body. The
**component** is the organizational unit: it scopes the tests, the code fills them, and a
component may carry more than one test module — the unit is a boundary, not a one-file rule.
Name test classes to relate them plainly to the component under test.

CAPTAIN dictates test **policy** (what to cover, how to organize); the repo dictates test
**tooling** (framework, runner, fixtures), read from the repo's own config and never from
intent — the same artifact-side rule as styling. A test may back a contract's
`evidence: test` when it happens to assert it; no contract requires a test, and no test is
bound to a contract.

**Where tests live.** Test location is **declared, never inferred.** `captain.yaml` gives
`code_path` and `tests_path` (defaults `src` / `tests`, repo-relative); the agent reads
them and does **not** guess a location from a folder it happens to see on disk. A
component's tests live in the **same repo as the artifact under test** (resolved from its
contracts' `artifact_repo` + `artifact_path`, §7), mirrored from `code_path` into
`tests_path`: an artifact at `<code_path>/<sub>` is tested at `<tests_path>/<sub>`.
`artifact_path` is unchanged — it stays repo-root-relative; `code_path` is only the prefix
the mirror strips. When the default mirror does not reach an artifact — it lives **outside
`code_path`** (e.g. infrastructure or CI) — the location is **overridden**, repo-relative in
the artifact's repo, at whichever level fits. Most specific wins:

1. a **contract**'s own `tests_path`, declared alongside its `binding`/`artifact_path` — for
   a component whose contracts sit in separate trees, each carrying its own tests;
2. otherwise the **component**'s `tests_path`, in its frontmatter, covering every contract
   it holds;
3. otherwise the default mirror.

This is the established locality override (§7's per-contract `artifact_repo`), on the test
side, and it follows §7's split: location is per-contract, the concept stays per-component.
The override moves **location only** — the component remains the organizational unit that
scopes the tests (above). A contract-level path says where one artifact's tests live; it
never makes a contract own a test, and no test binds to a contract. If an out-of-`code_path`
component declares **no** `tests_path` at either level and is not genuinely untestable, the
agent **does not generate its tests and notifies the human** that the missing `tests_path` is
the cause — location is declared, never guessed. Only a
**genuinely untestable** component is legitimately left without tests, and then it must say
so (mechanically impossible) — never a silent skip, never an invented path. The intent workspace (`intent_path`) holds no tests.

**Completion and maintenance.** Unless testing the component is **mechanically impossible**
(then say so, and why), its implementation is **not complete** until test code exists and
**all its tests pass** — absent or failing tests mean the component is unfinished. Tests
are ungoverned (§13 — no `artifact_path` names them), so when they fail outside a `sync`
because the artifact drifted — e.g. the human edited the code — `assist` is the path that
fixes them.

---

## 15. Artifact kinds — `code` and `idea`

An artifact is not always a deterministic product. A strategy, a concept, a research
direction, an argument — these are artifacts an intent can govern, and they have no symbol
to match and no test to run. The entity declares which it is:

- **`code`** (default) — a deterministic artifact: source, tests, data, configuration,
  documents with mechanical structure. Everything in §1–§14 applies unchanged.
- **`idea`** — a non-deterministic artifact: prose that advances a concept. Its commitments
  are real and checkable, but checkable **by reading**, not by execution.

`artifact_kind` is **declared, never inferred** — it cannot be read off the binding (a code
artifact may be all-`semantic`) or off a file extension. The entity declares it; a contract
may override it, the same locality rule as `artifact_repo` (§2, §7). Absent, it is `code`.

### What the kind changes

Three things, and nothing else:

1. **Binding rationale** (§7) — `semantic` is the *native* binding for `idea`, not the
   binding of last resort.
2. **Tests** (§14) — an `idea` artifact generates none. This is a declared consequence of
   the kind, **not** the "mechanically impossible" exemption in §14, which exists for the
   rare untestable code component and must not be stretched to cover a whole artifact class.
3. **Verification** — for an `idea`, *verifiable* means: does the artifact address this
   commitment, judged by reading it. `audit` needs no new machinery — the verdict is
   `honored`/`violated`/`undetermined` as always, with `evidence: reasoning` and the
   `citation` pointing at the passage that carries it.

Everything else is untouched. An `idea` entity has components and contracts, an IRN, a G
floor, a `binding`, an `artifact_path`; `refine` polishes it, `audit` judges it, `sync`
forward writes it. **A commitment you cannot state is not an idea artifact — it is an
unwritten intent.** The kind relaxes the artifact's determinism, never the contract's
obligation to say something checkable (R9).

`artifact_kind` and exploration (§16) are **orthogonal**: code designs can be explored, and
an `idea` artifact can be settled.

---

## 16. Exploration — epochs, before the artifact is settled

Sometimes the intent is not yet knowable. What the artifact *should* be is the open
question, and the only way to answer it is to build one and look at the result. §1–§15
describe a settled workspace: one intent, authored, implemented. **Exploration is the phase
before that**, and it ends.

The shape is deliberately the learning loop:

    intent_1 -> artifact_1 -> finding_1 -> intent_2 -> ... -> adopt

Each pass is an **epoch**. An epoch commits to an intent, produces an artifact from it,
assesses what the artifact revealed, and hands that finding to its successor. Convergence is
reached when an epoch's assessment finds no flaw worth another pass — and **the human
declares it, never the framework** (§1).

### Two moves per epoch

- **Successor** — `intent_1 -> intent_2`. The next epoch addresses a flaw the previous one's
  finding exposed.
- **Siblings** — `(intent_A, intent_B)`. Two intents explored in parallel from the same
  parent, assessed against each other.

Siblings are why exploration is **on disk and not in git history**. A successor chain is
sequential and git holds it; comparing siblings requires both intents *and* both artifacts
present at once, at the moment of the decision. Git is single-headed; exploration is a tree
with live branches.

### Layout

An exploratory workspace is a container of epochs. Each epoch folder is a **complete intent
workspace** — its own entities, its own `compliance.yaml`, its own `.trace.md` — plus one
`epoch.md`. That regularity is what leaves every other capability exploration-blind.

```
intents/                      # intent_path — the epoch container
  captain.yaml
  0001-intent/
    epoch.md
    compliance.yaml
    .trace.md
    Entity/
  0002-intent-a/              # sibling A of epoch 2
  0002-intent-b/              # sibling B
  0003-intent/                # successor, converged from a sibling
artifacts/
  0001-artifact/
  0002-artifact-a/
  0002-artifact-b/
  0003-artifact/
```

Naming is a **rule, not a convention**:

- Epoch folder — `NNNN-intent`, or `NNNN-intent-<x>` with a lowercase sibling letter.
- Artifact folder — strictly parallel (`0002-intent-b` -> `0002-artifact-b`), so the
  artifact location is **derived, never declared**.
- Same `NNNN` reads as siblings; different `NNNN` as successive epochs. Numbers are
  chronological, never reused and never renumbered.

### `epoch.md`

Two frontmatter fields and one body section. No other key is valid.

```markdown
---
parent: 0002-intent-b
question: >
  The flaw of the parent this epoch addresses, or — for 0001 — what it explores
  from scratch.
---

## Finding

What the artifact revealed, and the flaw it carries forward.
```

- **`parent`** — an epoch folder name; empty only for `0001`. This is the **authoritative
  lineage edge** and cannot be derived from the numbering: numbers are chronological,
  lineage is not, so `0005-intent` may carry `parent: 0002-intent-b`. **Siblings are exactly
  the epochs sharing a parent**; the same-number naming is a cheap read of that fact, not
  its source.
- **`question`** — one or two sentences, written at epoch creation. It must name the flaw it
  addresses, because the finding is graded against it — a vague question yields a worthless
  finding. **Frozen once the artifact is built**: changing it retroactively invalidates a
  finding the artifact was built to produce. A wrong question is a new epoch or a sibling,
  never an edit.
- **`## Finding`** — written by `explore assess`, empty until then, **replaced on
  reassessment and never appended** (§11). Its length budget is set by the fact that **every
  future epoch reads every prior finding**: at epoch 8 you read seven before authoring.

Three rules follow from that schema:

- **Abandonment writes a finding.** A sibling dropped before its artifact is built is still
  assessed, stating why. So an empty finding means *not yet assessed* and never conflates
  with *abandoned* — and no `status` field is needed.
- **A finding naming no flaw is the `adopt` signal.** The framework surfaces the condition;
  the human still makes the call.
- **`epoch.md` is exempt from the no-backticks invariant** (§4), which binds intent files
  under an entity folder. `epoch.md` is not intent and no IRN addresses it, so `refine` never
  touches it. Only `explore` writes it; `explain` may read it.

**Ranked comparison.** When an epoch holds more than one entity under
assessment, `explore assess` additionally renders its comparison as a ranked
artifact — format and regeneration rule live in `capabilities/explore.md`.
Like `epoch.md`, it is not intent: no IRN addresses it, and `refine` never
touches it.

### Resolution — the one rule other capabilities need

Exploration is **opt-in**, declared by the presence of `explore:` in `captain.yaml`:

```yaml
intent_path: intents
explore:
  current: 0002-intent-b        # exactly one epoch is authoritative
  artifacts_path: artifacts
```

> When `explore:` is declared, the effective intent root is
> `<intent_path>/<explore.current>`, and the artifact root is `<artifacts_path>/` + the
> current epoch's derived artifact folder. Otherwise the effective intent root is
> `<intent_path>` and artifacts resolve through `repos:` (§7).

Exactly one epoch is **current**; every other is **frozen** — readable, never a source of
truth for `sync`, `audit`, or `refine`. With this one rule in place, `refine`, `sync`,
`audit`, and `assist` operate inside the current epoch **without knowing epochs exist**.

Two consequences, stated so they are not mistaken for gaps:

- **Exploration is single-repo.** During exploration the artifact root is the epoch's
  folder, so `repos:`, `code_path`, and `tests_path` do not govern epoch artifacts.
  Cross-repo exploration is out of scope.
- **Exploration ends.** `explore adopt` copies the chosen epoch's intent to the flat
  layout, verbatim — never moves it. The source epoch folder is untouched: every epoch,
  adopted or not, stays on disk as frozen history (§16 *Layout*), same as siblings and
  predecessors already do. `explore adopt` also drops `explore:` from `captain.yaml`. The
  workspace returns to §1–§15 governance at the flat root. Exploration is a **phase, not
  a mode**.

`explore` is the only capability that reads or writes epoch structure (`SKILL.md`).
