"""Durable MOCK reservation approval, dispatch claim and read-only reconciliation."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.graph.connection import GraphUnavailable
from app.promise_seal.canonicalize import canonical_bytes, digest, strict_json
from app.promise_seal.models import ReceiptEnvelope, ReceiptPayload
from app.services.mutations import MutationStore, now
from app.services.verification import evaluate_receipt

READ = "MATCH (a:ActionProposal {id:$id,tenant_id:$tenant,access_label:'PUBLIC_DEMO'}) RETURN a.result_json"
TARGET = "MATCH (t:WorkloadSnapshot {id:$id,tenant_id:$tenant,mode:'MOCK'}) RETURN t.state_json,t.attempt_id"


class MockWorkloadAdapter:
    mode = "MOCK"

    def __init__(self, repository):
        self.repository = repository

    def read(self, tenant, target):
        rows = self.repository._read(tenant, TARGET, {"tenant": tenant, "id": target})
        if not rows:
            return {}, None
        return strict_json(rows[0][0].encode()), rows[0][1]

    def execute(self, tenant, action, attempt):
        # Caller already persisted its exclusive EXECUTING claim. This is an atomic
        # mock target CAS; no vendor API or actual human capacity is involved.
        desired = action["requested_changes"]
        before = action["before_state"]
        query = """
        MATCH (a:ActionProposal {id:$action,tenant_id:$tenant,status:'EXECUTING'})
        WHERE a.attempt_id=$attempt
        MERGE (t:WorkloadSnapshot {id:$target,tenant_id:$tenant,mode:'MOCK'})
        ON CREATE SET t.state_json='{}',t.access_label='PUBLIC_DEMO'
        WITH a,t WHERE t.state_json=$before OR t.attempt_id=$attempt
        SET t.state_json=$desired,t.attempt_id=$attempt,t.updated_at=$at
        RETURN t.state_json
        """
        try:
            rows = (
                self.repository.connection.graph_for_tenant(tenant)
                .query(
                    query,
                    params=dict(
                        action=action["id"],
                        tenant=tenant,
                        attempt=attempt,
                        target=action["target_id"],
                        before=canonical_bytes(before).decode(),
                        desired=canonical_bytes(desired).decode(),
                        at=now(),
                    ),
                    timeout=self.repository.connection.settings.falkordb_query_timeout_ms,
                )
                .result_set
            )
        except (RedisError, OSError) as exc:
            raise GraphUnavailable("mock adapter outcome unknown") from exc
        return bool(rows)


class ActionService:
    def __init__(self, settings, repository):
        self.settings, self.repository = settings, repository
        self.store = MutationStore(settings, repository)
        self.adapter = MockWorkloadAdapter(repository)

    def get(self, actor, action_id):
        rows = self.repository._read(
            actor.tenant_id, READ, {"id": action_id, "tenant": actor.tenant_id}
        )
        if not rows:
            raise HTTPException(404)
        action = strict_json(rows[0][0].encode())
        self.receipt(actor, action["promise_id"], verify=False)
        return action

    def receipt(self, actor, promise_id, verify=True):
        row = self.repository.promise_detail(actor.tenant_id, promise_id)
        if row is None:
            raise HTTPException(404)
        receipt = ReceiptEnvelope(
            payload=ReceiptPayload.model_validate(strict_json(row[11].encode())),
            payload_sha256=row[12],
            signature_base64url=row[13],
        )
        if receipt.payload.promise_id != promise_id or receipt.payload.tenant_id != actor.tenant_id:
            raise HTTPException(404)
        for ref in receipt.payload.source_refs:
            if ref.access_label != "PUBLIC_DEMO" or self.repository.source_version(
                actor.tenant_id, ref.source_id, ref.source_version_id
            ) != [ref.source_hash, ref.representation_hash, "AVAILABLE"]:
                raise HTTPException(404)
        if verify:
            result = evaluate_receipt(
                self.settings, self.repository, receipt, actor.tenant_id, row[4]
            )
            if (
                row[3] != "CONFIRMED"
                or row[4] != "ACTIVE"
                or result.integrity != "VALID"
                or any(check.result != "PASS" for check in result.checks)
            ):
                raise HTTPException(409)
        return receipt

    def save(self, actor, route, key, body, action, request_id, old=None, boundary=None):
        match, params = (
            "",
            {
                "action": action["id"],
                "action_json": canonical_bytes(action).decode(),
                "status": action["status"],
                "action_revision": action["revision"],
                "attempt": action.get("attempt_id"),
                "scenario": action["scenario_id"],
            },
        )
        if old is None:
            match = "MATCH (sc:Scenario {id:$scenario,tenant_id:$tenant}) "
            mutation = """
            CREATE (a:ActionProposal {id:$action,tenant_id:$tenant,access_label:'PUBLIC_DEMO',
              result_json:$action_json,status:$status,revision:$action_revision,created_at:$at})
            CREATE (sc)-[:HAS_ACTION {id:$action+'-scenario',tenant_id:$tenant,status:'ACTIVE',
              access_label:'PUBLIC_DEMO',provenance_kind:'DERIVED',provenance_json:'[]'}]->(a)
            """
        else:
            params.update(old_revision=old["revision"], old_status=old["status"])
            match = """
            MATCH (a:ActionProposal {id:$action,tenant_id:$tenant})
            WHERE a.revision=$old_revision AND a.status=$old_status
            """
            mutation = """SET a.result_json=$action_json,a.status=$status,
               a.revision=$action_revision,a.attempt_id=$attempt,a.updated_at=$at """
        result = self.store.commit(
            actor,
            route,
            key,
            body,
            "ACTION_" + action["status"],
            {
                "action_id": action["id"],
                "proposal_hash": action["proposal_hash"],
                "status": action["status"],
                "mode": "MOCK",
                "revision": action["revision"],
            },
            {"request_id": request_id, "action": action},
            match=match,
            mutation=mutation,
            params=params,
            boundary=boundary,
        )
        result["request_id"] = request_id
        return result

    def propose(self, actor, scenario_id, body, key, request_id):
        route = f"/api/simulations/{scenario_id}/actions"
        raw = body.model_dump(mode="json")
        replay = self.store.replay(actor, route, key, raw)
        if replay is not None:
            self.get(actor, replay["action"]["id"])
            return {**replay, "request_id": request_id}
        boundary = self.repository.audit_boundary(actor.tenant_id)
        rows = self.repository._read(
            actor.tenant_id,
            "MATCH (sc:Scenario {id:$id,tenant_id:$tenant,access_label:'PUBLIC_DEMO'}) "
            "RETURN sc.result_json",
            {"tenant": actor.tenant_id, "id": scenario_id},
        )
        if not rows:
            raise HTTPException(404)
        scenario = strict_json(rows[0][0].encode())
        if scenario["input_digest"] != body.expected_scenario_digest:
            raise HTTPException(409)
        promise_id = scenario["inputs"]["receipt"]["promise_id"]
        receipt = self.receipt(actor, promise_id)
        if receipt.payload.receipt_id != scenario["inputs"]["receipt"]["receipt_id"]:
            raise HTTPException(409)
        before, _ = self.adapter.read(actor.tenant_id, body.target_id)
        action_id = "action-" + uuid4().hex
        dependency = digest(
            {
                "receipt": receipt.payload_sha256,
                "scenario": scenario["input_digest"],
                "sources": [ref.model_dump(mode="json") for ref in receipt.payload.source_refs],
            }
        )
        action = dict(
            id=action_id,
            revision=1,
            scenario_id=scenario_id,
            promise_id=promise_id,
            action_type="WORKLOAD_UPDATE",
            target_system="WORKLOAD_MOCK",
            target_id=body.target_id,
            mode="MOCK",
            before_state=before,
            before_state_hash=digest(before),
            requested_changes=raw["requested_changes"],
            dependency_digest=dependency,
            receipt_ids=[receipt.payload.receipt_id],
            receipt_digests=[receipt.payload_sha256],
            evidence_refs=[ref.model_dump(mode="json") for ref in receipt.payload.source_refs],
            graph_paths=scenario.get("graph_paths", []),
            impact=scenario.get("calculations", []),
            auditor_verdict="MOCK_PROTOCOL_ONLY",
            policy_checks=[
                {
                    "rule_id": "MOCK_ONLY",
                    "outcome": "PASS",
                    "reason": "Tests reservation protocol only; no claim of real capacity or delivery feasibility.",
                    "evidence_ref_ids": [],
                }
            ],
            required_approval_role="reviewer",
            status="PROPOSED",
            idempotency_key=key,
            approval=None,
            attempts=[],
            external_response_reference=None,
            read_back=None,
            scenario_caveats=scenario.get("missing_inputs", []),
        )
        action["proposal_hash"] = digest(
            {
                "action_id": action_id,
                "tenant_id": actor.tenant_id,
                "action_type": action["action_type"],
                "target_system": action["target_system"],
                "target_id": body.target_id,
                "mode": "MOCK",
                "requested_changes": raw["requested_changes"],
                "before_state_hash": action["before_state_hash"],
                "dependency_digest": dependency,
                "receipt_ids": action["receipt_ids"],
                "receipt_digests": action["receipt_digests"],
                "scenario_id": scenario_id,
                "scenario_digest": scenario["input_digest"],
                "auditor_result_digest": digest(action["auditor_verdict"]),
                "policy_version": "v1",
            }
        )
        return self.save(actor, route, key, raw, action, request_id, boundary=boundary)

    def transition(self, actor, action_id, decision, body, key, request_id):
        route = f"/api/actions/{action_id}/{decision}"
        raw = body.model_dump(mode="json")
        action = self.get(actor, action_id)
        replay = self.store.replay(actor, route, key, raw)
        if replay is not None:
            return {**replay, "request_id": request_id}
        boundary = self.repository.audit_boundary(actor.tenant_id)
        if action["revision"] != body.expected_revision:
            raise HTTPException(409)
        if hasattr(body, "proposal_hash") and body.proposal_hash != action["proposal_hash"]:
            raise HTTPException(409)
        allowed = {
            "request-approval": {"PROPOSED"},
            "approve": {"NEEDS_APPROVAL"},
            "reject": {"NEEDS_APPROVAL", "APPROVED"},
            "execute": {"APPROVED"},
            "reconcile": {"EXECUTING", "NEEDS_RECONCILIATION"},
        }
        if action["status"] not in allowed[decision]:
            raise HTTPException(409)
        changed = {**action, "revision": action["revision"] + 1}
        if decision in {"request-approval", "approve", "execute"}:
            receipt = self.receipt(actor, action["promise_id"])
            if [receipt.payload_sha256] != action["receipt_digests"]:
                raise HTTPException(409)
            before, _ = self.adapter.read(actor.tenant_id, action["target_id"])
            if digest(before) != action["before_state_hash"]:
                raise HTTPException(409)
        if decision == "request-approval":
            changed["status"] = "NEEDS_APPROVAL"
        elif decision == "approve":
            changed["status"] = "APPROVED"
            changed["approval"] = dict(
                id="approval-" + uuid4().hex,
                actor_id=actor.id,
                approved_at=now(),
                expires_at=(datetime.now(UTC) + timedelta(minutes=15))
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z"),
                proposal_hash=action["proposal_hash"],
                reason=body.reason,
            )
        elif decision == "reject":
            changed.update(
                status="CANCELLED", rejection={"actor_id": actor.id, "reason": body.reason}
            )
        elif decision == "execute":
            approval = action["approval"]
            user = self.settings.demo_users.get(approval["actor_id"])
            if (
                approval["expires_at"] <= now()
                or approval["proposal_hash"] != action["proposal_hash"]
                or user is None
                or user.tenant_id != actor.tenant_id
                or "reviewer" not in user.roles
            ):
                raise HTTPException(409)
            changed.update(status="EXECUTING", attempt_id="attempt-" + uuid4().hex)
            changed["attempts"] = [
                *action["attempts"],
                dict(id=changed["attempt_id"], started_at=now(), mode="MOCK", status="CLAIMED"),
            ]
        else:
            changed = self.readback(actor, action)
        result = self.save(
            actor, route, key, raw, changed, request_id, old=action, boundary=boundary
        )
        if decision == "execute":
            try:
                self.adapter.execute(actor.tenant_id, changed, changed["attempt_id"])
                self.finish(actor, changed, request_id)
            except GraphUnavailable, HTTPException:
                # The persisted claim survives. A retry replays the claim and never dispatches.
                pass
        return result

    def readback(self, actor, action):
        actual, attempt = self.adapter.read(actor.tenant_id, action["target_id"])
        matches = actual == action["requested_changes"] and attempt == action.get("attempt_id")
        return {
            **action,
            "revision": action["revision"] + 1,
            "status": "SUCCEEDED" if matches else "NEEDS_RECONCILIATION",
            "external_response_reference": "mock:" + action.get("attempt_id", "unknown"),
            "read_back": dict(
                expected=action["requested_changes"],
                actual=actual,
                mismatches=[] if matches else ["target state or attempt identity differs"],
                checked_at=now(),
                verified=matches,
                mode="MOCK",
            ),
        }

    def finish(self, actor, action, request_id):
        boundary = self.repository.audit_boundary(actor.tenant_id)
        changed = self.readback(actor, action)
        return self.save(
            actor,
            "internal/action-result",
            action["attempt_id"],
            {"attempt": action["attempt_id"]},
            changed,
            request_id,
            old=action,
            boundary=boundary,
        )
