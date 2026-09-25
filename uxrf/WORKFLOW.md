# Git workflow for this fork

Plain-language version. Everything here happens inside `presentt/hyperspy`
unless a step says otherwise.

## Branches

```
hyperspy/hyperspy : RELEASE_next_minor      (upstream, features)
        │ fork
presentt/hyperspy : RELEASE_next_minor      (mirror of upstream, keep it clean)
                    uxrf                    (your stable "it works" branch)
                    uxrf-<topic>            (short-lived: one recipe, one doc, one fix)
```

- `RELEASE_next_minor` in the fork is only ever updated from upstream. Never
  commit to it directly.
- `uxrf` is the branch you use for real work on your data. It only receives
  merges from topic branches, so it stays in a working state.
- Topic branches are named `uxrf-something` with a hyphen. Git will not allow
  `uxrf/something` next to a branch called `uxrf`.

## Everyday cycle

```bash
# 1. Start from an up-to-date uxrf
git checkout uxrf
git pull origin uxrf

# 2. Make a topic branch
git checkout -b uxrf-rgb-composite

# 3. Work, then stage and commit (see message template below)
git add uxrf/recipes/03_rgb_composite.py uxrf/NOTES.md
git commit            # your editor opens; paste the template

# 4. Push the topic branch
git push -u origin uxrf-rgb-composite

# 5. Open a pull request on GitHub: base = uxrf, compare = uxrf-rgb-composite.
#    Review the diff yourself, merge, then delete the topic branch.

# 6. Back to uxrf and pull the merge
git checkout uxrf
git pull origin uxrf
```

The pre-commit hooks run automatically on `git commit`. If `ruff` reformats a
file, the commit stops; run `git add` on the changed file and commit again.

## Keeping up with upstream

Do this every few weeks, or before starting something that touches library code.

```bash
git remote add upstream https://github.com/hyperspy/hyperspy.git   # once
git fetch upstream
git checkout RELEASE_next_minor
git merge --ff-only upstream/RELEASE_next_minor
git push origin RELEASE_next_minor

git checkout uxrf
git merge RELEASE_next_minor      # bring upstream changes into your working branch
git push origin uxrf
```

If the merge reports conflicts, stop and ask for help in a session rather than
guessing; conflicts should be rare because `uxrf/` is separate from `hyperspy/`.

## Commit message template

```
<area>: <what changed, imperative, under 60 characters>

<Why this change was made and what it enables, two to five lines.
Mention anything a reader would not guess from the diff.>

Assisted-by: Claude Code:<model-id>
```

Examples of `<area>`: `uxrf`, `uxrf/recipes`, `uxrf/notes`, `docs`.

HyperSpy rejects `Co-authored-by:` trailers that name an AI tool. The
`Assisted-by:` line is the accepted form. Leave it out for commits you wrote
without assistance.

## Pull request template (inside the fork)

```
Title: uxrf: <what this PR adds>

## Summary
<What the branch does, two or three sentences.>

## Why
<The scientific or practical reason.>

## How it was checked
<Which recipe or command was run, on which data, and what the result was.>

## Notes for review
<Anything uncertain, and any follow-up left for a later branch.>
```

## If something goes wrong

```bash
git status                    # what is modified / staged
git diff                      # what changed since the last commit
git restore <file>            # throw away uncommitted edits to one file
git log --oneline -10         # recent history
git checkout uxrf             # get back to the working branch
```

Nothing that has been pushed is ever truly lost; when in doubt, stop and ask.
