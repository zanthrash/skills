---
name: architecture-map
description: Given a page, component, or file path in a codebase, traces all dependencies and call chains, classifies them into architectural layers, sequences the primary user flow (including auth paths and error branches), analyzes concerns across six categories (auth, correctness, conventions, complexity, observability, performance), proposes refactoring opportunities, and generates a self-contained interactive HTML explorer (architecture view + sequence view + issue cards + next-steps checklist + commenting + prompt output) saved to docs/architecture-maps/<name>.html. Use whenever the user says "map out this component", "investigate this page", "trace the dependencies of", "show me the architecture of", "analyze this flow", "what calls what in", "create an architecture map", "document this feature's call chain", or "show me what this component depends on". Also trigger when someone pastes a file path and asks what it does, connects to, or how it's wired up. Especially useful for auth flows, API integration surfaces, multi-service calls, and components that span client/BFF/external-service boundaries.
---

# Architecture Map

Produce an interactive HTML architecture map for a given page, component, or entry-point file. The output is a single self-contained HTML file the user can open in their browser to explore component dependencies, sequence flows, issues, and refactoring opportunities.

## Before you start

Read the current project's `CLAUDE.md` (and any convention docs it links — e.g. `docs/conventions/naming.md`) to extract project-specific rules. These feed into **Step 5 (Analyze)** under the "Conventions" category.

## Step 1 — Entry

Identify the target file from the user's message. If ambiguous (e.g., they named a feature not a file), search for the most likely entry component and confirm before proceeding.

## Step 2 — Trace

Starting from the entry file, trace outward:

- **Components**: which React/framework components does it import and render?
- **Hooks**: which custom hooks does it use, and what do those hooks call?
- **API functions**: which client-side fetch/axios calls does it make? What are the endpoint paths?
- **API handlers / BFF**: follow those endpoint paths to their Next.js API route files, then to any handler functions those routes delegate to.
- **External services**: what does each handler ultimately call? (databases, third-party APIs, internal K8s services, Auth0, etc.)

Stop at library package boundaries (node_modules) or after 3 hops from the entry, whichever comes first. Note library calls (e.g. `useUser()` from `@auth0/nextjs-auth0`) but don't trace into them.

Read each file you trace. Don't guess at what it does.

## Step 2.5 — Collect references

Grep the repo for imports of the entry component's file path and its exported name. Also check for any barrel `index.ts` files that re-export it, and search for those barrel imports too. Record each match as `{ file, line }`.

Exclude any path matching `\.test\.`, `\.spec\.`, or `/__tests__/`. Cap the list at 50 importers; if the real count is higher, set `truncated: true` and record `totalCount`. Include this data in the top-level `references` array of the SPEC even if `importers` is empty (it tells the reader the count was checked, not unknown).

## Step 2.6 — Detect tests

For every node you collected in Step 2, look for a co-located test file. Specifically, look for:

- `<basename>.test.ts` / `<basename>.test.tsx` / `<basename>.spec.ts` / `<basename>.spec.tsx` in the same directory
- Any file named `<basename>.*` inside a `__tests__/` sibling directory

Do this in one batched glob, not N separate lookups. Set `hasTests: true` and `testFile: "<path>"` on each node that has a match; set `hasTests: false` (with no `testFile`) on nodes that don't. Always set the field — never omit it.

## Step 2.7 — Build child tree

Starting from the entry component, trace only what is **rendered** in JSX (i.e., what appears as `<ComponentName …>` in the return/render output). Do not follow hooks, event handlers, or API calls — those belong in the main architecture trace.

- Depth cap: 4 levels from the entry.
- Mark any component from `node_modules` as `external: true` and stop descending into it.
- If a component appears in multiple render sites, include it once in the flat `nodes` array and reference its `id` from all parents' `children` arrays.
- Populate `hasTests` on each child node using the same check as Step 2.6.
- Omit `childTree` entirely if the entry renders no custom children (is a leaf).

This data feeds the top-level `childTree` key in the SPEC.

## Step 3 — Classify

Assign each discovered file to a layer. Use `references/layering-guide.md` for common patterns. Standard layers for a Next.js app:

| Layer id | Contents |
|---|---|
| `client-ui` | React components, page files |
| `client-data` | Client-side fetch functions, API wrappers |
| `bff` | Next.js API routes, handler functions, BFF utilities |
| `external` | Third-party services, internal microservices, databases |

Add or rename layers if the traced code calls for it (e.g. a `worker` or `db` layer). Keep it to 3-5 layers.

## Step 4 — Sequence

Identify **every distinct user interaction** required to complete the feature's purpose. For an auth-gated flow this typically means multiple attempts: e.g. (1) anonymous click → redirect, (2) authenticated click → success. Capture each as a `scenario` block with a numbered title. Within each scenario, trace the call chain from the user action to its terminal side-effect, including any auth branches and error paths. Between scenarios, use `note` entries to describe transitions the user experiences outside the app (e.g. "Redirect to Auth0 login", "User completes login", "Return to original page").

Aim for 1–4 scenarios. A single-scenario map is fine for pure UI interactions (no auth, no external state); use multi-scenario when the first user attempt can fail/redirect and a second attempt completes the goal.

For each scenario, note which actor does the work and what flows between actors.

## Step 5 — Analyze

Walk `references/investigation-rubric.md` category by category against the code you read. Produce ISSUE entries for concrete problems found. Use the exact severity definitions in the rubric. Don't manufacture issues — if a category has no findings, skip it.

Also pull in the project-specific rules you extracted at the start and check them as part of the "Conventions" category.

## Step 6 — Propose

For each ISSUE (and for any smell that didn't reach issue severity), write a NEXT_STEP. Each step should be actionable: name the file, the change, and why it improves maintainability. Group related issues into a single step where that's cleaner.

## Step 7 — Assemble the JSON spec

Build the data object following the schemas in `references/data-model.md`. The spec must include all standard fields **plus** the three new top-level fields gathered in steps 2.5–2.7:

- `references` — importer list from Step 2.5 (always present, even if empty)
- `childTree` — render-only tree from Step 2.7 (omit only if entry is a true leaf)
- `hasTests` / `testFile` on every node — from Step 2.6

Key constraints:

- Node `id` values must be stable kebab-case strings (used as cross-references in ISSUE `nodeId` fields).
- Nodes should be laid out in horizontal bands by layer (`x`, `y`, `w`, `h` in logical units 0-800 wide, 30 units per layer band).
- `sequence.actors` must be ordered left-to-right as the call flows (browser → component → client fn → BFF → external).
- `sequence.messages` must be in call order, top-to-bottom, with `type: "call"` for forward messages and `type: "return"` for responses. Mark error/auth messages with `style: "dashed"` and attach `issueId` where relevant.
- Scenario blocks segment `sequence.messages` into user-journey chapters. Messages appear *inside* the scenario that contains them (array order determines containment). Use `note` entries for transitions between scenarios.

## Step 8 — Render

Before writing the output, compute these values from the entry file path:

- **`entryComponent`** — the component name as it appears in code (e.g. `ItemCard`).
- **`entryFile`** — the path of the entry file relative to the repo root (e.g. `libs/shared-components/src/lib/ItemCard/ItemCard.tsx`).
- **`generatedAt`** — the current local time in ISO 8601 format with timezone offset (e.g. `2026-04-14T14:53:00-07:00`). Use `date -Iseconds` in a shell if needed.
- **`group`** — derived from `entryFile`: match `^(apps|libs)/([^/]+)` and use `$1/$2` (e.g. `libs/shared-components`). If no match, use `other`.
- **`issueTitles`** — pipe-separated list of ISSUE titles from your analysis (e.g. `PRICE_TYPE enum|Double API call|NX boundary`). Omit if no issues.

Then:

1. Read `assets/template.html` — this is the complete scaffold. Do not modify the scaffold logic.
2. Find the single line: `const SPEC = {};`
3. Replace the `{}` with your assembled JSON spec. The spec must include a top-level `meta` object:
   ```json
   "meta": {
     "entryComponent": "<entryComponent>",
     "entryFile": "<entryFile>",
     "generatedAt": "<generatedAt>",
     "group": "<group>"
   }
   ```
4. Replace all five `arch-map-*` meta tag placeholders in `<head>`:
   - `__ARCH_MAP_COMPONENT__` → `entryComponent`
   - `__ARCH_MAP_ENTRY_FILE__` → `entryFile`
   - `__ARCH_MAP_GENERATED_AT__` → `generatedAt`
   - `__ARCH_MAP_GROUP__` → `group`
   - `__ARCH_MAP_ISSUES__` → `issueTitles` (or empty string)
5. Determine the output filename: `<component-kebab>--<YYYYMMDD-HHmm>.html`, where `<component-kebab>` is the kebab-case component name and the timestamp matches `generatedAt`. Example: `item-card--20260414-1453.html`.
6. Ensure `docs/architecture-maps/` exists in the project (create if not).
7. Write the complete file to `docs/architecture-maps/<filename>.html`.

## Step 9 — Update Index

After writing the map, regenerate the architecture-maps index:

1. Run: `python3 ~/.claude/skills/architecture-map/scripts/build_index.py docs/architecture-maps/`
2. This scans all maps, extracts metadata, and overwrites `docs/architecture-maps/index.html`.
3. Open both the new map and the index in the browser:
   ```
   open docs/architecture-maps/<filename>.html
   open docs/architecture-maps/index.html
   ```

Tell the user both output paths. Note any issues from your analysis that warrant immediate action.