# repo-size-guardian consumer test — expected results

This branch (`test/repo-size-guardian`) is meant to be opened as a single PR
against `main`, which already has `technic960183/repo-size-guardian@claude`
installed (`.github/workflows/repo-size-guardian.yml` +
`.github/repo-size-guardian.yml`). This PR's own commits then extend that
workflow to four jobs and add the files needed to exercise every one of
them, so one PR gives full signal instead of needing several.

**All numbers below were verified by running the actual CLI
(`python -m repo_size_guardian`) from a local checkout against these exact
commits, with `--base-ref`/`--head-ref` set explicitly and `GITHUB_OUTPUT`/
`GITHUB_STEP_SUMMARY` pointed at temp files** — not just predicted from
reading the docs. They are what the real Actions run should also produce
(same tool, same commit range); the one thing only the real run can prove is
that it behaves identically inside `actions/checkout` + the composite
action's `pip install` step on `ubuntu-latest`, which local testing can't
touch.

## Jobs and their expected outcome

| Job | `policy_path` | `scan_mode` | `fail_on` | Expected result | Violations found (verified) |
|---|---|---|---|---|---|
| `scan-history-error` | `.github/repo-size-guardian.yml` | `history` | `error` | **FAILS** (exit 1) — `continue-on-error: true` | 3 errors: `big-binary.dat`, `ghost-large-log.txt`, `analysis-notebook.ipynb` |
| `scan-diff-mode` | `.github/repo-size-guardian.yml` | `diff` | `error` | **FAILS** (exit 1) — `continue-on-error: true` | 2 errors: `big-binary.dat`, `analysis-notebook.ipynb` — **`ghost-large-log.txt` is absent here** |
| `warn-rule-fail-on-error` | `.github/repo-size-guardian-warn-demo.yml` | `history` | `error` | **PASSES** (exit 0, green) | 1 warn: `run-output.log` (a warn alone does not fail `fail_on: error`) |
| `warn-rule-fail-on-warn` | `.github/repo-size-guardian-warn-demo.yml` | `history` | `warn` | **FAILS** (exit 1) — `continue-on-error: true` | Same 1 warn: `run-output.log` (`fail_on: warn` fails on *any* violation, including warn-severity) |

All four jobs report `Commits scanned: 8`. `scan-history-error` and both
warn-rule jobs report `Blobs scanned: 10 | Unique blobs: 9` (history mode);
`scan-diff-mode` reports `Blobs scanned: 8 | Unique blobs: 8` (diff mode, one
net-diff blob per changed path — no `ghost-large-log.txt` entry at all).
**If your real run shows different commit/blob counts, ref resolution
probably picked the wrong range** (see the README's note on this) — that's
the first thing to check before assuming a code problem.

## Files and what should (not) flag them

| File | Size / kind | Introduced / removed | What it's testing | Flagged in `scan-history-error` | Flagged in `scan-diff-mode` | Flagged in `warn-rule-*` |
|---|---|---|---|---|---|---|
| `ci-test/repo-size-guardian/big-binary.dat` | 300 KB, binary | added, stays | binary size threshold (`thresholds.max_binary_size_kb: 100`) | ERROR — binary threshold | ERROR — binary threshold | not flagged (warn-demo policy doesn't set thresholds) |
| `ci-test/repo-size-guardian/ghost-large-log.txt` | 600 KB, text | **added then deleted within this PR** | history vs. diff — the tool's whole reason to exist | **ERROR — text threshold** (only mode that catches it) | **not flagged** (net diff for this path is empty) | not flagged |
| `ci-test/repo-size-guardian/analysis-notebook.ipynb` | 495 B | added, stays | `disallow.extensions: ["ipynb"]` | ERROR — disallowed extension | ERROR — disallowed extension | not flagged (warn-demo policy has no `disallow`) |
| `ci-test/repo-size-guardian/fixtures/legacy-golden.dat` | 300 KB, binary | added, stays | `ignore.globs` **negative test** — must NOT be flagged despite being 3x over the binary threshold | **not flagged** (must stay silent) | **not flagged** | not flagged |
| `ci-test/repo-size-guardian/run-output.log` | 150 KB, text | added, stays | `warn` severity vs. `error`, and `fail_on: warn` vs `fail_on: error` | not flagged (150 KB is under the main policy's 200 KB text threshold) | not flagged | **WARN** in both warn-rule jobs — but only fails the job when `fail_on: warn` |

The `fixtures/legacy-golden.dat` row is the one to look at most carefully:
if it shows up as flagged in the real run, `ignore.globs` isn't working as
documented — that's a false positive and exactly the failure mode that
destroys trust in this tool.

## How this maps to commits

1. `Extend CI workflow into 4 jobs for one-PR test coverage` — workflow only.
2. `Add oversized binary test artifact` — adds `big-binary.dat`.
3. `Add debug dump (forgot to exclude before committing)` — adds `ghost-large-log.txt`.
4. `Add exported analysis notebook` — adds `analysis-notebook.ipynb`.
5. `Add golden fixture and exempt fixtures/ from scanning` — adds `fixtures/legacy-golden.dat` **and** adds `ignore.globs` to the policy in the same commit (a realistic "add fixture + exempt it" PR pattern).
6. `Add warn-only demo policy and a log file that trips it` — adds `.github/repo-size-guardian-warn-demo.yml` and `run-output.log`.
7. `Remove accidental debug dump` — deletes `ghost-large-log.txt`.
8. `Add TEST_PLAN.md with verified expected results` — this file.

## Before merging this PR

If you decide to merge (rather than just review the check results and
close), consider trimming `.github/workflows/repo-size-guardian.yml` back
down to a single production job (`scan-history-error`'s config is the
reasonable permanent one) and deleting `.github/repo-size-guardian-warn-demo.yml`
plus everything under `ci-test/repo-size-guardian/` — the extra jobs and
fixtures here exist to get maximum signal from this one test PR, not to
live in `main` permanently.

## Text to paste into the PR description

```
Consumer test of technic960183/repo-size-guardian@claude (Stage 2 release
testing). Base already has the action installed on main; this PR's commits
exercise it end to end via 4 jobs over the same commit range:

- scan-history-error: the real production gate (history mode, fail_on=error).
  Expected: FAILS — 3 errors (oversized binary, disallowed .ipynb, and a
  600 KB text file that was added then deleted within this same PR).
- scan-diff-mode: identical policy/commits, scan_mode=diff instead of
  history. Expected: FAILS too, but with only 2 errors — the added-then-
  deleted file is invisible to diff mode, which is exactly the gap
  history mode exists to close.
- warn-rule-fail-on-error: an isolated warn-severity rule, fail_on=error.
  Expected: PASSES (green) — a warn-only violation doesn't fail the job.
- warn-rule-fail-on-warn: same warn-severity rule, fail_on=warn. Expected:
  FAILS — fail_on=warn fails on ANY violation, including warn-severity.

Also included: a file under ci-test/repo-size-guardian/fixtures/ that is
3x over the binary size threshold but is covered by ignore.globs — it
should NOT appear in either scan job's violation list. If it does, that's
a bug worth stopping on before adopting this tool further.

See TEST_PLAN.md on this branch for the full expected-results table.
Jobs expected to fail have continue-on-error: true so all four results
are visible on this one PR instead of GitHub Actions hiding results
behind an early red X.
```
