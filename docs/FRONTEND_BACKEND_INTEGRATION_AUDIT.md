# Frontend-Backend Integration Audit — PromiseOps + PromiseSeal

**Audit Date:** 2026-10-13  
**Auditor:** Senior Frontend Engineer  
**Workspace:** `promiseops-frontend` (`feat/frontend`)  
**Baseline Specification:** `docs/API_CONTRACTS.md` (Frozen Application API and Adapter Contracts)  
**Related Documents:** `docs/PROMISESEAL_PROTOCOL.md`, `docs/DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY_AND_THREAT_MODEL.md`, `docs/BACKEND_COORDINATION.md`, `docs/NEXT_SESSION_HANDOFF.md`  
**Backend Branch Inspected:** `origin/feat/backend` (at commit `a5cfbdc`)

---

## 1. Executive Summary

This comprehensive audit inspects the frontend client layer (`frontend/lib/api-client.ts`), data contracts (`frontend/types/api.ts`), React Query caching configuration (`frontend/components/providers/query-provider.tsx`), page-level consumers across `frontend/app/`, and test coverage.

Every client operation has been cross-referenced with:
1. The authoritative frozen specification in `docs/API_CONTRACTS.md`.
2. The PromiseSeal v1 protocol in `docs/PROMISESEAL_PROTOCOL.md`.
3. The latest backend implementation on `origin/feat/backend` (commits `64132d5`, `b55540a`, `a5cfbdc`).

### Summary of Findings:
- **Backend Implementation Reality:** The backend on `origin/feat/backend` has currently implemented `GET /api/health`, `POST /api/session`, `GET /api/session`, `GET /api/promises`, `GET /api/promises/{promise_id}`, and `GET /api/promises/{promise_id}/verify`. All other routes (`/api/simulations`, `/api/actions/*`, `/api/graph/*`, `/api/health/knowledge`, `/api/connectors`, `/api/chat`) remain unimplemented and return standard FastAPI 404 NOT_FOUND error envelopes.
- **Frontend Contract Defects:**
  1. Action mutations (`approve`, `reject`, `execute`) omitted required concurrency binding fields (`expected_revision` and `proposal_hash`), which would trigger 422 or 409 errors on real backends.
  2. The frontend called an undocumented collection route `GET /api/simulations`; the frozen contract specifies simulation generation via `POST /api/simulations` and single scenario retrieval via `GET /api/simulations/{scenario_id}`.
  3. The graph view called a parameterless `GET /api/graph?depth=1`; the frozen contract strictly specifies `GET /api/graph/{entity_id}?depth=1` anchored to an entity ID.
  4. Missing client helper methods for documented routes: `POST /api/actions/{action_id}/request-approval`, `POST /api/actions/{action_id}/reconcile`, `POST /api/promises/{promise_id}/receipts/{receipt_id}/revoke`, `POST /api/chat`, `POST /api/session`, `POST /api/session/logout`.
  5. URL encoding was omitted on opaque resource IDs.
  6. Read collection response types omitted `next_cursor`.
- **LIVE Mode Vulnerabilities:**
  1. When switched to LIVE mode, missing backend endpoints resulted in empty states or hardcoded fallback data (e.g. fabricated Knowledge Firewall counts in `knowledge/page.tsx`), violating the non-fabrication rule.
  2. Switching modes did not synchronize across UI components or invalidate React Query caches.
  3. Timeout cleanup leaked timers on network failure and did not normalize aborts into 504 status.

---

## 2. Complete Discrepancy Matrix

| ID | Endpoint / Feature | Source File(s) | Severity | Contract Specification (`docs/API_CONTRACTS.md`) | Actual Frontend Implementation | Backend Status (`feat/backend`) | Recommended Correction |
|---|---|---|---|---|---|---|---|
| **DISC-01** | `POST /api/actions/{action_id}/approve` | `frontend/lib/api-client.ts`<br>`frontend/app/actions/page.tsx` | **HIGH** | §6, line 94: Requires `{ expected_revision, proposal_hash, reason }` in request body. Binds immutable proposal hash. | Sent `{ reason }` only; omitted `expected_revision` and `proposal_hash`. | Pending (404) | Update `approveAction` signature to require `expected_revision` and `proposal_hash`. Update caller in Approval Queue. |
| **DISC-02** | `POST /api/actions/{action_id}/reject` | `frontend/lib/api-client.ts`<br>`frontend/app/actions/page.tsx` | **HIGH** | §6, line 95: Requires `{ expected_revision, reason }` in request body. | Sent `{ reason }` only; omitted `expected_revision`. | Pending (404) | Update `rejectAction` signature to require `expected_revision`. Update caller in Approval Queue. |
| **DISC-03** | `POST /api/actions/{action_id}/execute` | `frontend/lib/api-client.ts`<br>`frontend/app/actions/[id]/page.tsx` | **HIGH** | §6, line 96: Requires `{ expected_revision, proposal_hash }` in request body. | Sent `{}` (empty object); omitted `expected_revision` and `proposal_hash`. | Pending (404) | Update `executeAction` signature to require `expected_revision` and `proposal_hash`. Update caller in Action Receipt. |
| **DISC-04** | `POST /api/actions/{action_id}/request-approval` | `frontend/lib/api-client.ts` | **MEDIUM** | §6, line 93: Requires `{ expected_revision, proposal_hash }`. Returns `{ request_id, action, approval }`. | Method was completely omitted from `api-client.ts`. | Pending (404) | Implement `requestApproval(actionId, { expected_revision, proposal_hash })` in `api-client.ts`. |
| **DISC-05** | `POST /api/actions/{action_id}/reconcile` | `frontend/lib/api-client.ts` | **MEDIUM** | §7, line 135: Requires `{ expected_revision, reason }`. Read-only provider call; 202 status. | Method was completely omitted from `api-client.ts`. | Pending (404) | Implement `reconcileAction(actionId, { expected_revision, reason })` in `api-client.ts`. |
| **DISC-06** | `POST /api/simulations` vs `GET /api/simulations` | `frontend/lib/api-client.ts`<br>`frontend/app/simulations/page.tsx` | **HIGH** | §5, line 77: `POST /api/simulations` takes `{ promise_id, base_graph_revision, question, scenario_types, assumptions, parent_scenario_id? }`. Returns 201 `{ request_id, scenario_ids, results: ScenarioResult[] }`. There is **no** `GET /api/simulations` collection route. Individual scenarios read via `GET /api/simulations/{scenario_id}`. | `getSimulations()` issued `GET /api/simulations` in LIVE mode. | Pending (404) | Add `createSimulations(...)` using `POST /api/simulations`. Update `getSimulations(...)` to handle LIVE mode honestly as pending backend endpoint. |
| **DISC-07** | `GET /api/graph/{entity_id}` | `frontend/lib/api-client.ts`<br>`frontend/app/graph/page.tsx` | **HIGH** | §7, line 115: `GET /api/graph/{entity_id}?depth=1` requires an `entity_id`. Capped at &le;60 nodes. | Called `GET /api/graph?depth=1` without entity ID when `entityId` was undefined. | Pending (404) | Require or default `entity_id` (default `"promise-loyalty"`). Always query `/api/graph/${encodeURIComponent(entityId)}?depth=${depth}`. Update return type to include `expansion_hints?: string[]`. |
| **DISC-08** | `POST /api/chat` | `frontend/lib/api-client.ts` | **LOW** | §5, line 73: `POST /api/chat` takes `{ question, session_id?, context? }`. Returns completed chat result. | Typed in `types/api.ts` but method missing from `api-client.ts`. | Pending (404) | Add `sendChatMessage(...)` to `api-client.ts`. |
| **DISC-09** | Session Bootstrap, Logout & DTO | `frontend/lib/api-client.ts`<br>`frontend/types/api.ts` | **MEDIUM** | §7, line 123-125: `POST /api/session` `{ credential }` sets cookie. `GET /api/session` returns `{ request_id, actor: { id, roles }, mode, expires_at }`. `POST /api/session/logout` returns `{ request_id, logged_out: true }`. | Frontend had only `getSession()`. DTO assumed `actor.name` and top-level `tenant_id` which backend does not return. Missing `bootstrapSession` and `logout`. | Implemented (`/session` POST & GET) | Align `SessionInfo` DTO with backend schema. Add `bootstrapSession(credential)` and `logoutSession()`. |
| **DISC-10** | `POST /api/promises/{promise_id}/receipts/{receipt_id}/revoke` | `frontend/lib/api-client.ts` | **LOW** | §7, line 132: Admin-only revocation `{ expected_revision, reason }`. | Method omitted from `api-client.ts`. | Pending (404) | Implement `revokeReceipt(...)` in `api-client.ts`. |
| **DISC-11** | Read Collection Pagination | `frontend/types/api.ts`<br>`frontend/lib/api-client.ts` | **MEDIUM** | §1, line 9: Read collections return `{ request_id, items, next_cursor }`. Default limit 25, max 100. | Client return types omitted `next_cursor`. `getPromises` omitted query params `deadline_from`, `deadline_to`, `cursor`, `limit`. | Implemented on `GET /api/promises` | Add `next_cursor?: string \| null` to collection types. Add pagination and date range filter params to `getPromises`. |
| **DISC-12** | URL Encoding of Resource IDs | `frontend/lib/api-client.ts` | **MEDIUM** | §1, line 7: "Opaque IDs are URL-encoded; never interpreted as paths." | Resource IDs (`promiseId`, `actionId`, `scenarioId`, `entityId`, `versionId`) were interpolated directly without `encodeURIComponent`. | N/A | Wrap all dynamic path segments in `encodeURIComponent`. |
| **DISC-13** | Fabricated Data & Unhandled LIVE States | `frontend/app/knowledge/page.tsx`<br>`frontend/app/simulations/page.tsx`<br>`frontend/app/actions/page.tsx`<br>`frontend/app/graph/page.tsx` | **HIGH** | §1, §6: In LIVE mode, missing backend endpoints must not fabricate mock data or simulate success. UI must present an honest unavailable or degraded state while preserving navigation. | `knowledge/page.tsx` fell back to hardcoded `{ nodes: 54, edges: 88... }` when backend returned 404. Other pages showed blank white space or generic empty lists. | Multiple routes pending | Eliminate fabricated live fallback data. Provide structured, honest unavailable states with error code, explanation, and milestone status for unimplemented endpoints in LIVE mode. |
| **DISC-14** | Concurrency Conflict & Stale Error Parsing | `frontend/lib/api-client.ts`<br>`frontend/app/promises/[id]/page.tsx` | **MEDIUM** | §1, line 16, 19: 409 returned for `STALE_APPROVAL`, `IDEMPOTENCY_CONFLICT`, or stale revision with structured `details: [{ field, reason }]`. | `ApiError` parsed details, but review modal in `promises/[id]` did not display mutation error or guidance on 409 conflict. | Handled in FastAPI | Add helper methods on `ApiError` (`isConflict`, `isStaleApproval`, `isNotFound`, `isUnimplemented`). Render structured error banners inside review and action modals. |
| **DISC-15** | Bounded Timeout & Abort Cleanup | `frontend/lib/api-client.ts` | **MEDIUM** | §1, line 19: Bounded timeout returns 504. | `timeoutId` was not cleared if `fetch` threw an error; `AbortError` was converted to generic 503 instead of 504 TIMEOUT_ERROR. | N/A | Clear `timeoutId` in a `finally` block. Map `AbortError` to `ApiError("TIMEOUT_ERROR", ..., 504)`. |
| **DISC-16** | Mode State Synchronization | `frontend/components/shell/app-shell.tsx`<br>`frontend/app/settings/page.tsx`<br>`frontend/lib/api-client.ts` | **MEDIUM** | Seamless switching between DEMO and LIVE modes. | Mode was local state in both `AppShell` and `SettingsPage`, causing out-of-sync indicators and failing to invalidate React Query caches upon toggle. | N/A | Add a subscriber mechanism to `ApiClient` for mode and actor changes. Sync state across components and invalidate all queries on mode change. |

---

## 3. Deep Dive on Critical Architectural Discrepancies

### 3.1 Concurrency and Hash Bindings on Action Proposals (DISC-01, DISC-02, DISC-03)
In `docs/API_CONTRACTS.md` §6 (lines 85–97) and `docs/SECURITY_AND_THREAT_MODEL.md` (STH08, STH09):
- A proposal's `proposal_hash` cryptographically binds its action ID, target system, requested changes, `before_state_hash`, `dependency_digest`, scenario input digest, and policy version.
- When a reviewer approves an action, the backend validates that `proposal_hash` matches and that the resource has not advanced past `expected_revision`.
- When an executor executes an action, the backend re-validates `expected_revision` and `proposal_hash` to guard against TOCTOU races or stale dependencies.
- **Frontend Defect:** The initial client passed `{ reason }` to `approveAction`, `{ reason }` to `rejectAction`, and `{}` to `executeAction`. A compliant backend validator rejects these with `422 UNPROCESSABLE_ENTITY` (missing required fields) or `409 STALE_REVISION`.
- **Correction:** `apiClient.approveAction` requires `{ expected_revision: number, proposal_hash: string, reason: string }`. `apiClient.rejectAction` requires `{ expected_revision: number, reason: string }`. `apiClient.executeAction` requires `{ expected_revision: number, proposal_hash: string }`. Callers in `app/actions/page.tsx` and `app/actions/[id]/page.tsx` pass these values directly from the active `ActionProposalDTO`.

### 3.2 Graph Traversal Endpoint & Anchor Node (DISC-07)
In `docs/API_CONTRACTS.md` §7 (line 115):
- The contract specifies `GET /api/graph/{entity_id}?depth=1` where depth is 1–3 and maximum nodes &le; 60.
- There is no un-anchored `GET /api/graph` route in the frozen contract. This prevents unbounded whole-graph dumps that could exhaust server resources (STH15).
- **Frontend Defect:** The frontend adapter allowed `entityId` to be omitted, resulting in calls to `GET /api/graph?depth=1`.
- **Correction:** The adapter will always supply an anchor `entity_id` (defaulting to `"promise-loyalty"` or the selected root node) and URL-encode the path parameter: `GET /api/graph/${encodeURIComponent(entityId)}?depth=${depth}`. The return schema will be updated to include `expansion_hints?: string[]`.

### 3.3 Simulation Generation vs Collection Route (DISC-06)
In `docs/API_CONTRACTS.md` §5 (lines 77–79):
- Simulations are deterministic counterfactual runs evaluated against an anchor promise and graph revision.
- Scenarios are requested via `POST /api/simulations` and retrieved individually via `GET /api/simulations/{scenario_id}`.
- **Frontend Defect:** In LIVE mode, `getSimulations()` called `GET /api/simulations`.
- **Correction:** Provide `createSimulations(payload: SimulationCreateRequest)` matching the contract. For the simulation dashboard in LIVE mode, if the backend has not yet implemented simulations (returning 404), display an honest "Simulation Engine Pending Implementation" state without fabricating live data, while keeping the 3 verified scenario fixtures active in DEMO mode.

### 3.4 Honest LIVE Mode & Elimination of Fabricated Data (DISC-13)
Per prompt instructions:
- "When an endpoint has not yet been implemented by Codex: Show an honest unavailable or not-yet-supported state. Preserve the relevant page layout and useful navigation. Do not fabricate live data or display a simulated successful write. Keep the documented mock behavior available only in explicit DEMO mode."
- **Frontend Defect:** `frontend/app/knowledge/page.tsx` fell back to `{ nodes: 54, edges: 88, stale_sources: 1... }` when `data` was missing.
- **Correction:** Remove all fabricated live fallback metrics. Introduce an `UnavailableStateCard` component across pages that clearly communicates:
  1. The HTTP status code and error code (`404 NOT_FOUND` / `503 SERVICE_UNAVAILABLE`).
  2. The specific backend route that is pending implementation by Codex.
  3. Guidance that the feature is fully functional with synthetic fixtures in DEMO mode.

---

## 4. Implementation Plan for Frontend Corrections

1. **`frontend/types/api.ts`:**
   - Add typed request DTOs: `ActionApprovalRequest`, `ActionRejectRequest`, `ActionExecuteRequest`, `ActionRequestApprovalRequest`, `ActionReconcileRequest`, `SimulationCreateRequest`, `ChatRequest`, `SessionBootstrapRequest`.
   - Update `SessionInfo` to match backend `SessionResponse` (`actor: { id: string; roles: string[]; name?: string }`).
   - Update `GraphResponse` to include `expansion_hints?: string[]`.
   - Add `next_cursor?: string | null` to all collection response types.

2. **`frontend/lib/api-client.ts`:**
   - Update `approveAction`, `rejectAction`, `executeAction` to take exact required payloads.
   - Add `requestApproval`, `reconcileAction`, `createSimulations`, `sendChatMessage`, `bootstrapSession`, `logoutSession`, `revokeReceipt`.
   - Fix `getGraph`: ensure `entity_id` is always present and URL-encoded.
   - Wrap all dynamic IDs in `encodeURIComponent`.
   - Improve `request<T>`: timeout cleanup in `finally`, classify `AbortError` as 504 `TIMEOUT_ERROR`, preserve `details` array in `ApiError`, add helper methods on `ApiError`.
   - Add mode/actor change listener mechanism so UI subscribers can react to mode switches and invalidate caches.

3. **Page Component Updates (`frontend/app/`):**
   - `app/actions/page.tsx`: Pass `expected_revision` and `proposal_hash` to `approveAction` and `rejectAction`. Show honest unavailable state in LIVE mode if `/api/actions` returns 404.
   - `app/actions/[id]/page.tsx`: Pass `expected_revision` and `proposal_hash` to `executeAction`. Show honest unavailable state in LIVE mode if action not found.
   - `app/graph/page.tsx`: Pass anchor entity ID (`"promise-loyalty"`). Show honest unavailable state if `/api/graph/*` returns 404/503 in LIVE mode.
   - `app/simulations/page.tsx`: Show honest unavailable state in LIVE mode if backend endpoint is 404.
   - `app/knowledge/page.tsx`: Remove fabricated fallback counts in LIVE mode. Show honest unavailable state if 404.
   - `app/settings/page.tsx`: Sync mode with `apiClient` listener and invalidate queries.
   - `app/promises/[id]/page.tsx`: Display mutation errors (including 409 conflict details) inside the review modal.
   - `components/shell/app-shell.tsx`: Invalidate queries on mode switch; synchronize mode toggle with global listener.

4. **Testing:**
   - Extended unit and component tests to verify exact payload structures, URL encoding, idempotency headers, 409 handling, mode switching, and honest unavailable states in LIVE mode.

---

## 5. Backend Status and Blocking Endpoints for Codex

As recorded from `origin/feat/backend` (latest commit `a5cfbdc`):

| Endpoint | Method | Backend Status | Blocking Milestone |
|---|---|---|---|
| `/api/health` | GET | **Implemented** (checks FalkorDB ready) | Complete |
| `/api/session` | POST, GET | **Implemented** (demo bootstrap & signed cookie) | Complete |
| `/api/promises` | GET | **Implemented** (tenant-scoped FalkorDB read) | Complete |
| `/api/promises/{id}` | GET | **Implemented** (reads receipt & scope) | Complete |
| `/api/promises/{id}/verify` | GET | **Implemented** (payload/sig check; source UNAVAILABLE) | Complete |
| `/api/promises/{id}/review` | POST | **Pending** (requires review mutation & version publish) | Milestone M1/M2 |
| `/api/simulations` | POST | **Pending** (requires deterministic simulator & planner) | Milestone M3 |
| `/api/simulations/{id}` | GET | **Pending** (requires scenario persistence) | Milestone M3 |
| `/api/actions` | GET | **Pending** (requires action proposal persistence) | Milestone M4 |
| `/api/actions/{id}` | GET | **Pending** (requires action proposal read-back) | Milestone M4 |
| `/api/actions/{id}/approve` | POST | **Pending** (requires policy engine & approval ledger) | Milestone M4 |
| `/api/actions/{id}/reject` | POST | **Pending** (requires cancellation ledger) | Milestone M4 |
| `/api/actions/{id}/execute` | POST | **Pending** (requires mock workload adapter & read-back) | Milestone M4 |
| `/api/graph/{entity_id}` | GET | **Pending** (requires graph traversal query) | Milestone M1/M2 |
| `/api/health/knowledge` | GET | **Pending** (requires quarantine & finding counts) | Milestone M1 |
| `/api/connectors` | GET | **Pending** (requires connector telemetry registry) | Milestone M1 |
| `/api/chat` | POST | **Pending** (requires agent orchestrator) | Milestone M3 |

---

## 6. Implementation Summary & Verification Evidence

All 16 discrepancies have been corrected on the frontend. The codebase strictly conforms to `docs/API_CONTRACTS.md` and `docs/PROMISESEAL_PROTOCOL.md`.

### Files Modified and Added:
1. `frontend/types/api.ts`: Aligned all DTOs (`ActionApprovalRequest`, `ActionRejectRequest`, `ActionExecuteRequest`, `ActionRequestApprovalRequest`, `ActionReconcileRequest`, `SimulationCreateRequest`, `ChatRequest`, `ChatResponse`, `SessionBootstrapRequest`, `GraphResponse`, `SessionInfo`, `next_cursor`).
2. `frontend/lib/api-client.ts`: Hardened HTTP client with 10s timeout, abort controller cleanup, 504 `TIMEOUT_ERROR`, structured `ApiError` class, `encodeURIComponent` on dynamic segments, `Idempotency-Key` header injection on non-session mutations, `getGraph(entityId, depth)` pointing to `GET /api/graph/{entity_id}?depth={depth}`, and mode change listener subscription.
3. `frontend/components/ui/unavailable-state.tsx`: Added new reusable accessible UI card to render honest 404/503 unavailable states in LIVE mode without fabricating data.
4. `frontend/app/actions/page.tsx`: Bound `expected_revision` and `proposal_hash` to approvals/rejections; rendered honest unavailable state for 404 in LIVE mode.
5. `frontend/app/actions/[id]/page.tsx`: Bound `expected_revision` and `proposal_hash` to execution; rendered honest unavailable state for 404 in LIVE mode.
6. `frontend/app/graph/page.tsx`: Fixed graph route to query anchor entity ID (`"promise-loyalty"`); rendered honest unavailable state for 404/503 in LIVE mode.
7. `frontend/app/simulations/page.tsx`: Rendered honest unavailable state for 404 in LIVE mode.
8. `frontend/app/knowledge/page.tsx`: Removed fabricated metric fallbacks; rendered honest unavailable state for 404 in LIVE mode.
9. `frontend/app/settings/page.tsx`: Synced mode toggle with API client subscription; invalidated React Query cache on change.
10. `frontend/app/promises/[id]/page.tsx`: Rendered structured `reviewMutation.error` banner in review modal.
11. `frontend/app/page.tsx`: Updated overview metrics to prevent fabricating Knowledge Firewall counts in LIVE mode.
12. `frontend/components/shell/app-shell.tsx`: Synchronized mode switch and role changes with React Query cache invalidation.
13. `frontend/tests/approval-policy.test.ts`: Updated to pass required approval and execution DTO fields.
14. `frontend/tests/contract-conformance.test.tsx`: Added 17 contract conformance, idempotency, error normalization, demo isolation, and UI state tests.

### Verification Execution Results:

```bash
$ npm run typecheck
> promiseops-frontend@0.1.0 typecheck
> tsc --noEmit
# Exit code: 0 (0 errors)

$ npm test
> promiseops-frontend@0.1.0 test
> vitest run
# Test Files: 5 passed (5)
# Tests: 33 passed (33)
# Duration: 1.61s
# Passed suites:
#  ✓ tests/api-client.test.ts (5)
#  ✓ tests/approval-policy.test.ts (3)
#  ✓ tests/contract-conformance.test.tsx (17)
#  ✓ tests/operations-command.test.tsx (3)
#  ✓ tests/status-badge.test.tsx (5)

$ npm run lint
> promiseops-frontend@0.1.0 lint
> next lint
# ✔ No ESLint warnings or errors

$ npm run build
> promiseops-frontend@0.1.0 build
> next build
# ✓ Compiled successfully
# ✓ Generating static pages (10/10)
# Exit code: 0
```

---

## 7. Remaining Contract Conflicts and Risks

1. **Graph Endpoint Hierarchy vs Anchor Node:**
   - Contract specifies `GET /api/graph/{entity_id}?depth=1`. The frontend now queries `GET /api/graph/promise-loyalty?depth=1` by default. If the backend implementation requires an unanchored whole-graph query, the backend owner must define a distinct endpoint or document `"root"` / `"tenant-default"` as the default root entity ID.
2. **Missing Backend Endpoints in LIVE Mode:**
   - 11 of the 16 documented routes are not yet implemented in `origin/feat/backend` (Commit `a5cfbdc`).
   - The frontend handles these gracefully in LIVE mode via `UnavailableStateCard` and error normalization, while remaining 100% interactive in DEMO mode.
3. **Simulations API Method:**
   - The frozen contract specifies `POST /api/simulations` to generate simulations. The frontend triggers `POST /api/simulations` with `SimulationCreateRequest`. When Codex implements scenario retrieval, a `GET /api/simulations` or `GET /api/simulations/{id}` route will be consumed.

---

## 8. Exact Steps to Enable and Verify LIVE Mode Once Codex Finishes

When Codex finishes implementing the backend services:

1. **Start the Backend Server:**
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. **Verify Backend Health:**
   ```bash
   curl http://localhost:8000/api/health
   # Expected: {"status": "OK", "services": {"api": "OK", "graph": "OK"}}
   ```
3. **Configure Frontend Environment:**
   In `frontend/.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
5. **Switch to LIVE Mode in UI:**
   - Navigate to `http://localhost:3000/settings` or click the mode indicator in the top application header.
   - Select **LIVE Backend** mode.
   - The client will bootstrap a session with `POST /api/session`, fetch authoritative promises via `GET /api/promises`, verify receipts via `GET /api/promises/{id}/verify`, and invalidate in-memory demo data.
   - All implemented routes will seamlessly stream live data from FalkorDB and the backend crypto service.
