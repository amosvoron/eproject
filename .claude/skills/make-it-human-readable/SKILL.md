---
name: make-it-human-readable
description: Rewrite AI-generated, compressed, jargon-heavy, or assumption-heavy prose into text a human can follow without reconstructing the author's reasoning. Use this whenever the user asks to make text "human readable", "clearer", "less dense", "less AI-sounding", to "de-jargon", "unpack", or "simplify" prose, or to prepare documentation, runbooks, PR descriptions, onboarding docs, or workflow explanations for readers who lack insider context — even if they only say "clean this up" or "make this understandable".
---

# make-it-human-readable

## Purpose

Rewrite AI-generated, technical, compressed, or assumption-heavy prose so that a human reader can understand it easily without having to reconstruct the author's reasoning.

The goal is not merely to simplify vocabulary. The goal is to reduce the amount of interpretation required from the reader while preserving the original meaning, rules, constraints, and technical accuracy.

## Core principle

**Make the reader follow the process instead of infer the process.**

A human-readable text should make clear:

- what happens,
- who does it,
- in what order,
- under what conditions,
- why it matters,
- and what state or outcome results.

Do not optimize for maximum information density. Optimize for understanding.

This principle applies at every level of the text: the document's section structure, the ordering of paragraphs, and the wording of individual sentences. The skill rewrites the document as a whole — it does not process it section by section with the structure treated as fixed.

## Two boundary conditions

Before applying the characteristics below, respect two limits.

### Never state what the source does not support

Making implicit relationships explicit is the heart of this skill, and it is also its main risk: it tempts the rewriter to invent specifics the source never stated. Expansion must surface meaning that is genuinely present in the source — stated, or clearly and unambiguously implied. It must never fill gaps with plausible guesses.

If the source does not say who performs an action, when a condition is checked, or what happens in a failure case, and the answer cannot be safely inferred:

- do not invent an actor, step, or condition;
- either keep the same level of vagueness as the source, ask the user, or flag the gap explicitly (for example: *"The source does not say who approves this step."*).

A rewrite that reads smoothly but asserts facts the source never contained is a failed rewrite, even if every individual sentence is clear.

### Calibrate expansion to the intended reader

"Human-readable" depends on who the human is. A doc for new team members needs branch–environment relationships spelled out; a doc for the engineers who built the system does not need `PR` expanded or `merge` explained.

- If the user states the audience, calibrate to it.
- If the audience is unclear and it materially affects how much to expand, ask.
- Otherwise, default to a competent professional who is new to *this specific system or workflow*: expand insider shorthand and system-specific relationships, but do not explain general professional vocabulary.

If the source text is already clear for its intended reader, say so and either return it unchanged or make only minimal targeted edits. Do not force a full rewrite onto text that does not need one.

## Main characteristics of human-readable text

### 1. Treat the document's structure as part of the rewrite

The section layout of the source is not sacred. Sections, their titles, and their order exist to serve the reader, and in AI-generated or organically grown documents they often don't: related content is scattered, one section covers three unrelated topics, or the order forces the reader to jump ahead for context.

Inspect every section together with its title and ask whether the current structure is the clearest way to present the content. You are free to:

- reorder sections so context comes before the material that depends on it,
- merge sections that cover the same topic or that are too small to stand alone,
- split a section that covers several distinct topics,
- retitle sections so the title accurately describes what the reader will find,
- promote or demote heading levels when the hierarchy misrepresents the content.

Restructure only when it improves understanding — if the existing structure is already the clearest arrangement, keep it. When you do restructure, the information-preservation rules still apply in full: content may move, merge, or split, but nothing may be lost or weakened, and cross-references and links to renamed or moved sections must be updated to match.

### 2. Explain processes in chronological or logical order

When the source describes a workflow, present the steps in the order in which they actually happen.

Prefer:

> The manifest is first deployed to development. We let it run there long enough to be confident that it works correctly. We then create a promotion PR.

Avoid starting with an abstract conclusion and forcing the reader to reconstruct the sequence.

### 3. Use explicit subjects and actions

State who performs an action and what they do.

Prefer:

> The person opening the promotion PR decides when the manifest is ready for production.

Avoid:

> Readiness is determined at promotion time.

Use concrete verbs such as: create, merge, deploy, run, review, decide, compare, remove, update, approve.

Prefer active constructions when they improve clarity.

### 4. Prefer concrete operational language over compressed abstractions

Describe what actually happens in the system.

Prefer:

> We create a new PR that merges `main` into `release`.

Avoid:

> Promotion is performed through branch synchronization.

The rewritten text should let the reader visualize the operation.

### 5. Introduce context before conclusions

Do not assume that the reader already understands the relationship between concepts, branches, environments, or states.

If `main` represents development and `release` represents production, make that relationship clear when it matters.

Explain the context first, then state the conclusion or rule.

### 6. Make implicit relationships explicit

Do not require the reader to infer important connections — provided the connection is actually present in the source (see the boundary conditions above).

For example, instead of:

> Once promoted, the release branch contains the manifest.

Prefer:

> Once the promotion PR is merged into `release`, the manifest is considered promoted to production.

Explicitly connect:

- branches to environments,
- actions to outcomes,
- conditions to decisions,
- terms to their operational meaning.

### 7. Keep one primary idea per sentence

Break apart sentences that contain several independent ideas, conditions, exceptions, or conclusions.

Dense technical sentences often become easier to understand when converted into two or three shorter sentences.

Do not shorten sentences mechanically. Split them where the reader would otherwise need to hold several concepts in memory at once.

### 8. Optimize for understanding, not information density

Useful repetition is allowed.

Repeat an important noun or concept when replacing it with a pronoun or abstraction would make the reader work harder. For example, repeating `manifest`, `promotion PR`, or `release` can be clearer than aggressively avoiding repetition.

The rewrite will often be longer than the source. That is acceptable — but every added sentence must reduce the reader's effort, not pad the text. Conciseness is valuable only when it does not reduce clarity; length is valuable only when it buys understanding.

### 9. Define important terms through observable actions or states

When a term such as *promoted*, *deployed*, *approved*, or *ready* has a specific operational meaning, explain what event makes that term true.

Prefer:

> Once that PR is merged into `release`, the manifest is considered promoted to production.

This is better than relying on the reader's assumed understanding of *promoted*.

### 10. Avoid unexplained technical shorthand

Do not replace an explanation with technical shorthand when the shorthand requires the reader to already know what it means.

Avoid:

> There is no automated soak-time check.

Prefer:

> There is no automated check that tells us when enough time has passed.

Technical terms are useful when they add necessary precision. They are harmful when they merely compress an idea that can be stated clearly in ordinary language. If a domain term must remain, explain it the first time it appears.

### 11. Preserve all original rules and constraints

Human-readable rewriting must not silently weaken, omit, or change requirements.

Before rewriting, identify:

- mandatory rules,
- prohibited actions,
- conditions,
- exceptions,
- sequencing constraints,
- exact relationships between systems or branches.

A rewrite is not successful if it is easier to read but less accurate.

## Transformation procedure

When rewriting text, follow this process.

### Step 1: Read the entire text, then extract the meaning

Read the whole document before rewriting any part of it. Do not rewrite section by section as you go — the right structure and the right level of expansion for each section only become visible once you know everything the document contains.

From the full text, identify the main point, the sequence of events, the actors, the conditions, the rules, and the outcome. Do this before changing the wording. Note anything the source leaves genuinely unspecified — these are the places where you must not invent.

### Step 2: Assess the structure

With the whole document in view, evaluate the section layout: titles, order, granularity, and hierarchy. Decide whether to reorder, merge, split, or retitle sections (see characteristic 1). Settle the target structure before rewriting sentences — restructuring afterward wastes work and risks losing content in the move.

### Step 3: Identify compressed or assumption-heavy language

Look for:

- jargon and internal shorthand,
- noun-heavy phrases,
- abstract passive constructions,
- long sentences with multiple clauses,
- references whose meaning is only obvious to insiders,
- phrases that compress an entire process into one term.

### Step 4: Reconstruct the process explicitly

Rewrite the content as a sequence the reader can follow. When useful, use this pattern:

1. What happens first.
2. What happens next.
3. Who decides or acts.
4. What rule applies.
5. What final state results.

### Step 5: Replace unnecessary shorthand

Expand technical shorthand into plain language unless the term is important to the domain. If the technical term must remain, explain it the first time it appears.

### Step 6: Check information preservation — in both directions

Compare the rewrite with the source and confirm:

- no rule, condition, restriction, or exception has disappeared, **and**
- no actor, step, condition, or claim has been added that the source does not support.

If you restructured, check the moved content specifically — merges and splits are where sentences silently fall out. Confirm that every piece of content from a merged or split section landed somewhere, and that internal cross-references and links still point to the right places under the new titles.

### Step 7: Read from the perspective of the intended reader

Ask:

- Does the section order let this reader build up context as they go, without jumping ahead?
- Would this reader understand what happens?
- Would they know who performs each action?
- Would they know when the process starts and ends?
- Would they know what is allowed and what is not allowed?
- Is any phrase understandable only to an insider?

If the reader must infer an important step that the source does contain, make it explicit. If the source itself omits the step, flag it instead of inventing it.

## Style quick reference

Use: plain direct language, concrete verbs, explicit actors, chronological ordering for workflows, short to medium-length sentences, paragraphs grouped by purpose, technical terms only when they add precision.

Avoid: unexplained jargon and acronyms, insider shorthand, noun-heavy abstractions, excessive passive voice, overly long sentences, clever phrasing, aggressive removal of useful repetition, and any change to technical meaning in the name of simplicity.

## Example

### Original AI-generated text

> A manifest is ready to promote once it has been live on `main` (i.e. already deployed to dev) long enough to be confident it's correct — there is no automated dev soak-time check, this is a judgment call by whoever opens the promotion PR. Promoting is not a new content change: the promotion PR's diff should be exactly the `main` commits not yet on `release`, never hand-edited manifests.

### Human-readable version

Promotion is not automatically triggered when a manifest is merged into `main` and deployed to the dev environment. We first let the manifest run in development long enough to be confident that it works correctly. There is no automated check that tells us when enough time has passed. The person opening the promotion PR decides when the manifest has been tested in development long enough and is ready for production.

To promote it, we create a new PR that merges `main` into `release`. This PR must contain exactly the commits that are already on `main` but not yet on `release`. No manifests should be edited or changed as part of the promotion PR.

Once that PR is merged into `release`, the manifest is considered promoted to production.

### Why the rewrite is better

The rewrite:

- presents the workflow in chronological order,
- makes the actors and actions explicit,
- explains the relationship between `main`, development, `release`, and production,
- replaces the insider phrase *soak-time check* with a direct explanation,
- separates distinct ideas into separate sentences,
- preserves the rule that promotion must contain only existing `main` commits,
- explicitly prohibits editing manifests during promotion,
- defines exactly when the manifest is considered promoted,
- adds nothing the source did not state or clearly imply.

## Quality checklist

Before returning a rewritten text, verify:

- [ ] The original meaning is preserved.
- [ ] All rules, constraints, and exceptions are preserved.
- [ ] Nothing has been added that the source does not state or clearly imply.
- [ ] Genuine gaps in the source are flagged or left open, not filled with guesses.
- [ ] The section structure (order, titles, granularity) serves the reader; sections were reordered, merged, or split where that improves understanding.
- [ ] If sections were restructured, no content was lost in the move and cross-references were updated.
- [ ] The process is presented in a natural chronological or logical order.
- [ ] Important actors are explicit.
- [ ] Actions use concrete verbs.
- [ ] Important relationships are stated rather than implied.
- [ ] Technical shorthand is removed or explained.
- [ ] Each sentence has one primary idea where practical.
- [ ] Useful repetition has not been removed merely for stylistic variety.
- [ ] Important terms are defined through observable actions or states.
- [ ] The level of expansion fits the intended reader.
- [ ] The rewrite is easier to understand, not merely shorter (or longer).

## Output expectation

Return only the rewritten content unless the user explicitly asks for an explanation, a before/after comparison, annotations, a list of changes, or a critique. One exception: if you flagged gaps in the source (unspecified actors, conditions, or steps), list those flags briefly after the rewrite so the user can resolve them.

If the source is already clear for its intended reader, say so instead of forcing a rewrite.

When rewriting, preserve Markdown formatting conventions, code blocks, commands, branch names, identifiers, technical names, and other syntax that carries meaning. Rewrite prose only — never alter code, configuration, or identifiers. The document's section structure is not protected by this rule: sections may be reordered, merged, split, or retitled as described in characteristic 1, as long as code blocks and other meaning-carrying syntax move intact with their surrounding content.
