from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.auth import authenticate, require_role
from app.models.actions import ActionGuard, ActionStatus, ApproveAction, ProposeAction, ReasonGuard
from app.models.common import Id
from app.services.actions import ActionService


def router(settings, repository):
    api = APIRouter()
    service = ActionService(settings, repository)

    @api.post("/api/simulations/{scenario_id}/actions", status_code=201)
    def propose(
        request: Request,
        scenario_id: Id,
        body: ProposeAction,
        key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ):
        actor = authenticate(request, settings)
        return service.propose(actor, scenario_id, body, key, request.state.request_id)

    @api.get("/api/actions")
    def collection(
        request: Request,
        status: ActionStatus | None = None,
        cursor: Id | None = None,
        limit: int = Query(default=25, ge=1, le=100),
    ):
        actor = authenticate(request, settings)
        rows = repository._read(
            actor.tenant_id,
            "MATCH (a:ActionProposal {tenant_id:$tenant,access_label:'PUBLIC_DEMO'}) "
            "WHERE a.id>$after AND ($status='' OR a.status=$status) "
            "RETURN a.id,a.result_json ORDER BY a.id LIMIT $limit",
            {
                "tenant": actor.tenant_id,
                "after": cursor or "",
                "status": status or "",
                "limit": limit + 1,
            },
        )
        items = []
        for row in rows[:limit]:
            try:
                items.append(service.get(actor, row[0]))
            except HTTPException as exc:
                if exc.status_code != 404:
                    raise
        return {
            "request_id": request.state.request_id,
            "items": items,
            "next_cursor": rows[limit - 1][0] if len(rows) > limit else None,
        }

    @api.get("/api/actions/{action_id}")
    def detail(request: Request, action_id: Id):
        return {
            "request_id": request.state.request_id,
            "action": service.get(authenticate(request, settings), action_id),
        }

    def change(request, action_id, decision, body, key, role=None):
        actor = authenticate(request, settings)
        if role:
            require_role(actor, role)
        result = service.transition(actor, action_id, decision, body, key, request.state.request_id)
        if decision in {"execute", "reconcile"}:
            return JSONResponse(
                {
                    "request_id": request.state.request_id,
                    "action_id": action_id,
                    "status": result["action"]["status"],
                    "status_url": f"/api/actions/{action_id}",
                },
                status_code=202,
            )
        result.setdefault("approval", result["action"].get("approval"))
        return result

    @api.post("/api/actions/{action_id}/request-approval")
    def request_approval(
        request: Request,
        action_id: Id,
        body: ActionGuard,
        key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ):
        return change(request, action_id, "request-approval", body, key)

    @api.post("/api/actions/{action_id}/approve")
    def approve(
        request: Request,
        action_id: Id,
        body: ApproveAction,
        key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ):
        return change(request, action_id, "approve", body, key, "reviewer")

    @api.post("/api/actions/{action_id}/reject")
    def reject(
        request: Request,
        action_id: Id,
        body: ReasonGuard,
        key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ):
        return change(request, action_id, "reject", body, key, "reviewer")

    @api.post("/api/actions/{action_id}/execute")
    def execute(
        request: Request,
        action_id: Id,
        body: ActionGuard,
        key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ):
        return change(request, action_id, "execute", body, key, "executor")

    @api.post("/api/actions/{action_id}/reconcile")
    def reconcile(
        request: Request,
        action_id: Id,
        body: ReasonGuard,
        key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ):
        return change(request, action_id, "reconcile", body, key, "executor")

    return api
