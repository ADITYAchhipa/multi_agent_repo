/**
 * PromiseOps + PromiseSeal Typed API Client
 * Centralizes base URL, correlation IDs, error normalization, timeouts, and DEMO/LIVE mode.
 * Conforms strictly to docs/API_CONTRACTS.md and docs/PROMISESEAL_PROTOCOL.md.
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
  ApiErrorEnvelope,
  ReceiptEnvelope,
  SessionInfo,
  ActionApprovalRequest,
  ActionRejectRequest,
  ActionExecuteRequest,
  ActionRequestApprovalRequest,
  ActionReconcileRequest,
  SimulationCreateRequest,
  ChatRequest,
  ChatResponse,
  GraphResponse,
  UploadAccepted,
  UploadNoChange,
  OperationResponse,
  SourceDetailResponse,
  AuditVerifyResponse,
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

  get isConflict(): boolean {
    return this.status === 409;
  }

  get isStaleApproval(): boolean {
    return this.code === "STALE_APPROVAL" || this.code === "IDEMPOTENCY_CONFLICT";
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isEndpointUnimplemented(): boolean {
    return this.status === 404;
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isUnavailable(): boolean {
    return this.status === 503;
  }

  get isTimeout(): boolean {
    return this.status === 504;
  }
}

// In-memory demo state stores to simulate stateful mutations during user interaction
let demoPromises = [...SEED_PROMISES];
let demoPromiseDetail = { ...SEED_PROMISE_DETAIL };
let demoScenarios = [...SEED_SCENARIOS];
let demoActions = [...SEED_ACTIONS];
let demoKnowledge = { ...SEED_KNOWLEDGE };

export type ModeChangeListener = (mode: "DEMO" | "LIVE") => void;

export const DEMO_CREDENTIALS: Record<string, string> = {
  admin: "admin-credential",
  reviewer: "reviewer-credential",
  executor: "executor-credential",
  viewer: "viewer-credential",
};

export class ApiClient {
  private baseUrl: string;
  private mode: "DEMO" | "LIVE";
  private currentActor: {
    id: string;
    name: string;
    roles: Array<"viewer" | "reviewer" | "executor" | "admin">;
  };
  private listeners: Set<ModeChangeListener> = new Set();

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
    this.listeners.forEach((listener) => {
      try {
        listener(mode);
      } catch {
        // Safe dispatch
      }
    });
  }

  public subscribe(listener: ModeChangeListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
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
      // Exclude session bootstrap from requiring Idempotency-Key per API_CONTRACTS.md §1
      const isSessionBootstrap =
        endpoint === "/session" && options.method.toUpperCase() === "POST";
      if (!isSessionBootstrap && !headers.has("Idempotency-Key")) {
        headers.set("Idempotency-Key", this.generateIdempotencyKey());
      }
      if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
      }
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    if (options.signal) {
      options.signal.addEventListener("abort", () => controller.abort());
    }

    try {
      const method = (options.method || "GET").toUpperCase();
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        method,
        headers,
        credentials: "include",
        signal: controller.signal,
      });

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
        const fallbackCode =
          response.status === 404
            ? "NOT_FOUND"
            : response.status === 401
            ? "UNAUTHORIZED"
            : response.status === 403
            ? "FORBIDDEN"
            : response.status === 409
            ? "CONFLICT"
            : response.status === 503
            ? "SERVICE_UNAVAILABLE"
            : "HTTP_ERROR";
        throw new ApiError(
          fallbackCode,
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
      if (err instanceof Error && (err.name === "AbortError" || controller.signal.aborted)) {
        throw new ApiError(
          "TIMEOUT_ERROR",
          "Request timed out after 10000ms",
          requestId,
          504
        );
      }
      const message =
        err instanceof Error ? err.message : "An unexpected network error occurred";
      throw new ApiError("NETWORK_ERROR", message, requestId, 503);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // --- Session & Health ---

  async getSession(): Promise<SessionInfo> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-session-demo",
        actor: {
          id: this.currentActor.id,
          name: this.currentActor.name,
          roles: [...this.currentActor.roles],
        },
        tenant_id: "tenant-demo",
        mode: "DEMO",
        expires_at: new Date(Date.now() + 3600000).toISOString(),
      };
    }
    return this.request<SessionInfo>("/session");
  }

  async bootstrapSession(credential?: string): Promise<SessionInfo> {
    if (this.mode === "DEMO") {
      if (credential) {
        if (credential.includes("admin")) this.setActor("admin");
        else if (credential.includes("executor")) this.setActor("executor");
        else if (credential.includes("viewer")) this.setActor("viewer");
        else if (credential.includes("reviewer")) this.setActor("reviewer");
      }
      return this.getSession();
    }
    const cred =
      credential ||
      DEMO_CREDENTIALS[this.currentActor.roles[0]] ||
      "reviewer-credential";
    return this.request<SessionInfo>("/session", {
      method: "POST",
      body: JSON.stringify({ credential: cred }),
    });
  }

  async logout(): Promise<{ request_id: string; logged_out: boolean }> {
    if (this.mode === "DEMO") {
      this.setActor("viewer");
      return {
        request_id: "req-logout-demo",
        logged_out: true,
      };
    }
    return this.request<{ request_id: string; logged_out: boolean }>("/session/logout", {
      method: "POST",
      body: JSON.stringify({}),
    });
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
        services: { api: "OK", graph: "OK" },
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
    next_cursor?: string | null;
  }> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-connectors-demo",
        items: SEED_CONNECTORS,
        next_cursor: null,
      };
    }
    return this.request("/connectors");
  }

  // --- Sources & Operations ---

  async uploadSource(params: {
    file: File | Blob;
    filename?: string;
    sourceType?: "TRANSCRIPT" | "NOTES" | "CONTRACT";
    accessLabel?: "PUBLIC_DEMO" | "INTERNAL" | "RESTRICTED";
    sourceKey?: string;
  }): Promise<UploadAccepted | UploadNoChange> {
    const {
      file,
      filename = (file as File).name || "notes.txt",
      sourceType = "NOTES",
      accessLabel = "PUBLIC_DEMO",
      sourceKey,
    } = params;

    if (this.mode === "DEMO") {
      const sourceId = `source-${Date.now()}`;
      const operationId = `operation-${Date.now()}`;
      return {
        request_id: this.generateRequestId(),
        operation_id: operationId,
        source_id: sourceId,
        status_url: `/api/operations/${operationId}`,
      };
    }

    const formData = new FormData();
    formData.append("file", file, filename);
    formData.append("source_type", sourceType);
    formData.append("access_label", accessLabel);
    if (sourceKey) {
      formData.append("source_key", sourceKey);
    }

    return this.request<UploadAccepted | UploadNoChange>("/sources/upload", {
      method: "POST",
      body: formData,
    });
  }

  async getSource(
    sourceId: string,
    versionId?: string,
    chunkId?: string
  ): Promise<SourceDetailResponse> {
    const encodedId = encodeURIComponent(sourceId);
    if (this.mode === "DEMO") {
      return {
        request_id: "req-source-demo",
        source: {
          id: sourceId,
          source_type: "NOTES",
          title: "demo-notes.txt",
          current_version_id: `${sourceId}-v1`,
          source_updated_at: new Date().toISOString(),
          ingested_at: new Date().toISOString(),
          content_hash: "hash-raw-demo",
          retention_state: "ACTIVE",
          parse_status: "SUCCESS",
          mode: "DEMO",
        },
        version: {
          id: `${sourceId}-v1`,
          source_hash: "hash-raw-demo",
          representation_hash: "hash-rep-demo",
          availability: "AVAILABLE",
        },
        snippets: demoPromiseDetail.evidence,
        versions: [
          {
            id: `${sourceId}-v1`,
            version: 1,
            source_updated_at: new Date().toISOString(),
            availability: "AVAILABLE",
          },
        ],
      };
    }

    const searchParams = new URLSearchParams();
    if (versionId) searchParams.set("version_id", versionId);
    if (chunkId) searchParams.set("chunk_id", chunkId);
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request<SourceDetailResponse>(`/sources/${encodedId}${query}`);
  }

  async getOperation(operationId: string): Promise<OperationResponse> {
    const encodedId = encodeURIComponent(operationId);
    if (this.mode === "DEMO") {
      return {
        request_id: "req-operation-demo",
        operation: {
          id: operationId,
          kind: "SOURCE_INGESTION",
          status: "COMPLETED",
          phase: "COMPLETED",
          created_at: new Date().toISOString(),
          started_at: new Date().toISOString(),
          finished_at: new Date().toISOString(),
          errors: [],
          progress: { completed: 1, total: 1 },
        },
      };
    }
    return this.request<OperationResponse>(`/operations/${encodedId}`);
  }

  async getAuditVerification(
    fromSequence = 1,
    toSequence?: number
  ): Promise<AuditVerifyResponse> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-audit-verify-demo",
        checked_range: { from_sequence: 1, to_sequence: 3 },
        chain_result: "VALID",
        checks: [
          { sequence: 1, code: "AUDIT_EVENT", result: "PASS" },
          { sequence: 2, code: "AUDIT_EVENT", result: "PASS" },
          { sequence: 3, code: "AUDIT_EVENT", result: "PASS" },
        ],
        checkpoint: { available: false, trusted: false, sequence: null },
        limitations: ["Simulated local demo audit ledger; external checkpoint not configured."],
      };
    }

    const searchParams = new URLSearchParams();
    searchParams.set("from_sequence", String(fromSequence));
    if (toSequence) {
      searchParams.set("to_sequence", String(toSequence));
    }
    return this.request<AuditVerifyResponse>(`/audit/verify?${searchParams.toString()}`);
  }


  // --- Promises & Verification ---

  async getPromises(params?: {
    status?: string;
    customer_id?: string;
    risk?: string;
    deadline_from?: string;
    deadline_to?: string;
    cursor?: string;
    limit?: number;
  }): Promise<{ request_id: string; items: PromiseSummary[]; next_cursor?: string | null }> {
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
        next_cursor: null,
      };
    }

    const searchParams = new URLSearchParams();
    if (params?.status && params.status !== "ALL") {
      searchParams.set("status", params.status);
    }
    if (params?.customer_id) {
      searchParams.set("customer_id", params.customer_id);
    }
    if (params?.risk && this.mode !== "LIVE") {
      searchParams.set("risk", params.risk);
    }
    if (params?.deadline_from) {
      searchParams.set("deadline_from", params.deadline_from);
    }
    if (params?.deadline_to) {
      searchParams.set("deadline_to", params.deadline_to);
    }
    if (params?.cursor) {
      searchParams.set("cursor", params.cursor);
    }
    if (params?.limit) {
      searchParams.set("limit", String(params.limit));
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request(`/promises${query}`);
  }

  async getPromiseDetail(
    promiseId: string,
    versionId?: string
  ): Promise<PromiseDetailResponse> {
    const encodedId = encodeURIComponent(promiseId);
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

    const query = versionId ? `?version_id=${encodeURIComponent(versionId)}` : "";
    return this.request<PromiseDetailResponse>(`/promises/${encodedId}${query}`);
  }

  async verifyPromiseReceipt(
    promiseId: string,
    versionId?: string
  ): Promise<{
    request_id: string;
    receipt_id: string;
    verification: Verification;
  }> {
    const encodedId = encodeURIComponent(promiseId);
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

    const query = versionId ? `?version_id=${encodeURIComponent(versionId)}` : "";
    return this.request(`/promises/${encodedId}/verify${query}`);
  }

  // Non-persisting verification test for tampered copies
  async verifyCustomReceipt(receipt: ReceiptEnvelope): Promise<{
    request_id: string;
    verification: Verification;
  }> {
    if (this.mode === "DEMO") {
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
    const encodedId = encodeURIComponent(promiseId);
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

    return this.request<ReviewResponse>(`/promises/${encodedId}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async revokeReceipt(
    promiseId: string,
    receiptId: string,
    payload: { expected_revision: number; reason: string }
  ): Promise<{
    request_id: string;
    receipt_id: string;
    standing: "REVOKED";
    audit_event_id: string;
  }> {
    const encodedPromiseId = encodeURIComponent(promiseId);
    const encodedReceiptId = encodeURIComponent(receiptId);
    if (!this.currentActor.roles.includes("admin")) {
      throw new ApiError(
        "ROLE_FORBIDDEN",
        `Actor '${this.currentActor.name}' does not hold 'admin' capability required to revoke receipts.`,
        this.generateRequestId(),
        403
      );
    }
    if (this.mode === "DEMO") {
      return {
        request_id: "req-revoke-demo",
        receipt_id: receiptId,
        standing: "REVOKED",
        audit_event_id: `audit-evt-${Date.now()}`,
      };
    }
    return this.request(`/promises/${encodedPromiseId}/receipts/${encodedReceiptId}/revoke`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // --- Simulations ---

  async createSimulations(
    payload: SimulationCreateRequest
  ): Promise<{
    request_id: string;
    scenario_ids: string[];
    results: ScenarioResult[];
  }> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-sim-create-demo",
        scenario_ids: demoScenarios.map((s) => s.id),
        results: demoScenarios,
      };
    }
    return this.request("/simulations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

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
    // In LIVE mode, contract specifies POST /api/simulations.
    return this.createSimulations({
      promise_id: "promise-loyalty",
      base_graph_revision: 12,
      question: "Compare Friday delivery options with supplied capacity",
      scenario_types: [
        "AS_REQUESTED",
        "RENEGOTIATE_DATE_OR_SCOPE",
        "CHANGE_ORDER_OR_EXTRA_CAPACITY",
      ],
      assumptions: [
        {
          id: "assumption-ben-option",
          description: "Use documented optional Ben capacity if approved.",
          value: "5",
          unit: "hours",
          evidence_ref_ids: ["evidence-capacity-option"],
          kind: "USER_ASSUMPTION",
        },
      ],
    }).then((res) => ({
      request_id: res.request_id,
      results: res.results,
    }));
  }

  async getSimulation(scenarioId: string): Promise<{
    request_id: string;
    scenario: ScenarioResult;
  }> {
    const encodedId = encodeURIComponent(scenarioId);
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
    return this.request(`/simulations/${encodedId}`);
  }

  // --- Actions & Approvals ---

  async getActions(params?: {
    status?: string;
    cursor?: string;
    limit?: number;
  }): Promise<{ request_id: string; items: ActionProposalDTO[]; next_cursor?: string | null }> {
    if (this.mode === "DEMO") {
      let filtered: ActionProposalDTO[] = JSON.parse(
        JSON.stringify(demoActions)
      );
      if (params?.status && params.status !== "ALL") {
        filtered = filtered.filter((a) => a.status === params.status);
      }
      return {
        request_id: "req-actions-demo",
        items: filtered,
        next_cursor: null,
      };
    }
    const searchParams = new URLSearchParams();
    if (params?.status && params.status !== "ALL") {
      searchParams.set("status", params.status);
    }
    if (params?.cursor) {
      searchParams.set("cursor", params.cursor);
    }
    if (params?.limit) {
      searchParams.set("limit", String(params.limit));
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return this.request(`/actions${query}`);
  }

  async getAction(actionId: string): Promise<{
    request_id: string;
    action: ActionProposalDTO;
  }> {
    const encodedId = encodeURIComponent(actionId);
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
    return this.request(`/actions/${encodedId}`);
  }

  async requestApproval(
    actionId: string,
    payload: ActionRequestApprovalRequest
  ): Promise<{
    request_id: string;
    action: ActionProposalDTO;
    approval?: ActionProposalDTO["approval"];
  }> {
    const encodedId = encodeURIComponent(actionId);
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
      action.status = "NEEDS_APPROVAL";
      return {
        request_id: "req-req-appr-demo",
        action,
      };
    }
    return this.request(`/actions/${encodedId}/request-approval`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async approveAction(
    actionId: string,
    payload: ActionApprovalRequest
  ): Promise<{
    request_id: string;
    action: ActionProposalDTO;
    audit_event_id: string;
  }> {
    const encodedId = encodeURIComponent(actionId);
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
        reason: payload.reason || "Approved within delivery policy capacity ceiling ($750)",
        approval_id: `appr-${Date.now()}`,
      };

      return {
        request_id: "req-approve-demo",
        action,
        audit_event_id: `audit-evt-${Date.now()}`,
      };
    }

    return this.request(`/actions/${encodedId}/approve`, {
      method: "POST",
      body: JSON.stringify({
        expected_revision: payload.expected_revision,
        proposal_hash: payload.proposal_hash,
        reason: payload.reason,
      }),
    });
  }

  async rejectAction(
    actionId: string,
    payload: ActionRejectRequest
  ): Promise<{
    request_id: string;
    action: ActionProposalDTO;
    audit_event_id: string;
  }> {
    const encodedId = encodeURIComponent(actionId);
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

    return this.request(`/actions/${encodedId}/reject`, {
      method: "POST",
      body: JSON.stringify({
        expected_revision: payload.expected_revision,
        reason: payload.reason,
      }),
    });
  }

  async executeAction(
    actionId: string,
    payload: ActionExecuteRequest
  ): Promise<{
    request_id: string;
    action_id: string;
    status: "EXECUTING" | "SUCCEEDED";
    status_url: string;
  }> {
    const encodedId = encodeURIComponent(actionId);
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

    return this.request(`/actions/${encodedId}/execute`, {
      method: "POST",
      body: JSON.stringify({
        expected_revision: payload.expected_revision,
        proposal_hash: payload.proposal_hash,
      }),
    });
  }

  async reconcileAction(
    actionId: string,
    payload: ActionReconcileRequest
  ): Promise<{
    request_id: string;
    action_id: string;
    status: string;
  }> {
    const encodedId = encodeURIComponent(actionId);
    if (!this.currentActor.roles.includes("executor")) {
      throw new ApiError(
        "ROLE_FORBIDDEN",
        `Reconcile denied: Actor '${this.currentActor.name}' lacks 'executor' role.`,
        this.generateRequestId(),
        403
      );
    }
    if (this.mode === "DEMO") {
      return {
        request_id: "req-reconcile-demo",
        action_id: actionId,
        status: "SUCCEEDED",
      };
    }
    return this.request(`/actions/${encodedId}/reconcile`, {
      method: "POST",
      body: JSON.stringify({
        expected_revision: payload.expected_revision,
        reason: payload.reason,
      }),
    });
  }

  // --- Graph ---

  async getGraph(
    entityId = "promise-loyalty",
    depth = 1,
    options?: { maxNodes?: number; types?: string[] }
  ): Promise<GraphResponse> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-graph-demo",
        graph_revision: 12,
        nodes: SEED_GRAPH_NODES,
        edges: SEED_GRAPH_EDGES,
        paths: demoPromiseDetail.graph_paths,
        truncated: false,
        expansion_hints: [],
      };
    }
    const resolvedId = entityId || "promise-loyalty";
    const searchParams = new URLSearchParams();
    searchParams.set("depth", String(depth));
    if (options?.maxNodes) {
      searchParams.set("max_nodes", String(options.maxNodes));
    }
    if (options?.types && options.types.length > 0) {
      searchParams.set("types", options.types.join(","));
    }
    return this.request<GraphResponse>(
      `/graph/${encodeURIComponent(resolvedId)}?${searchParams.toString()}`
    );
  }

  // --- Chat ---

  async sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
    if (this.mode === "DEMO") {
      return {
        request_id: "req-chat-demo",
        answer:
          "Based on the FalkorDB graph, Acme loyalty integration is excluded under Contract Clause C2. A 5-hour capacity deficit exists for Friday delivery.",
        confirmed_claims: [
          {
            claim_id: "claim-scope",
            text: "Clause C2 excludes loyalty integration from signed SOW.",
            evidence_ref_ids: ["ev-clause-c2"],
            graph_path_ids: ["path-scope-exclusion"],
          },
        ],
        hypotheses: [],
        promise_ids: ["promise-loyalty"],
        graph_paths: demoPromiseDetail.graph_paths,
        sources: demoPromiseDetail.evidence,
        conflicts: [],
        freshness: {
          level: "FRESH",
          as_of: "2026-10-12T09:00:00.000Z",
          evaluated_at: new Date().toISOString(),
          threshold_seconds: 3600,
          source_version_ids: ["src-ver-meeting-1"],
        },
        evidence_quality: "HIGH",
        caveats: ["Ben Ortiz reservation requires reviewer approval."],
        calculations: demoPromiseDetail.calculations,
        scenario_ids: demoScenarios.map((s) => s.id),
        trace: { steps: [] },
        analysis_mode: "DETERMINISTIC_ONLY",
        graph_revision: 12,
      };
    }
    return this.request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
}

// Export singleton instance for client-side queries
export const apiClient = new ApiClient();
