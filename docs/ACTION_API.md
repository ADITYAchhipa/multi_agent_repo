# Action delivery contract (additive implementation specification)

This contract precedes the new endpoints. Existing action route semantics in API_CONTRACTS
remain authoritative. All mutations require a 16–128 character Idempotency-Key and session.
Tenant/actor come from session; errors use the shared safe envelope. Mutations use signed
AuditEvent + OperationRun + GraphState revision/sequence/head CAS in one graph write.

`POST /api/simulations/{scenario_id}/actions` is an additive scenario-scoped proposal factory,
not arbitrary graph/action creation. Body `{expected_scenario_digest, target_id,
requested_changes:{resource_id,task_id,allocation_slots:[{start,end}],cost_ceiling:{amount,currency}}}`.
It creates an explicitly MOCK workload reservation, with a confirmed current signed promise
receipt, source verification, a saved scenario and exact proposal/dependency digests.
The initial mock target state is explicitly an empty reservation, not observed provider data.
Mock reservation is a test of the approval/dispatch protocol; it makes no assertion that a real
person has capacity or that a customer's delivery/change order is approved.
201 `{request_id,action,audit_event_id}`. Scenario inputs and conditional assumptions stay visible.

`GET /api/actions?status=&cursor=&limit=25` returns `{request_id,items,next_cursor}` (max 100).
`GET /api/actions/{id}` returns `{request_id,action}`. PUBLIC_DEMO tenant visibility only.

Transitions: request-approval (authenticated), approve/reject (reviewer), execute/reconcile
(executor). Request-approval/execute body `{expected_revision,proposal_hash}`; approve adds
`reason`; reject/reconcile body `{expected_revision,reason}`. Success read/review is 200;
execute/reconcile return 202 operation reference. Revision conflict/invalid transition is 409.
Approval expires after 15 minutes, binds exact proposal and is rechecked against current receipt,
source hashes, key trust and target state before dispatch. Uncertain execution never redispatches;
reconcile performs read-back only. Terminal actions cannot be recycled.

A durable EXECUTING claim precedes dispatch. The mock adapter persists target state and an
attempt identity in FalkorDB, with a target before-state compare-and-set. Repeated calls with
same attempt cannot apply another change. Crash between claim/dispatch/result publication
leaves EXECUTING and is recoverable through read-only reconciliation (without re-dispatch).
No real external adapter is selected by these routes until live adapter policy gates are added.
