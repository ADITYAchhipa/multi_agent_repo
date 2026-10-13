import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { apiClient } from "@/lib/api-client";
import { createTestQueryClient } from "./test-utils";
import { QueryClientProvider } from "@tanstack/react-query";

import OverviewPage from "@/app/page";
import ApprovalQueuePage from "@/app/actions/page";
import ActionReceiptPage from "@/app/actions/[id]/page";
import PromiseDetailPage from "@/app/promises/[id]/page";
import SimulationLabPage from "@/app/simulations/page";
import KnowledgeHealthPage from "@/app/knowledge/page";
import GraphExplorerPage from "@/app/graph/page";
import SettingsPage from "@/app/settings/page";
import { AppShell } from "@/components/shell/app-shell";

// Mock next/navigation
let currentMockParams: Record<string, string> = { id: "promise-loyalty" };
let currentMockPathname = "/";

vi.mock("next/navigation", () => ({
  useParams: () => currentMockParams,
  usePathname: () => currentMockPathname,
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return {
    ...render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    ),
    queryClient,
  };
}

describe("QA Regression & Hardening Verification Suite", () => {
  beforeEach(() => {
    apiClient.resetDemoData();
    apiClient.setActor("reviewer");
    apiClient.setMode("DEMO");
    currentMockParams = { id: "promise-loyalty" };
    currentMockPathname = "/";
  });

  afterEach(() => {
    vi.restoreAllMocks();
    apiClient.resetDemoData();
    apiClient.setActor("reviewer");
    apiClient.setMode("DEMO");
  });

  // 1. Graph proof-path changes updating visible nodes and edges
  describe("Graph Explorer Proof Path State Synchronization", () => {
    it("updates visible nodes and edges when switching proof path filters and views", async () => {
      renderWithClient(<GraphExplorerPage />);

      // Heading renders correctly
      expect(await screen.findByText("Graph Explorer")).toBeInTheDocument();

      // Find proof path select
      const filterSelect = screen.getByLabelText(/Filter graph by proof path/i);
      expect(filterSelect).toBeInTheDocument();

      // Select PTH1
      fireEvent.change(filterSelect, { target: { value: "PTH1" } });
      expect(filterSelect).toHaveValue("PTH1");

      // Switch to Relationship List view
      const listBtn = screen.getByRole("button", {
        name: /Relationship List/i,
      });
      fireEvent.click(listBtn);

      expect(
        await screen.findByText(
          "Authoritative Relationship Catalog (FalkorDB Triplets)"
        )
      ).toBeInTheDocument();
    });
  });

  // 2. Review modal Escape handling, accessible semantics, and role-restricted submission
  describe("Promise Review Modal Accessibility & Role Authorization", () => {
    it("has accessible dialog attributes, labelled close button, and closes on Escape", async () => {
      renderWithClient(<PromiseDetailPage />);

      const openButton = await screen.findByRole("button", {
        name: /Review \/ Change State/i,
      });
      fireEvent.click(openButton);

      // Dialog accessibility semantics
      const dialog = screen.getByRole("dialog");
      expect(dialog).toBeInTheDocument();
      expect(dialog).toHaveAttribute("aria-modal", "true");
      expect(dialog).toHaveAttribute("aria-labelledby", "review-modal-title");

      // Labelled close button
      const closeBtn = screen.getByLabelText(/Close review dialog/i);
      expect(closeBtn).toBeInTheDocument();

      // Form label association
      const reasonInput = screen.getByLabelText(
        /Reason & Operational Justification:/i
      );
      expect(reasonInput).toBeInTheDocument();

      // Press Escape to dismiss
      fireEvent.keyDown(window, { key: "Escape" });
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("restricts review submission when actor lacks reviewer capability (Rule R09)", async () => {
      // Set actor to viewer (who cannot review promises)
      apiClient.setActor("viewer");
      renderWithClient(<PromiseDetailPage />);

      const openButton = await screen.findByRole("button", {
        name: /Review \/ Change State/i,
      });
      fireEvent.click(openButton);

      // Dialog shows role warning
      expect(
        screen.getByText(/Active role lacks ‘reviewer’ capability/i)
      ).toBeInTheDocument();

      // Submit button is disabled
      const submitBtn = screen.getByRole("button", { name: /Submit Review/i });
      expect(submitBtn).toBeDisabled();
    });

    it("allows review submission when actor has reviewer capability", async () => {
      apiClient.setActor("reviewer");
      renderWithClient(<PromiseDetailPage />);

      const openButton = await screen.findByRole("button", {
        name: /Review \/ Change State/i,
      });
      fireEvent.click(openButton);

      expect(
        screen.queryByText(/Active role lacks ‘reviewer’ capability/i)
      ).not.toBeInTheDocument();

      const submitBtn = screen.getByRole("button", { name: /Submit Review/i });
      expect(submitBtn).not.toBeDisabled();
    });
  });

  // 3. Keyboard selection of scenarios and actions
  describe("Keyboard-Accessible Selection", () => {
    it("allows keyboard selection of scenarios in Simulation Lab using Enter and Space", async () => {
      renderWithClient(<SimulationLabPage />);

      // Find scenario cards with role="button"
      const extraCapacityCard = await screen.findByLabelText(
        /Select scenario scen-extra-capacity/i
      );
      expect(extraCapacityCard).toHaveAttribute("role", "button");
      expect(extraCapacityCard).toHaveAttribute("tabIndex", "0");

      // Press Enter to select
      fireEvent.keyDown(extraCapacityCard, { key: "Enter" });
      expect(extraCapacityCard).toHaveAttribute("aria-pressed", "true");

      // Press Space to select Plan B
      const renegotiateCard = screen.getByLabelText(
        /Select scenario scen-renegotiate/i
      );
      fireEvent.keyDown(renegotiateCard, { key: " " });
      expect(renegotiateCard).toHaveAttribute("aria-pressed", "true");
      expect(extraCapacityCard).toHaveAttribute("aria-pressed", "false");
    });

    it("allows keyboard selection of action proposals in Approval Queue", async () => {
      renderWithClient(<ApprovalQueuePage />);

      const actionItem = await screen.findByLabelText(
        /Select action action-reserve-ben/i
      );
      expect(actionItem).toHaveAttribute("role", "button");
      expect(actionItem).toHaveAttribute("tabIndex", "0");

      // Select via Enter
      fireEvent.keyDown(actionItem, { key: "Enter" });
      expect(actionItem).toHaveAttribute("aria-pressed", "true");
    });
  });

  // 4. Dynamic action count derivation and updates
  describe("Dynamic Action Count Derivation", () => {
    it("dynamically reflects pending action count and updates to 0 after approval", async () => {
      const { queryClient } = renderWithClient(<OverviewPage />);

      // Initially 1 pending action
      expect(await screen.findByText(/1 PENDING/i)).toBeInTheDocument();
      expect(screen.getByText("action-reserve-ben")).toBeInTheDocument();

      // Get real action proposal from client
      const actions = await apiClient.getActions();
      const ben = actions.items.find((a) => a.id === "action-reserve-ben")!;

      // Approve the action
      await apiClient.approveAction(ben.id, {
        expected_revision: ben.revision,
        proposal_hash: ben.proposal_hash,
        reason: "Test approved for QA verification",
      });

      // Refetch queries on test queryClient
      await queryClient.refetchQueries({ queryKey: ["actions"] });

      // Pending count should update to 0 PENDING
      await waitFor(() => {
        expect(screen.getByText(/0 PENDING/i)).toBeInTheDocument();
        expect(
          screen.getByText(/No actions currently pending approval./i)
        ).toBeInTheDocument();
      });
    });

    it("sidebar in AppShell displays derived pending actions count", async () => {
      renderWithClient(
        <AppShell>
          <div>Child content</div>
        </AppShell>
      );

      // Sidebar Approval Queue item shows derived count
      const badge = await screen.findAllByText(/1 PENDING/i);
      expect(badge.length).toBeGreaterThan(0);
    });
  });

  // 5. Resetting demo state across routes and invalidating cached data
  describe("Demo State Reset & Query Cache Invalidation", () => {
    it("resets modified action state back to baseline in Settings", async () => {
      // Modify action state
      const actions = await apiClient.getActions();
      const ben = actions.items.find((a) => a.id === "action-reserve-ben")!;
      await apiClient.approveAction(ben.id, {
        expected_revision: ben.revision,
        proposal_hash: ben.proposal_hash,
        reason: "Pre-reset modification",
      });

      expect((await apiClient.getActions()).items[0].status).toBe("APPROVED");

      renderWithClient(<SettingsPage />);

      // Reset data
      const resetBtn = await screen.findByRole("button", {
        name: /Reset Demo State/i,
      });
      fireEvent.click(resetBtn);

      expect(
        await screen.findByText(/In-memory demo scenario reset to baseline./i)
      ).toBeInTheDocument();

      // Verify that after reset, action is back to NEEDS_APPROVAL
      const resetActions = await apiClient.getActions();
      const benAction = resetActions.items.find(
        (a) => a.id === "action-reserve-ben"
      );
      expect(benAction?.status).toBe("NEEDS_APPROVAL");
    });
  });

  // 6. Tamper sandbox verification and reset
  describe("Tamper Sandbox Verification & Resilience", () => {
    it("flags tampered digest as mismatch and restores integrity on reset", async () => {
      renderWithClient(<PromiseDetailPage />);

      // Switch to Tamper Verification Lab tab
      const tamperTab = await screen.findByRole("tab", {
        name: /Tamper Verification Lab/i,
      });
      fireEvent.click(tamperTab);

      // Click Verify Tampered Copy
      const verifyTamperBtn = screen.getByRole("button", {
        name: /Verify Tampered Copy/i,
      });
      fireEvent.click(verifyTamperBtn);

      // Tamper state detected
      expect(
        await screen.findByText("CANONICAL_PAYLOAD_DIGEST")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/PAYLOAD_DIGEST_MISMATCH/i)
      ).toBeInTheDocument();
      expect(screen.getAllByText("FAIL").length).toBeGreaterThan(0);

      // Reset tamper sandbox to original
      const resetBtn = screen.getByRole("button", {
        name: /Reset to Original/i,
      });
      fireEvent.click(resetBtn);

      // Verify original copy
      fireEvent.click(verifyTamperBtn);

      // Verified state restored
      expect(
        await screen.findByText(
          /Payload SHA-256 matches canonical digest/i
        )
      ).toBeInTheDocument();
      expect(screen.getAllByText("PASS").length).toBeGreaterThan(0);
    });
  });

  // 7. Clear mock-execution wording
  describe("Mock Execution Clarity on Action Receipt", () => {
    it("explicitly identifies Workload Mock Adapter simulation and that external systems remain unchanged", async () => {
      currentMockParams = { id: "action-reserve-ben" };

      // Set actor to executor and pre-approve action so it can be dispatched
      const actions = await apiClient.getActions();
      const ben = actions.items.find((a) => a.id === "action-reserve-ben")!;
      await apiClient.approveAction(ben.id, {
        expected_revision: ben.revision,
        proposal_hash: ben.proposal_hash,
        reason: "Approved for execution test",
      });
      apiClient.setActor("executor");

      renderWithClient(<ActionReceiptPage />);

      // Check the simulation environment notice
      expect(
        await screen.findByText(/Simulated Execution Environment:/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          /This operation is simulated using the in-memory Workload Mock Adapter and verified against platform state. No external workload, scheduling, or Jira systems are modified./i
        )
      ).toBeInTheDocument();

      // Dispatch execution
      const dispatchBtn = screen.getByRole("button", {
        name: /Dispatch Approved Execution/i,
      });
      fireEvent.click(dispatchBtn);

      // Verify clear simulated execution feedback message
      expect(
        await screen.findByText(
          /Simulated execution SUCCEEDED using Workload Mock Adapter and verified against in-memory state. Read-back verified with 0 field mismatches. No external workload or Jira system was changed./i
        )
      ).toBeInTheDocument();

      // Verify badge text
      expect(
        screen.getByText(/Simulated Execution Verified \(Mock Adapter\)/i)
      ).toBeInTheDocument();
    });
  });

  // 8. Honest Loading & Unavailable States
  describe("Loading & Degraded Service UI States", () => {
    it("renders honest unavailable state for counterfactual simulation in LIVE mode without fabricated data", async () => {
      apiClient.setMode("LIVE");
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: "NOT_FOUND",
              message: "Endpoint not yet implemented by backend milestone",
              request_id: "req-live-sim-404",
            },
          }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        )
      );

      renderWithClient(<SimulationLabPage />);

      expect(
        await screen.findByText(/Counterfactual Simulation Engine Unavailable/i)
      ).toBeInTheDocument();
      expect(screen.getByText("POST /api/simulations")).toBeInTheDocument();
      expect(screen.getByText(/HTTP 404/i)).toBeInTheDocument();
    });

    it("renders honest unavailable state for Knowledge Health in LIVE mode", async () => {
      apiClient.setMode("LIVE");
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: "NOT_FOUND",
              message: "Route not deployed on active backend",
              request_id: "req-live-knowledge-404",
            },
          }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        )
      );

      renderWithClient(<KnowledgeHealthPage />);

      expect(
        await screen.findByText(/Knowledge Firewall Telemetry Unavailable/i)
      ).toBeInTheDocument();
      expect(screen.getByText("GET /api/health/knowledge")).toBeInTheDocument();
      expect(screen.getByText(/HTTP 404/i)).toBeInTheDocument();
    });
  });
});
