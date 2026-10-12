# Frontend Next-Session Handoff — PromiseOps + PromiseSeal

**Document Version:** 1.0.0  
**Date:** 2026-10-12  
**Target Repository:** `promiseops-frontend`  
**Current Branch:** `feat/frontend`  
**Commit:** `6cc8f7a`  

---

## 1. Project and Purpose

### 1.1 Business Purpose
PromiseOps protects delivery margin for B2B implementation consultancies and managed IT service providers by reconciling spoken commitments against signed contract scope, task dependencies, delivery capacity, and billing prerequisites.

PromiseSeal is the verifiable, versioned application receipt protocol (`promiseseal-v1`) that cryptographically binds an extracted oral commitment, its underlying source evidence, review state, and transition history via Ed25519 service signatures.

### 1.2 Frontend Responsibilities
The frontend is an operational decision console (not a generic AI chat landing page) engineered to help delivery directors and operations leads answer the core operational question:

> *“We promised Acme loyalty integration by Friday. Is it in scope, can we deliver it with available capacity, what is at risk, and what is the safest next action?”*

### 1.3 Relationship to Backend & FalkorDB
- **Backend Authority:** The backend owns FalkorDB graph traversals, agent orchestration, cryptographic receipt signing/verification, and policy gate enforcement.
- **Frontend Role:** The frontend renders real nodes, edges, and provenance returned by the backend; enforces role-based view controls; simulates counterfactual scenarios without modifying live graph facts; and submits review, approval, and execution mutations with idempotent headers.

---

## 2. Git and Workspace State

- **Current Working Directory:** `/Users/sama/Downloads/promiseops-frontend`
- **Current Git Branch:** `feat/frontend`
- **Configured Remotes:**
  - `origin`: `git@github.com:ADITYAchhipa/multi_agent_repo.git` (fetch & push)
- **HEAD Commit:** `6cc8f7a feat(frontend): deliver PromiseOps + PromiseSeal operational decision console`
- **Upstream Sync:**
  - `feat/frontend` is fully pushed to `origin/feat/frontend`.
  - Working tree is clean.
- **Rule of Engagement:** Do not reset, discard, stash, or overwrite existing commits without explicit user approval.

---

## 3. Implemented Frontend Surface

### 3.1 Routes and Pages
All pages are located under [`frontend/app/`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app):

1. **Operations Command (`/`):** [`frontend/app/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/page.tsx)
   - Core delivery decision alert card with live answers for scope, capacity deficit, milestone exposure, and recommended action.
   - KPI cards with formula provenance (F01 unpriced cost $800, F02 delivery milestone at risk $40,000, F04 capacity gap 5h, Knowledge Firewall findings).
   - Segregates at-risk milestone exposure ($40,000) from renewal opportunity context ($180,000).
   - Tracked commitments table with live link to receipts.

2. **Promise Inbox (`/promises`):** [`frontend/app/promises/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/promises/page.tsx)
   - Searchable, filterable promise table supporting all lifecycle states: `PROPOSED`, `NEEDS_REVIEW`, `CONFIRMED`, `DISPUTED`, `SUPERSEDED`, `FULFILLED`, `REJECTED`.
   - Prominent badges for `PROPOSED` (unconfirmed) and `DISPUTED` (conflicting quotes).
   - Customer filter and quick filter buttons. Empty, loading, and error states handled.

3. **Promise Detail / PromiseSeal Receipt (`/promises/[id]`):** [`frontend/app/promises/[id]/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/promises/%5Bid%5D/page.tsx)
   - **Tab 1 — Receipt & Cryptography:** Canonical JSON payload inspector (`promiseops-json-v1`), SHA-256 digest, Ed25519 signature from `key-demo-2026`, version timeline (`v1` &rarr; `v2`), and fresh verification checklist.
   - **Tab 2 — Evidence & Conflicts:** Verbatim transcript cues (`00:00:12`), Clause C2 scope exclusion, and open commercial conflicts (`conflict-loyalty`).
   - **Tab 3 — Tasks & Capacity:** 5-hour capacity deficit analysis (8h required vs 3h available) and connected Jira task dependencies (`ACME-101` depends on `ACME-102` BLOCKED).
   - **Tab 4 — Milestones:** Contract milestone requirements and missing acceptance criteria.
   - **Tab 5 — Tamper Sandbox:** Interactive live tamper sandbox enabling users to edit payload fields and test the non-persisting verification endpoint (`PAYLOAD_DIGEST_MISMATCH` demonstration for Demo Question #12).
   - **Review Modal Dialog:** Reviewer action modal allowing transitions (`CONFIRM`, `DISPUTE`, `REJECT`, `REVISE`) with reason input.

4. **Simulation Lab (`/simulations`):** [`frontend/app/simulations/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/simulations/page.tsx)
   - Side-by-side comparison of 3 scenarios:
     - `AS_REQUESTED`: INFEASIBLE (5h deficit + credentials blocked).
     - `RENEGOTIATE_DATE_OR_SCOPE`: FEASIBLE (conditional on customer agreement to move to Monday 16:00).
     - `CHANGE_ORDER_OR_EXTRA_CAPACITY`: FEASIBLE (conditional on internal reservation of Ben's 5h slot, extra cost $750).
   - Value provenance categorizing configured inputs, deterministic calculations (F03 extra spend, F05 total cost, F06 variance), and unknowns.
   - Schedule slot breakdown and independent auditor challenge findings.

5. **Approval Queue (`/actions`):** [`frontend/app/actions/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/actions/page.tsx)
   - Governance gate displaying proposed mutations (`action-reserve-ben`), target system (`WORKLOAD_MOCK`), and immutable proposal hash.
   - Exact before vs after field diff for target allocations.
   - Policy checks and auditor verdict.
   - Role separation: Approver must have `reviewer` role; executors cannot self-approve.

6. **Action Receipt (`/actions/[id]`):** [`frontend/app/actions/[id]/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/actions/%5Bid%5D/page.tsx)
   - Read-back verification comparing expected allocation vs actual returned state (0 mismatches).
   - Idempotency ledger record and audit chain verification (`promiseops-audit-v1`).
   - Pre-approval gate check: Execution blocked before approval is granted (Demo Question #10).

7. **Graph Explorer (`/graph`):** [`frontend/app/graph/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/graph/page.tsx)
   - Interactive React Flow (`@xyflow/react`) canvas rendering backend graph nodes and edges.
   - Template path highlighting (`PTH1` transcript quote, `PTH2` scope exclusion, `PTH3` task dependency).
   - Solid borders, distinct line styles for hypothetical scenario edges (dashed) vs conflicts (red).
   - Accessible relationship-list fallback view for mobile screens and screen readers.

8. **Knowledge Health (`/knowledge`):** [`frontend/app/knowledge/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/knowledge/page.tsx)
   - Graph Quality Firewall quarantine monitoring:
     - Orphaned tasks: `jira-orphan`.
     - Unsupported relations: `CAN_DO_MAGIC`.
     - Ambiguous identity duplicates: `person-ben-candidate` vs `person-ben`.
     - Stale sources: `src-incident`.

9. **Settings & Connectors (`/settings`):** [`frontend/app/settings/page.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/app/settings/page.tsx)
   - Health status cards for FalkorDB, LLM, Jira REST, Transcripts, and Workload mock adapter.
   - Safe masked identifier display (zero secrets revealed).
   - Demo reset trigger and DEMO / LIVE mode toggle.

### 3.2 Shared Components
- [`frontend/components/shell/app-shell.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/components/shell/app-shell.tsx): Top operational banner, active role switcher (Reviewer Aria Chen vs Executor Casey Rao vs Admin vs Viewer), mode toggle, sidebar navigation, and mobile menu.
- [`frontend/components/ui/status-badge.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/components/ui/status-badge.tsx): Universal accessible status badge mapping all lifecycle, scope, standing, and feasibility states to semantic icons and text.
- [`frontend/components/providers/query-provider.tsx`](file:///Users/sama/Downloads/promiseops-frontend/frontend/components/providers/query-provider.tsx): TanStack Query provider with standardized freshness configuration.

### 3.3 Design System & Invariants
- **Palette:** Zero purple, zero gradients. Deep navy (`#0F172A`, `#1E293B`), neutral gray borders (`#E2E8F0`, `#CBD5E1`), solid white cards, controlled blue accent (`#1481EE`).
- **Typography:** Modern readable system sans font stack, monospace identifiers, 8px-based grid spacing.
- **Accessibility:** Visible focus rings (`2px solid #1481ee`), semantic tags, screen-reader-friendly table headers, and status labels coupled with icons.

---

## 4. API Integration Status

### 4.1 Client Architecture
- Single typed client located at [`frontend/lib/api-client.ts`](file:///Users/sama/Downloads/promiseops-frontend/frontend/lib/api-client.ts).
- Centralizes base URL (`NEXT_PUBLIC_API_URL` or `/api`), request correlation header (`X-Request-ID`), idempotency key generation (`Idempotency-Key`), timeout handling (10s), and error envelope normalization into `ApiError`.

### 4.2 Data Models & TypeScript Types
Defined in [`frontend/types/api.ts`](file:///Users/sama/Downloads/promiseops-frontend/frontend/types/api.ts):
- Mirrored exactly from `docs/API_CONTRACTS.md` and `docs/PROMISESEAL_PROTOCOL.md`.
- Shared DTOs: `EvidenceRef`, `SourceSummary`, `Freshness`, `Calculation`, `GraphNode`, `GraphEdge`, `GraphPath`, `PolicyCheck`, `AuditRecord`, `TraceStep`, `ReceiptPayload`, `ReceiptEnvelope`, `Verification`, `ScopeAssessment`, `ScenarioResult`, `ActionProposalDTO`, `KnowledgeHealthResponse`, `ConnectorSummary`.

### 4.3 Mode & Seed Fixtures
- **Default Mode:** `DEMO` mode active by default.
- **Seed Fixtures:** [`frontend/lib/fixtures/seed-data.ts`](file:///Users/sama/Downloads/promiseops-frontend/frontend/lib/fixtures/seed-data.ts) deterministically mirrors `docs/SEED_SCENARIO.md`:
  - Company: Northstar Systems, Customer: Acme Retail.
  - Anchor Date: `2026-10-12` (Evaluation anchor Friday 09:00 UTC, Deadline Friday 19:00 UTC).
  - People: Aria Chen ($100/hr), Ben Ortiz ($150/hr), Casey Rao ($100/hr).
  - Promise: `promise-loyalty`, Contract clauses: C1–C5, Jira tickets: ACME-101..105.
- **Stateful In-Memory Mutations:** In `DEMO` mode, review transitions, action approval, and mock workload execution update in-memory objects to simulate live backend behavior for demo testing.
- **Live Mode:** Toggling to `LIVE` dispatches real `fetch` calls to `/api/*`.

### 4.4 Freshness & Caching Rules
- Queries have a `staleTime` of 20 seconds.
- Mutations strictly invalidate dependent query keys:
  - Review mutation invalidates `["promise-detail"]`, `["promises"]`, `["promise-verify"]`.
  - Approval mutation invalidates `["actions"]`.
  - Execution mutation invalidates `["action-detail"]`, `["actions"]`.
- No optimistic updates for consequential operations. Authoritative read-back determines success.

---

## 5. Tests and Build Evidence

### 5.1 Package Scripts
In [`frontend/package.json`](file:///Users/sama/Downloads/promiseops-frontend/frontend/package.json):
- `npm run dev`: Next.js development server
- `npm run build`: Production compilation
- `npm run lint`: Next.js Core Web Vitals ESLint
- `npm run typecheck`: `tsc --noEmit`
- `npm test`: `vitest run`

### 5.2 Verification Log (Executed 2026-10-12)
1. **TypeScript Typecheck:**
   ```bash
   npm run typecheck
   # Output: Exited with code 0 (zero errors)
   ```
2. **Vitest Unit/Component Suite:**
   ```bash
   npm test
   # Output: 4 test files passed, 16/16 tests passed:
   # ✓ tests/api-client.test.ts (5 tests)
   # ✓ tests/approval-policy.test.ts (3 tests)
   # ✓ tests/operations-command.test.tsx (3 tests)
   # ✓ tests/status-badge.test.tsx (5 tests)
   ```
3. **ESLint:**
   ```bash
   npm run lint
   # Output: ✔ No ESLint warnings or errors
   ```
4. **Next.js Production Build:**
   ```bash
   npm run build
   # Output: Next.js 14.2.24 build succeeded; 10/10 static/dynamic routes compiled cleanly.
   ```

---

## 6. Known Gaps and Dependencies

1. **Backend Integration Boundary:**
   - The backend service lives on `feat/backend`. Real endpoints have not been invoked against a live server because the backend worktree is running separately.
   - When the backend service is deployed or running locally, the frontend can be pointed to it by setting `NEXT_PUBLIC_APP_MODE=LIVE` and `NEXT_PUBLIC_API_URL=http://localhost:8000/api`.
2. **Mock Workload Adapter:**
   - The workload API contract remains unspecified in real enterprise environments. Per specification, the system intentionally fails closed to the safe `MockWorkloadAdapter`.
3. **Chat Assistant UI:**
   - The `/api/chat` interactive assistant endpoint contract is fully typed in `frontend/types/api.ts` but the UI currently focuses on the operational console pages (Overview, Inbox, Detail, Lab, Queue, Receipt, Graph, Health, Settings). A dedicated chat panel can be added in a future phase if required.

---

## 7. Prioritized Next Steps for Upcoming Session

1. **Keep Branch and Work Tree Clean:** Verify `git status` on `feat/frontend` before starting.
2. **Backend Coordination:**
   - Confirm backend endpoint availability on `feat/backend` (or Docker environment).
   - Verify that backend response schemas for `/api/promises`, `/api/simulations`, and `/api/actions` match the contract in `frontend/types/api.ts`.
3. **Live Mode Smoke Test:**
   - Start backend server on port 8000 (or configured URL).
   - Set `NEXT_PUBLIC_APP_MODE=LIVE` and `NEXT_PUBLIC_API_URL=http://localhost:8000/api` in `frontend/.env.local`.
   - Run end-to-end smoke verification against live FalkorDB queries.
4. **Demo Script Walkthrough:**
   - Run through Scenes D1–D8 from [`docs/DEMO_SCRIPT.md`](file:///Users/sama/Downloads/promiseops-frontend/docs/DEMO_SCRIPT.md):
     - Scene D1: Overview risk banner ($40k milestone at risk).
     - Scene D2: Candidate quote inspection (`00:00:12`).
     - Scene D3: Graph Explorer path traversal (`PTH1`–`PTH3`).
     - Scene D4: Simulation Lab 5-hour deficit vs Ben capacity.
     - Scene D5: Challenge and review transition.
     - Scene D6: PromiseSeal verification and Tamper Sandbox check.
     - Scene D7: Pre-approval execution block & approved execution read-back.
     - Scene D8: Audit chain verification.
5. **Quality Gates:** Always run `npm run typecheck && npm test && npm run build` before committing.

---

## 8. Continuation Prompt for the Next Session

Copy and paste the following prompt to resume in the next session:

```text
You are continuing development on PromiseOps + PromiseSeal Frontend in ~/Downloads/promiseops-frontend on branch feat/frontend.

First steps:
1. Run `pwd`, `git status --short --branch`, and verify HEAD commit.
2. Read `docs/FRONTEND_NEXT_SESSION_HANDOFF.md`, `docs/API_CONTRACTS.md`, and `docs/DEMO_SCRIPT.md`.
3. Check backend availability or instructions from the backend worktree.
4. If backend endpoints are ready, configure `NEXT_PUBLIC_APP_MODE=LIVE` and test live integration. If backend is still pending, proceed with demo scenario polish, accessibility checks, and end-to-end rehearsal.
5. In all tasks, maintain the strict design rules: ZERO purple, ZERO gradients, solid surfaces, deep navy navigation, controlled blue accent, and accessible icon+label status badges.
6. Verify all changes with `npm run typecheck`, `npm test`, and `npm run build` before committing.
```
