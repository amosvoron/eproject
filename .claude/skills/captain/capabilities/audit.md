---
capability: audit
purpose: >
  Report whether the contracts in intent are honored by the artifact.
  Writes only <intent_path>/compliance.yaml; modifies neither intent nor code.
---

# `audit`

**`audit` answers one question — do the contracts hold against the artifact? — and
records the answer in `<intent_path>/compliance.yaml`.** It does not modify intent. It does not
modify code. A `not-honored` verdict is a successful audit of a non-conforming artifact,
not a capability failure — `audit` reports the world as it finds it.

## Trigger

```
/captain audit @irn
```

- `@irn` — the scope to audit: an entity, a component, or a single contract. Omitted →
  the whole workspace.

## What it does

1. Assemble the in-memory view from the intent files under `@irn` and resolve each
   contract's artifact via `captain.yaml` + `artifact_path` (`FOUNDATION.md` §7, §11).
   Under exploration, the intent root and artifact root are the **current epoch's**
   (`SKILL.md` → *Exploratory workspaces*, §16); `compliance.yaml` is then per-epoch.
   `audit` never judges a frozen epoch — only the current one is a source of truth.
2. Run the **intent-clarity checks** (`FOUNDATION.md` §11): every IRN in prose resolves;
   no floating nouns. A failure here halts — an unclear contract cannot be judged.
3. Evaluate every contract against its artifact, per its `binding`:
   - `name` / `shape` / `literal` — **mechanically checkable** (symbol exists / shape
     conforms / bytes equal).
   - `semantic` — **judged** step-by-step against the numbered body. Cite the code each
     step rests on.

   For `artifact_kind: idea` (`FOUNDATION.md` §15) the machinery is unchanged: judge whether
   the artifact **addresses** each commitment, by reading it. The verdict vocabulary is the
   same, `evidence` is `reasoning`, and `citation` points at the passage that carries it —
   a section heading or a quoted line, never a fabricated line number.
4. Write `<intent_path>/compliance.yaml` (below), fully regenerated for the scope. No
   acyclicity or orphan check — the framework owns no dependency graph (`FOUNDATION.md`
   §10–§11).

## `compliance.yaml` — format

**One file for all contracts**, keyed by IRN. Fully replaced on each run for the audited
scope; history lives in git.

```yaml
audited_at: <ISO 8601 timestamp>
contracts:
  Executor.manifest_executor.InputContract.v1_0:
    binding: name
    verdict: honored            # honored | violated | undetermined
    evidence: test | code-trace | reasoning
    citation: <file[:lines] | test name>   # required when honored
    reason: <one sentence>      # required when violated | undetermined
  Registry.cicd.RegistryCicdDeployContract:
    binding: semantic
    verdict: violated
    evidence: reasoning
    citation: deploy_manifest.py:60-95
    reason: immutability check (step 6) is missing
totals:
  contracts: <n>
  honored: <n>
  violated: <n>
  undetermined: <n>
```

- **`verdict`** — three honest values. `violated` = a real gap; `undetermined` = the
  agent could not establish either way (e.g. a `semantic` step it cannot judge from the
  code). Both are non-honored, distinguished by `reason`.
- **`evidence`** — `test` (a passing test asserts it), `code-trace` (a named thing
  located in code), or `reasoning` (read semantically). **No citation → cannot be
  `honored`.** A `test` is incidental evidence (`FOUNDATION.md` §14), not a requirement —
  most verdicts rest on `code-trace` or `reasoning`.
- **`citation`** — required when `honored`; recommended otherwise (point at the gap).

## Output

- `<intent_path>/compliance.yaml`, fully regenerated for the scope. `audit` is exempt
  from the approval gate (`FOUNDATION.md` §12) — it writes `compliance.yaml` directly,
  touching no artifact, intent, or framework.
- A one-line stdout summary: `N contracts: X honored, Y violated, Z undetermined.`
- Anything needing prose → stdout (the session is the prose channel; `audit` writes
  only `compliance.yaml`, never `.trace.md`).

## Halt

- The IRN does not resolve, or a contract lacks a `binding`/`artifact_path` → report;
  suggest `refine`. `audit` cannot record a verdict against an incomplete contract.
- A clarity check fails (unresolved IRN, floating noun) → report; suggest `refine`.
- Material uncertainty about a contract's *meaning* (distinct from inability to judge an
  artifact — that is an `undetermined` verdict, a recorded outcome, not a halt).

## Boundary

- `audit` reports; `sync` reconciles. After a clean `sync`, `audit` should report all
  honored; persistent `violated` means intent the artifact cannot satisfy.
- `audit` writes only `compliance.yaml` — never intent, never code, never the framework,
  never epoch structure.
- **`audit` is not `explore assess`.** `audit` asks *does the artifact match the intent?*,
  per contract. `explore assess` asks *was the intent any good?*, per epoch, into `epoch.md`
  (`FOUNDATION.md` §16). An artifact can honor every contract of an intent that turns out to
  be a bad idea; `audit` reports the first, `explore` the second, and a weak `audit` result
  weakens the epoch's finding.
