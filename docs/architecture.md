# PRISM Architecture

## Overview

PRISM is a monorepo developer tool that analyzes GitHub pull requests using a **deterministic analysis engine**. An optional AI provider can enhance reports later without rewriting the core pipeline.

```
Next.js (apps/web)
        |
        | middleware: prism_session | prism_guest → / ; else /welcome
        | POST /api/v1/analyze  (+ optional prism_session cookie)
        | GET  /api/v1/me/pull-requests?filter=...
        v
FastAPI (apps/api)
        |
        +-- Auth (optional GitHub OAuth) → encrypted session cookie
        +-- GitHubClient (REST | Mock) — uses viewer token when present
        +-- Normalizer → domain models
        +-- AnalysisOrchestrator
              +-- Change / Test / Risk / Dependency / Complexity / Impact
              +-- ReviewQuestionGenerator
              +-- AnalysisProvider (optional AI)
        |
        v
AnalysisReport → Dashboard
```

## Boundaries

1. **GitHub integration** — only `GitHubClient` implementations talk to GitHub.
2. **Normalization** — analyzers never see raw GitHub JSON.
3. **Analyzers** — pure domain logic; no FastAPI/httpx imports.
4. **Providers** — AI is behind `AnalysisProvider`; MVP keeps `AI_ENABLED=false`.
5. **Cache** — `AnalysisCache` keyed by `owner/repo#pr@head_sha`, or `viewer:{login}:...` when authenticated so private reports never leak across users. Open-PR search results use `viewer:{login}:open_prs:{filter}` (60s TTL).

## Data flow

1. Parse and validate PR URL (or load demo fixture).
2. Fetch PR, files, commits (with optional OAuth user token).
3. Normalize into `PullRequest` / `ChangedFile`.
4. Enforce size limits; allow partial analysis.
5. Run analyzers (structured findings with evidence).
6. Aggregate summary + contextual review questions.
7. Optionally call AI provider with structured context.
8. Return `AnalysisReport` (never raw GitHub payloads).

## Web session gate

Next.js middleware checks cookie *presence* only (no decryption):

- `prism_session` or `prism_guest=1` → allow `/` (home workspace).
- Neither → redirect to `/welcome`.
- Signed-in users hitting `/welcome` → redirect to `/`.

Guest mode is for public PRs and the demo. Auth callback errors redirect to `/welcome?auth_error=...`.

## Private repositories (Connect GitHub)

Public PR analysis works with no sign-in. For private repos and the open-PRs feed:

1. User signs in with GitHub → OAuth authorize (`repo` scope).
2. Callback exchanges the code for a token and stores `{token, login, avatar_url, exp}` in an encrypted HttpOnly `prism_session` cookie (Fernet via `SESSION_SECRET`).
3. Subsequent `/analyze` and `/me/pull-requests` calls include the cookie; the API never sends the token to the browser JS.
4. Logout best-effort revokes the OAuth grant and clears the cookie.

**Open PRs:** `GET /api/v1/me/pull-requests` queries GitHub Search (`is:pr is:open … author:@me` / `review-requested:@me` / `assignee:@me`) and returns normalized `OpenPullRequest` items.

**Scope tradeoff:** GitHub OAuth Apps have no read-only private-repo scope, so PRISM requests `repo`. A future GitHub App with fine-grained read-only permissions is the upgrade path.

**404 disambiguation:** when a PR fetch 404s, PRISM probes the repository endpoint to distinguish missing PR vs private/no-access, and surfaces a Connect GitHub hint for anonymous private-repo attempts.

## Security posture

- No repository cloning or code execution.
- Diffs treated as untrusted input.
- Tokens never logged or exposed to the frontend.
- Session cookie: HttpOnly, SameSite=Lax, Secure when `PUBLIC_WEB_URL` is https.
- Configurable `MAX_FILES`, `MAX_PATCH_SIZE`, `MAX_TOTAL_DIFF_SIZE`.
