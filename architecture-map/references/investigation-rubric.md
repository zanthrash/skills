# Investigation Rubric

Walk these six categories in order for each file traced. Not every file will have findings in every category — that's fine. Only report real issues; don't manufacture them.

---

## 1. Auth & Authorization

Questions to answer from the code:
- Does the component/route require authentication? How is that enforced?
- Is auth checked client-side only, server-side only, or both?
- What happens when the auth check fails? Is the failure visible to the caller, or swallowed?
- Are tokens or credentials forwarded correctly (header format, expiry, scope)?
- Are there unauthenticated code paths that should be gated?

Common patterns to flag as ISSUES:
- Handler calls `res.end()` (or returns nothing) when token is missing → `critical` (silent success)
- Auth gated only on the client (`useUser()`, session check) with no server-side enforcement → `warning`
- No `withApiAuthRequired` (or equivalent) on mutating routes → `warning`
- Token forwarded as custom JSON string where standard Bearer is expected → `warning`
- Auth session expiry not handled at the call site → `warning`

---

## 2. Correctness

Questions to answer from the code:
- Does every code path that can fail produce an observable error? Or are failures swallowed?
- Are HTTP status codes set correctly on all responses (especially error paths)?
- Are there unhandled promise rejections or missing catch blocks?
- Is response parsing robust against unexpected shapes (empty body, null, 204)?
- Are mutation handlers idempotent where they need to be?

Common patterns to flag as ISSUES:
- `res.end()` without a status code → defaults to 200, misleads callers → `critical`
- Catch block that logs but returns a success-shaped object → `critical`
- Absence of a fallback when an API response has an unexpected shape → `warning`
- Race condition: state updated before async confirmation → `warning`
- Response assumed to have `.data` without checking status first → `warning`

---

## 3. Convention Violations

Questions to answer from the code:
- Are there TypeScript enums where union types should be used (per project convention)?
- Are barrel exports (index.ts) exporting test helpers, side-effecting imports, or vitest symbols?
- Do names follow the project's naming conventions (per CLAUDE.md / naming.md)?
- Is the module boundary for an Nx library being crossed in a way that's flagged by the linter?
- Are there `// eslint-disable` comments suppressing boundary or naming rules?

Common patterns to flag as ISSUES:
- `enum Foo { … }` where project convention requires `type Foo = 'A' | 'B'` → `minor`
- Test helper exported from a production barrel (`index.ts`) → `warning` (crashes Next.js at runtime)
- `// eslint-disable-next-line @nx/enforce-module-boundaries` comments → `minor` (may indicate structural debt)
- File names not matching the component name (per naming convention) → `minor`

---

## 4. Complexity

Questions to answer from the code:
- Are any functions longer than ~50 lines? What's the fan-out (number of distinct things called)?
- Is there duplicated logic across sibling files (e.g. two handlers doing the same auth dance)?
- Is a component doing data fetching, state management, and rendering all at once ("god component")?
- Are there deeply nested conditionals that could be extracted or early-returned?
- Is the same API called multiple times in a component tree without a shared cache or context?

Common patterns to flag as ISSUES:
- Handler with 4+ separate responsibilities → `warning` (separation of concerns)
- Two handlers with identical auth boilerplate → `warning` (extract shared utility)
- Component with 200+ lines mixing data fetching, business logic, and JSX → `warning`
- Deep nesting (4+ levels) that obscures the happy path → `minor`

---

## 5. Observability

Questions to answer from the code:
- Are errors logged with enough context to diagnose in production (status code, URL, payload shape)?
- Are distributed traces started/propagated across the BFF→service call boundary?
- Is there an error boundary above this component in the component tree?
- Are analytics events fired on failure paths, not just success?
- Would a failing watchlist call be visible in logs/APM with enough context to debug?

Common patterns to flag as ISSUES:
- `console.error("Error removing item from watchlist", error)` with no structured context → `minor`
- No tracing span on outbound BFF→service call → `minor`
- Silent failure path produces no log entry at all → `warning`
- Analytics events fire on success but no event on failure → `minor`

---

## 6. Performance

Questions to answer from the code:
- Are there N+1 request patterns (a list component issuing one request per item)?
- Are heavy components memoized where renders would be frequent?
- Are API calls de-duplicated (SWR/React Query key, shared context) or duplicated per component instance?
- Is a large dependency (icon set, charting lib) imported at the component level when it could be lazy-loaded?
- Is there an unnecessary re-render when the only changed prop is a stable function reference?

Common patterns to flag as ISSUES:
- Multiple sibling components each calling the same endpoint → `warning` (lift to shared context)
- Inline anonymous function passed as prop to memoized child → `minor` (breaks memo)
- Full icon library imported instead of individual icons → `minor`
- No `useCallback` on handlers passed down the tree → `minor` (depends on tree depth)

---

## Severity cheat sheet

| Severity | Meaning |
|---|---|
| `critical` | Incorrect behavior in production — data not saved, auth bypassed, wrong HTTP status, data loss |
| `warning` | High likelihood of bugs or fragile patterns that will cause incidents |
| `minor` | Code quality, convention, or maintainability concerns with no immediate correctness risk |