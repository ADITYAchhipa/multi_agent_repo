import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import { apiClient, ApiError } from "@/lib/api-client";
import { UnavailableStateCard } from "@/components/ui/unavailable-state";
import { SimulationCreateRequest } from "@/types/api";

describe("Frontend API Contract Conformance & Client Hardening", () => {
  beforeEach(() => {
    apiClient.resetDemoData();
    apiClient.setActor("reviewer");
    apiClient.setMode("DEMO");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    apiClient.setMode("DEMO");
  });

  describe("LIVE Mode Path, Method, and URL Encoding Conformance", () => {
    beforeEach(() => {
      apiClient.setMode("LIVE");
    });

    it("encodes opaque IDs with special characters in GET /api/graph/{entity_id}", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            request_id: "req-graph-1",
            graph_revision: 12,
            nodes: [],
            edges: [],
            paths: [],
            truncated: false,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      const res = await apiClient.getGraph("promise/acme:loyalty#1", 1);
      expect(fetchSpy).toHaveBeenCalledTimes(1);

      const [calledUrl, calledInit] = fetchSpy.mock.calls[0];
      expect(calledUrl).toContain("/api/graph/promise%2Facme%3Aloyalty%231?depth=1");
      expect(calledInit?.method).toBe("GET");
      expect(res.graph_revision).toBe(12);
      expect(res.nodes).toBeDefined();
    });

    it("encodes opaque promise IDs in GET /api/promises/{id}", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            promise: { id: "promise/acme:1" },
            receipt: {},
            evidence: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      await apiClient.getPromiseDetail("promise/acme:1");
      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [calledUrl] = fetchSpy.mock.calls[0];
      expect(calledUrl).toContain("/api/promises/promise%2Facme%3A1");
    });

    it("conforms to ActionApprovalRequest schema on POST /api/actions/{id}/approve", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            action: { id: "action-123", status: "APPROVED" },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      const payload = {
        expected_revision: 2,
        proposal_hash: "hash-proposal-abc123456",
        reason: "Approval within budget ceiling",
      };

      await apiClient.approveAction("action/special:123", payload);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [calledUrl, calledInit] = fetchSpy.mock.calls[0];
      expect(calledUrl).toContain("/api/actions/action%2Fspecial%3A123/approve");
      expect(calledInit?.method).toBe("POST");

      const body = JSON.parse(calledInit?.body as string);
      expect(body).toEqual(payload);
      expect(body.expected_revision).toBe(2);
      expect(body.proposal_hash).toBe("hash-proposal-abc123456");
      expect(body.reason).toBe("Approval within budget ceiling");
    });

    it("conforms to ActionRejectRequest schema on POST /api/actions/{id}/reject", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            action: { id: "action-123", status: "REJECTED" },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      const payload = {
        expected_revision: 3,
        reason: "Resource constraint violation",
      };

      await apiClient.rejectAction("action-123", payload);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [calledUrl, calledInit] = fetchSpy.mock.calls[0];
      expect(calledUrl).toContain("/api/actions/action-123/reject");
      expect(calledInit?.method).toBe("POST");

      const body = JSON.parse(calledInit?.body as string);
      expect(body).toEqual(payload);
      expect(body.expected_revision).toBe(3);
      expect(body.reason).toBe("Resource constraint violation");
    });

    it("conforms to ActionExecuteRequest schema on POST /api/actions/{id}/execute", async () => {
      apiClient.setActor("executor");
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            action_id: "action-123",
            status: "SUCCEEDED",
            idempotency_key: "idem-123",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      const payload = {
        expected_revision: 2,
        proposal_hash: "hash-proposal-abc123456",
      };

      await apiClient.executeAction("action-123", payload);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [calledUrl, calledInit] = fetchSpy.mock.calls[0];
      expect(calledUrl).toContain("/api/actions/action-123/execute");
      expect(calledInit?.method).toBe("POST");

      const body = JSON.parse(calledInit?.body as string);
      expect(body).toEqual(payload);
    });

    it("conforms to SimulationCreateRequest on POST /api/simulations", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            simulation_id: "sim-new",
            status: "COMPLETED",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      const reqPayload: SimulationCreateRequest = {
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
      };

      await apiClient.createSimulations(reqPayload);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [calledUrl, calledInit] = fetchSpy.mock.calls[0];
      expect(calledUrl).toContain("/api/simulations");
      expect(calledInit?.method).toBe("POST");

      const body = JSON.parse(calledInit?.body as string);
      expect(body.promise_id).toBe("promise-loyalty");
      expect(body.scenario_types).toHaveLength(3);
    });
  });

  describe("Idempotency-Key Header Handling", () => {
    beforeEach(() => {
      apiClient.setMode("LIVE");
    });

    it("generates 16-128 char Idempotency-Key header on mutation requests", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

      await apiClient.approveAction("action-1", {
        expected_revision: 1,
        proposal_hash: "hash-1",
        reason: "Valid",
      });

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [, calledInit] = fetchSpy.mock.calls[0];
      const headers = calledInit?.headers as Headers;
      const idempotencyKey = headers.get("Idempotency-Key");

      expect(idempotencyKey).toBeDefined();
      expect(typeof idempotencyKey).toBe("string");
      expect(idempotencyKey!.length).toBeGreaterThanOrEqual(16);
      expect(idempotencyKey!.length).toBeLessThanOrEqual(128);
      expect(idempotencyKey).toMatch(/^idem-/);
    });

    it("does NOT send Idempotency-Key header on POST /api/session bootstrap (per API_CONTRACTS.md §1)", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            tenant_id: "tenant-default",
            user_id: "usr-1",
            role: "reviewer",
            csrf_token: "csrf-tok",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      await apiClient.bootstrapSession("dev-reviewer-token");

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [, calledInit] = fetchSpy.mock.calls[0];
      const headers = calledInit?.headers as Headers;
      expect(headers.get("Idempotency-Key")).toBeNull();
    });

    it("does NOT send Idempotency-Key header on GET requests", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ items: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

      await apiClient.getPromises();

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [, calledInit] = fetchSpy.mock.calls[0];
      const headers = calledInit?.headers as Headers;
      expect(headers.get("Idempotency-Key")).toBeNull();
    });
  });

  describe("Error Envelope Normalization & Status Classification", () => {
    beforeEach(() => {
      apiClient.setMode("LIVE");
    });

    it("normalizes 404 endpoint not found into structured ApiError", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: "NOT_FOUND",
              message: "The requested route does not exist",
              request_id: "req-err-404",
            },
          }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        )
      );

      try {
        await apiClient.getGraph("loyalty");
        expect.unreachable("Should have thrown ApiError");
      } catch (err: any) {
        expect(err).toBeInstanceOf(ApiError);
        expect(err.status).toBe(404);
        expect(err.code).toBe("NOT_FOUND");
        expect(err.requestId).toBe("req-err-404");
        expect(err.isNotFound).toBe(true);
        expect(err.isEndpointUnimplemented).toBe(true);
      }
    });

    it("normalizes 409 STALE_APPROVAL with revision conflict details", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: "STALE_APPROVAL",
              message: "Action proposal revision has changed since fetch",
              request_id: "req-err-409",
              details: {
                current_revision: 2,
                current_proposal_hash: "hash-updated-456",
              },
            },
          }),
          { status: 409, headers: { "Content-Type": "application/json" } }
        )
      );

      try {
        await apiClient.approveAction("action-1", {
          expected_revision: 1,
          proposal_hash: "hash-old-123",
          reason: "Approve",
        });
        expect.unreachable("Should have thrown ApiError");
      } catch (err: any) {
        expect(err).toBeInstanceOf(ApiError);
        expect(err.status).toBe(409);
        expect(err.code).toBe("STALE_APPROVAL");
        expect(err.isConflict).toBe(true);
        expect(err.isStaleApproval).toBe(true);
        expect(err.details).toEqual({
          current_revision: 2,
          current_proposal_hash: "hash-updated-456",
        });
      }
    });

    it("normalizes 503 GRAPH_SERVICE_UNAVAILABLE properly", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: "GRAPH_SERVICE_UNAVAILABLE",
              message: "FalkorDB service connection refused",
              request_id: "req-503",
            },
          }),
          { status: 503, headers: { "Content-Type": "application/json" } }
        )
      );

      try {
        await apiClient.getGraph("loyalty");
        expect.unreachable("Should have thrown ApiError");
      } catch (err: any) {
        expect(err).toBeInstanceOf(ApiError);
        expect(err.status).toBe(503);
        expect(err.code).toBe("GRAPH_SERVICE_UNAVAILABLE");
        expect(err.isUnavailable).toBe(true);
      }
    });

    it("normalizes fetch abort/timeout into 504 TIMEOUT_ERROR", async () => {
      const abortError = new Error("The operation was aborted");
      abortError.name = "AbortError";
      vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(abortError);

      try {
        await apiClient.getPromises();
        expect.unreachable("Should have thrown ApiError");
      } catch (err: any) {
        expect(err).toBeInstanceOf(ApiError);
        expect(err.status).toBe(504);
        expect(err.code).toBe("TIMEOUT_ERROR");
        expect(err.isTimeout).toBe(true);
      }
    });
  });

  describe("DEMO Mode Isolation vs LIVE Mode Network Execution", () => {
    it("isolates DEMO mode mutations from LIVE mode network calls", async () => {
      // Step 1: In DEMO mode, approving modifies in-memory state
      apiClient.setMode("DEMO");
      apiClient.setActor("reviewer");
      const demoRes = await apiClient.approveAction("action-reserve-ben", {
        expected_revision: 1,
        proposal_hash:
          "b6a41f8903c719e27c10b490d1829e1f3790184b9012cba8912ef09124018291",
        reason: "Demo approve",
      });
      expect(demoRes.action.status).toBe("APPROVED");

      // Step 2: Switch to LIVE mode, verify it invokes fetch and never reads demo memory
      apiClient.setMode("LIVE");
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            action: {
              id: "action-reserve-ben",
              status: "PROPOSED", // Server returns PROPOSED, completely independent of DEMO memory
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      const liveRes = await apiClient.getAction("action-reserve-ben");
      expect(fetchSpy).toHaveBeenCalledTimes(1);
      expect(liveRes.action.status).toBe("PROPOSED");
    });

    it("notifies subscribers when mode transitions between DEMO and LIVE", () => {
      const listener = vi.fn();
      const unsubscribe = apiClient.subscribe(listener);

      apiClient.setMode("LIVE");
      expect(listener).toHaveBeenCalledWith("LIVE");

      apiClient.setMode("DEMO");
      expect(listener).toHaveBeenCalledWith("DEMO");

      unsubscribe();
      apiClient.setMode("LIVE");
      expect(listener).toHaveBeenCalledTimes(2); // No 3rd call after unsubscribe
    });
  });

  describe("UnavailableStateCard Component", () => {
    it("renders honest 404 endpoint not deployed state without fabricating data", () => {
      render(
        <UnavailableStateCard
          endpoint="POST /api/simulations"
          statusCode={404}
          title="Simulation Engine Unavailable in LIVE Mode"
          message="Simulation execution endpoint is pending backend deployment by Codex (Milestone 2)."
          milestoneStatus="Codex Milestone 2"
        />
      );

      expect(
        screen.getByText("Simulation Engine Unavailable in LIVE Mode")
      ).toBeInTheDocument();
      expect(screen.getByText("POST /api/simulations")).toBeInTheDocument();
      expect(screen.getByText(/HTTP 404/i)).toBeInTheDocument();
      expect(screen.getByText("Codex Milestone 2")).toBeInTheDocument();
      expect(
        screen.getByText(/Simulation execution endpoint is pending backend deployment/i)
      ).toBeInTheDocument();
    });

    it("renders 503 Service Degraded state with retry capability", () => {
      const retryFn = vi.fn();
      render(
        <UnavailableStateCard
          endpoint="GET /api/graph/promise-loyalty"
          statusCode={503}
          errorCode="GRAPH_SERVICE_UNAVAILABLE"
          title="FalkorDB Graph Service Offline"
          message="Graph topology service returned 503."
          onRetry={retryFn}
        />
      );

      expect(screen.getByText("FalkorDB Graph Service Offline")).toBeInTheDocument();
      expect(screen.getByText(/HTTP 503/i)).toBeInTheDocument();
      expect(screen.getByText("Retry Query")).toBeInTheDocument();
    });
  });
});
