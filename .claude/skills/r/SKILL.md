---
name: r
argument-hint: "[-d] <prompt> | [-d] -c | close"
description: >
  Human-optimized request protocol. Governs one small request from opening to closure,
  including human handoff, request status, the short on-screen Lead, and the concise
  Report stored in append-only history. Invoke with `/r [-d] <prompt>`, `/r [-d] -c`,
  or `/r close`. `-d` explicitly opts a request into one sidecar Deliverable.
---

# `/r` — request protocol

`/r` governs one small, focused human-agent request from opening to closure.

It standardizes:

- the request lifecycle;
- when the agent must return control to the human;
- request status;
- the response shown on screen;
- the Report stored in history.

Only one `/r` request may be active at a time.

## Core model

Every turn produces two representations of the same result:

- **Lead** — shown on screen; optimized for skimming.
- **Report** — appended to history; optimized for reading. It may hold one sidecar Deliverable only when the request was opened with `-d`.

The Report may contain three layers:

1. **Lead** — status bar + Gist.
2. **Deliverable** — optional and opt-in; one explicit sidecar artifact, allowed only when the request was opened with `-d`.
3. **Body** — concise status information: Completed, Needs Attention, Next Steps.

The Report is not an execution log, and Deliverable is not an exception to that rule. Status/context
content belongs only when it changes one of these:

1. what was achieved;
2. what needs attention;
3. what happens next.

The Deliverable may contain additional content only because the human explicitly requested that sidecar
artifact with `-d`; it must never be used to preserve otherwise-discarded report prose.

Generate in this order:

1. Validate the opening invocation. If `-d` was used, identify the one concrete sidecar Deliverable explicitly requested in the opening prompt. If none exists, reject the request as `R-- | REJECTED` before doing the work.
2. Finish the work and determine the request state.
3. Produce the sidecar Deliverable only when `-d` authorized it; without `-d`, a Deliverable is forbidden.
4. Remove status/context information that does not affect achievement, attention, or next action.
5. Write the concise Body.
6. Derive the Gist from the completed result, optional Deliverable, and Body.
7. Build the canonical Report: Lead + optional Deliverable + Body.
8. Apply `/make-it-human-readable` and the `/r` text styling rules to every textual part of the Report, including prose Deliverables.
9. Write the canonical Report and the current human message to temporary files.
10. Run the mandatory `r_protocol.py commit` gate.
11. If validation fails, fix the Report and retry; do not emit a response.
12. If validation succeeds, return the command's stdout **verbatim** and nothing else.

The model drafts the Lead exactly once, inside the Report. `r_protocol.py` validates that Report, appends
the exact Human + Report turn to history, and only then extracts the canonical Lead to stdout. The final
assistant response is that stdout; it is never regenerated, paraphrased, prefixed, or extended.

**Selection comes before readability.** Never write a comprehensive status response first and merely
shorten it afterward. Deliverable is not an overflow channel for detail: without `-d` it does not exist;
with `-d` it contains only the explicit sidecar artifact named in the opening prompt.

## Mechanical enforcement — mandatory

`r_protocol.py` is part of the protocol contract, not optional lint. For every `/r` turn, use the helper
at `.claude/skills/r/r_protocol.py`. Do not manually append a turn to history and do not manually compose
the final on-screen response.

### Active-request pointer — local per-worktree

Before minting `rname` for any opening form, and whenever recovering state after context
clearing or compaction, run:

```bash
python3 .claude/skills/r/r_protocol.py active
```

This is the only correct way to determine whether a request is active and, if so, its
`rname`, `TCOUNT`, and history file. It reads a small pointer file at
`.claude/skills/r/.active/<session-id>.txt`, gitignored and local to this worktree's
checkout — deliberately independent of `history_path`, which `config.local.yaml` may
repoint at a directory shared across worktrees or machines. Never determine "the active
request" by listing or inspecting `history_path` itself: when it is shared, the most
recently touched file there may belong to a different, concurrent session.

The pointer is session-scoped (keyed by `$CLAUDE_CODE_SESSION_ID`) as well as
worktree-local, so two sessions running in the same worktree still get separate pointers.
It is written by `init`, refreshed with the new `TCOUNT` by every open `commit`, and
removed by the `commit` that closes the request — so `active` exits non-zero exactly when
no request of this session's is open. It is a convenience/recovery aid, not the source of
truth: the history file's own last status bar remains authoritative.

### Opening a request

After minting `rname`, create the history file once. For a normal request:

```bash
python3 .claude/skills/r/r_protocol.py init \
  --history "$HISTORY_FILE" \
  --rname "$RNAME" \
  --opened "$OPENED"
```

If and only if the request was opened with `-d`, add `--deliverable`:

```bash
python3 .claude/skills/r/r_protocol.py init \
  --history "$HISTORY_FILE" \
  --rname "$RNAME" \
  --opened "$OPENED" \
  --deliverable
```

`$HISTORY_FILE` is `<history_path>/<YYYYMMDD-HHMMSS>-<rname>.md`. `$OPENED` is the human-local opening
time in `YYYY-MM-DD HH:MM:SS` form. `init` must succeed before the first turn is committed. The helper
records Deliverable permission as durable request state; it cannot be enabled or disabled on later turns.

### Committing every turn

Write the exact canonical Report to `$REPORT_TMP` and the exact current human message to `$HUMAN_TMP`,
then run:

```bash
python3 .claude/skills/r/r_protocol.py commit "$REPORT_TMP" \
  --history "$HISTORY_FILE" \
  --human "$HUMAN_TMP"
```

Do not pass any per-turn Deliverable switch to `commit`. Deliverable permission is read mechanically
from the request history created by `init`; the agent cannot opt in later.

For the special protocol error of an opening `/r` call while another request is already active —
including the turn that asks the human to choose between closing and continuing — use
`--protocol-error "<one-line reason>"` instead of `--human`: a distinct turn shape, labeled
`**Protocol Error:**` in history, that is the only way an open response may preserve `TCOUNT`
instead of incrementing it. An ordinary `--human` turn always increments `TCOUNT` or closes; there
is no flag to make it do otherwise, so a continuing "still waiting" reply can never silently freeze
the counter.

`commit` must exit `0`. On failure it writes diagnostics to stderr and nothing to stdout. Fix the Report
and run it again. **Never bypass the gate and never provide a fallback response that was not emitted by
the helper.**

On success, stdout is the complete user-visible response. Return it byte-for-byte except for the final
newline. No preamble, explanation, Deliverable, Body, or commentary may be added before or after it.

## Governance

`/r` governs the whole request, including other skills invoked during it.

Other skills may control **how** work is performed. `/r` remains authoritative over:

- when control returns to the human;
- request status;
- the Lead/Report response shape.

Content that materially affects the human — required identifiers, paths, risks, assumptions,
decisions — must still be preserved, but expressed through this protocol.

If another skill governs the format of an explicitly requested `-d` Deliverable, preserve that
artifact's required domain-specific structure. `/r` still governs its textual readability and styling.

### Pull requests — `open-pr` is mandatory

When a request needs a pull request opened, `/r` never opens it itself. Delegate to the
`open-pr` skill, without exception — including when the change is a one-line docs edit and a
direct `gh pr create` would be faster.

The reason is ownership. `open-pr` governs the whole arc: branch, commit, push, open, then
drive CI and Greptile to green, and merge when merging was asked for. A PR opened outside that
skill has no owner the moment the `/r` request closes — and the request does close, because
`/r` reads "the PR is open" as an outcome. What is left behind is a PR with red CI or
unanswered review comments and nobody watching it.

This covers `gh pr create` in every form, and it covers the `github-pr-creator` skill, which
stops at "the PR is open" and is therefore not a substitute.

Take `open-pr`'s arguments from the human's request — target branch, effort, subagent count,
auto-merge. Never turn on auto-merge on your own initiative; merging stays the human's call
unless they asked for it.

`/r` still owns the response. Report the PR through the protocol's Lead and Report, not
through whatever `open-pr` prints on the way.

#### Closing a request that opened a PR

A request that opened a PR must not close as resolved while that PR is still unfinished.
Closure follows the PR's real state:

- CI green and Greptile at `5/5`, and the PR either merged or deliberately left for the human to merge — close as resolved.
- The PR is open and `open-pr` is still working it — do not return control just to announce the PR; finish the loop. When the drive agent reports back, record it as an event turn (see *Asynchronous events*) before deciding closure.
- The PR is blocked on something only the human can clear, such as a merge approval, an external review, or a failing check that needs a decision — increment `TCOUNT` and return control with the blocker in Needs Attention.
- The PR is open and green but unmerged because merging was out of scope — close as partially resolved and name the merge in Next Steps.

Name the PR number and URL in the Report on the turn the PR is created, and its final state in
the closing Report.

## Invocation

There are three invocation forms and one optional flag:

| Form | Meaning |
|---|---|
| `/r [-d] <prompt>` | open a new request |
| `/r [-d] -c` | open a chained request from the previous request's Next Steps |
| `/r close` | force the active request toward closure |

`-d` means: **this new request explicitly includes one sidecar Deliverable**. No other flags exist.

Flags belong to the new request only and never carry across chaining. A chained request therefore uses
`/r -d -c` when its inherited Next Steps explicitly call for a sidecar Deliverable.

After opening, ordinary human replies belong to the active request automatically and do not use
`/r`.

### `/r` while a request is active

Every opening form — `/r <prompt>`, `/r -d <prompt>` and `/r -c` — is valid only when no request
is active. Determine this by running `r_protocol.py active` (see *Active-request pointer*) for
this session — never by inspecting `history_path`, which other concurrent sessions may share.

Invoking one while another request is still open is a protocol error, but a recoverable one: the
human has usually just lost track of the active request. Do not reject the call, and do not guess
which way out they want. Return control and let them choose:

- **(A)** close the active request and open the attempted one — `/r close`, then
  `/r <flags> <prompt>`, both carried out by the agent;
- **(B)** continue the current request.

Until they answer:

- do not process the attempted prompt;
- do not close or modify the active request.

Keep the attempted invocation — flags and prompt text alike — in context, because option (A)
replays it verbatim.

**Option (A)** applies the ordinary `/r close` logic to the active request, then opens the
attempted request exactly as if it had been typed with nothing in its way: new `rname`, new
history file, its own `TCOUNT`, and the original flags taking effect at OPENING. Neither step
asks for further approval — the choice was the approval.

**Option (B)** leaves the request state untouched; the active request simply continues. When the
conflicting call carried prompt text, forward that text as an ordinary reply to the active
request instead of discarding what the human typed. A conflicting `/r -c` carries no text of its
own, so (B) there is a plain continuation.

The turn that poses the choice is still the protocol error itself, not a human-input turn: it
does **not** increment `TCOUNT`, and it preserves the active request's state. Commit it with
`--protocol-error`, not `--human` — see *Committing every turn*. It carries the open-turn Body,
with the two options stated under `Needs Attention`.

The human's answer is an ordinary reply to the active request and follows the normal rules from
there. Under (A) the next Report committed to that request is its closing Report; under (B) work
resumes with no change of state.

## Lifecycle

Three stages:

- **OPENING** — receive and evaluate the prompt.
- **PROCESSING** — perform the work.
- **CLOSURE** — produce the final state and close the request.

A single-turn request passes through all three in one turn.

## Human-in-the-loop turns (`TCOUNT`)

`TCOUNT` starts at `0`.

Increment it when the agent cannot continue autonomously and returns control for substantive human
input, such as clarification, a decision, approval, or a human-only blocker.

The first such response already carries `TCOUNT = 1`.

Do not increment it for:

- ordinary human follow-up messages;
- protocol misuse such as opening `/r` while another request is active, including the turn that offers the (A)/(B) choice;
- an asynchronous event (see below) — nothing was asked of the human.

## Asynchronous events

Work `/r` delegates — an `open-pr` drive agent, a background subagent, a scheduled job —
completes without a human message. That completion belongs in history, but it is not a
human turn: there is nothing to pair a Report with, and nothing is being asked of anyone.

Record it as an **event turn**:

```bash
python3 .claude/skills/r/r_protocol.py commit "$REPORT_TMP" \
  --history "$HISTORY_FILE" --event "<one line: what completed>"
```

An event turn:

- appends an **Event:** line plus the Report, in the same append-only form as a human turn;
- does **not** increment `TCOUNT`, and cannot change it;
- does **not** close the request — an event is an input to the request, not an outcome of
  it, so the closure character stays `-`;
- carries the **closing Body shape** (Completed / Needs Attention / Next Steps) and the
  closing Gist-opener rules, because it reports rather than waits. With Needs Attention at
  `- None.` the Gist opens `**Complete:**`; with anything in it, `**Action required:**`.

`--event` and `--human` are mutually exclusive, and exactly one is required.

The screen invariant is unchanged: an event turn emits its Lead and nothing else. **Never
report an asynchronous result as free prose outside the protocol.** Record its relevant outcome in
the Report Body. Do not promote event findings, diagnostics, or execution detail into Deliverable.
Deliverable remains reserved for the one explicit sidecar artifact authorized by `-d` at OPENING.

## Request name (`rname`)

Mint a short semantic name closely related to the request.

- Format: lowercase semantic slug with at least two hyphen-separated parts
- Maximum: 25 characters
- Examples: `pipeline-watch`, `merge-safety`, `storage-layout`

Favor recognizability over uniqueness.

## Request code (`rcode`)

Format:

```text
<opening><turns><closure>
```

### Opening

- `0` — accepted
- `R` — rejected because no meaningful actionable intent exists

A meaningful but unclear prompt is accepted; clarification belongs to PROCESSING.

### Turns

Second character = `TCOUNT`:

- `0` — none
- `1`–`9` — exact count
- `.` — ten or more

### Closure

- `-` — still open
- `0` — fully resolved
- `p` — partially resolved
- `/` — unresolved

Examples:

- `000` — resolved in one turn
- `01-` — open after one human handoff
- `030` — resolved after three handoffs
- `00p` — partially resolved without human handoff
- `02p` — partially resolved after two handoffs
- `01/` — unresolved after one handoff
- `R--` — rejected at OPENING

### Invariants

`00-` does not occur in normal processing: an open response that needs human input first increments
`TCOUNT`.

The agent must not unilaterally close as unresolved. `00/` is therefore reachable only through
`/r close`.

`00p` is valid only when unfinished work was deliberately left outside scope by a judgment the
agent could make alone. If a human decision, approval, or human-clearable blocker caused the stop,
return control first; closure becomes `01p` or later.

## Status message (`rmessage`)

| `rcode` | `rmessage` |
|---|---|
| `000` | `OK` |
| `0m0`, `m > 0` | `RESOLVED` |
| `0m-`, `m > 0` | `NEEDS HUMAN` |
| `0mp` | `PARTIALLY RESOLVED` |
| `0m/` | `UNRESOLVED` |
| `R--` | `REJECTED` |

## Status bar

Every response starts with:

```text
<rname> | <rcode> | <rmessage>
```

Nothing precedes it.

The last status bar is the recoverable request state. After context clearing or compaction,
recover `rname` and `TCOUNT` from it instead of resetting them. If the transcript itself is
gone, recover the same fields from `r_protocol.py active` (see *Active-request pointer*)
instead — never by inspecting `history_path` for "the" open request.

## Workflow

1. Open `/r <prompt>` or a valid chained request.
2. Mint `rname`; evaluate the prompt.
3. No meaningful actionable intent → close as `R--`.
4. Otherwise process the request.
5. If no human input is needed → continue to CLOSURE.
6. If human input is required → increment `TCOUNT`, return control with `0m-`.
7. Human replies normally; continue processing.
8. Repeat until closure.

### Unresolved

If continuing is no longer reasonable, first return control with `NEEDS HUMAN` and explain the
blocking issue. Close as `UNRESOLVED` only after the human agrees to stop or invokes `/r close`.

### `/r close`

Finish useful work already in progress, then close according to the actual state:

- fully resolved;
- partially resolved;
- unresolved.

Do not ask for another clarification, decision, or approval. `TCOUNT` does not change.

## Request chaining

Chaining always starts a **new request** from the **immediately preceding closed request**.

The new request gets its own `rname`, `TCOUNT`, lifecycle, status, and history file.

### `/r -c`

Start a new request from the previous Report's **Next Steps**.

It is valid after any closure status if meaningful Next Steps exist.

The Next Steps section becomes the new request's input. If several steps exist, include all relevant
ones unless the human narrows them.

If chaining is invalid, say so briefly and ask for `/r <prompt>`. Never invent missing context.

## History

Every `/r` request is recorded automatically.

One file per request:

```text
<YYYYMMDD-HHMMSS>-<rname>.md
```

### Where it goes — `config.yaml` and `config.local.yaml`

Two files sit next to this skill, and the effective configuration is the second layered over
the first:

- **`config.yaml`** — committed, and it **must always exist**. It carries the default every
  clone gets, and it is the schema of record: a key that appears nowhere in it is not a
  setting. Its absence is a hard error, not an empty default.
- **`config.local.yaml`** — gitignored, optional, per-machine. Any key it defines wins. Keys
  it omits fall through to `config.yaml`.

Never hand-edit `config.yaml` to suit one machine — that is what the local file is for, and a
committed edit follows every clone to machines it was never meant for.

Resolve the effective value mechanically rather than by reading the files yourself:

```bash
python3 .claude/skills/r/r_protocol.py config --key history_path
```

It prints the effective value and exits non-zero if `config.yaml` is missing. With no `--key`
it prints every effective key, each tagged with the file it came from.

**`history_path` is resolved relative to the directory holding `config.yaml`** unless it is
absolute or begins with `~`. A relative path therefore lands inside whichever worktree is
running — which is the right default for per-repo history, and the wrong one if you want a
single shared location. For one location across every worktree, set an absolute or
`~`-anchored path in `config.local.yaml`.

History is **append-only and helper-owned**. Create the file only through `r_protocol.py init`; append
every Human + Report turn only through `r_protocol.py commit`. Do not use shell redirection, an editor,
or another tool to patch an existing request history file. Corrections are new committed turns.

The helper-created header contains only durable metadata: `rname`, opening timestamp, and the immutable
Deliverable permission (`yes` or `no`). The request's state is read from the last committed Report status
bar; never patch the header with an outcome or change Deliverable permission after OPENING.

Read the final state from the last appended status bar; do not patch the header later.

History is for reference and review. It is not authoritative project memory or complete session
history.

## Lead — screen

The screen contains exactly:

```text
<status bar>

<Gist>
```

No heading, list, second paragraph, Deliverable, Body section, draft, code block, explanation, or
extra commentary may follow.

The Lead shown on screen is not regenerated. It is copied **verbatim** from the Lead stored in the
canonical Report.

### Final-output invariant

Before sending any `/r` response, validate the user-visible output as:

```text
<status bar>

<one Gist paragraph>
<EOF>
```

Anything after the Gist is a protocol violation. This remains true when the human asks to produce
a message, code, config, document, table, plan, or other content "here" or "below". That content is
the Deliverable and belongs in the Report.

Do not validate this invariant by inspection alone. The normal user-visible response must come from
`r_protocol.py commit` stdout.

### Gist

The Gist tells the human, and nothing else:

1. what came of this turn;
2. whether human action is required.

If a fact does not serve one of those two jobs, it does not belong in the Gist, no matter how
central it was to the work — that includes specific findings, names, dates, versions, identifiers,
and sub-decisions. Those belong in the Report body. The Gist states the *outcome*, not the
*evidence* for it.

Rules:

- one paragraph;
- normally one sentence per job above (outcome, then action-needed) — two sentences, not one
  sentence carrying both plus supporting detail;
- maximum two short sentences;
- maximum 50 words;
- no implementation detail.
- use inline code backticks only when an exact literal is important to the outcome or required human action; otherwise keep literals in the Report to avoid visual noise in the Lead.

Use direct openings when useful:

- `**Complete:** ...`
- `**Action required:** ...`
- `**Partially complete:** ...`
- `**Unresolved:** ...`
- `**Rejected:** ...`

**The opener is driven first by Needs Attention.** If Needs Attention contains any item, the Gist
starts with `**Action required:**` regardless of closure code; the status bar already carries
`PARTIALLY RESOLVED` or `UNRESOLVED` when applicable. If Needs Attention is `- None.`, use the opener
that matches closure: `**Complete:**`, `**Partially complete:**`, or `**Unresolved:**`. A request may
therefore close `000` while the Gist still starts `**Action required:**`.

The human must be able to stop reading after the Gist, and doing so must never cause them to miss
an item that was sitting in Needs Attention.

When a Deliverable exists, the Gist should say that it is ready and stored in the Report/history;
do not paste or preview the Deliverable on screen.

The Gist may summarize Report information because it must stand alone, but it must not copy the same
wording.

## Report — history

The Report is canonical. It contains:

1. the Lead shown on screen;
2. an optional Deliverable;
3. the Body.

The screen Lead must be an exact copy of item 1.

### Deliverable

Deliverable is a **strict opt-in sidecar artifact**, not a general-purpose place for long-form output.

A Deliverable is allowed only when **both** conditions are true:

1. the request was opened with `-d`;
2. the opening prompt explicitly asks for one concrete sidecar artifact.

Examples of valid Deliverable asks:

- "write a Slack message to Alessio";
- "draft an email reply";
- "prepare the text of a Jira comment";
- "write an announcement I can paste into Teams";
- "deliver an image showing ...".

If `-d` is present but the opening prompt does not clearly identify the sidecar artifact, reject the
request at OPENING as `R-- | REJECTED`. Do not guess a Deliverable from the work.

If `-d` is absent, a `Deliverable` section is forbidden on every turn. The helper enforces this from
the durable request state recorded at `init`.

#### What is not a Deliverable

Deliverable is **not the primary work performed by the request**. The following are request actions,
artifacts, findings, or outcomes and must never be moved into Deliverable merely to escape Report
density limits:

- source code created or modified in a repository;
- repository documentation or files written as part of the requested work;
- commits, branches, pull requests, or tickets;
- configuration changes;
- tests, analyses, audits, verification results, diagnostics, or findings;
- generated project artifacts;
- descriptions of implementation, migration, or execution work.

These belong in the work itself and, when human-relevant, are summarized under `Completed`,
`Needs Attention`, or `Next Steps`.

Use this semantic test:

> **Could this content exist unchanged as a separate artifact the human directly reads, sends, pastes,
> presents, or otherwise consumes outside the Report?**

If not, it is not a Deliverable.

#### Deliverable content

The Deliverable contains only the requested sidecar artifact itself — not a report about that artifact.

Format it as:

```text
**Deliverable**

<sidecar artifact>
```

Do not add findings, rationale, implementation notes, verification evidence, status reporting, extra
recommendations, or "here is the deliverable" framing around it. If such information matters, compress
it into the Body.

Do not duplicate Deliverable content in `Completed`, `Needs Attention`, or `Next Steps`; those sections
may refer to the artifact briefly when necessary.

A `-d` request may remain open before the artifact is ready. A fully or partially resolved `-d` request
must contain the requested Deliverable. An unresolved or rejected request may end without one.

The unified `/r` readability and Markdown styling rules apply to every textual part of the Report,
including Deliverable. An explicit tone or format requested for the Deliverable takes precedence only
where it conflicts with general `/r` styling. Non-text sidecar artifacts keep their native format; any
textual reference to them in the Report follows `/r` styling.

### Closing Body

Every closing Report contains exactly these sections, in this order:

```text
**Completed**
- ...

**Needs Attention**
- ...

**Next Steps**
- ...
```

Use `- None.` when a section has nothing material to report.

#### Completed

In-scope completed actions and verified outcomes.

- Maximum 4 bullets.
- Maximum 40 words per bullet; each bullet stays on one physical line.
- One outcome per bullet.
- One short sentence per bullet.
- Lead with the result.
- Omit the execution story unless it changes the meaning.
- Name the conclusion, not the method: collapse every check, file, workflow, or mechanism that
  fed one outcome into that one outcome. "Verified Alessio's root-cause analysis against the
  repos; it is correct" is a bullet. Listing each workflow file, resolver rule, and Terragrunt
  validation that went into confirming it is an execution log, even split across bullets.
- A bullet that names more than one system, file, or mechanism is a sign it should be one outcome
  sentence with the detail dropped, not multiple bullets.

#### Needs Attention

Only items requiring human awareness or intervention. Maximum 4 bullets; maximum 40 words per
bullet; each bullet stays on one physical line.

- decisions;
- approvals;
- blockers;
- system errors;
- impossible constraints;
- important unresolved risks.

Do not put ordinary remaining work here.

#### Next Steps

Concrete actions that remain after this turn.

- Maximum 3 bullets.
- Maximum 40 words per bullet; each bullet stays on one physical line.
- State actions, not explanations.
- Do not repeat Needs Attention.
- Add out-of-scope recommendations only when genuinely useful.

### Open-turn Body

When the agent returns control because human input is required, Body contains only:

```text
**Needs Attention**
- ...
```

Do not add Completed or Next Steps just to report progress while waiting.

The same one-section Body is used for a protocol error such as invoking `/r <prompt>` while a
request is already active; that error does not increment `TCOUNT`. Its `Needs Attention` states
the (A)/(B) choice the human has to make.

## Density filter

Apply these rules strictly to all textual Report prose, including prose Deliverables. Deliverable
is not exempt from the human-readability goal; its explicitly requested content and format must still
be preserved:

- one idea per sentence;
- one outcome per bullet;
- no nested lists;
- no Body subsections beyond the protocol sections;
- no prose paragraphs inside Body sections;
- no chronological narration;
- no intermediate reasoning;
- no command output unless the evidence itself matters;
- no routine implementation rationale;
- no incidental findings unless they affect the request;
- no duplication between Body sections;
- no repeated explanation in Next Steps.

For every Report detail outside the explicitly requested sidecar artifact itself, ask:

> **If removing it does not change what was achieved, what needs attention, or what happens next, remove it.**

This rule overrides the impulse to be comprehensive about execution. `-d` does not weaken it: only the
explicitly requested sidecar artifact is protected from outcome-level compression.

## Readability

After filtering, apply `.claude/skills/make-it-human-readable/SKILL.md` to every textual part of the
Report, including Deliverable.

That skill improves wording and sentence structure only. It must not reintroduce discarded detail. If
the human explicitly requested a specific Deliverable tone or format, preserve that requirement while
still applying the common `/r` readability and Markdown styling rules.

Prefer plain language for prose and use Markdown consistently to expose structure:
**bold** for semantic emphasis and `backticks` for literals.

### Literals

Use inline code backticks for literals that the human should visually distinguish from prose,
including:

- file and directory names;
- paths;
- branch names;
- workflow and job names;
- commands and command fragments;
- configuration keys and literal values;
- identifiers, tags, versions, and status values when referenced literally;
- code symbols and expressions.

Examples: `main`, `II-442`, `mda>=0.9.0`, `workflow_dispatch`,
`06-publish-provider-image.yml`, `mda-pod:0.10.0`.

Do not use backticks merely for emphasis or around ordinary concepts, roles, or product names.

Apply this rule to the entire textual Report, including Deliverable. Deliverables are sidecar artifacts,
not repository code/config work; where a non-text artifact is referenced, style the surrounding Report
text normally.

Success means:

- the screen ends immediately after the canonical Gist;
- the human can understand state and required action from that Lead;
- Deliverable appears only for `-d` requests and contains only the explicit sidecar artifact;
- the Report can be read quickly without encountering an execution diary.

## Mechanical validation contract

The prose rules above define semantics; the helper enforces the mechanically checkable subset. In
particular, `r_protocol.py` rejects invalid status/message pairs, `00-`, malformed Report sections, Gists
over 50 words, excess or multiline Body bullets, unauthorized Deliverables on non-`-d` requests, missing
Deliverables on resolved/partial `-d` requests, non-empty Needs Attention without `Action required:`, invalid
request-state transitions, and commits after closure.

The script cannot judge whether the agent selected the *right* facts, whether prose is genuinely
human-readable, or whether a `-d` opening prompt semantically names a legitimate sidecar artifact. Those
remain model responsibilities. Passing the helper is necessary, not sufficient.
