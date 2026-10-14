/**
 * PromiseOps + PromiseSeal TypeScript API types
 * Exact mirror of docs/API_CONTRACTS.md and docs/PROMISESEAL_PROTOCOL.md
 */

export type PromiseState =
  | "PROPOSED"
  | "NEEDS_REVIEW"
  | "CONFIRMED"
  | "DISPUTED"
  | "SUPERSEDED"
  | "FULFILLED"
  | "REJECTED";

export type ReceiptStanding = "ACTIVE" | "SUPERSEDED" | "REVOKED";

export type VerificationIntegrity =
  | "VALID"
  | "INVALID"
  | "UNSIGNED"
  | "INDETERMINATE";

export type KeyTrust = "TRUSTED" | "RETIRED" | "COMPROMISED" | "UNKNOWN";

export type FreshnessLevel = "FRESH" | "AGING" | "STALE" | "UNKNOWN";

export type ScopeStatus =
  | "IN_SCOPE"
  | "OUT_OF_SCOPE"
  | "POSSIBLE_OUT_OF_SCOPE"
  | "AMBIGUOUS"
  | "INSUFFICIENT_EVIDENCE";

export type PolicyOutcome = "PASS" | "BLOCK" | "NEEDS_REVIEW";

export interface EvidenceRef {
  evidence_ref_id: string;
  source_id: string;
  source_version_id: string;
  source_hash: string;
  representation_hash: string;
  origin_reference: string;
  quote: string | null;
  start_offset: number | null;
  end_offset: number | null;
  start_ms: number | null;
  end_ms: number | null;
  structured_pointer: string | null;
  source_updated_at: string | null;
  observed_at: string;
  verification: "VERIFIED" | "REJECTED" | "UNAVAILABLE";
  access_label: string;
}

export interface SourceSummary {
  id: string;
  source_type: string;
  title: string;
  current_version_id: string;
  source_updated_at: string | null;
  ingested_at: string;
  content_hash: string;
  retention_state: string;
  parse_status: string;
  mode: "IMPORT" | "MOCK" | "LIVE" | "DEMO";
}

export interface Freshness {
  level: FreshnessLevel;
  as_of: string | null;
  evaluated_at: string;
  threshold_seconds: number;
  source_version_ids: string[];
}

export interface CalculationInput {
  name: string;
  value?: string;
  unit: string;
  evidence_ref_ids: string[];
}

export interface Calculation {
  calculation_id: string;
  formula_id: string;
  formula_version: string;
  amount: string | null;
  currency: string | null;
  status: "ESTIMATE" | "AT_RISK" | "CONFIRMED" | "UNKNOWN";
  inputs: CalculationInput[];
  computed_at: string;
  missing_inputs: string[];
}

export interface PromiseDeadline {
  original_text?: string;
  precision?: "UNKNOWN" | "DATE" | "INSTANT";
  local_date?: string | null;
  instant?: string | null;
  timezone?: string | null;
  resolution_basis?: string | null;
}

export interface PromiseSummary {
  id: string;
  current_version_id: string;
  revision: number;
  current_state: PromiseState;
  receipt_standing: ReceiptStanding;
  customer_id: string | null;
  customer_name?: string;
  project_id: string | null;
  deliverable: string;
  deadline: PromiseDeadline | string | null;
  scope_status: ScopeStatus;
  risk_flags: string[];
  freshness: Freshness;
  open_conflict_ids: string[];
  commercial_value?: {
    amount: string;
    currency: string;
  } | null;
}

export interface GraphNode {
  id: string;
  label: string;
  display_name: string;
  status?: string | null;
  source_ref_ids: string[];
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  type: string;
  from_id: string;
  to_id: string;
  status: string;
  provenance_kind: string;
  evidence_refs: EvidenceRef[];
  derived: boolean;
  underlying_edge_ids: string[];
  scenario_only: boolean;
}

export interface GraphPath {
  path_id: string;
  template_id: string;
  node_ids: string[];
  edge_ids: string[];
  graph_revision: number;
  evidence_ref_ids: string[];
}

export interface PolicyCheck {
  rule_id: string;
  outcome: PolicyOutcome;
  reason: string;
  evidence_ref_ids: string[];
}

export interface AuditRecord {
  id: string;
  sequence: number;
  event_type: string;
  actor_id: string;
  occurred_at: string;
  request_id: string;
  payload: Record<string, unknown>;
  prev_event_hash: string | null;
  event_hash: string;
  signature_base64url: string;
  key_id: string;
  canonicalization: string;
}

export interface TraceStep {
  step_id: string;
  phase: string;
  tool_id: string;
  template_id: string | null;
  safe_parameters: Record<string, unknown>;
  started_at: string;
  duration_ms: number;
  row_count: number;
  returned_entity_ids: string[];
  returned_edge_ids: string[];
  source_ref_ids: string[];
  outcome: string;
  error_code: string | null;
}

export interface Operation {
  id: string;
  kind: string;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "SUCCEEDED" | "FAILED" | "CANCELLED";
  phase: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  result?: Record<string, unknown>;
  errors: string[];
  progress: {
    completed: number;
    total?: number;
  };
}

export interface ReceiptConfirmation {
  confirmed_by: string;
  confirmed_at: string;
  confirmation_event_id: string;
  authority_scope: string;
  reviewed_content_hash: string;
}

export interface ReceiptPayload {
  protocol_version: "promiseseal-v1";
  receipt_id: string;
  promise_id: string;
  tenant_id: string;
  version: number;
  issuer_id: string;
  created_at: string;
  issued_at: string | null;
  statement: {
    exact_excerpt: string;
    interpretation: string;
  };
  deliverable: string;
  customer_id: string | null;
  project_id: string | null;
  deadline: PromiseDeadline | null;
  price_condition: {
    kind: string;
    original_text: string;
  };
  commercial_value: {
    amount: string;
    currency: string;
    evidence_ref_id: string;
  } | null;
  commitment_class:
    | "explicit"
    | "conditional"
    | "suggestion"
    | "hypothetical"
    | "ambiguous";
  source_refs: EvidenceRef[];
  contract_refs: Array<{
    entity_id: string;
    source_version_id: string;
    evidence_ref_ids: string[];
  }>;
  jira_refs: Array<{
    entity_id: string;
    source_version_id: string;
    evidence_ref_ids: string[];
  }>;
  workload_refs: Array<{
    entity_id: string;
    source_version_id: string;
    evidence_ref_ids: string[];
  }>;
  status_at_issuance: PromiseState;
  confirmation: ReceiptConfirmation | null;
  review_event_id: string | null;
  previous_receipt_version_id: string | null;
  previous_payload_sha256: string | null;
  canonicalization: "promiseops-json-v1";
  signature_algorithm: "Ed25519";
  signing_key_id: string | null;
}

export interface ReceiptEnvelope {
  payload: ReceiptPayload;
  payload_sha256: string;
  signature_base64url: string | null;
}

export interface VerificationCheck {
  code: string;
  result: "PASS" | "FAIL" | "UNAVAILABLE";
  field?: string;
  reason: string;
}

export interface Verification {
  integrity: VerificationIntegrity;
  standing: ReceiptStanding;
  checked_at: string;
  checks: VerificationCheck[];
  source_results: Array<{
    source_id?: string;
    evidence_ref_id?: string;
    result: "MATCH" | "MISMATCH" | "UNAVAILABLE";
    details?: string;
    reason?: string | null;
  }>;
  key_trust: KeyTrust;
  eligible_for_action: boolean;
}

export interface ScopeAssessment {
  status: ScopeStatus;
  claim: string;
  clause_ids: string[];
  evidence_refs: EvidenceRef[];
  conflict_ids: string[];
  missing_evidence: string[];
  assessment_kind: "LLM_REVIEWED" | "DETERMINISTIC_RULE";
  reviewed_by?: string;
}

export interface ConflictItem {
  id: string;
  promise_id: string;
  title: string;
  description: string;
  conflicting_sources: Array<{
    source_id: string;
    quote: string;
    speaker?: string;
    timestamp: string;
  }>;
  status: "OPEN" | "RESOLVED" | "DISMISSED";
  detected_at: string;
}

export interface PromiseDetailResponse {
  request_id: string;
  promise: PromiseSummary;
  receipt: ReceiptEnvelope;
  versions: Array<{
    receipt_id: string;
    version: number;
    status_at_issuance: PromiseState;
    standing: ReceiptStanding;
    created_at?: string;
  }>;
  evidence: EvidenceRef[];
  scope_assessment: ScopeAssessment;
  calculations: Calculation[];
  related_issue_ids: string[];
  related_issues_details?: Array<{
    id: string;
    key: string;
    summary: string;
    status: string;
    effort_hours: number;
    assignee_id: string;
    assignee_name: string;
    depends_on?: string[];
  }>;
  workload_deficit?: {
    required_hours: number;
    available_hours: number;
    deficit_hours: number;
    deadline: string;
  };
  milestone_ids: string[];
  milestones_details?: Array<{
    id: string;
    title: string;
    amount: string;
    currency: string;
    target_date: string;
    status: "READY" | "AT_RISK" | "PAID";
    required_criteria: string[];
    missing_criteria: string[];
  }>;
  conflicts: ConflictItem[];
  graph_paths: GraphPath[];
}

export interface ReviewRequest {
  expected_version_id: string;
  expected_revision: number;
  decision: "CONFIRM" | "DISPUTE" | "REJECT" | "FULFILL" | "REVISE";
  reason: string;
  evidence_ref_ids: string[];
  revised_content?: Partial<ReceiptPayload>;
}

export interface ReviewResponse {
  request_id: string;
  promise: PromiseSummary;
  receipt: ReceiptEnvelope;
  audit_event_id: string;
}

export interface ScenarioAssumption {
  id: string;
  description: string;
  value?: string;
  unit?: string;
  evidence_ref_ids: string[];
  kind: "OBSERVED" | "USER_ASSUMPTION";
}

export interface ScheduleItem {
  issue_id: string;
  person_id: string;
  person_name?: string;
  start: string | null;
  end: string | null;
  hours: number;
}

export interface ConstraintResult {
  rule_id: string;
  outcome: "PASS" | "BLOCK" | "NEEDS_REVIEW";
  reason: string;
  evidence_ref_ids: string[];
}

export interface ScenarioResult {
  id: string;
  type:
    | "AS_REQUESTED"
    | "RENEGOTIATE_DATE_OR_SCOPE"
    | "CHANGE_ORDER_OR_EXTRA_CAPACITY";
  status: "COMPUTED" | "FAILED" | "PENDING";
  base_graph_revision: number;
  input_digest: string;
  inputs: Record<string, unknown>;
  overlay: Record<string, unknown>;
  assumptions: ScenarioAssumption[];
  feasibility: "FEASIBLE" | "INFEASIBLE" | "UNKNOWN";
  conditional: boolean;
  schedule: ScheduleItem[];
  constraint_results: ConstraintResult[];
  calculations: Calculation[];
  affected_entity_ids: string[];
  graph_paths: GraphPath[];
  missing_inputs: string[];
  auditor?: {
    verdict: "APPROVED" | "CHALLENGED" | "REJECTED";
    findings: string[];
    challenged_assumptions: string[];
  };
  policy_checks: PolicyCheck[];
  candidate_actions: ActionProposalDTO[];
  computed_at: string;
  calculator_version: string;
}

export interface ActionProposalDTO {
  id: string;
  revision: number;
  scenario_id: string;
  action_type:
    | "WORKLOAD_UPDATE"
    | "JIRA_UPDATE"
    | "JIRA_CREATE"
    | "DRAFT_CUSTOMER_MESSAGE";
  target_system: "WORKLOAD_MOCK" | "WORKLOAD_LIVE" | "JIRA" | "LOCAL_DRAFT";
  target_id: string;
  mode: "MOCK" | "LIVE" | "DRAFT";
  before_state: Record<string, unknown>;
  before_state_hash: string;
  requested_changes: Record<string, unknown>;
  proposal_hash: string;
  dependency_digest: string;
  receipt_ids: string[];
  evidence_refs: EvidenceRef[];
  graph_paths: GraphPath[];
  impact: Calculation[];
  auditor_verdict: string;
  policy_checks: PolicyCheck[];
  required_approval_role: "reviewer";
  status:
    | "PROPOSED"
    | "NEEDS_APPROVAL"
    | "APPROVED"
    | "EXECUTING"
    | "SUCCEEDED"
    | "FAILED"
    | "CANCELLED"
    | "BLOCKED"
    | "NEEDS_RECONCILIATION";
  idempotency_key: string;
  approval?: {
    approved_by: string;
    approved_at: string;
    expires_at: string;
    reason: string;
    approval_id: string;
  };
  attempts: Array<{
    attempt_id: string;
    started_at: string;
    finished_at?: string;
    status: string;
    http_status?: number;
  }>;
  external_response_reference?: string;
  read_back?: {
    expected: Record<string, unknown>;
    actual: Record<string, unknown>;
    mismatches: string[];
    checked_at: string;
    verified: boolean;
  };
}

export interface KnowledgeFinding {
  id: string;
  category:
    | "ORPHAN_NODE"
    | "UNSUPPORTED_RELATION"
    | "DUPLICATE_CANDIDATE"
    | "STALE_SOURCE"
    | "FAILED_QUOTE_VERIFICATION"
    | "OPEN_CONFLICT";
  severity: "HIGH" | "MEDIUM" | "LOW";
  title: string;
  description: string;
  entity_ids: string[];
  detected_at: string;
  status: "QUARANTINED" | "OPEN" | "RESOLVED" | "DISMISSED";
  recommendation: string;
}

export interface KnowledgeHealthResponse {
  request_id: string;
  graph_revision: number;
  counts: {
    nodes: number;
    edges: number;
    stale_sources: number;
    open_conflicts: number;
    unresolved_promises: number;
    open_findings: number;
  };
  findings: KnowledgeFinding[];
  next_cursor?: string;
}

export interface ConnectorSummary {
  id: string;
  type: "FALKORDB" | "LLM" | "JIRA" | "TRANSCRIPTS" | "WORKLOAD";
  title: string;
  mode: "MOCK" | "LIVE";
  configured: boolean;
  health: "OK" | "DEGRADED" | "DOWN" | "NOT_CONFIGURED";
  checked_at: string;
  write_enabled: boolean;
  missing_configuration_keys: string[];
  safe_details: Record<string, string>;
}

export interface ActionApprovalRequest {
  expected_revision: number;
  proposal_hash: string;
  reason: string;
}

export interface ActionRejectRequest {
  expected_revision: number;
  reason: string;
}

export interface ActionExecuteRequest {
  expected_revision: number;
  proposal_hash: string;
}

export interface ActionRequestApprovalRequest {
  expected_revision: number;
  proposal_hash: string;
}

export interface ActionReconcileRequest {
  expected_revision: number;
  reason: string;
}

export interface SimulationCreateRequest {
  promise_id: string;
  base_graph_revision: number;
  question: string;
  scenario_types: Array<
    | "AS_REQUESTED"
    | "RENEGOTIATE_DATE_OR_SCOPE"
    | "CHANGE_ORDER_OR_EXTRA_CAPACITY"
  >;
  assumptions: ScenarioAssumption[];
  parent_scenario_id?: string;
}

export interface ChatRequest {
  question: string;
  session_id?: string;
  context?: {
    promise_id?: string;
    customer_id?: string;
  };
}

export interface ChatConfirmedClaim {
  claim_id: string;
  text: string;
  evidence_ref_ids: string[];
  graph_path_ids: string[];
}

export interface ChatHypothesis {
  claim_id: string;
  text: string;
  assumptions: string[];
  evidence_ref_ids: string[];
}

export interface ChatResponse {
  request_id: string;
  answer: string;
  confirmed_claims: ChatConfirmedClaim[];
  hypotheses: ChatHypothesis[];
  promise_ids: string[];
  graph_paths: GraphPath[];
  sources: EvidenceRef[];
  conflicts: ConflictItem[];
  freshness: Freshness;
  evidence_quality: "LOW" | "MEDIUM" | "HIGH";
  caveats: string[];
  calculations: Calculation[];
  scenario_ids: string[];
  trace: { steps: TraceStep[] };
  analysis_mode: "GENERATED" | "DETERMINISTIC_ONLY" | "REPLAY";
  graph_revision: number;
}

export interface SessionBootstrapRequest {
  credential: string;
}

export interface GraphResponse {
  request_id: string;
  graph_revision: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  paths: GraphPath[];
  truncated: boolean;
  expansion_hints?: string[];
}

export interface ApiErrorDetail {
  field?: string;
  reason: string;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    request_id: string;
    details?: ApiErrorDetail[];
  };
}

export interface SessionInfo {
  request_id: string;
  actor: {
    id: string;
    name?: string;
    roles: Array<"viewer" | "reviewer" | "executor" | "admin" | string>;
  };
  tenant_id?: string;
  mode: "DEMO" | "LIVE" | "MOCK" | string;
  expires_at: string;
}

export interface UploadAccepted {
  request_id: string;
  operation_id: string;
  source_id: string;
  status_url: string;
}

export interface UploadNoChange {
  request_id: string;
  source_id: string;
  source_version_id: string;
  outcome: "NO_CHANGE";
}

export interface OperationResponse {
  request_id: string;
  operation: Operation;
}

export interface SourceVersionSummary {
  id: string;
  source_hash: string;
  representation_hash: string;
  availability: string;
}

export interface SourceVersionItem {
  id: string;
  version: number;
  source_updated_at: string | null;
  availability: string;
}

export interface SourceDetailResponse {
  request_id: string;
  source: SourceSummary;
  version: SourceVersionSummary;
  snippets: EvidenceRef[];
  versions: SourceVersionItem[];
}

export interface AuditCheck {
  sequence: number;
  code: string;
  result: "PASS" | "FAIL" | "UNAVAILABLE" | "VALID" | "INVALID" | "INDETERMINATE" | string;
  actor_id?: string;
  event_hash?: string;
  field?: string | null;
  reason?: string | null;
}

export interface AuditVerifyResponse {
  request_id: string;
  checked_range: {
    from_sequence: number;
    to_sequence: number;
  };
  chain_result: "VALID" | "INVALID" | "INDETERMINATE";
  checks: AuditCheck[];
  checkpoint: {
    available: boolean;
    trusted: boolean;
    sequence?: number | null;
  };
  limitations: string[];
}

