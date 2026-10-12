# `pr-drive-*` agent brief

Template for the background agent spawned in step 7 of [SKILL.md](SKILL.md). Fill in every
`<placeholder>` with a real value before launching — the agent is fresh and gets none of the
coordinator's context, so anything left as a placeholder is information it cannot recover.

Launch with `subagent_type: "general-purpose"`, `name: "pr-drive-<owner>-<repo>-<pr_number>"`,
and `model` per step 0 / step 2 of SKILL.md.

---

```
Drive GitHub PR #<n> in <owner>/<repo> (<pr_url>) to a finished state: all CI checks green,
Greptile's confidence score 5/5 for the current HEAD, every Greptile comment answered, and —
if the merge gate below passes — merged, pulled back locally, and with the post-merge pipeline
on <target_branch> watched through to success.

The merge is not the end of your job. If the PR gets merged (by you, or by a human while you
were looping), you are not done until the post-merge section below is satisfied.

Local checkout: <repo_path>
  Run every git and gh command from that directory. Do NOT cd anywhere else; this is a git
  worktree and leaving it will be refused. Never use bare `git stash` / `git stash pop` — the
  stash stack is shared with other worktrees. Set work aside with a WIP commit instead.

Base branch: <target_branch>
Head branch: <head_branch>
Effort: <low|medium|high>
Iteration cap: <3|5|8>   Wall-clock cap: 45 minutes for the PR loop, plus 30 for post-merge
Auto-merge: <true|false>   (defaults to false; only true if the user asked for it)
Required approving reviews on <target_branch>: <0|N>   (from
  `gh api repos/<owner>/<repo>/rules/branches/<target_branch>`)
Merge method to use: <squash|merge|rebase>

## Effort scope

- low: fix CI failures only. Reply to every Greptile comment, but only change code for
  findings that are unambiguously correct bugs.
- medium: CI failures plus every actionable Greptile finding — correctness, missing tests for
  changed behavior, obvious simplifications.
- high: the above, plus a self-review pass over the diff before the first CI result lands
  (security, performance, API consistency, doc accuracy) with pre-emptive fixes pushed; run
  the repo's own test and lint commands locally rather than waiting on CI to report.

## Loop

1. Poll `gh pr checks <n> -R <owner>/<repo> --json name,state,link` every 30-60s until every
   check's state is COMPLETED. Use the Monitor tool's until-loop pattern or `--watch`, not a
   manual sleep loop.

2. For each check whose conclusion is not SUCCESS / NEUTRAL / SKIPPED: parse the run id out of
   the check's link (`.../actions/runs/<id>/job/...`), read
   `gh run view <run-id> --log-failed -R <owner>/<repo>`, diagnose from the log, and fix the
   actual source. Never weaken, skip, or work around a check to make it pass. Commit in
   Conventional Commits style and `git push`. New commits on top only — never force-push,
   never rebase.

3. Read Greptile's output for the current HEAD. Verify empirically how this repo receives it
   rather than assuming a format:
   - `gh pr view <n> -R <owner>/<repo> --json body,comments` — Greptile has been observed
     embedding a `<!-- greptile_comment --> ... <!-- /greptile_comment -->` block in the PR
     body, carrying a `Confidence Score: X/5` line and a `Last reviewed commit: <sha>` line.
   - `gh api repos/<owner>/<repo>/pulls/<n>/comments` — inline review comments from a
     Greptile-looking bot login.
   If the last reviewed commit is not current HEAD, Greptile has not caught up to your last
   push. Wait and re-check, up to ~10 minutes, before reading the score.

4. Reply to every distinct Greptile comment you have not already answered. If it is a real,
   actionable finding: fix it (loop back through step 2's commit/push) and reply saying what
   changed. If it is not — false positive, out of scope, a deliberate design choice — reply
   briefly explaining why. Never leave one unanswered. Greptile posting "no findings" needs no
   reply; any comment it did leave does.

5. After any push, go back to step 1 — new commits reset CI and re-trigger Greptile.

## Merge gate

Once every check is SUCCESS/NEUTRAL/SKIPPED, Greptile is 5/5, and every comment is answered,
merge only if ALL of these hold:

- Auto-merge is true (see the header above).
- Required approving reviews on <target_branch> is 0.
- `gh pr view <n> -R <owner>/<repo> --json mergeable,mergeStateStatus` reports
  `mergeable: MERGEABLE` and `mergeStateStatus: CLEAN`.

Then, as a standalone Bash call — never chained onto another gh command:

  gh pr merge <n> -R <owner>/<repo> --<merge_method> --delete-branch

--delete-branch is MANDATORY. The remote head branch always goes with the merge; never merge
without it.

If any condition fails, do NOT merge. Post one short PR comment saying the PR is green and
what it is waiting on, and report the reason back.

`mergeStateStatus: BEHIND` means the base moved — that is the human's call, not yours.
`DIRTY` means conflicts — never resolve them unilaterally. Report either and stop.

## After a merge — pull back and delete the local branch

Whether you merged it or a human merged it while you were looping, bring <repo_path> up to
date:

  git fetch --prune origin

- If <target_branch> is checked out in <repo_path>: `git pull --ff-only origin <target_branch>`
- Else if <target_branch> exists locally and is checked out in no worktree
  (check `git worktree list`): `git fetch origin <target_branch>:<target_branch>`
- Else: leave it; `origin/<target_branch>` is current. Report which worktree still needs a pull.

Then delete the local head branch <head_branch> — it always goes once merged. You cannot delete
the branch you are standing on, so get off it first:

  git checkout <target_branch>              # preferred, if no sibling worktree holds it
  git checkout --detach origin/<target_branch>   # otherwise; always works
  git branch -D <head_branch>

Use -D, not -d: after a squash merge the commits do not exist on the target by identity, so -d
refuses. The PR being MERGED is the authority, not git's ancestry check.

STOP and report instead of deleting if any of these hold:
- `gh pr view <n> -R <owner>/<repo> --json state -q .state` is not MERGED. Never delete on the
  strength of "the merge command seemed to work".
- The branch has work not in the merge: after the fetch, check
  `git log --oneline origin/<target_branch>..<head_branch>` and, for a squash merge, confirm
  `git diff origin/<target_branch> <head_branch>` is empty. Non-empty means work would be lost.
- The working tree is dirty. Never discard uncommitted edits to win a checkout.

`gh pr merge --delete-branch` often already deleted the local branch and switched you to the
base. Verify with `git branch --list <head_branch>`; an empty result means done, not an error.
In a worktree it frequently cannot do the local half, which is why the sequence above exists.

If you end up on a detached HEAD, say so in your report.

## After a merge — watch the post-merge pipeline

A green PR does not mean a green target branch. Merging fires a different set of workflows —
push-triggered builds, release/tag jobs, deploys — which can fail on things the PR checks never
exercised: secrets and env vars that only exist on the base branch, deploy targets, or a
semantic conflict with another PR that merged in between. Do not report success until these
finish.

  MERGE_SHA=$(gh pr view <n> -R <owner>/<repo> --json mergeCommit -q .mergeCommit.oid)

  gh run list -R <owner>/<repo> --branch <target_branch> --commit "$MERGE_SHA" \
    --json databaseId,name,status,conclusion,workflowName,event

Poll with the Monitor tool's until-loop (interval ~60s — post-merge deploys are slower than PR
checks) until no run is `queued` or `in_progress`. Wall-clock cap: 30 minutes, separate from
the PR-loop budget above.

Two timing traps:
- An EMPTY LIST IS NOT SUCCESS. Runs take time to register. Treat empty as "not started yet"
  for the first ~3 minutes; only after that window stays empty may you conclude the repo runs
  no post-merge workflows.
- A run with status `waiting` is sitting in a GitHub Environment approval gate. That is not a
  failure and not yours to fix — report it as blocked on a human approver and stop waiting on
  that run.

### When a post-merge run fails

<target_branch> IS PROTECTED. Never commit or push to it directly, never force-push. The fix is
a new PR, not a hotfix commit on the base.

1. Read it: `gh run view <run-id> --log-failed -R <owner>/<repo>`.
2. Classify before touching anything:
   - Infra or flake (runner died, network timeout, rate limit) → rerun once:
     `gh run rerun <run-id> --failed -R <owner>/<repo>`. Same failure twice means it is not a
     flake; reclassify.
   - Environment-only (missing secret, absent deploy credential, permissions on the target
     environment) → not fixable from code. Stop and report with the exact log line; this needs
     a human with access.
   - Real defect introduced by this merge → fix it.
3. To fix: branch off the freshly-pulled <target_branch> as `fix/<head_branch_slug>-post-merge`,
   make the change, push, and open a follow-up PR against <target_branch>. Say in its body that
   it repairs a post-merge failure, and link the failed run. Then run this whole brief again
   for that PR.
4. BOUND THE RECURSION AT ONE FOLLOW-UP PR. If the follow-up's own post-merge run also fails,
   stop and escalate — two consecutive post-merge failures mean the diagnosis is wrong, and a
   third automated attempt makes the branch worse.
5. If auto-merge is false, the follow-up PR stops at green like any other. Do NOT merge a repair
   PR the user has not authorized just because the branch is broken — report that the branch is
   broken and the fix is waiting.

Report <target_branch> green only once every run at $MERGE_SHA (or at the follow-up's merge
commit) concluded SUCCESS / NEUTRAL / SKIPPED.

## Safety valve

If you reach <cap> loop iterations or ~45 minutes of wall clock without hitting the exit
condition, stop. Post one PR comment summarizing exactly what is still unresolved and why (a
flaky infra-only check, a Greptile point you disagree with and already explained, a base that
needs updating), then end. Do not loop indefinitely.

## Hard rules

- Never force-push.
- Never rebase or resolve conflicts on your own initiative.
- Never merge when the gate above does not pass.
- Never include "Generated with Claude Code", "Co-Authored-By: Claude", 🤖, or any other
  Claude/Anthropic attribution in a commit message or a PR comment. Write as the PR's author
  addressing the feedback, not as a disclosed bot.
- Keep every `gh --body` / `git -m` payload short and plain, write longer text to a temp file
  and pass `--body-file` / `--file`, and issue one gh mutation per Bash call. Long chained
  commands get denied by the permission layer.

## Report back

When you finish, state: final CI status, final Greptile score, how many comments you answered,
what you changed (commit subjects), whether it merged and by which method or why not, what was
pulled back locally, and the post-merge pipeline outcome on <target_branch> — which workflows
ran, whether they concluded green, and if not, what failed, how you classified it, and whether
a follow-up PR exists. If the repo runs no post-merge workflows, say that explicitly rather
than leaving it out.
```
