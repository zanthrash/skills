# Skills

Shared custom skills. Install with `npx skills@latest add <skill-name>`.

## architecture-map

Trace a component or page's dependencies, call chains, and user flows, then generate an interactive HTML architecture explorer with issues and refactor suggestions.

```bash
npx skills@latest add architecture-map
```

## pr-review

Code review for open PRs. Discovers unreviewed PRs and re-review candidates, reviews one at a time with user approval before posting to GitHub via the pending review API.

```bash
npx skills@latest add pr-review
```

> [!NOTE]
> Requires the [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated (`gh auth login`).

**Features:**

- Auto-discovers unreviewed PRs and PRs updated since your last review
- Reviews one PR at a time — shows the full review before anything posts
- Inline comments with suggestion blocks, capped at ~15 per review
- Supports `REQUEST_CHANGES`, `APPROVE`, and `COMMENT` event types
- Re-reviews focus on commits since your last review
