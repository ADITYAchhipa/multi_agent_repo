"""Tenant-scoped read boundary for the contract's promise projections."""

from redis.exceptions import RedisError

from app.graph.connection import GraphConnection, GraphUnavailable
from app.graph.queries import promises, sources


class GraphRepository:
    def __init__(self, connection: GraphConnection):
        self.connection = connection

    def _read(self, tenant_id: str, query: str, params: dict):
        graph = self.connection.graph_for_tenant(tenant_id)
        try:
            return graph.ro_query(
                query,
                params=params,
                timeout=self.connection.settings.falkordb_query_timeout_ms,
            ).result_set
        except (RedisError, OSError) as exc:
            raise GraphUnavailable("graph query failed") from exc

    def list_promises(
        self,
        tenant_id: str,
        *,
        after: str = "",
        status: str = "",
        customer: str = "",
        deadline_from: str = "",
        deadline_to: str = "",
        limit: int = 26,
    ):
        return self._read(
            tenant_id,
            promises.LIST,
            {
                "tenant": tenant_id,
                "after": after,
                "status": status,
                "customer": customer,
                "deadline_from": deadline_from,
                "deadline_to": deadline_to,
                "limit": limit,
            },
        )

    def promise_detail(self, tenant_id: str, promise_id: str, version_id: str | None = None):
        rows = self._read(
            tenant_id,
            promises.DETAIL,
            {"tenant": tenant_id, "id": promise_id, "version": version_id or ""},
        )
        return rows[0] if rows else None

    def _pages(self, tenant_id: str, query: str, params: dict):
        # Stable tie-breakers preserve duplicate rows for validation, rather than skipping them.
        offset = 0
        while True:
            rows = self._read(tenant_id, query, {**params, "offset": offset, "limit": 100})
            yield from rows
            if len(rows) < 100:
                return
            offset += len(rows)

    def promise_versions(self, tenant_id: str, promise_id: str):
        return self._pages(tenant_id, promises.VERSIONS, {"tenant": tenant_id, "id": promise_id})

    def history_state(self, tenant_id: str, promise_id: str):
        rows = self._read(
            tenant_id, promises.HISTORY_STATE, {"tenant": tenant_id, "id": promise_id}
        )
        return rows[0] if rows else None

    def history_links(self, tenant_id: str, promise_id: str, version_id: str):
        return self._read(
            tenant_id,
            promises.HISTORY_LINKS,
            {"tenant": tenant_id, "id": promise_id, "version": version_id},
        )

    def review_state(self, tenant_id: str, promise_id: str):
        rows = self._read(tenant_id, promises.REVIEW_STATE, {"tenant": tenant_id, "id": promise_id})
        return rows[0] if rows else None

    def review_evidence(self, tenant_id: str, evidence_id: str):
        rows = self._read(
            tenant_id, promises.REVIEW_EVIDENCE, {"tenant": tenant_id, "id": evidence_id}
        )
        return rows[0] if rows else None

    def review_ledger(self, tenant_id: str, actor_id: str, operation_id: str):
        rows = self._read(
            tenant_id,
            promises.REVIEW_LEDGER,
            {"tenant": tenant_id, "actor": actor_id, "operation": operation_id},
        )
        return rows[0] if rows else None

    def source_version(self, tenant_id: str, source_id: str, version_id: str):
        rows = self._read(
            tenant_id,
            promises.SOURCE_VERSION,
            {"tenant": tenant_id, "source": source_id, "version": version_id},
        )
        return rows[0] if rows else None

    def graph_revision(self, tenant_id: str) -> int:
        rows = self._read(tenant_id, promises.GRAPH_REVISION, {"tenant": tenant_id})
        if not rows or not isinstance(rows[0][0], int):
            raise GraphUnavailable("graph state is unavailable")
        return rows[0][0]

    def related_issues(self, tenant_id: str, version_id: str) -> list[str]:
        return [
            row[0]
            for row in self._read(
                tenant_id,
                promises.RELATED_ISSUES,
                {"tenant": tenant_id, "version": version_id},
            )
        ]

    def milestones(self, tenant_id: str, version_id: str) -> list[str]:
        return [
            row[0]
            for row in self._read(
                tenant_id,
                promises.MILESTONES,
                {"tenant": tenant_id, "version": version_id},
            )
        ]

    def source_detail(self, tenant_id: str, source_id: str, admin: bool = False):
        # Preserve the full-history response contract while bounding each DB query.
        # Retry a read across concurrent writes, never return a mixed snapshot.
        for _ in range(3):
            revision = self.graph_revision(tenant_id)
            rows = list(
                self._pages(
                    tenant_id,
                    sources.SOURCE_DETAIL,
                    {"tenant": tenant_id, "source": source_id, "admin": admin},
                )
            )
            if revision == self.graph_revision(tenant_id):
                return rows
        raise GraphUnavailable("source history changed during read")

    def operation(self, tenant_id: str, actor_id: str, operation_id: str, admin: bool):
        rows = self._read(
            tenant_id,
            sources.OPERATION,
            {"tenant": tenant_id, "actor": actor_id, "operation": operation_id, "admin": admin},
        )
        return rows[0] if rows else None

    def source_chunks(
        self, tenant_id: str, source_id: str, version_id: str, chunk_id: str | None, admin: bool
    ):
        return self._read(
            tenant_id,
            sources.SOURCE_CHUNKS,
            {
                "tenant": tenant_id,
                "source": source_id,
                "version": version_id,
                "chunk": chunk_id or "",
                "admin": admin,
            },
        )

    def audit_boundary(self, tenant_id: str):
        state = self._read(tenant_id, sources.AUDIT_STATE, {"tenant": tenant_id})
        if not state or not isinstance(state[0][2], int):
            raise GraphUnavailable("graph audit state is unavailable")
        return state[0]

    def audit_chain(self, tenant_id: str):
        state = self.audit_boundary(tenant_id)
        events = self._pages(tenant_id, sources.AUDIT_EVENTS, {"tenant": tenant_id})
        return state, events
