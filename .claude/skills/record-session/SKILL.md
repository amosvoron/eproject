---
name: record-session
description: Save the minimum recovery context needed to continue work after /clear, or restore that context with /record-session restore. Uses .memory/session.md as a short recovery index that points to authoritative memory and project files and stores only the small unrecoverable live-context diff.
---

# record-session

Preserve only the minimum context required to continue the current work after `/clear`.

This skill has two modes:

- `/record-session` - record the current recovery state into `.memory/session.md`.
- `/record-session restore` - restore the working context from `.memory/session.md` after `/clear`.

The session file is a **recovery bootstrap**, not a conversation summary, transcript, memory archive, or compacted session.

## Core principle

Optimize for this test:

> After `/clear`, reading `.memory/session.md` and following its references should provide exactly enough context to continue the work seamlessly, without reconstructing the full previous conversation.

Use **recoverability**, not token count, to determine what belongs in the session file:

- If information already exists in a durable file, store only a reference to that file.
- If information exists only in the live session and is necessary to continue, store the smallest sufficient statement.
- If information is not necessary for seamless continuation, omit it.

Never use this skill as `/compact`.

---

# Mode: record

Use this mode for `/record-session` with no `restore` argument.

## Goal

Overwrite `.memory/session.md` with the smallest useful recovery index for the current work.

The file may already exist or may not exist:

- If it exists, overwrite it completely.
- If it does not exist, create it.

Do not merge with, append to, or preserve old session recovery state.

## Procedure

### 1. Identify the current work

Determine what the user would expect to continue immediately after `/clear`.

Focus only on active work, relevant decisions, current state, and the next useful continuation point.

Do not preserve unrelated topics merely because they appeared earlier in the conversation.

### 2. Find already-persisted context

Inspect the project for durable files that already contain relevant context in structured form.

Give highest priority to memory files, especially files under `.memory/` created or maintained by memory-oriented workflows such as `/mem`.

Also use other authoritative project files when they already contain context needed for recovery, for example:

- specifications
- plans
- decision records
- design documents
- task files
- drafts being actively edited

Prefer authoritative, narrow references over broad references.

### 3. Store references, not duplicated content

For every relevant durable source, add a short instruction describing exactly why it should be read during restore.

Preferred form:

```markdown
- Read `.memory/<file>.md` for <specific kind of context needed to continue>.
```

Examples:

```markdown
- Read `.memory/architecture.md` for the accepted architecture and design decisions.
- Read `.memory/current-plan.md` for the active implementation plan and completed steps.
- Read `docs/provider-base-rebuild.md` for the draft currently being refined.
```

Do not summarize the contents of those files into `session.md`.

### 4. Compute the live-context diff

Compare the context required for continuation with what can already be recovered from the referenced files.

Only the remainder is the **session diff**.

Store a piece of the diff only when all of these are true:

1. It is not already recoverable from a referenced durable file.
2. It matters for seamless continuation after `/clear`.
3. Losing it would cause meaningful rework, ambiguity, or a wrong continuation.

Typical valid diff items include:

- a decision made in the live conversation but not yet written elsewhere
- the exact current stopping point
- a small unresolved question or constraint
- the immediate next action when it is not represented in another file
- a temporary assumption needed to continue the active work

Express each item in the shortest unambiguous form.

### 5. Apply an aggressive omission test

Before writing each line, ask:

> If this line is removed, can the work still be resumed correctly by following the remaining references?

If yes, remove it.

Do not include:

- conversation history
- rationale already stored elsewhere
- broad summaries of the session
- facts that are merely useful or interesting
- duplicate decisions
- completed discussion that has no effect on the continuation
- generic user preferences unless required for the active work
- information recoverable from source control or referenced files

### 6. Write `.memory/session.md`

Keep the file short and operational.

Use this structure only as needed:

```markdown
---
id: session
title: Session recovery — <the active work, in a few words>
updated: <YYYY-MM-DD>
status: active
ticket: <II-NNN, or: none>
---

# Session recovery

- Read `<path>` for <specific recovery purpose>.
- Read `<path>` for <specific recovery purpose>.

## Live diff

- <only unrecoverable context required to continue>
- Next: <immediate continuation point, only if not recoverable elsewhere>
```

Omit `## Live diff` entirely when there is no necessary diff.

Do not add empty sections.

**The frontmatter is required and is not optional decoration.** `.memory/README.md` requires it on
every file in the workspace except `INDEX.md`, and `.memory/bin/mem-check.py` reports its absence
on every run — so omitting it leaves a permanent complaint that trains people to stop reading the
checker's output.

It also earns its place here. `updated:` is what tells a restore whether the bootstrap it is about
to trust was written today or three weeks ago, and `status: active` is what makes the checker say
so out loud once the file goes stale. Set `updated:` to the date you write the file, and name the
ticket the active work belongs to when there is one.

A session file containing only a few references is ideal when those references are sufficient.

## Record-mode quality check

Before finishing, verify:

- `.memory/session.md` was overwritten rather than appended.
- The frontmatter is present, and `updated:` is today's date.
- Every referenced file is relevant to the active work.
- Every reference explains what should be recovered from that file.
- Referenced information was not duplicated inline.
- Inline information is limited to the unrecoverable live diff.
- The result is substantially smaller than a normal session summary.
- Nothing was included solely to preserve conversational history.
- The file is enough to resume work after `/clear`.

---

# Mode: restore

Use this mode for:

```text
/record-session restore
```

## Goal

Recover the minimum working context saved by the last `/record-session` and make it available to the current session so work can continue after `/clear`.

Do not create a new summary and do not rewrite `.memory/session.md` during restore unless the user separately asks to record the session again.

## Procedure

### 1. Read the recovery file

Read `.memory/session.md`.

If it does not exist, report briefly that no recorded session is available and stop the restore operation.

### 2. Follow its references

Read the files explicitly referenced by `.memory/session.md` that are needed for recovery.

Treat those referenced files as the authoritative source for the context they cover.

Follow the purpose stated beside each reference. Do not broaden the restore into unrelated files or project-wide exploration unless a referenced file itself requires another source to understand the recorded context.

### 3. Apply the live diff

Incorporate any inline `Live diff` items from `.memory/session.md` on top of the referenced durable context.

The diff supplements the referenced files; it does not override them unless the session file explicitly records a newer decision.

When the session file clearly records a newer live-session decision than a referenced file, use the newer decision for continuation and treat updating the durable source as pending work when relevant.

### 4. Reconstruct working state, not conversation history

Restore only what is needed to act correctly:

- active objective
- relevant constraints
- accepted decisions
- current artifact or work state
- unresolved issue, if any
- immediate continuation point

Do not attempt to recreate the wording, chronology, or full contents of the cleared conversation.

### 5. Continue from the recorded point

After restoration, behave as if the necessary working context had remained available across `/clear`.

Do not require the user to repeat information recovered successfully from the referenced files or session diff.

Briefly confirm what was restored at a high level, then continue with the user's next instruction.

## Restore-mode quality check

Verify that:

- `.memory/session.md` was read first.
- Relevant references in it were followed.
- Referenced files were treated as authoritative rather than re-summarized into a new memory artifact.
- The live diff was applied only where needed.
- No unrelated historical context was reconstructed.
- The active work can now continue without asking the user to restate recovered information.

---

# Examples

## Good recorded session

```markdown
---
id: session
title: Session recovery — provider release documentation
updated: 2026-09-22
status: active
ticket: II-541
---

# Session recovery

- Read `.memory/provider-framework.md` for the provider build/release model and accepted terminology.
- Read `docs/provider-release.md` for the text currently being edited.

## Live diff

- The latest rewrite should avoid the phrase `soak-time check`; explain it plainly instead.
- Next: refine the paragraph about promotion readiness.
```

This is good because the durable files contain almost all context and `session.md` stores only the small live-session delta.

## Better when no diff is needed

```markdown
---
id: session
title: Session recovery — DataDog observability spike
updated: 2026-09-22
status: active
ticket: II-515
---

# Session recovery

- Read `.memory/datadog-spike.md` for decisions, constraints, and open questions.
- Read `spikes/datadog-aks.md` for the current spike draft and continuation point.
```

Do not add a summary just to make the file look more complete.

## Bad recorded session

```markdown
# Session recovery

We spent the session discussing the architecture. First we considered option A, then option B...
<several paragraphs summarizing the discussion>
```

This is session compaction and defeats the purpose of this skill.

---

# Non-goals

`record-session` must not:

- replace `/compact`
- summarize the entire conversation
- persist every useful fact
- duplicate structured memory
- become a permanent project knowledge base
- preserve conversational chronology
- infer that more context is safer

The best `session.md` is the smallest recovery map that lets the next empty session continue correctly.
