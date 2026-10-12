"""Initialize a configured empty tenant graph for the local demo.

This command never resets, deletes, or overwrites an existing graph.
"""

import argparse
from datetime import UTC, datetime

from falkordb import FalkorDB

from app.config import Settings


def initialize(settings: Settings, tenant_id: str) -> str:
    graph_name = settings.tenant_graphs.get(tenant_id)
    if graph_name is None:
        raise ValueError("tenant is not configured")
    client = FalkorDB(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        password=settings.falkordb_password.get_secret_value()
        if settings.falkordb_password
        else None,
        ssl=settings.falkordb_tls,
        socket_connect_timeout=settings.falkordb_socket_timeout_seconds,
        socket_timeout=settings.falkordb_socket_timeout_seconds,
    )
    try:
        if graph_name in client.list_graphs():
            raise ValueError("configured graph already exists; initialization refused")
        graph = client.select_graph(graph_name)
        now = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        graph.query(
            "CREATE (:GraphState {id:'graph-state',tenant_id:$tenant,revision:0,"
            "audit_sequence:0,ontology_version:'v1',policy_version:'v1',"
            "access_label:'PUBLIC_DEMO',acl_principals_json:'[]',"
            "created_at:$now,updated_at:$now})",
            {"tenant": tenant_id, "now": now},
        )
        for label in (
            "SourceRecord",
            "SourceVersion",
            "OperationRun",
            "AuditEvent",
            "Promise",
            "PromiseVersion",
        ):
            graph.query(f"CREATE INDEX FOR (n:{label}) ON (n.id)")
        graph.query("CREATE INDEX FOR (a:AuditEvent) ON (a.sequence)")
        return graph_name
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args()
    print(f"Initialized configured graph {initialize(Settings(), args.tenant)}")


if __name__ == "__main__":
    main()
