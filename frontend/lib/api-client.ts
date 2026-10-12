/**
 * PromiseOps + PromiseSeal Typed API Client
 * Centralizes base URL, correlation IDs, error normalization, and DEMO/LIVE mode.
 */

import {
  PromiseSummary,
  PromiseDetailResponse,
  ReviewRequest,
  ReviewResponse,
  Verification,
  ScenarioResult,
  ActionProposalDTO,
  KnowledgeHealthResponse,
  ConnectorSummary,
  GraphNode,
  GraphEdge,
  GraphPath,
  ApiErrorEnvelope,
  ReceiptEnvelope,
  SessionInfo,
} from "@/types/api";
import {
  SEED_PROMISES,
  SEED_PROMISE_DETAIL,
  SEED_SCENARIOS,
  SEED_ACTIONS,
  SEED_KNOWLEDGE,
  SEED_CONNECTORS,
  SEED_GRAPH_NODES,
  SEED_GRAPH_EDGES,
} from "./fixtures/seed-data";

export class ApiError extends Error {
  code: string;
  requestId: string;
  details?: Array<{ field?: string; reason: string }>;
  status: number;

  constructor(
    code: string,
    message: string,
    requestId: string,
    status = 400,
    details?: Array<{ field?: string; reason: string }>
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.requestId = requestId;
    this.status = status;
    this.details = details;
  }
}

// In-memory demo state stores to simulate stateful mutations during user interaction
let demoPromises = [...SEED_PROMISES];
let demoPromiseDetail = { ...SEED_PROMISE_DETAIL };
let demoScenarios = [...SEED_SCENARIOS];
let demoActions = [...SEED_ACTIONS];
let demoKnowledge = { ...SEED_KNOWLEDGE };

export class ApiClient {
  private baseUrl: string;
  private mode: "DEMO" | "LIVE";
  private currentActor: {
    id: string;
    name: string;
    roles: Array<"viewer" | "reviewer" | "executor" | "admin">;
  };

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || "/api";
    // Default to DEMO mode unless NEXT_PUBLIC_APP_MODE is explicitly LIVE
    this.mode =
      (process.env.NEXT_PUBLIC_APP_MODE as "DEMO" | "LIVE") || "DEMO";
    this.currentActor = {
      id: "actor-reviewer",
      name: "Aria Chen (Delivery Lead / Reviewer)",
      roles: ["reviewer", "viewer"],
    };
  }

  public getMode(): "DEMO" | "LIVE" {
    return this.mode;
  }

  public setMode(mode: "DEMO" | "LIVE") {
    this.mode = mode;
  }

  public getActor() {
    return this.currentActor;
  }

  public setActor(actorId: "reviewer" | "executor" | "admin" | "viewer") {
    if (actorId === "reviewer") {
      this.currentActor = {
        id: "actor-reviewer",
        name: "Aria Chen (Delivery Lead / Reviewer)",
        roles: ["reviewer", "viewer"],
      };
    } else if (actorId === "executor") {
      this.currentActor = {
        id: "actor-executor",
        name: "Casey Rao (Operations Executor)",
        roles: ["executor", "viewer"],
      };
    } else if (actorId === "admin") {
      this.currentActor = {
        id: "actor-admin",
        name: "System Administrator",
        roles: ["admin", "reviewer", "executor", "viewer"],
      };
    } else {
      this.currentActor = {
        id: "actor-viewer",
        name: "Read-only Stakeholder",
        roles: ["viewer"],
      };
    }
  }

  public resetDemoData() {
    demoPromises = JSON.parse(JSON.stringify(SEED_PROMISES));
    demoPromiseDetail = JSON.parse(JSON.stringify(SEED_PROMISE_DETAIL));
    demoScenarios = JSON.parse(JSON.stringify(SEED_SCENARIOS));
    demoActions = JSON.parse(JSON.stringify(SEED_ACTIONS));
    demoKnowledge = JSON.parse(JSON.stringify(SEED_KNOWLEDGE));
  }

  private generateRequestId(): string {
    return `req-${Math.random().toString(36).substring(2, 10)}`;
  }

  private generateIdempotencyKey(): string {
    return `idem-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const requestId = this.generateRequestId();
    const headers = new Headers(options.headers);
    headers.set("Accept", "application/json");
    headers.set("X-Request-ID", requestId);

    if (
      options.method &&
      ["POST", "PUT", "PATCH", "DELETE"].includes(options.method.toUpperCase())
    ) {
      if (!headers.has("Idempotency-Key")) {
        headers.set("Idempotency-Key", this.generateIdempotencyKey());
      }
      if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
      }
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorData = data as ApiErrorEnvelope | null;
        if (errorData?.error) {
          throw new ApiError(
            errorData.error.code,
            errorData.error.message,
            errorData.error.request_id || requestId,
            response.status,
            errorData.error.details
          );
        }
        throw new ApiError(
          "HTTP_ERROR",
          `Server returned status ${response.status}`,
          requestId,
          response.status
        );
      }

      return data as T;
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        throw err;
      }
      const message =
        err instanceof Error ? err.message : "An unexpected network error occurred";
      throw new ApiError("NETWORK_ERROR", message, requestId, 503);
    }
  }

  // --- Session & Health ---

  async getSession(): Promise<SessionInfo> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-session-demo",
        actor: this.currentActor,
        tenant_id: "tenant-demo",
        mode: "DEMO",
        expires_at: new Date(Date.now() + 3600000).toISOString(),
      };
    }
    return this.request<SessionInfo>("/session");
  }

  async getHealth(): Promise<{
    request_id: string;
    status: "OK" | "DEGRADED";
    services: { api: string; graph: string };
    checked_at: string;
  }> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-health-demo",
        status: "OK",
        services: { api: "healthy", graph: "falkordb_mock_active" },
        checked_at: new Date().toISOString(),
      };
    }
    return this.request("/health");
  }

  async getKnowledgeHealth(): Promise<KnowledgeHealthResponse> {
    if (this.mode === "DEMO") {
      return JSON.parse(JSON.stringify(demoKnowledge));
    }
    return this.request<KnowledgeHealthResponse>("/health/knowledge");
  }

  async getConnectors(): Promise<{
    request_id: string;
    items: ConnectorSummary[];
  }> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-connectors-demo",
        items: SEED_CONNECTORS,
      };
    }
    return this.request("/connectors");
  }

  // --- Promises & Verification ---

  async getPromises(params?: {
    status?: string;
    customer_id?: string;
    risk?: string;
  }): Promise<{ request_id: string; items: PromiseSummary[] }> {
    if (this.mode === "DEMO") {
      let filtered = [...demoPromises];
      if (params?.status && params.status !== "ALL") {
        filtered = filtered.filter((p) => p.current_state === params.status);
      }
      if (params?.customer_id) {
        filtered = filtered.filter((p) => p.customer_id === params.customer_id);
      }
      return {
        request_id: "req-promises-demo",
        items: filtered,
      };
    }

    const searchParams = new URLSearchParams();
    if (params?.status && params.status !== "ALL") {
      searchParams.set("status", params.status);
    }
    if (params?.customer_id) {
      searchParams.set("customer_id", params.customer_id);
    }
    if (params?.risk) {
      searchParams.set("risk", params.risk);
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request(`/promises${query}`);
  }

  async getPromiseDetail(
    promiseId: string,
    versionId?: string
  ): Promise<PromiseDetailResponse> {
    if (this.mode === "DEMO") {
      if (promiseId === "promise-loyalty") {
        return JSON.parse(JSON.stringify(demoPromiseDetail));
      }
      const found = demoPromises.find((p) => p.id === promiseId);
      if (!found) {
        throw new ApiError(
          "PROMISE_NOT_FOUND",
          `Promise with ID ${promiseId} was not found.`,
          this.generateRequestId(),
          404
        );
      }
      // Return synthetic detail for other items
      return {
        request_id: "req-detail-demo",
        promise: found,
        receipt: demoPromiseDetail.receipt,
        versions: [
          {
            receipt_id: found.current_version_id,
            version: found.revision,
            status_at_issuance: found.current_state,
            standing: found.receipt_standing,
            created_at: "2026-10-12T09:15:00.000Z",
          },
        ],
        evidence: demoPromiseDetail.evidence,
        scope_assessment: {
          status: found.scope_status,
          claim: found.deliverable,
          clause_ids: ["clause-c1"],
          evidence_refs: [],
          conflict_ids: [],
          missing_evidence: [],
          assessment_kind: "DETERMINISTIC_RULE",
        },
        calculations: demoPromiseDetail.calculations,
        related_issue_ids: demoPromiseDetail.related_issue_ids,
        related_issues_details: demoPromiseDetail.related_issues_details,
        milestone_ids: demoPromiseDetail.milestone_ids,
        milestones_details: demoPromiseDetail.milestones_details,
        conflicts: [],
        graph_paths: demoPromiseDetail.graph_paths,
      };
    }

    const query = versionId ? `?version_id=${versionId}` : "";
    return this.request<PromiseDetailResponse>(`/promises/${promiseId}${query}`);
  }

  async verifyPromiseReceipt(
    promiseId: string,
    versionId?: string
  ): Promise<{
    request_id: string;
    receipt_id: string;
    verification: Verification;
  }> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-verify-demo",
        receipt_id: versionId || demoPromiseDetail.receipt.payload.receipt_id,
        verification: {
          integrity: "VALID",
          standing: demoPromiseDetail.receipt.payload.confirmation
            ? "ACTIVE"
            : "ACTIVE",
          checked_at: new Date().toISOString(),
          checks: [
            {
              code: "CANONICAL_PAYLOAD_DIGEST",
              result: "PASS",
              reason:
                "Computed SHA-256 matches payload_sha256 exactly (e4f3a748...)",
            },
            {
              code: "ED25519_SERVICE_SIGNATURE",
              result: "PASS",
              reason:
                "Signature verified against trusted key 'key-demo-2026' in local trust registry",
            },
            {
              code: "SOURCE_ARTIFACT_HASHES",
              result: "PASS",
              reason:
                "Exact transcript quote matched in src-meeting-1 at cue 00:00:12",
            },
            {
              code: "PREDECESSOR_CHAIN_SEQUENCE",
              result: "PASS",
              reason: "Contiguous version sequence v1 with null genesis predecessor",
            },
          ],
          source_results: [
            { source_id: "src-meeting-1", result: "MATCH" },
            { source_id: "src-contract", result: "MATCH" },
          ],
          key_trust: "TRUSTED",
          eligible_for_action:
            demoPromiseDetail.promise.current_state === "CONFIRMED",
        },
      };
    }

    const query = versionId ? `?version_id=${versionId}` : "";
    return this.request(`/promises/${promiseId}/verify${query}`);
  }

  // Non-persisting verification test for tampered copies
  async verifyCustomReceipt(receipt: ReceiptEnvelope): Promise<{
    request_id: string;
    verification: Verification;
  }> {
    if (this.mode === "DEMO") {
      // Simulate real verification check: if deliverable or text changed, digest mismatch
      const originalExcerpt =
        "We can deliver the loyalty integration by Friday at no extra charge.";
      const isTampered =
        receipt.payload.deliverable !==
          "Deliver loyalty integration by Friday at no extra charge" ||
        receipt.payload.statement.exact_excerpt !== originalExcerpt;

      if (isTampered) {
        return {
          request_id: "req-verify-tamper-demo",
          verification: {
            integrity: "INVALID",
            standing: "ACTIVE",
            checked_at: new Date().toISOString(),
            checks: [
              {
                code: "CANONICAL_PAYLOAD_DIGEST",
                result: "FAIL",
                field: "payload.deliverable",
                reason:
                  "PAYLOAD_DIGEST_MISMATCH: Computed canonical SHA-256 does not match envelope payload_sha256 header. Content modified after signing.",
              },
              {
                code: "ED25519_SERVICE_SIGNATURE",
                result: "FAIL",
                reason:
                  "Signature verification rejected: cryptographic signature does not attest altered payload bytes.",
              },
            ],
            source_results: [
              {
                source_id: "src-meeting-1",
                result: "MISMATCH",
                details: "Payload quote does not match retained source bytes.",
              },
            ],
            key_trust: "TRUSTED",
            eligible_for_action: false,
          },
        };
      }

      return {
        request_id: "req-verify-custom-demo",
        verification: {
          integrity: "VALID",
          standing: "ACTIVE",
          checked_at: new Date().toISOString(),
          checks: [
            {
              code: "CANONICAL_PAYLOAD_DIGEST",
              result: "PASS",
              reason: "Payload SHA-256 matches canonical digest",
            },
            {
              code: "ED25519_SERVICE_SIGNATURE",
              result: "PASS",
              reason: "Valid Ed25519 signature from key-demo-2026",
            },
          ],
          source_results: [{ source_id: "src-meeting-1", result: "MATCH" }],
          key_trust: "TRUSTED",
          eligible_for_action: false,
        },
      };
    }

    return this.request("/receipts/verify", {
      method: "POST",
      body: JSON.stringify({ receipt }),
    });
  }

  async reviewPromise(
    promiseId: string,
    payload: ReviewRequest
  ): Promise<ReviewResponse> {
    if (!this.currentActor.roles.includes("reviewer")) {
      throw new ApiError(
        "ROLE_FORBIDDEN",
        `Actor '${this.currentActor.name}' does not hold 'reviewer' capability required for promise review decisions.`,
        this.generateRequestId(),
        403
      );
    }

    if (this.mode === "DEMO") {
      const targetPromise = demoPromises.find((p) => p.id === promiseId);
      if (!targetPromise) {
        throw new ApiError(
          "PROMISE_NOT_FOUND",
          `Promise with ID ${promiseId} was not found.`,
          this.generateRequestId(),
          404
        );
      }

      let newState = targetPromise.current_state;
      if (payload.decision === "CONFIRM") {
        newState = "CONFIRMED";
      } else if (payload.decision === "DISPUTE") {
        newState = "DISPUTED";
      } else if (payload.decision === "REJECT") {
        newState = "REJECTED";
      } else if (payload.decision === "FULFILL") {
        newState = "FULFILLED";
      } else if (payload.decision === "REVISE") {
        newState = "NEEDS_REVIEW";
      }

      targetPromise.current_state = newState;
      targetPromise.revision += 1;
      const newVersionId = `receipt-loyalty-v${targetPromise.revision}`;
      targetPromise.current_version_id = newVersionId;

      demoPromiseDetail.promise = { ...targetPromise };
      demoPromiseDetail.versions.unshift({
        receipt_id: newVersionId,
        version: targetPromise.revision,
        status_at_issuance: newState,
        standing: "ACTIVE",
        created_at: new Date().toISOString(),
      });

      if (newState === "CONFIRMED") {
        demoPromiseDetail.receipt.payload.confirmation = {
          confirmed_by: this.currentActor.id,
          confirmed_at: new Date().toISOString(),
          confirmation_event_id: `evt-conf-${Date.now()}`,
          authority_scope: "INTERNAL_OPERATIONS_ONLY",
          reviewed_content_hash: "hash-reviewed-content-v2",
        };
      }

      return {
        request_id: "req-review-demo",
        promise: targetPromise,
        receipt: demoPromiseDetail.receipt,
        audit_event_id: `audit-evt-${Date.now()}`,
      };
    }

    return this.request<ReviewResponse>(`/promises/${promiseId}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // --- Simulations ---

  async getSimulations(): Promise<{
    request_id: string;
    results: ScenarioResult[];
  }> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-sim-demo",
        results: demoScenarios,
      };
    }
    return this.request("/simulations");
  }

  async getSimulation(scenarioId: string): Promise<{
    request_id: string;
    scenario: ScenarioResult;
  }> {
    if (this.mode === "DEMO") {
      const found = demoScenarios.find((s) => s.id === scenarioId);
      if (!found) {
        throw new ApiError(
          "SCENARIO_NOT_FOUND",
          `Scenario ${scenarioId} not found`,
          this.generateRequestId(),
          404
        );
      }
      return {
        request_id: "req-sim-detail-demo",
        scenario: found,
      };
    }
    return this.request(`/simulations/${scenarioId}`);
  }

  // --- Actions & Approvals ---

  async getActions(params?: {
    status?: string;
  }): Promise<{ request_id: string; items: ActionProposalDTO[] }> {
    if (this.mode === "DEMO") {
      let filtered = [...demoActions];
      if (params?.status && params.status !== "ALL") {
        filtered = filtered.filter((a) => a.status === params.status);
      }
      return {
        request_id: "req-actions-demo",
        items: filtered,
      };
    }
    const query =
      params?.status && params.status !== "ALL"
        ? `?status=${params.status}`
        : "";
    return this.request(`/actions${query}`);
  }

  async getAction(actionId: string): Promise<{
    request_id: string;
    action: ActionProposalDTO;
  }> {
    if (this.mode === "DEMO") {
      const found = demoActions.find((a) => a.id === actionId);
      if (!found) {
        throw new ApiError(
          "ACTION_NOT_FOUND",
          `Action ${actionId} not found`,
          this.generateRequestId(),
          404
        );
      }
      return {
        request_id: "req-action-detail-demo",
        action: found,
      };
    }
    return this.request(`/actions/${actionId}`);
  }

  async approveAction(
    actionId: string,
    reason: string
  ): Promise<{
    request_id: string;
    action: ActionProposalDTO;
    audit_event_id: string;
  }> {
    if (!this.currentActor.roles.includes("reviewer")) {
      throw new ApiError(
        "ROLE_FORBIDDEN",
        `Approval denied: Actor '${this.currentActor.name}' lacks 'reviewer' role.`,
        this.generateRequestId(),
        403
      );
    }

    if (this.mode === "DEMO") {
      const action = demoActions.find((a) => a.id === actionId);
      if (!action) {
        throw new ApiError(
          "ACTION_NOT_FOUND",
          `Action ${actionId} not found`,
          this.generateRequestId(),
          404
        );
      }

      action.status = "APPROVED";
      action.approval = {
        approved_by: this.currentActor.id,
        approved_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
        reason: reason || "Approved within delivery policy capacity ceiling ($750)",
        approval_id: `appr-${Date.now()}`,
      };

      return {
        request_id: "req-approve-demo",
        action,
        audit_event_id: `audit-evt-${Date.now()}`,
      };
    }

    return this.request(`/actions/${actionId}/approve`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  async rejectAction(
    actionId: string,
    reason: string
  ): Promise<{
    request_id: string;
    action: ActionProposalDTO;
    audit_event_id: string;
  }> {
    if (!this.currentActor.roles.includes("reviewer")) {
      throw new ApiError(
        "ROLE_FORBIDDEN",
        `Rejection denied: Actor '${this.currentActor.name}' lacks 'reviewer' role.`,
        this.generateRequestId(),
        403
      );
    }

    if (this.mode === "DEMO") {
      const action = demoActions.find((a) => a.id === actionId);
      if (!action) {
        throw new ApiError(
          "ACTION_NOT_FOUND",
          `Action ${actionId} not found`,
          this.generateRequestId(),
          404
        );
      }
      action.status = "CANCELLED";
      return {
        request_id: "req-reject-demo",
        action,
        audit_event_id: `audit-evt-${Date.now()}`,
      };
    }

    return this.request(`/actions/${actionId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  async executeAction(actionId: string): Promise<{
    request_id: string;
    action_id: string;
    status: "EXECUTING" | "SUCCEEDED";
    status_url: string;
  }> {
    if (!this.currentActor.roles.includes("executor")) {
      throw new ApiError(
        "ROLE_FORBIDDEN",
        `Execution denied: Actor '${this.currentActor.name}' lacks 'executor' role. Operations executor role is required to dispatch external/workload modifications.`,
        this.generateRequestId(),
        403
      );
    }

    if (this.mode === "DEMO") {
      const action = demoActions.find((a) => a.id === actionId);
      if (!action) {
        throw new ApiError(
          "ACTION_NOT_FOUND",
          `Action ${actionId} not found`,
          this.generateRequestId(),
          404
        );
      }

      if (action.status !== "APPROVED") {
        throw new ApiError(
          "ACTION_NOT_APPROVED",
          `Execution blocked by backend policy: Action '${actionId}' status is '${action.status}', must be 'APPROVED' before dispatch.`,
          this.generateRequestId(),
          409
        );
      }

      action.status = "SUCCEEDED";
      const now = new Date().toISOString();
      action.attempts.push({
        attempt_id: `att-${Date.now()}`,
        started_at: now,
        finished_at: now,
        status: "SUCCESS",
        http_status: 200,
      });

      action.external_response_reference =
        "mock-workload://ledger/record-ben-friday-09-14#id=slot-res-902";

      action.read_back = {
        expected: {
          resource_id: "person-ben",
          task_id: "jira-acme-101",
          hours: 5,
          slot_start: "2026-10-16T09:00:00.000Z",
          slot_end: "2026-10-16T14:00:00.000Z",
        },
        actual: {
          resource_id: "person-ben",
          task_id: "jira-acme-101",
          hours: 5,
          slot_start: "2026-10-16T09:00:00.000Z",
          slot_end: "2026-10-16T14:00:00.000Z",
        },
        mismatches: [],
        checked_at: now,
        verified: true,
      };

      return {
        request_id: "req-execute-demo",
        action_id: actionId,
        status: "SUCCEEDED",
        status_url: `/api/actions/${actionId}`,
      };
    }

    return this.request(`/actions/${actionId}/execute`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  // --- Graph ---

  async getGraph(
    entityId?: string,
    depth = 1
  ): Promise<{
    request_id: string;
    graph_revision: number;
    nodes: GraphNode[];
    edges: GraphEdge[];
    paths: GraphPath[];
    truncated: boolean;
  }> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-graph-demo",
        graph_revision: 12,
        nodes: SEED_GRAPH_NODES,
        edges: SEED_GRAPH_EDGES,
        paths: demoPromiseDetail.graph_paths,
        truncated: false,
      };
    }
    const query = entityId ? `/${entityId}?depth=${depth}` : `?depth=${depth}`;
    return this.request(`/graph${query}`);
  }
}

// Export singleton instance for client-side queries
export const apiClient = new ApiClient();
