import { describe, it, expect, beforeEach } from "vitest";
import { apiClient, ApiError } from "@/lib/api-client";

describe("Approval Queue & Execution Policy Enforcement", () => {
  beforeEach(() => {
    apiClient.resetDemoData();
  });

  it("blocks execution when action has not yet been approved (Gate Rule Demo Question 10)", async () => {
    // Switch to executor role
    apiClient.setActor("executor");

    // Attempting to execute unapproved action must throw ACTION_NOT_APPROVED
    try {
      await apiClient.executeAction("action-reserve-ben", {
        expected_revision: 1,
        proposal_hash:
          "b6a41f8903c719e27c10b490d1829e1f3790184b9012cba8912ef09124018291",
      });
      expect.unreachable("Should have blocked pre-approval execution");
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.code).toBe("ACTION_NOT_APPROVED");
      expect(err.status).toBe(409);
    }
  });

  it("blocks executor from self-approving an action proposal", async () => {
    apiClient.setActor("executor");

    try {
      await apiClient.approveAction("action-reserve-ben", {
        expected_revision: 1,
        proposal_hash:
          "b6a41f8903c719e27c10b490d1829e1f3790184b9012cba8912ef09124018291",
        reason: "Self approval attempt",
      });
      expect.unreachable("Should have blocked executor approval");
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.code).toBe("ROLE_FORBIDDEN");
      expect(err.status).toBe(403);
    }
  });

  it("permits reviewer to approve, and executor to execute with verified read-back", async () => {
    // Step 1: Reviewer approves
    apiClient.setActor("reviewer");
    const approveRes = await apiClient.approveAction("action-reserve-ben", {
      expected_revision: 1,
      proposal_hash:
        "b6a41f8903c719e27c10b490d1829e1f3790184b9012cba8912ef09124018291",
      reason: "Approved within capacity ceiling",
    });
    expect(approveRes.action.status).toBe("APPROVED");
    expect(approveRes.action.approval?.approved_by).toBe("actor-reviewer");

    // Step 2: Executor executes
    apiClient.setActor("executor");
    const execRes = await apiClient.executeAction("action-reserve-ben", {
      expected_revision: 1,
      proposal_hash:
        "b6a41f8903c719e27c10b490d1829e1f3790184b9012cba8912ef09124018291",
    });
    expect(execRes.status).toBe("SUCCEEDED");

    // Step 3: Authoritative read-back verification
    const verifiedAction = await apiClient.getAction("action-reserve-ben");
    expect(verifiedAction.action.status).toBe("SUCCEEDED");
    expect(verifiedAction.action.read_back?.verified).toBe(true);
    expect(verifiedAction.action.read_back?.mismatches.length).toBe(0);
  });
});
