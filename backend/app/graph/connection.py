from threading import Lock

from falkordb import FalkorDB
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from app.config import Settings


class GraphUnavailable(Exception):
    """Safe application error; never expose driver exception text."""


class GraphConnection:
    """Sync official client, used only from FastAPI threadpool routes.

    Lazy construction permits process liveness while the required graph is offline.
    No graph mutation is enabled before the S01 compatibility gate.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: FalkorDB | None = None
        self._lock = Lock()

    def _connect(self) -> FalkorDB:
        if self._client is None:
            self._client = FalkorDB(
                host=self.settings.falkordb_host,
                port=self.settings.falkordb_port,
                password=(
                    self.settings.falkordb_password.get_secret_value()
                    if self.settings.falkordb_password
                    else None
                ),
                ssl=self.settings.falkordb_tls,
                ssl_check_hostname=True,
                socket_connect_timeout=self.settings.falkordb_socket_timeout_seconds,
                socket_timeout=self.settings.falkordb_socket_timeout_seconds,
                retry=Retry(NoBackoff(), 0),
            )
        return self._client

    def graph_for_tenant(self, tenant_id: str):
        graph_name = self.settings.tenant_graphs.get(tenant_id)
        if graph_name is None:
            raise GraphUnavailable("tenant graph is not configured")
        with self._lock:
            try:
                client = self._connect()
                if graph_name not in client.list_graphs():
                    raise GraphUnavailable("tenant graph is unavailable")
                return client.select_graph(graph_name)
            except (RedisError, OSError) as exc:
                raise GraphUnavailable("tenant graph is unavailable") from exc

    def ready(self) -> bool:
        with self._lock:
            try:
                self._connect()
                # A typo/missing graph must not silently create application state.
                if self.settings.falkordb_graph not in self._client.list_graphs():
                    return False
                rows = (
                    self._client.select_graph(self.settings.falkordb_graph)
                    .ro_query(
                        "RETURN $probe",
                        params={"probe": 1},
                        timeout=self.settings.falkordb_query_timeout_ms,
                    )
                    .result_set
                )
                return rows == [[1]]
            except RedisError, OSError:
                return False

    def close(self) -> None:
        with self._lock:
            if self._client is not None:
                self._client.close()
                self._client = None
