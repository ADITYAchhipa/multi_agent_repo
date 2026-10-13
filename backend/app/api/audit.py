from fastapi import APIRouter, HTTPException, Query, Request

from app.auth import authenticate, require_role
from app.config import Settings
from app.graph.repository import GraphRepository
from app.models.audit import AuditCheck, AuditVerifyResponse, CheckedRange, Checkpoint
from app.services.audit import UNSTABLE_SNAPSHOT, verify_stable_audit


def router(settings: Settings, repository: GraphRepository) -> APIRouter:
    api = APIRouter()

    @api.get("/api/audit/verify", response_model=AuditVerifyResponse)
    def verify(
        request: Request,
        from_sequence: int = Query(default=1, ge=1),
        to_sequence: int | None = Query(default=None, ge=1),
    ):
        actor = authenticate(request, settings)
        require_role(actor, "admin")
        state, result, checks, limitations = verify_stable_audit(
            settings, repository, actor.tenant_id
        )
        head = state[0]
        unstable = UNSTABLE_SNAPSHOT in limitations
        if not unstable and (
            (head and from_sequence > head) or (to_sequence is not None and to_sequence > head)
        ):
            raise HTTPException(400)
        if to_sequence is not None and to_sequence < from_sequence:
            raise HTTPException(400)
        upper = 0 if unstable else (to_sequence if to_sequence is not None else head)
        selected = [
            AuditCheck.model_validate(check)
            for check in checks
            if from_sequence <= check["sequence"] <= upper
        ]
        return AuditVerifyResponse(
            request_id=request.state.request_id,
            checked_range=CheckedRange(
                from_sequence=from_sequence if upper else 0, to_sequence=upper
            ),
            chain_result=result,
            checks=selected,
            checkpoint=Checkpoint(available=False, trusted=False, sequence=None),
            limitations=limitations,
        )

    return api
