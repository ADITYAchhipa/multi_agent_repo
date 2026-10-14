import hashlib
from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException, Request
from redis.exceptions import RedisError

from app.auth import authenticate
from app.config import Settings
from app.graph.connection import GraphUnavailable
from app.graph.queries import scenarios
from app.graph.repository import GraphRepository
from app.models.common import Id
from app.models.scenarios import SimulationDetail, SimulationRequest, SimulationResponse
from app.promise_seal.canonicalize import canonical_bytes, digest, strict_json
from app.services.audit import sign_audit
from app.services.scenarios import compute


def accessible(repository: GraphRepository, tenant: str, value: dict):
    receipt = value["inputs"]["receipt"]
    row = repository.promise_detail(tenant, receipt["promise_id"], receipt["receipt_id"])
    if row is None:
        raise HTTPException(404)
    for ref in receipt["source_refs"]:
        source = repository.source_version(tenant, ref["source_id"], ref["source_version_id"])
        if ref["access_label"] != "PUBLIC_DEMO" or source != [
            ref["source_hash"],
            ref["representation_hash"],
            "AVAILABLE",
        ]:
            raise HTTPException(404)
    for assumption in value["assumptions"]:
        for ref_id in assumption["evidence_ref_ids"]:
            if repository.review_evidence(tenant, ref_id) is None:
                raise HTTPException(404)


def get_scenario(repository: GraphRepository, tenant: str, actor: str, scenario_id: str) -> dict:
    rows = repository._read(
        tenant, scenarios.READ, {"tenant": tenant, "actor": actor, "id": scenario_id}
    )
    if not rows:
        raise HTTPException(404)
    value = strict_json(rows[0][0].encode())
    accessible(repository, tenant, value)
    if repository.graph_revision(tenant) != rows[0][1]:
        value["status"] = "STALE"
    return value


def router(settings: Settings, repository: GraphRepository) -> APIRouter:
    api = APIRouter()

    @api.get("/api/simulations/{scenario_id}", response_model=SimulationDetail)
    def get(request: Request, scenario_id: Id):
        actor = authenticate(request, settings)
        value = get_scenario(repository, actor.tenant_id, actor.id, scenario_id)
        return {"request_id": request.state.request_id, "scenario": value}

    @api.post("/api/simulations", status_code=201, response_model=SimulationResponse)
    def create(
        request: Request,
        body: SimulationRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ):
        actor = authenticate(request, settings)
        request_digest = digest(body.model_dump(mode="json"))
        run = (
            "simulation-"
            + hashlib.sha256(
                f"{actor.tenant_id}\0{actor.id}\0{idempotency_key}".encode()
            ).hexdigest()[:40]
        )

        def replay():
            rows = repository._read(
                actor.tenant_id,
                scenarios.LEDGER,
                {"tenant": actor.tenant_id, "actor": actor.id, "id": run},
            )
            if not rows:
                return None
            if rows[0][0] != request_digest:
                raise HTTPException(409)
            value = strict_json(rows[0][1].encode())
            for item in value["results"]:
                accessible(repository, actor.tenant_id, item)
            value["request_id"] = request.state.request_id
            return value

        previous = replay()
        if previous:
            return previous
        state = repository.review_state(actor.tenant_id, body.promise_id)
        if state is None:
            raise HTTPException(404)
        if state[0] != body.base_graph_revision:
            raise HTTPException(409)
        if body.parent_scenario_id:
            parent = get(request, body.parent_scenario_id)["scenario"]
            if parent["inputs"]["receipt"]["promise_id"] != body.promise_id:
                raise HTTPException(422)
        receipt = strict_json(state[6].encode())
        ids = [f"{run}-{index}" for index in range(len(body.scenario_types))]
        now = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        results = compute(body, receipt, ids, now)
        for result in results:
            accessible(repository, actor.tenant_id, result)
        response = {"request_id": request.state.request_id, "scenario_ids": ids, "results": results}
        if settings.signing_private_key_path is None or settings.signing_key_id is None:
            raise GraphUnavailable("scenario signing is not configured")
        audit_id = f"audit-{run}"
        payload = {
            "protocol_version": "promiseops-audit-v1",
            "event_id": audit_id,
            "tenant_id": actor.tenant_id,
            "sequence": state[1] + 1,
            "event_type": "SCENARIO_COMPUTED",
            "actor_id": actor.id,
            "occurred_at": now,
            "request_id": request.state.request_id,
            "payload": {
                "scenario_ids": ids,
                "input_digest": request_digest,
                "result_digest": digest(results),
            },
            "prev_event_hash": state[2],
            "signing_key_id": settings.signing_key_id,
        }
        try:
            signed = sign_audit(payload, settings.signing_private_key_path)
            params = {
                "tenant": actor.tenant_id,
                "actor": actor.id,
                "promise": body.promise_id,
                "receipt": receipt["receipt_id"],
                "revision": state[0],
                "previous_sequence": state[1],
                "sequence": state[1] + 1,
                "prev_hash": state[2],
                "run": run,
                "digest": request_digest,
                "result_json": canonical_bytes(response).decode(),
                "audit_id": audit_id,
                "now": now,
                "audit_payload": signed.payload_json,
                "audit_hash": signed.event_hash,
                "signature": signed.signature,
                "key_id": settings.signing_key_id,
                "request_id": request.state.request_id,
                "parent": body.parent_scenario_id,
                "scenarios": [
                    {"id": item["id"], "result_json": canonical_bytes(item).decode()}
                    for item in results
                ],
            }
            graph = repository.connection.graph_for_tenant(actor.tenant_id)
            rows = graph.query(
                scenarios.PUBLISH, params=params, timeout=settings.falkordb_query_timeout_ms
            ).result_set
        except (RedisError, OSError, ValueError) as exc:
            raise GraphUnavailable("scenario publication failed") from exc
        if not rows:
            previous = replay()
            if previous:
                return previous
            raise HTTPException(409)
        return response

    return api
