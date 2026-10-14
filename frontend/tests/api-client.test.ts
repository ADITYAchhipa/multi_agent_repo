import { describe, it, expect, beforeEach } from "vitest";
import { apiClient, ApiError } from "@/lib/api-client";

describe("ApiClient & Envelope Handling", () => {
  beforeEach(() => {
    apiClient.resetDemoData();
    apiClient.setActor("reviewer");
  });

  it("returns promises in DEMO mode adhering to PromiseSummary contract", async () => {
    const res = await apiClient.getPromises();
    expect(res.items.length).toBeGreaterThan(0);
    const loyalty = res.items.find((p) => p.id === "promise-loyalty");
    expect(loyalty).toBeDefined();
    expect(loyalty?.current_state).toBe("PROPOSED");
    expect(loyalty?.scope_status).toBe("POSSIBLE_OUT_OF_SCOPE");
  });

  it("retrieves full promise detail with canonical receipt envelope and Ed25519 signature", async () => {
    const detail = await apiClient.getPromiseDetail("promise-loyalty");
    expect(detail.promise.id).toBe("promise-loyalty");
    expect(detail.receipt.payload.protocol_version).toBe("promiseseal-v1");
    expect(detail.receipt.payload.signature_algorithm).toBe("Ed25519");
    expect(detail.receipt.payload.signing_key_id).toBe("key-demo-2026");
    expect(detail.receipt.payload_sha256).toBeDefined();
    expect(detail.evidence.length).toBeGreaterThan(0);
    expect(detail.evidence[0].quote).toContain("loyalty integration by Friday");
  });

  it("verifies receipt integrity through fresh verification checks", async () => {
    const verify = await apiClient.verifyPromiseReceipt("promise-loyalty");
    expect(verify.verification.integrity).toBe("VALID");
    expect(verify.verification.key_trust).toBe("TRUSTED");
    expect(verify.verification.checks.length).toBeGreaterThan(0);

    const digestCheck = verify.verification.checks.find(
      (c) => c.code === "CANONICAL_PAYLOAD_DIGEST"
    );
    expect(digestCheck?.result).toBe("PASS");
  });

  it("fails verification with PAYLOAD_DIGEST_MISMATCH when payload is tampered", async () => {
    const detail = await apiClient.getPromiseDetail("promise-loyalty");
    const tamperedReceipt = {
      ...detail.receipt,
      payload: {
        ...detail.receipt.payload,
        deliverable: "Tampered deliverable text",
      },
    };

    const res = await apiClient.verifyCustomReceipt(tamperedReceipt);
    expect(res.verification.integrity).toBe("INVALID");
    const digestCheck = res.verification.checks.find(
      (c) => c.code === "CANONICAL_PAYLOAD_DIGEST"
    );
    expect(digestCheck?.result).toBe("FAIL");
    expect(digestCheck?.reason).toContain("PAYLOAD_DIGEST_MISMATCH");
    expect(res.verification.eligible_for_action).toBe(false);
  });

  it("enforces reviewer role capability on review transitions", async () => {
    // Switch to viewer role (unauthorized)
    apiClient.setActor("viewer");

    try {
      await apiClient.reviewPromise("promise-loyalty", {
        expected_version_id: "receipt-loyalty-v1",
        expected_revision: 1,
        decision: "CONFIRM",
        reason: "Test confirmation without role",
        evidence_ref_ids: ["ev-meeting-1-quote"],
      });
      expect.unreachable("Should have thrown ApiError");
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.code).toBe("ROLE_FORBIDDEN");
      expect(err.status).toBe(403);
    }
  });

  it("handles source document upload and operation tracking in DEMO mode", async () => {
    const blob = new Blob(["We will deliver the loyalty integration by Friday at no extra charge."], {
      type: "text/plain",
    });

    const uploadRes = await apiClient.uploadSource({
      file: blob,
      filename: "notes.txt",
      sourceType: "NOTES",
      accessLabel: "PUBLIC_DEMO",
      sourceKey: "test-meeting-notes",
    });

    expect("operation_id" in uploadRes).toBe(true);
    if ("operation_id" in uploadRes) {
      expect(uploadRes.operation_id).toBeDefined();
      expect(uploadRes.source_id).toBeDefined();
      expect(uploadRes.status_url).toContain("/api/operations/");

      const op = await apiClient.getOperation(uploadRes.operation_id);
      expect(op.operation.id).toBe(uploadRes.operation_id);
      expect(op.operation.status).toBe("COMPLETED");
      expect(op.operation.phase).toBe("COMPLETED");

      const src = await apiClient.getSource(uploadRes.source_id);
      expect(src.source.id).toBe(uploadRes.source_id);
      expect(src.source.source_type).toBe("NOTES");
      expect(src.snippets.length).toBeGreaterThan(0);
    }
  });

  it("verifies immutable cryptographic audit hash chain", async () => {
    const auditRes = await apiClient.getAuditVerification(1, 3);
    expect(auditRes.chain_result).toBe("VALID");
    expect(auditRes.checked_range.from_sequence).toBe(1);
    expect(auditRes.checked_range.to_sequence).toBe(3);
    expect(auditRes.checks.length).toBe(3);
    expect(auditRes.checks.every((c) => c.result === "PASS")).toBe(true);
  });

  it("bootstraps session and handles role permissions", async () => {
    const session = await apiClient.getSession();
    expect(session.actor).toBeDefined();
    expect(session.expires_at).toBeDefined();

    const bootRes = await apiClient.bootstrapSession("admin-credential");
    expect(bootRes.actor.roles).toContain("admin");
    expect(apiClient.getActor().roles).toContain("admin");
  });

  it("retrieves historical version receipt without mutating head pointer", async () => {
    const detail = await apiClient.getPromiseDetail("promise-loyalty", "receipt-loyalty-v1");
    expect(detail.promise.id).toBe("promise-loyalty");
    expect(detail.receipt.payload.receipt_id).toBe("receipt-loyalty-v1");
    expect(detail.promise.current_version_id).toBe("receipt-loyalty-v1");
    expect(detail.versions.length).toBeGreaterThan(0);
  });

  it("extracts supported proof path graph topology", async () => {
    const graph = await apiClient.getGraph("promise-loyalty", 1);
    expect(graph.nodes.length).toBeGreaterThan(0);
    expect(graph.edges.length).toBeGreaterThan(0);
    expect(graph.paths.length).toBeGreaterThan(0);
    expect(graph.paths[0].template_id).toBeDefined();
  });
});


