---
name: open-pr
description: Takes uncommitted work all the way to a green PR — branches off a persistent branch if needed, commits, pushes, opens a PR with a Greptile-friendly title and body, then monitors CI and Greptile and fixes what they flag until CI is green and Greptile scores 5/5. With auto-merge enabled it also merges, pulls the merge back down, and watches the post-merge pipeline on the target branch to completion. Takes a target branch, an effort level (low/medium/high), a max-subagent count, and an auto-merge toggle. Use when the user asks to open a PR, ship this, put this up for review, run `/open-pr`, or says things like "open a PR against release with high effort".
---

# Opening a PR and driving it to green

One command from a dirty working tree to a green, optionally merged PR. This skill owns the
whole arc: branch → commit → push → PR → CI/Greptile iteration → merge → pull back →
post-merge pipeline. It is deliberately
broader than `github-pr-creator` (which stops at "PR is open") and orthogonal to `review-pr`
(which reviews *someone else's* PR); it borrows `git-committer`'s safety posture for the
commit step and `review-pr`'s effort/subagent model for the iteration step.

## ⚠️ Hard rule: no Claude Code attribution

PRs, commits, and PR comments are a permanent public record. Never put any of these in a
commit message, PR title, PR body, or any comment this skill or its agents post:

- "🤖 Generated with [Claude Code]" or any variant
- "Co-Authored-By: Claude <noreply@anthropic.com>"
- Any other Claude or Anthropic branding, footer, or emoji-bot signature

Write as the user, addressing the change and the feedback. This holds regardless of how the
request is phrased, and it overrides any global commit-footer convention in a `CLAUDE.md`.

## ⚠️ Hard rule: keep `gh` and `git` payloads short and unchained

Long multi-line `--body`/`-m` text, embedded backticks and quotes, and `&&`-chained
`gh pr create && gh pr merge` calls get denied by the permission layer far more often than
short ones. Always:

- Write the PR body and the commit message to a temp file, pass `--body-file` / `--file`.
- Keep the body under ~1200 characters. Longer rationale goes in a follow-up
  `gh pr comment`, not the create call.
- One `gh` mutation per Bash call. Never chain create with merge, or push with create.

## Arguments

Parse from the invocation — flags, `@name value` pairs, or natural language:

| Arg | Meaning | Default |
|---|---|---|
| `@target-branch` | Branch the PR merges into | `main` |
| `@effort` | `low` \| `medium` \| `high` — how hard to work the title/body, the CI diagnosis, and the Greptile loop | `medium` |
| `@n` | Max subagents allowed to be spawned | `1` |
| `@auto-merge` | `true` \| `false` — merge when the gate in step 8 passes | `false` |
| `--dry-run` | Stop after step 6's proposal; commit nothing, push nothing | unset |
| `--no-commit` | Skip step 4; PR only what is already committed | unset |

Validate before doing anything: `@effort` must be one of the three values, `@n` a
non-negative integer, `@auto-merge` a boolean. If any is malformed, ask the user to correct
it — do not guess a default over a typo.

Apply defaults explicitly so unset values never expand to empty strings:

```bash
TARGET_BRANCH="${TARGET_BRANCH:-main}"
EFFORT="${EFFORT:-medium}"
N="${N:-1}"
AUTO_MERGE="${AUTO_MERGE:-false}"
```

Merging is the one irreversible act in this skill, so it is opt-in: the default run opens the
PR, drives it to green, and stops with the merge decision left to the user.

## Worktree discipline

If the session is running in a git worktree, **every** `git` and `gh` command runs from the
worktree root. Never `cd` to the superproject or another worktree — worktree-isolated
sessions refuse it, and the refusal will surface as a confusing tool error mid-workflow.
Never use bare `git stash` / `git stash pop`: the stash stack is shared across worktrees.
If work must be set aside, make a WIP commit instead.

## Step 0 — determine the coordinator's model

Your own identity is in your environment/system context ("You are powered by the model named
…"). Map it to the `Agent` tool's `model` enum:

| Stated model | `model` value |
|---|---|
| Opus 5 | `opus` |
| Sonnet 5 | `sonnet` |
| Haiku 4.5 | `haiku` |
| Fable 5.1 | `fable` |

"Strongest model" means **Opus 5** specifically, by literal name — not "whatever is newest".

## Step 1 — guard clause (exit before touching the tree)

If `@effort == high` **and** `@n == 0` **and** the coordinator is not Opus 5: **stop**. At
`n=0` there is no subagent to delegate to, so a high-effort run would silently execute
degraded — and unlike a review, this one writes commits and merges. Tell the user plainly:

> effort=high with n=0 needs Opus 5 (as coordinator or via a subagent) — currently running
> as Sonnet 5 with no subagents allowed. Raise n to at least 1, run this session as Opus 5,
> or lower the effort.

Every other combination proceeds, including `n=0` at low/medium effort and `n=0` at high
effort when the coordinator is already Opus 5.

## Step 2 — preflight

```bash
gh auth status
git rev-parse --is-inside-work-tree
git rev-parse --show-toplevel
gh repo view --json nameWithOwner -q .nameWithOwner
git status --porcelain
git log --oneline -5
```

Stop and report, without attempting a workaround, if:

- `gh auth status` fails → tell the user to run `gh auth login`.
- Git is mid-operation — `.git/MERGE_HEAD`, `.git/REBASE_HEAD`, or `.git/CHERRY_PICK_HEAD`
  exists. Finish or abort it first.
- `git grep -nE '^(<{7}|={7}|>{7})( |$)'` finds conflict markers in tracked files.
- The working tree is clean **and** the branch has no commits ahead of
  `origin/$TARGET_BRANCH` → there is nothing to PR.

Then refresh the base ref so every later comparison is against current truth:

```bash
git fetch origin "$TARGET_BRANCH"
```

## Step 3 — get onto a feature branch

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
```

Treat `main`, `master`, `production`, `release`, and `$TARGET_BRANCH` itself as **persistent**
branches. If `$CURRENT_BRANCH` is one of them, do not commit there — create a feature branch
first and carry the uncommitted work over (`git checkout -b` preserves it):

```bash
git checkout -b "$NEW_BRANCH"
```

Name `$NEW_BRANCH` yourself from what is actually changing, in `<type>/<slug>` form matching
the repo's existing branch style (check `git branch -a --sort=-committerdate | head -20`).
If the work belongs to a ticket and the repo's history references ticket IDs, use
`<type>/<TICKET>-<slug>` (e.g. `docs/II-435-docname-generator`). Keep it under ~50 chars,
lowercase, hyphenated.

If `$CURRENT_BRANCH` is already a feature branch, stay on it.

Announce the branch name before creating it. This is the one place where guessing wrong is
cheap to fix but annoying, so state it rather than creating silently.

## Step 4 — commit

Skip entirely if `--no-commit`.

Default behavior is **commit everything**: staged and unstaged, tracked and untracked. That
is this skill's contract, and it differs from `git-committer`'s staged-only default. Honor an
explicit narrower instruction ("just the docs", "only `src/`") by restricting paths.

Before staging anything, scan the untracked set for secrets — `.env*`, `*.pem`, `*.key`,
`id_rsa*`, `*.p12`, anything under a `secrets/` path. Never sweep those in silently: list
them and ask explicitly, or exclude them and say you did.

```bash
git add -A            # or: git add -A -- "${PATHS[@]}"
git diff --cached --stat
git diff --cached --name-status
```

Write the message yourself from the staged diff and the repo's recent history — do not
template it from filenames. Format:

```
<type>(<scope>): <imperative summary, <=72 chars>

<optional body: why, not what>
```

Type by priority when the diff mixes concerns: `feat` > `fix` > `refactor` > `perf` >
`docs` > `test` > `ci` > `build` > `chore`. Match the repo's own convention for scope — in a
repo whose log uses ticket IDs as scope (`docs(II-399): …`), use the ticket ID.

Commit via a temp file, never inline `-m` with a long body:

```bash
TMPFILE=$(mktemp)
printf '%s\n' "$COMMIT_MESSAGE" > "$TMPFILE"
git commit --file="$TMPFILE"
rm -f "$TMPFILE"
```

If a pre-commit hook rejects or rewrites files, show its output verbatim and stop — let the
user decide whether to restage and retry. Do not auto-retry, and do not reach for
`--no-verify` unless the user asked for it.

## Step 5 — push

```bash
git push -u origin "$CURRENT_BRANCH"
```

If the push is rejected as non-fast-forward, **stop**. Present the options
(`git pull --rebase`, `git pull`, `git push --force-with-lease`) and let the user pick. Never
force-push on your own initiative — not here, and not anywhere later in this skill.

## Step 6 — PR title and body

First check whether a PR already exists for this branch (use `gh pr list`, not
`gh pr view <branch>`, which is unreliable for branch lookup):

```bash
gh pr list --head "$CURRENT_BRANCH" --state open --json number,title,url
```

If one exists, ask the user whether to update title and body (`gh pr edit`) or leave them and
just carry the new commits into the existing PR. Either way, jump to step 7 afterwards — the
push in step 5 already re-triggered CI and Greptile.

Otherwise read the branch's commits and write the PR content:

```bash
git log "origin/$TARGET_BRANCH..HEAD" --pretty=format:"%h %s%n%b%n---"
git diff --name-only "origin/$TARGET_BRANCH..HEAD"
git diff "origin/$TARGET_BRANCH..HEAD" --stat
```

### What "Greptile-compliant" means

Greptile's confidence score reacts to how well the description explains the change. A body
that answers *what changed*, *why*, and *how it was checked* — and that pre-empts the obvious
objections — scores higher than one that does not, before a single line of code is read. So:

- **Title**: conventional commit, lowercase, ≤72 chars, states the change, not the activity.
  `docs(II-435): add deterministic docname generator`, not `update some docs`.
- **Body**: three short sections, plain ASCII, no code fences, no tables, ≤1200 chars total.

```markdown
## Summary
- <2-4 bullets: what changed and why, in your own words, not the commit list>

## Verification
- <what you actually ran or checked; be specific to the diff>

## Notes for review
- <anything deliberate a reviewer would otherwise flag: a design choice, an
  intentional omission, something out of scope. Omit the section if there is nothing.>
```

That third section is the highest-leverage part for the Greptile score — every intentional
oddity you name here is one finding it will not raise against you.

Show the title and body to the user and get confirmation before creating. Then:

```bash
BODYFILE=$(mktemp)
printf '%s\n' "$PR_BODY" > "$BODYFILE"
gh pr create --title "$PR_TITLE" --body-file "$BODYFILE" --base "$TARGET_BRANCH"
rm -f "$BODYFILE"
```

Capture the URL from stdout, then `gh pr view <url> --json number -q .number`.

Before sending, re-scan the title and body for `Generated with [Claude Code]`,
`Co-Authored-By: Claude`, and `🤖`. Strip anything that slipped through.

**`--dry-run` stops here** — after showing the proposed branch, commit message, title, and
body, having written nothing.

## Step 7 — drive CI and Greptile to green

The exit condition for *this* step: every check is SUCCESS/NEUTRAL/SKIPPED, Greptile's
confidence score for the current HEAD is 5/5 (or the repo demonstrably does not run Greptile),
and every distinct Greptile comment has a reply.

The merge is not the end of the job. Whoever runs this loop — the coordinator at `n=0`, the
background agent at `n>=1` — stays alive through steps 8, 9 and 10, and does not report done
until the post-merge pipeline in step 10 has also finished green.

### What effort governs

| Effort | Scope of the loop | Iteration cap |
|---|---|---|
| `low` | CI failures only. Reply to every Greptile comment, but only change code for findings that are unambiguously correct bugs. | 3 |
| `medium` | CI failures plus every actionable Greptile finding — correctness, missing tests for changed behavior, obvious simplifications. | 5 |
| `high` | The above plus a self-review pass over the diff *before* the first CI result lands (security, performance, API consistency, doc accuracy), pushing pre-emptive fixes; run the repo's own test/lint commands locally rather than waiting on CI to tell you. | 8 |

### What `@n` governs

- **`n == 0`** — the coordinator runs the loop itself, in the foreground. Use the `Monitor`
  tool's until-loop pattern to wait on `gh pr checks`; never a bare `sleep`.
- **`n >= 1`** — hand the loop to a background agent so it does not block the conversation.
  Before spawning, call `ListAgents` and look for `pr-drive-<owner>-<repo>-<pr_number>`. If
  one is active, do not spawn a second — two agents pushing to one branch will race. Say so
  in step 11 instead.

  ```
  Agent({
    subagent_type: "general-purpose",
    name: "pr-drive-<owner>-<repo>-<pr_number>",
    description: "Drive PR #<n> to green and merge",
    model: <mapped value from step 0; use "opus" if effort==high and coordinator is not Opus 5>,
    prompt: <the brief in AGENT-BRIEF.md, with every placeholder filled in>
  })
  ```

  The agent is fresh — it has none of this conversation. The brief must be self-contained:
  repo, PR number, URL, local repo path, base and head branch, effort level, iteration cap,
  auto-merge decision from step 8, and the worktree discipline above.

- **`n >= 2`** — only at `high` effort does a second agent earn its cost: one drives the
  loop, another does the pre-emptive self-review of the diff in parallel and reports findings
  back to the driver. Launch them in a single message so they run concurrently. Do not split
  the *pushing* across agents; exactly one agent ever pushes to the branch.

### The loop

1. Poll `gh pr checks <n> -R <owner>/<repo> --json name,state,link` until every state is
   `COMPLETED`.
2. For each check not SUCCESS/NEUTRAL/SKIPPED: parse the run id from the check's link, read
   `gh run view <run-id> --log-failed -R <owner>/<repo>`, diagnose, and fix the **source** —
   never weaken the check to make it pass. Commit and push (new commits on top; never
   force-push, never rebase).
3. Read Greptile's output. Verify empirically how this repo receives it rather than assuming:
   check `gh pr view <n> -R <owner>/<repo> --json body,comments` (Greptile has been observed
   embedding a `<!-- greptile_comment -->` block in the PR body carrying
   `Confidence Score: X/5` and `Last reviewed commit: <sha>`) and
   `gh api repos/<owner>/<repo>/pulls/<n>/comments` for inline review comments. If the last
   reviewed commit is not current HEAD, Greptile has not caught up — wait and re-check (up to
   ~10 minutes) before reading the score.
4. Reply to every Greptile comment. Actionable and correct → fix, push, reply saying what
   changed. Not actionable → reply briefly explaining why (false positive, deliberate design,
   out of scope). Never leave one unanswered.
5. Any push resets CI and re-triggers Greptile → back to 1.
6. On hitting the iteration cap or ~45 minutes wall clock without converging: stop, post one
   PR comment stating exactly what is unresolved and why, and report to the user. Do not loop
   indefinitely.

## Step 8 — merge gate

Merge only when **all three** hold:

1. `@auto-merge` is `true`.
2. The PR is mergeable and green.
3. The target branch does not require a human reviewer.

Check (3) against the branch rules — this endpoint works without repo-admin rights:

```bash
gh api "repos/<owner>/<repo>/rules/branches/$TARGET_BRANCH" \
  --jq '[.[] | select(.type=="pull_request") | .parameters.required_approving_review_count]'
```

`0` (or no `pull_request` rule at all) means no human reviewer is required. Anything ≥ 1
means a human must approve — **do not merge**; report that the PR is green and waiting on a
human, and stop.

Cross-check (2) empirically before merging, because branch rules are not the only thing that
can block (required conversation resolution, unattributed-change approval rules, a stale
base):

```bash
gh pr view <n> -R <owner>/<repo> --json mergeable,mergeStateStatus,reviewDecision
```

Merge only on `mergeable: MERGEABLE` and a `mergeStateStatus` of `CLEAN`. If it is `BLOCKED`,
`BEHIND`, or `DIRTY`, report the status and stop — a `BEHIND` base needs an update the user
should authorize, and `DIRTY` means conflicts, which this skill never resolves unilaterally.

```bash
gh pr merge <n> -R <owner>/<repo> --squash --delete-branch
```

**`--delete-branch` is mandatory on every merge.** The remote head branch always goes with the
merge — a merged branch left on `origin` is dead weight that shows up in every branch listing
and every stale-branch sweep afterwards. Never merge without it.

Use the repo's dominant merge method — read `allowed_merge_methods` from the same rules
output and match what recent merges into `$TARGET_BRANCH` actually used
(`git log --merges --oneline -10 origin/$TARGET_BRANCH`). Never chain the merge onto another
`gh` call in the same Bash invocation.

If `@auto-merge` is `false`, or the gate fails, say so explicitly in step 11 with the reason —
never silently skip the merge.

## Step 9 — pull the merge back down and delete the local branch

Once the PR is merged — whether this skill merged it or a human did while the loop was
running — bring the local repo up to date. In a worktree, the target branch may be checked
out somewhere else, so pick the right form:

```bash
git fetch --prune origin
```

- Target branch is checked out **here** → `git pull --ff-only origin "$TARGET_BRANCH"`.
- Target branch exists locally, checked out in **no** worktree (`git worktree list`) →
  `git fetch origin "$TARGET_BRANCH:$TARGET_BRANCH"` — fast-forwards the ref without a
  checkout.
- Target branch is checked out in **another** worktree → leave it alone. `origin/$TARGET_BRANCH`
  is current; say the other worktree still needs its own pull, and name it.

### Delete the local head branch

The merged branch always goes, locally too — its content now lives in `$TARGET_BRANCH`, and
leaving it behind is exactly the debris `/clean-up-branches` exists to sweep up later. Do it
here instead.

You cannot delete the branch you are standing on, so get off it first. Which move is available
depends on whether `$TARGET_BRANCH` is free to check out in this worktree:

```bash
# Preferred: land on the target branch, if no other worktree holds it
git checkout "$TARGET_BRANCH"

# Otherwise (target checked out in a sibling worktree) — detach, which always works
git checkout --detach "origin/$TARGET_BRANCH"

git branch -D "$MERGED_BRANCH"
```

Use `-D`, not `-d`. After a **squash** merge the branch's commits do not exist on the target
by identity, so git considers it unmerged and `-d` refuses — the PR being merged is the
authority here, not git's ancestry check.

Three conditions on this, all of which mean **stop and report instead of deleting**:

- The PR is not actually merged (`gh pr view <n> --json state -q .state` must be `MERGED`).
  Never delete a branch on the strength of "the merge command seemed to work".
- The branch has commits not in the merge — check
  `git log --oneline "origin/$TARGET_BRANCH..$MERGED_BRANCH"` after the fetch, and for a squash
  merge confirm the diff is empty (`git diff "origin/$TARGET_BRANCH" "$MERGED_BRANCH"`) rather
  than trusting the commit list. Non-empty means work would be lost.
- The working tree is dirty. Do not discard someone's uncommitted edits to win a checkout.

`gh pr merge --delete-branch` will often have deleted the local branch already and switched
you to the base. That is fine — verify with `git branch --list "$MERGED_BRANCH"` and treat an
empty result as done rather than an error. In a worktree it frequently cannot do the local
half, which is why the explicit sequence above exists.

If the worktree ends up detached, say so in step 11 — a detached HEAD is a state the user
should know they are in, not discover later.

## Step 10 — watch the post-merge pipeline

A green PR does not mean a green target branch. Merging usually fires a second, different set
of workflows — `push`-triggered builds, release and tag jobs, deploys, scheduled
publish steps — and those can fail on things the PR checks never exercised (secrets and
environment variables only present on the base branch, deploy targets, a semantic conflict
with another PR that merged in between). Skipping this leaves a broken `$TARGET_BRANCH` behind
under a run the user was told had succeeded.

Run this whenever the PR reaches a merged state, whether this skill merged it or a human did
while the loop was running.

Capture the merge commit first — it is what identifies the runs to watch:

```bash
MERGE_SHA=$(gh pr view <n> -R <owner>/<repo> --json mergeCommit -q .mergeCommit.oid)
```

Then poll runs on the target branch at that SHA until none are queued or in progress:

```bash
gh run list -R <owner>/<repo> --branch "$TARGET_BRANCH" --commit "$MERGE_SHA" \
  --json databaseId,name,status,conclusion,workflowName,event
```

Use the `Monitor` tool's until-loop, not a bare `sleep`. Two timing traps:

- Runs are not registered instantly. An **empty list is not success** — treat it as "not
  started yet" for the first ~3 minutes, and only conclude the repo runs no post-merge
  workflows after that window stays empty.
- Deploy jobs can sit in a GitHub **Environment** approval gate with status `waiting`. That is
  not a failure and not something to fix — report it as blocked on a human approver and stop
  waiting on that run.

Wall-clock cap: 30 minutes, on top of step 7's budget. Post-merge deploys are slower than PR
checks, so use a longer poll interval (~60s).

### When a post-merge run fails

**`$TARGET_BRANCH` is protected — never commit or push to it directly, and never force-push.**
The fix is a new PR, not a hotfix commit on the base.

1. Read the failure: `gh run view <run-id> --log-failed -R <owner>/<repo>`.
2. Classify it before touching anything:
   - **Infra or flake** (runner died, network timeout, rate limit) → re-run it once:
     `gh run rerun <run-id> --failed -R <owner>/<repo>`. If it fails the same way twice, stop
     treating it as a flake.
   - **Environment-only** (a missing secret, an absent deploy credential, a permissions
     problem on the target environment) → not fixable from the code. Stop and report it with
     the exact log line; this needs a human with access.
   - **Real defect introduced by this merge** → fix it.
3. To fix: branch off the freshly-pulled `$TARGET_BRANCH` as
   `fix/<original-slug>-post-merge`, make the change, push, and open a follow-up PR through
   steps 4–9 of this skill. Say plainly in that PR's body that it repairs a post-merge failure
   on `$TARGET_BRANCH`, and link the failed run.
4. **Bound the recursion at one follow-up PR.** If the follow-up's own post-merge run also
   fails, stop and escalate to the user — two consecutive post-merge failures mean the
   diagnosis is wrong, and a third automated attempt makes the branch worse, not better.
5. If `@auto-merge` is `false`, the follow-up PR stops at green like any other run of this
   skill. Do not merge a repair PR the user has not authorized just because the branch is
   broken — say the branch is broken and the fix is waiting.

Report `$TARGET_BRANCH` as green only once every run at `$MERGE_SHA` (or at the follow-up's
merge commit) concluded SUCCESS / NEUTRAL / SKIPPED.

## Step 11 — report back

State, in this order:

- PR number, title, URL, and whether it was created or updated.
- Whether the drive loop is running in the background (and under which agent name), or
  finished, or was run inline.
- Merge outcome: merged (and by which method), or not merged **and the specific reason** —
  auto-merge off (the default), human reviewer required, `mergeStateStatus` blocked, cap
  reached.
- Post-merge pipeline status: which workflows ran on `$TARGET_BRANCH`, whether they finished
  green, and — if not — what failed, how it was classified, and whether a follow-up PR exists.
  If the repo runs no post-merge workflows, say that rather than leaving it unmentioned.
- What was pulled back locally, whether the local head branch was deleted (or why it was kept),
  which branch the worktree is now on — naming a detached HEAD explicitly if that is the
  result — and any worktree that still needs its own pull.
- Anything left unresolved on the PR.

If a background agent is still running, say the user will get a separate notification when it
finishes; do not wait on it.

## Reference

- [AGENT-BRIEF.md](AGENT-BRIEF.md) — the self-contained prompt for the `pr-drive-*` background agent
