---
capability: explore
purpose: >
  Run the exploratory phase — epochs of intent, each producing an artifact whose
  result informs the next, until one is adopted. The only capability that reads or
  writes epoch structure.
---

# `explore`

**`explore` owns the phase before the intent is settled.** When what the artifact should be
is itself the open question, `explore` runs the loop — commit to an intent, build the
artifact, assess what it revealed, author the next epoch from that finding — until an epoch
is adopted (`FOUNDATION.md` §16).

It is the only capability that reads or writes **epoch structure** (`epoch.md`, the epoch
folders, `explore:` in `captain.yaml`). Inside an epoch it writes no intent and no artifact:
`sync`, `refine`, and `audit` do that, exploration-blind, through the resolution rule (§16).
`explore` moves *between* epochs; they work *within* one.

**`audit` and `explore assess` ask different questions.** `audit` asks *does the artifact
match the intent?* — per contract, into `compliance.yaml`. `explore assess` asks *was the
intent any good?* — per epoch, into `epoch.md`. They are orthogonal: an artifact can
perfectly honor an intent that turns out to be a bad idea, and that gap is the whole signal
exploration runs on. A weak `audit` result weakens the finding — an artifact that does not
even honor its intent teaches you about your implementation, not your idea.

## Trigger

```
/captain explore @action [@epoch]
```

- `@action` ∈ `{start, branch, advance, assess, adopt}`. A selector, not a behavioral
  `@mode` (`SKILL.md`) — the same shape as `sync`'s `@what`.
- `@epoch` — an epoch folder name (`0002-intent-b`). Optional; defaults to
  `explore.current`.

## The five actions

- **`start`** — initialize the exploratory workspace: create the epoch container, write
  `explore:` into `captain.yaml`, create `0001-intent/` with its `epoch.md` and its artifact
  folder. An existing **flat** workspace is converted — its entity folders,
  `compliance.yaml`, and `.trace.md` move into `0001-intent/` intact.
- **`branch`** — create a sibling of `@epoch`, sharing its `parent` (§16). When the first
  sibling of a lone `NNNN-intent` appears, rename it to `NNNN-intent-a` and carry its
  artifact folder with it. Sets the new epoch current.
- **`advance`** — create the successor of `@epoch`, with `parent: @epoch`, seeding the new
  `question` from the parent's finding. Sets it current.
- **`assess`** — read `@epoch`'s artifact against its `question` and write the finding. When
  the epoch has siblings, assess them comparatively in one pass and state which answers the
  question better, and on what evidence. Replaces any existing finding; never appends (§11).
- **`adopt`** — end exploration. Copy `@epoch`'s intent to the flat layout, verbatim —
  never move it — drop `explore:` from `captain.yaml`, and leave every epoch folder,
  `@epoch` included, in place as frozen history for the human to keep or delete. The
  workspace returns to `FOUNDATION.md` §1–§15 governance at the flat root.

## What it does

1. Read `captain.yaml` (located per `SKILL.md` → *Locating the workspace*) — `intent_path`,
   and `explore:` for `current` and `artifacts_path`.
2. For every action but `start`, resolve `@epoch` and read its `epoch.md`. For `advance` and
   `assess`, also read the **prior findings** along the `parent` chain — assembled in memory,
   used, discarded (§11; nothing aggregates them on disk).
3. Perform the action. Creating an epoch creates the folder, its `epoch.md`, and its artifact
   folder; it authors **no intent** — the human authors that, or `sync intent` does, inside
   the new epoch.
4. Update `explore.current` when the action changes which epoch is authoritative (`start`,
   `branch`, `advance`), and clear `explore:` on `adopt`.

## Output

- Epoch structure: epoch folders, `epoch.md`, artifact folders, `explore:` in `captain.yaml`.
- A concise change list on stdout (file, what, why), presented for approval **before**
  anything is written (`FOUNDATION.md` §12). `explore` is mutating and gated.
- `assess` prints the finding for approval before writing it — the finding is the signal
  every later epoch is authored from, so it is the human's to confirm.
- **Ranked comparison, when there's more than one entity to compare.** When `@epoch`
  holds more than one entity under assessment, `assess` additionally renders the
  comparison as `<artifacts_path>/<epoch's artifact folder>/ranked.md` — a plain ordered
  list, strongest to weakest, one line of justification each, derived from the same
  finding. Regenerated in full each time `assess` runs; printed alongside the finding for
  the same approval (`FOUNDATION.md` §12). Not intent — no IRN addresses it, `refine`
  never touches it, same footing as `epoch.md`.
- **No `.trace.md` entry.** The epoch structure is `explore`'s own record; `refine` and
  `sync intent` trace normally *within* an epoch (`SKILL.md` *Communication*).
- **`--dry-run`** prints the change list and exits, writing nothing (`FOUNDATION.md` §12).
  Re-run without the flag to apply.

## Completion

- `start` / `branch` / `advance` — the epoch exists, its `epoch.md` carries a `parent` and a
  `question`, its artifact folder exists, and `explore.current` names it.
- `assess` — `@epoch`'s finding is written, and it either names a flaw to carry forward or
  states that none remains (the `adopt` signal, §16).
- `adopt` — the chosen intent is at the flat layout, `explore:` is gone from `captain.yaml`,
  and the workspace passes as a settled §1–§15 workspace.

## Halt

- **`advance` from an epoch with no finding** — the successor's whole purpose is to address
  what the parent revealed; without a finding there is nothing to address. Run `assess`
  first. (`branch` is exempt: a sibling explores a parallel option, not a discovered flaw.)
- **`assess` with no artifact** — nothing to assess. Report it; the artifact comes from
  `sync code` or the human, never from `explore`. The exception is an **abandoned** sibling,
  assessed without an artifact, stating why it was dropped (§16).
- **`explore:` absent** and the action is not `start` — the workspace is flat; report that
  exploration must be started.
- **`@epoch` is frozen** and the action would write intent into it — only the current epoch
  is a source of truth (§16). Advance or branch instead of editing history.
- **`adopt` with unassessed siblings** — adopting while a parallel option is unjudged
  discards the comparison exploration exists for. Report them and ask.
- Material uncertainty about the epoch's `question` — ask on stdout; a vague question yields
  a worthless finding (§16).

## Boundary

- **Epoch structure only.** `explore` writes `epoch.md`, epoch and artifact folders, and
  `explore:` in `captain.yaml`. It never authors intent (`refine` / `sync intent`), never
  writes artifact (`sync` forward, or the human), never writes `compliance.yaml` (`audit`),
  and never touches the framework (`evolve`).
- **`assess` is not `audit`.** It records a finding per epoch, not a verdict per contract,
  and writes `epoch.md`, never `compliance.yaml`.
- **Single-repo.** During exploration the artifact root is the epoch's artifact folder;
  `repos:` does not govern epoch artifacts (§16). Cross-repo exploration is out of scope.
- Exploration is a **phase**: `adopt` ends it and returns the workspace to the flat layout.
