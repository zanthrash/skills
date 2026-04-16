---
name: pr-review
description: >
  Code review for open PRs. Discovers unreviewed PRs and
  re-review candidates, reviews one at a time with user approval before posting
  each to GitHub via the pending review API. Trigger on: reviewing PRs, code review,
  "what PRs need attention", "review my PRs", pull requests needing review.
allowed-tools: AskUserQuestion
---

# PR Review

## Step 0: Prerequisites

Before anything else, verify the GitHub CLI is available and authenticated:

```bash
gh --version
gh auth status
```

If `gh` is not installed, stop and tell the user:

```
The GitHub CLI (gh) is required but not installed.

Install: brew install gh  (macOS) or see https://cli.github.com/
Then authenticate: gh auth login
```

Do not proceed until `gh` is installed and authenticated.

## Step 1: Identify yourself and the repo

```bash
gh api user --jq '.login'
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Store as `MY_LOGIN` and `OWNER/REPO`.

## Step 2: Determine how many new PRs to review

Check the user's prompt for a number (e.g., "review 5 PRs", "give me 2 reviews"). If none is
specified, default to **3**.

Call this `N` — it controls how many **unreviewed** PRs to pull. Re-reviews are always included
in full regardless of N.

## Step 3: Find PRs to review

Get all open, non-draft PRs authored by others:

```bash
gh pr list --state open --limit 100 \
  --json number,title,author,createdAt,isDraft,reviews,updatedAt,additions,deletions,changedFiles \
  --jq '[.[] | select(.isDraft == false and .author.login != "<YOUR_LOGIN>")] | sort_by(.createdAt) | reverse'
```

Replace `<YOUR_LOGIN>` with your actual login from Step 1.

**Skip Snyk PRs**: Exclude any PR where the title starts with `[Snyk]` — these are automated dependency bumps, not code review candidates.

Skip bot reviewers (`unblocked`, `qltysh`, `github-actions`, etc.) when checking the reviews array.

Classify each PR:

| Bucket              | Condition                                                                           | How many to take       |
| ------------------- | ----------------------------------------------------------------------------------- | ---------------------- |
| **Unreviewed**      | You have no review on this PR                                                       | Up to N (newest first) |
| **Needs re-review** | You reviewed it, but the PR's `updatedAt` is after your last review's `submittedAt` | All of them            |
| **Up to date**      | You reviewed it and nothing changed since                                           | Skip                   |

To check if a PR needs re-review:

```bash
gh api repos/{owner}/{repo}/pulls/<number>/reviews \
  --jq '[.[] | select(.user.login == "<YOUR_LOGIN>")] | last | .submitted_at'
# If PR updatedAt > submitted_at → needs re-review
```

The final review list = (up to N unreviewed) + (all needs-re-review). There is no cap on re-reviews.

## Step 4: Present the queue

Before starting reviews, show the user what you found:

```
Found X PRs to review:

**Unreviewed (N):**
1. #2153 — "Add user preferences API" by @alice (3 files, +120/-30)
2. #2148 — "Fix pagination in search" by @bob (1 file, +15/-8)

**Re-review (N):**
3. #2130 — "Refactor notification service" by @dave (updated 2h ago)

I'll review these one at a time. For each PR you can post, skip, or revise before anything goes to GitHub.
```

This is informational output — no approval needed. Then proceed to the first PR.

## Step 5: For each PR — Gather context and review

```bash
# PR metadata
gh pr view <number> --json number,title,body,author,baseRefName,headRefName,headRefOid,additions,deletions,changedFiles,labels,commits

# Full diff — primary source for file paths and line numbers
gh pr diff <number>

# Existing comments (don't repeat what's already been said)
gh api repos/{owner}/{repo}/pulls/<number>/reviews
gh api repos/{owner}/{repo}/pulls/<number>/comments --paginate

# Latest commit SHA (needed for the pending review API)
gh pr view <number> --json commits --jq '.commits[-1].oid'
```

When reading the diff, note the exact file paths and line numbers as you go. The diff format shows
`+++ b/path/to/file` and `@@ -old +new @@` headers; use these to derive accurate line numbers.

For re-reviews, also note what changed since your last review so you can focus on the new commits.

Analyze the PR and draft your review. Organize findings into:

### Inline comments

Every finding with a specific file path and line number becomes an inline comment. For each:

- `path`: file path relative to repo root
- `line`: line number in the new version of the file (from the diff's `+` side)
- `side`: `RIGHT` for added/modified lines (most common), `LEFT` for deleted lines
- `body`: the comment markdown

For code fixes, use GitHub's suggestion syntax in the body:

````
Your explanation of the issue...

```suggestion
const fixed = value ?? defaultValue;
```
````

For markdown files with nested backticks, use 4 backticks or tildes to wrap suggestions.

**Cap at ~15 inline comments.** If you have more, keep the highest-priority ones as inline comments
and fold the rest into the review body. This avoids shell argument length limits and keeps the
review digestible.

### Review body

- 2–3 sentence summary of what the PR does and whether it's headed in the right direction
- Any findings that are general or file-level (no specific line to attach to)

### Event type

- Any **blocking** findings → `REQUEST_CHANGES`
- Only suggestions/praise, but PR is solid → `APPROVE`
- Only suggestions/praise, neutral stance → `COMMENT`

## Step 6: For each PR — Present for approval

**CRITICAL: Always get explicit user approval before posting any review comments.** Show exactly what will be posted and ask for yes/no confirmation using AskUserQuestion.

This step has two parts. The AskUserQuestion tool does NOT render markdown well — all formatting
collapses into a single flat block. So you must split presentation into two phases:

### Phase 1: Print the detailed review to the terminal

Output the full review as regular text (NOT inside AskUserQuestion). Use markdown formatting
since the terminal renders it properly:

```
---

## Review: PR #123 — "Title"

**Event type:** REQUEST_CHANGES
**Inline comments:** 3

**Overall message:** "Found 3 issues that need to be addressed before merging."

---

### Inline Comments

**1. `src/auth.ts:20` [blocking]**
Token expiry validation is missing...
```suggestion
const token = validateExpiry(rawToken);
```

**2. `src/auth.ts:35` [suggestion]**
Missing error handling...

**3. `tests/auth.test.ts:12` [praise]**
Nice edge case coverage here.

---
```

### Phase 2: Ask for approval via AskUserQuestion

After the detailed review is printed, use `AskUserQuestion` with a **short, plain-text** question.
Keep the question to one or two sentences — the user has already read the full review above.

Use these options:
- **"Post this review"** — proceeds to GitHub submission
- **"Skip this PR"** — moves to next PR, nothing posted
- **"Let me revise"** — returns to conversation for the user to give revision instructions

Example question text (keep it this short):

```
PR #123: REQUEST_CHANGES with 3 inline comments. Post this review?
```

**Important:** Never put the full review content, inline comments, or suggestion blocks inside
the AskUserQuestion question field. The tool renders everything as flat unformatted text, making
it unreadable. Always print the detail to the terminal first.

## Step 7: For each PR — Handle response

### If "Post this review"

Execute the two-step pending review API:

```bash
# Step 1: Create pending review with all inline comments
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  -X POST \
  -f commit_id="{commit_sha}" \
  -f 'comments[][path]=src/auth.ts' \
  -F 'comments[][line]=20' \
  -f 'comments[][side]=RIGHT' \
  -f 'comments[][body]=Token expiry validation is missing...' \
  -f 'comments[][path]=src/auth.ts' \
  -F 'comments[][line]=35' \
  -f 'comments[][side]=RIGHT' \
  -f 'comments[][body]=Missing error handling...' \
  --jq '{id, state}'

# Returns: {"id": <REVIEW_ID>, "state": "PENDING"}

# Step 2: Submit the pending review with event type and overall message
gh api repos/{owner}/{repo}/pulls/{number}/reviews/{review_id}/events \
  -X POST \
  -f event="REQUEST_CHANGES" \
  -f body="Overall review message here..."
```

**Syntax rules:**
- Use `-f` for string values (paths, bodies, side, commit_id)
- Use `-F` for numeric values (line numbers only)
- Use single quotes around `comments[][]` parameters
- Always use the pending review pattern, even for a single comment

After successful submission, print:
```
Posted REQUEST_CHANGES review on PR #123 with 3 inline comments.
```

If the API returns 403/429 (rate limit), inform the user and pause.

### If "Skip this PR"

Print `Skipped PR #123.` and move to the next PR.

### If "Let me revise"

Ask what the user wants to change. They might say things like:
- "Tone down comment 2"
- "Remove the security finding"
- "Change event type to COMMENT"
- "Add a note about the missing index"

Incorporate changes and loop back to Step 6 (re-present via AskUserQuestion).

---

## Red flags — you're about to violate the pattern

Stop if you're thinking:
- "User said ASAP so I'll skip the approval step"
- "Only one comment so I'll post directly without pending review"
- "I'll post it and then tell them what I posted"
- "The approval step slows things down"
- "User already approved the review idea, so I'll skip showing them the comments"

**All of these mean: STOP. Always show the full review and get explicit approval before posting.**

Review comments are public and permanent. The user needs to see exactly what will go out.

---

## Notes

- For diffs >2000 lines, note this upfront and focus on highest-risk areas rather than exhaustive line-by-line coverage.
- For re-reviews, focus analysis on commits since the last review and preface the body with "Re-review focusing on changes since [date]."
- If a finding references code outside the PR diff, note it in the review body rather than as an inline comment (inline comments must attach to lines in the diff).
