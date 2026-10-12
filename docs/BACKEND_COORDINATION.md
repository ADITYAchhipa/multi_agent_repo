# Backend coordination — 2026-10-12

Branch: `feat/backend`. Backend owns `backend/` and its tests/configuration. No frontend files
modified. No GitHub connector is available in this session, so this file is the coordination
fallback. No shared contract, ontology, lifecycle or frontend schema is changed.

| API / component | Status |
|---|---|
| `GET /api/health` | Implemented; exact top-level contract, graph offline → 503 |
| Internal process liveness | `/internal/live`, not a frontend product endpoint |
| EvidenceRef, ReceiptPayload, ReceiptEnvelope | Strict Python models implemented; not a complete API model freeze |
| Session, sources, promises, verification routes | Pending real graph/auth/provenance implementation |
| Chat, simulations, graph, traces, audit, keys, connectors | Pending |
| Actions, approvals, execution, reconciliation | Pending; zero dispatch paths enabled |

Health service values use `OK` / `UNAVAILABLE` (inner `services` scalar values were unspecified
in the contract); top-level `OK` / `DEGRADED` is unchanged. All pending product routes return the
safe 404 envelope, not fixture success. Debug docs are off unless explicitly configured locally.

Blocking dependency: Docker executable/runtime absent. S01 has not established any query,
index, atomicity or persistence compatibility. Backend graph mutation/action work must not
be represented as available. Public health tests with injected probes are API tests only.

Do not use byte-signature validity as business confirmation or action approval. The phase-0
crypto function is intentionally not published as the contract's full verification endpoint.

Status and exact check outcomes are maintained in IMPLEMENTATION_NOTES.md. Next milestone:
run/fix/extend S01 against the pinned server, then implement the no-LLM graph publication slice.
