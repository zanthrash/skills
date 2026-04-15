# Layering Guide

How to classify traced files into architectural layers. Match the pattern closest to the codebase you're analyzing. Keep layers to 3-5; more than that makes the diagram crowded.

---

## Next.js Pages Router (standard for this repo)

| Layer id | label | What belongs here |
|---|---|---|
| `client-ui` | CLIENT\nCOMPONENTS | React components, page files (`pages/*.tsx` excluding `api/`), context providers consumed on the client |
| `client-data` | CLIENT\nAPI CALLS | Client-side fetch wrappers, axios helpers, SWR/React Query hooks that hit internal BFF routes |
| `bff` | BFF /\nNEXT.JS API | `pages/api/**`, handler functions, BFF utilities (handlerWrapper, shared middleware), server-side session utilities |
| `external` | EXTERNAL\nSERVICES | Third-party APIs (Auth0, Stripe, etc.), internal microservices (K8s services), databases, CDNs |

**When to add extra layers:**
- Add `worker` for Web Workers, background jobs, or queue consumers
- Add `db` if the repo contains ORM models/migrations and you want to distinguish DB schema from HTTP services
- Add `shared` for pure utility libraries (formatters, validators) that don't belong to client or server

---

## Next.js App Router

| Layer id | label | What belongs here |
|---|---|---|
| `client-ui` | CLIENT\nCOMPONENTS | `'use client'` components, client hooks |
| `server-ui` | SERVER\nCOMPONENTS | RSC components, `page.tsx`, `layout.tsx` |
| `server-actions` | SERVER\nACTIONS | `'use server'` functions, Route Handlers (`app/api/**`) |
| `external` | EXTERNAL\nSERVICES | Databases, third-party services, auth providers |

---

## React SPA (Vite / CRA, no BFF)

| Layer id | label | What belongs here |
|---|---|---|
| `client-ui` | CLIENT\nCOMPONENTS | React components, pages |
| `client-data` | CLIENT\nAPI CALLS | Axios/fetch wrappers, React Query hooks |
| `external` | EXTERNAL\nSERVICES | Backend APIs (not owned by this repo), auth providers |

---

## Node.js / Express (API-only)

| Layer id | label | What belongs here |
|---|---|---|
| `route` | ROUTES | Express router files |
| `controller` | CONTROLLERS | Request/response orchestration |
| `service` | SERVICES | Business logic |
| `data` | DATA LAYER | ORM models, DB clients, cache clients |
| `external` | EXTERNAL | Third-party APIs, message queues |

---

## Color palette reference

Pick one set of colors per layer. These are visually distinct on dark backgrounds:

| Semantic | fill | stroke | text |
|---|---|---|---|
| Blue (client) | #1e2a3a | #3b82f6 | #93c5fd |
| Purple (data/hooks) | #231d35 | #8b5cf6 | #c4b5fd |
| Amber (BFF/server) | #2a2314 | #f59e0b | #fcd34d |
| Green (external) | #142218 | #10b981 | #6ee7b7 |
| Pink (DB) | #2a1525 | #ec4899 | #f9a8d4 |
| Orange (queue/worker) | #2a1e10 | #f97316 | #fdba74 |

---

## Naming conventions

- Layer IDs: lowercase kebab-case, no spaces (`client-ui`, `bff`, not `BFF` or `Client UI`)
- Match layer IDs exactly in `node.layer` and in preset `layers` arrays
- Layer labels use `\n` to split into two lines: `"BFF /\nNEXT.JS API"`