# Architecture Map — Data Model

This is the authoritative schema for the JSON spec embedded in the HTML template. The template reads `const SPEC = {...}` and drives all rendering from it.

## Top-level shape

```json
{
  "title": "ComponentName — Feature Description",
  "subtitle": "Brief one-line summary of what this map covers",
  "layers": [...],
  "presets": [...],
  "nodes": [...],
  "connections": [...],
  "issues": [...],
  "nextSteps": [...],
  "sequence": { "actors": [...], "messages": [...] }
}
```

---

## `layers` — array

Defines the horizontal bands in the architecture view. Order determines top-to-bottom rendering.

```json
{
  "id": "client-ui",           // kebab-case, referenced by node.layer
  "label": "CLIENT\nCOMPONENTS", // \n splits into two lines in the sidebar label
  "fill": "#1e2a3a",           // background color of the band
  "stroke": "#3b82f6",         // node border color for this layer
  "text": "#93c5fd",           // node label text color
  "y": 15,                     // top of band in SVG units
  "h": 105                     // height of band in SVG units
}
```

**Standard layer stack (adjust y/h to fit node count):**

| id | label | fill | stroke | text | typical y | typical h |
|---|---|---|---|---|---|---|
| `client-ui` | CLIENT\nCOMPONENTS | #1e2a3a | #3b82f6 | #93c5fd | 15 | 90 |
| `client-data` | CLIENT\nAPI CALLS | #231d35 | #8b5cf6 | #c4b5fd | 115 | 70 |
| `bff` | BFF /\nNEXT.JS API | #2a2314 | #f59e0b | #fcd34d | 198 | 100 |
| `external` | EXTERNAL\nSERVICES | #142218 | #10b981 | #6ee7b7 | 311 | 85 |

Adjust `y` and `h` when you have many nodes in a layer. The last layer's `y + h` should be around 400-450 for comfortable viewing.

---

## `presets` — array

Buttons that snap the layer visibility to common views. Include 3-5.

```json
{
  "id": "full",             // used to mark which button is active
  "label": "Full System",
  "layers": ["client-ui", "client-data", "bff", "external"],  // all visible layer ids
  "conns": ["dependency", "tool-call", "data-flow", "event"]  // all visible conn types
}
```

Good defaults: `"Full System"` (everything), `"<FeatureName> Flow"` (feature-relevant subset), `"Auth Focus"` (hide client-data, show bff + external), `"Issues Only"` (same as Full but connection types stripped).

---

## `nodes` — array

One entry per significant file or service in the traced dependency graph.

```json
{
  "id": "watchlist-btn",          // kebab-case, used as from/to in connections and nodeId in issues
  "label": "AddToWatchlist\nButtonNewUI",  // \n for line breaks; keep under ~20 chars per line
  "sub": "libs/shared-components/…/ItemCard/\nAddToWatchlistButtonNewUI.tsx",  // file path; \n ok
  "x": 200,                       // left edge in SVG units (0-800 range)
  "y": 32,                        // top edge in SVG units
  "w": 190,                       // width
  "h": 58,                        // height; use 45-50 for 1-line labels, 55-65 for 2-line
  "layer": "client-ui",           // must match a layer id
  "issues": [3],                  // issue ids whose nodeId === this node (for badge rendering)
  "hasTests": true,               // boolean — co-located test file exists next to this file
  "testFile": "libs/shared-components/…/AddToWatchlistButtonNewUI.test.tsx"  // optional; path shown in badge tooltip
}
```

**Test detection guidance (for the producer):** For each node, check for a file matching the source basename with `.test.tsx`, `.test.ts`, `.spec.tsx`, `.spec.ts` in the same directory, or inside a `__tests__/` sibling directory. Set `hasTests: false` explicitly when no test file is found — don't omit the field. Omitting `testFile` is fine when `hasTests` is false.

**Layout guidelines:**
- Within a layer band, distribute nodes horizontally with ~10-20px gaps.
- Keep node x+w < 790.
- The `issues` array on the node should be populated automatically when you know which issues map to this node — it drives the red/amber badge circles rendered on the node.

---

## `connections` — array

Directed edges between nodes.

```json
{
  "from": "watchlist-btn",     // source node id
  "to": "add-items",           // target node id
  "type": "tool-call",         // see connection types below
  "label": "on add"            // short edge label (optional but recommended)
}
```

**Connection types and rendering:**

| type | color | dash | use for |
|---|---|---|---|
| `dependency` | #6b7280 | dashed 5,3 | renders / imports / wraps |
| `tool-call` | #10b981 | solid | function calls, hook usage |
| `data-flow` | #3b82f6 | solid | HTTP requests, Bearer tokens, data passing |
| `event` | #ef4444 | dashed 5,3 | redirects, auth failures, async events |

---

## `issues` — array

Concrete concerns found in the traced code. Only include real findings — don't pad.

```json
{
  "id": 1,
  "severity": "critical",       // "critical" | "warning" | "minor"
  "title": "Silent 200 on missing auth token",
  "file": "changeWatchlistHandler.ts:53",   // file + line where issue lives
  "nodeId": "change-handler",              // which node to highlight
  "desc": "When getAccessToken() returns no token, the handler calls res.end() with no status code — defaulting to 200. The client receives an empty successful response and treats it as success."
}
```

**Severity guide:**
- `critical` — incorrect behavior in production; data loss, silent failures, auth bypass, security hole
- `warning` — likely to cause bugs; fragile patterns, missing error handling, convention violations with impact
- `minor` — code quality, style, maintainability without immediate correctness risk

---

## `nextSteps` — array

Actionable refactoring steps derived from issues (and non-issue smells).

```json
{
  "id": 1,
  "text": "Return 401 instead of silent res.end() — In changeWatchlistHandler.ts:53, replace res.end() with res.status(401).json({ error: \"Unauthorized\" }) when accessToken is falsy.",
  "code": "changeWatchlistHandler.ts:53"   // short monospace chip shown in the UI
}
```

---

## `sequence` — object

Drives the swimlane sequence diagram.

### `sequence.actors` — array

Left-to-right columns; order should follow the natural call direction.

```json
{
  "id": "btn",
  "label": "AddToWatchlist\nButtonNewUI"   // \n ok
}
```

Typical ordering: `user` → component → client fn → api-route → handler → auth-service → external-service

### `sequence.messages` — array

Ordered list of messages (arrows) from top to bottom.

```json
{
  "from": "user",          // actor id
  "to": "btn",             // actor id (same as from = self-loop, shown as curved arrow)
  "label": "click button",
  "type": "call",          // "call" | "return"
  "style": "solid",        // "solid" | "dashed" (dashed = return, error, or async)
  "color": "#e2e8f0",      // optional override; omit to use semantic default
  "issueId": null          // number | null — attaches ⚠ Issue #N badge to this arrow
}
```

**Color semantics (use these, not raw hex, when color is omitted):**
- Call messages: `#e2e8f0` (neutral) or `#3b82f6` (data/HTTP)
- Return / success: `#10b981`
- Error / auth fail: `#ef4444`
- Function calls: `#10b981`

**Structuring multi-scenario journeys (preferred):**

Use `scenario` blocks to group messages into distinct user-journey chapters. Each scenario renders as a titled, bordered container spanning all lifelines. Messages following a `scenario` entry belong to that scenario until the next one.

```json
{
  "type": "scenario",
  "id": "anon-attempt",
  "title": "1. Anonymous user clicks Add",
  "subtitle": "User has no session cookie",
  "color": "#3b82f6"
}
```

- `id`: kebab-case; stable identifier
- `title`: displayed in the scenario header bar
- `subtitle`: optional secondary descriptor shown below the title
- `color`: optional accent color for the left border stripe; defaults to `#3b82f6`

Use `note` entries between scenarios to describe transitions that happen outside the app (Auth0 redirect, email verification, etc.):

```json
{
  "type": "note",
  "label": "Redirect to Auth0 login",
  "icon": "↪"
}
```

- `label`: italic text shown in the callout pill
- `icon`: optional single character prepended to the label

**Structuring branches (within a scenario):**

Add a `divider` entry between branches to visually separate conditional paths within a single scenario:

```json
{
  "type": "divider",
  "label": "— Branch: no token (silent failure) —"
}
```

**Outcome annotations** (text at the bottom of a lifeline):

```json
{
  "type": "outcome",
  "actor": "btn",
  "label": "❌ UI shows 'watched' — item NOT saved",
  "color": "#ef4444"
}
```

---

## `references` — array (top-level, optional)

Reverse-dependency data: who imports each traced node. Only populate for the entry node (and any other node worth highlighting). Exclude test files.

```json
"references": [
  {
    "nodeId": "watchlist-btn",
    "importers": [
      { "file": "apps/shell/src/components/ItemCard/ItemCard.tsx", "line": 23 },
      { "file": "libs/search/src/components/SearchResults.tsx", "line": 88 }
    ],
    "truncated": false,    // true if more than 50 importers were found (list is capped)
    "totalCount": 2        // actual importer count before any truncation
  }
]
```

**Producer notes:**
- Search for `import … from '…<component-name>…'` and barrel re-exports that forward the component.
- Exclude paths matching `\.test\.`, `\.spec\.`, or `/__tests__/`.
- Cap `importers` at 50. If truncated, set `truncated: true` and `totalCount` to the real number.
- If no non-test importers are found, include the entry with `"importers": []` so the UI can show "0 references" rather than "unknown".

---

## `childTree` — object (top-level, optional)

Pure render-tree rooted at the entry component. Covers only JSX render output (not hooks, not API calls). Library components are included but marked `external: true` and not descended into.

```json
"childTree": {
  "rootId": "watchlist-btn",
  "nodes": [
    {
      "id": "watchlist-btn",
      "label": "AddToWatchlistButtonNewUI",
      "file": "libs/shared-components/…/AddToWatchlistButtonNewUI.tsx",
      "hasTests": true,
      "children": ["icon-btn", "tooltip-wrap"]
    },
    {
      "id": "icon-btn",
      "label": "IconButton",
      "file": "@mui/material",
      "hasTests": false,
      "external": true,
      "children": []
    },
    {
      "id": "tooltip-wrap",
      "label": "Tooltip",
      "file": "@mui/material",
      "hasTests": false,
      "external": true,
      "children": []
    }
  ]
}
```

**Field reference:**

| field | type | notes |
|---|---|---|
| `rootId` | string | `id` of the entry node in the `nodes` array |
| `nodes[].id` | string | stable kebab-case identifier |
| `nodes[].label` | string | display name (no `\n` needed — tree view wraps) |
| `nodes[].file` | string | source path or package name for library components |
| `nodes[].hasTests` | boolean | same detection rule as the per-node field above |
| `nodes[].external` | boolean | `true` for node_modules components; omit or `false` for internal |
| `nodes[].children` | string[] | ordered list of child node `id`s rendered by this node |

**Producer notes:**
- Depth cap: 4 levels from the entry.
- If a component is rendered in multiple places (e.g. a shared Button appears twice), include it once in the flat `nodes` array and reference it by `id` in both parents' `children` arrays.
- Stop descending at `external: true` nodes.
- `childTree` and `childTree.nodes` may be omitted entirely if the entry is a leaf (renders no custom children).