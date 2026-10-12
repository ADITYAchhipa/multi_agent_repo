"""Tenant-scoped read boundary for the contract's promise projections."""

from redis.exceptions import RedisError

from app.graph.connection import GraphConnection, GraphUnavailable
from app.graph.queries import promises


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

    def promise_detail(self, tenant_id: str, promise_id: str):
        rows = self._read(tenant_id, promises.DETAIL, {"tenant": tenant_id, "id": promise_id})
        return rows[0] if rows else None

    def promise_versions(self, tenant_id: str, promise_id: str):
        return self._read(tenant_id, promises.VERSIONS, {"tenant": tenant_id, "id": promise_id})

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
