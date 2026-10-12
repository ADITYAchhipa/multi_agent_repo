from datetime import date
from typing import Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, model_validator

from app.models.api import EvidenceRef
from app.models.common import Digest, Id, Quantity, SafeInt, StrictModel, Text, Timestamp
from app.promise_seal.canonicalize import canonical_bytes, strict_json

BusinessState = Literal[
    "PROPOSED", "NEEDS_REVIEW", "CONFIRMED", "DISPUTED", "SUPERSEDED", "FULFILLED", "REJECTED"
]


class Statement(StrictModel):
    exact_excerpt: Text
    interpretation: Text


class Deadline(StrictModel):
    original_text: Text | None
    precision: Literal["UNKNOWN", "DATE", "INSTANT"]
    local_date: str | None
    instant: Timestamp | None
    timezone: str | None
    resolution_basis: Text | None

    @model_validator(mode="after")
    def precision_matches(self) -> Self:
        if self.local_date is not None:
            parsed = date.fromisoformat(self.local_date)
            if parsed.isoformat() != self.local_date:
                raise ValueError("date must use YYYY-MM-DD")
        if self.timezone is not None:
            try:
                ZoneInfo(self.timezone)
            except (ZoneInfoNotFoundError, ValueError) as exc:
                raise ValueError("unknown timezone") from exc
        if self.precision == "UNKNOWN" and (
            self.local_date is not None or self.instant is not None
        ):
            raise ValueError("unknown deadline cannot imply a date")
        if self.precision == "DATE" and (self.local_date is None or self.instant is not None):
            raise ValueError("DATE requires a date and no implied instant")
        if self.precision == "INSTANT" and (self.instant is None or self.timezone is None):
            raise ValueError("INSTANT requires instant and timezone")
        return self


class PriceCondition(StrictModel):
    kind: Literal["NO_ADDITIONAL_CHARGE", "CHANGE_ORDER_REQUIRED", "PRICED", "UNKNOWN"]
    original_text: Text | None


class CommercialValue(StrictModel):
    amount: Quantity
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    evidence_ref_id: Id


class EntityRef(StrictModel):
    entity_id: Id
    source_version_id: Id
    evidence_ref_ids: list[Id] = Field(min_length=1, max_length=200)


class Confirmation(StrictModel):
    confirmed_by: Id
    confirmed_at: Timestamp
    confirmation_event_id: Id
    authority_scope: Text
    reviewed_content_hash: Digest


class ReceiptPayload(StrictModel):
    protocol_version: Literal["promiseseal-v1"]
    receipt_id: Id
    promise_id: Id
    tenant_id: Id
    version: SafeInt = Field(ge=1)
    issuer_id: Id
    created_at: Timestamp
    issued_at: Timestamp | None
    statement: Statement
    deliverable: Text
    customer_id: Id | None
    project_id: Id | None
    deadline: Deadline
    price_condition: PriceCondition
    commercial_value: CommercialValue | None
    commitment_class: Literal["explicit", "conditional", "suggestion", "hypothetical", "ambiguous"]
    source_refs: list[EvidenceRef] = Field(min_length=1, max_length=200)
    contract_refs: list[EntityRef] = Field(max_length=200)
    jira_refs: list[EntityRef] = Field(max_length=200)
    workload_refs: list[EntityRef] = Field(max_length=200)
    status_at_issuance: BusinessState
    confirmation: Confirmation | None
    review_event_id: Id | None
    previous_receipt_version_id: Id | None
    previous_payload_sha256: Digest | None
    canonicalization: Literal["promiseops-json-v1"]
    signature_algorithm: Literal["Ed25519"]
    signing_key_id: Id | None

    @model_validator(mode="after")
    def coherent_payload(self) -> Self:
        if (self.issued_at is None) != (self.signing_key_id is None):
            raise ValueError("issuance time and signing key must be present together")
        if self.signing_key_id is None and self.status_at_issuance != "PROPOSED":
            raise ValueError("only proposed receipts may be unsigned")
        if self.status_at_issuance == "SUPERSEDED":
            raise ValueError("SUPERSEDED is effective standing, not an issuance state")
        parents = (self.previous_receipt_version_id, self.previous_payload_sha256)
        if self.version == 1:
            if any(v is not None for v in parents) or self.review_event_id is not None:
                raise ValueError("initial extraction cannot have predecessor or review event")
            if self.status_at_issuance != "PROPOSED":
                raise ValueError("initial extraction must be PROPOSED")
        elif any(v is None for v in parents) or self.review_event_id is None:
            raise ValueError("successor requires predecessor and review event")
        if self.status_at_issuance in {"CONFIRMED", "FULFILLED"}:
            if self.confirmation is None:
                raise ValueError("confirmed content requires confirmation metadata")
        elif self.confirmation is not None:
            raise ValueError("confirmation must be cleared for this state")
        if not any(ref.quote == self.statement.exact_excerpt for ref in self.source_refs):
            raise ValueError("statement excerpt must equal a source quote")
        evidence_ids = [ref.evidence_ref_id for ref in self.source_refs]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("duplicate evidence reference")
        if self.commercial_value and self.commercial_value.evidence_ref_id not in evidence_ids:
            raise ValueError("commercial value requires included evidence")
        for refs in (self.contract_refs, self.jira_refs, self.workload_refs):
            for ref in refs:
                if not set(ref.evidence_ref_ids).issubset(evidence_ids):
                    raise ValueError("entity references require included evidence")
        canonical_bytes(self.model_dump(mode="json"))
        return self


class ReceiptEnvelope(StrictModel):
    payload: ReceiptPayload
    payload_sha256: Digest
    signature_base64url: str | None = Field(pattern=r"^[A-Za-z0-9_-]{86}$")

    @model_validator(mode="after")
    def signing_presence(self) -> Self:
        if (self.signature_base64url is None) != (self.payload.signing_key_id is None):
            raise ValueError("signature and signed payload metadata must be present together")
        return self


def parse_receipt(raw: bytes) -> ReceiptEnvelope:
    return ReceiptEnvelope.model_validate(strict_json(raw))
