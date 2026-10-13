"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  CheckSquare,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Hash,
  Database,
  UserCheck,
} from "lucide-react";
import { UnavailableStateCard } from "@/components/ui/unavailable-state";

export default function ApprovalQueuePage() {
  const queryClient = useQueryClient();
  const [selectedActionId, setSelectedActionId] =
    useState<string>("action-reserve-ben");
  const [approvalReason, setApprovalReason] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const currentActor = apiClient.getActor();
  const isReviewer = currentActor.roles.includes("reviewer");
  const isExecutor = currentActor.roles.includes("executor");
  const isLive = apiClient.getMode() === "LIVE";

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["actions"],
    queryFn: () => apiClient.getActions(),
  });

  const actions = data?.items || [];
  const selectedAction =
    actions.find((a) => a.id === selectedActionId) || actions[0];

  const approveMutation = useMutation({
    mutationFn: (actionId: string) => {
      if (!selectedAction) throw new Error("No action selected");
      return apiClient.approveAction(actionId, {
        expected_revision: selectedAction.revision,
        proposal_hash: selectedAction.proposal_hash,
        reason:
          approvalReason || "Approved within delivery policy ceiling ($750)",
      });
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["actions"] });
      setFeedbackMessage(
        `Action '${res.action.id}' successfully APPROVED by ${res.action.approval?.approved_by}. Ready for executor dispatch.`
      );
      setTimeout(() => setFeedbackMessage(null), 5000);
    },
    onError: (err: any) => {
      setFeedbackMessage(`Approval failed: ${err.message}`);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (actionId: string) => {
      if (!selectedAction) throw new Error("No action selected");
      return apiClient.rejectAction(actionId, {
        expected_revision: selectedAction.revision,
        reason: "Rejected by operational reviewer",
      });
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["actions"] });
      setFeedbackMessage(`Action '${res.action.id}' CANCELLED.`);
      setTimeout(() => setFeedbackMessage(null), 5000);
    },
    onError: (err: any) => {
      setFeedbackMessage(`Rejection failed: ${err.message}`);
    },
  });

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
              Approval Queue
            </h1>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-200 text-slate-800">
              Governance Gate (Rule R09)
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Authoritative approval required before external workload or system modifications are dispatched.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="p-2 rounded bg-slate-100 border border-slate-200 font-mono text-slate-700">
            Active Actor: <strong>{currentActor.name}</strong>
          </span>
        </div>
      </div>

      {feedbackMessage && (
        <div className="p-3 bg-sky-50 border border-sky-300 rounded-md text-sky-900 text-xs flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 text-sky-600 shrink-0" />
          <span>{feedbackMessage}</span>
        </div>
      )}

      {/* Role Separation Notice */}
      <div className="p-3 bg-slate-100 border border-slate-200 rounded-md text-xs text-slate-700 flex items-start gap-2">
        <UserCheck className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-bold">Role Separation Policy (Rule R09 / D09):</span>{" "}
          Approver actor must hold the <strong>reviewer</strong> role. An executor cannot self-approve an action proposal. Reviewer approval does not execute the action; a separate executor claim is required to dispatch writes.
        </div>
      </div>

      {isLive && (error || actions.length === 0) && (
        <UnavailableStateCard
          title="Approval Queue Service Unavailable"
          endpoint="GET /api/actions"
          statusCode={404}
          errorCode="NOT_FOUND"
          message="The action proposals and approval queue endpoints have not yet been deployed on the active backend (scheduled for Codex Milestone M4). In DEMO mode, the reserve-ben action proposal workflow is fully interactive."
          onRetry={() => refetch()}
        />
      )}

      {/* Action Items List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Proposals List */}
        <div className="space-y-3">
          <span className="text-xs font-bold text-slate-600 uppercase tracking-wider block">
            Pending Proposals ({actions.length})
          </span>

          {isLoading ? (
            <div className="p-8 text-center text-xs text-slate-500">
              Loading proposals...
            </div>
          ) : (
            actions.map((act) => {
              const isSelected = act.id === selectedActionId;
              return (
                <div
                  key={act.id}
                  role="button"
                  tabIndex={0}
                  aria-pressed={isSelected}
                  aria-label={`Select action ${act.id}`}
                  onClick={() => setSelectedActionId(act.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelectedActionId(act.id);
                    }
                  }}
                  className={`p-4 rounded-lg border cursor-pointer transition-all space-y-2 text-left ${
                    isSelected
                      ? "bg-white border-sky-600 shadow-md ring-1 ring-sky-600"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-slate-900">
                      {act.id}
                    </span>
                    <StatusBadge status={act.status} size="sm" />
                  </div>
                  <p className="text-xs text-slate-700 line-clamp-2">
                    Reserve Ben Ortiz optional 5-hour Friday slot for ACME-101.
                  </p>
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-1 border-t border-slate-100">
                    <span>Target: {act.target_system}</span>
                    <span>Role: {act.required_approval_role}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Column: Deep-Dive Diff & Approval Controls (2 cols) */}
        {selectedAction && (
          <div className="lg:col-span-2 space-y-5">
            <div className="bg-white rounded-lg border border-slate-300 shadow-sm p-6 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-slate-900">
                      {selectedAction.id}
                    </h2>
                    <StatusBadge status={selectedAction.status} size="md" />
                  </div>
                  <span className="text-xs text-slate-500 font-mono mt-0.5 block">
                    Target: {selectedAction.target_system} &bull; Mode:{" "}
                    {selectedAction.mode}
                  </span>
                </div>

                <Link
                  href={`/actions/${selectedAction.id}`}
                  className="inline-flex items-center text-xs font-semibold text-sky-600 hover:underline"
                >
                  View Action Receipt & Audit Head
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Link>
              </div>

              {/* Immutable Binding Hashes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1">
                  <span className="text-slate-500 text-[11px] block">Proposal Hash (SHA-256):</span>
                  <span className="text-slate-900 font-bold break-all select-all text-[11px]">
                    {selectedAction.proposal_hash}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1">
                  <span className="text-slate-500 text-[11px] block">Before State Hash:</span>
                  <span className="text-slate-900 font-bold break-all select-all text-[11px]">
                    {selectedAction.before_state_hash}
                  </span>
                </div>
              </div>

              {/* Before vs After Field Diff */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                  Authoritative Field Diff (Before vs Requested Changes):
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1">
                    <span className="text-slate-500 text-[11px] font-bold block">
                      Before State (Current):
                    </span>
                    <pre className="text-[11px] text-slate-700 whitespace-pre-wrap">
                      {JSON.stringify(selectedAction.before_state, null, 2)}
                    </pre>
                  </div>

                  <div className="p-3 bg-emerald-50/50 border border-emerald-200 rounded space-y-1">
                    <span className="text-emerald-800 text-[11px] font-bold block">
                      Requested Changes (Target):
                    </span>
                    <pre className="text-[11px] text-slate-800 whitespace-pre-wrap">
                      {JSON.stringify(selectedAction.requested_changes, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Policy Checks & Auditor Verdict */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                  Policy Checks & Auditor Verdict:
                </span>
                <div className="space-y-2">
                  {selectedAction.policy_checks.map((check) => (
                    <div
                      key={check.rule_id}
                      className="p-3 rounded border border-slate-200 bg-slate-50 flex items-center justify-between text-xs"
                    >
                      <div className="space-y-0.5">
                        <span className="font-mono font-bold text-slate-900 block">
                          {check.rule_id}
                        </span>
                        <span className="text-slate-600 text-[11px]">
                          {check.reason}
                        </span>
                      </div>
                      <span className="font-mono font-bold text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                        {check.outcome}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Approval Controls */}
              <div className="pt-4 border-t border-slate-200 space-y-3">
                {selectedAction.status === "NEEDS_APPROVAL" && (
                  <>
                    <div>
                      <label htmlFor="approval-reason-input" className="text-xs font-bold text-slate-800 block mb-1">
                        Approval Reason & Operational Authorization:
                      </label>
                      <input
                        id="approval-reason-input"
                        type="text"
                        value={approvalReason}
                        onChange={(e) => setApprovalReason(e.target.value)}
                        placeholder="e.g. Approved within delivery policy capacity ceiling ($750)"
                        className="w-full p-2 text-xs rounded border border-slate-300 focus:outline-none focus:border-sky-500 font-sans"
                      />
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        onClick={() => approveMutation.mutate(selectedAction.id)}
                        disabled={!isReviewer || approveMutation.isPending}
                        className={`px-4 py-2 rounded-md font-bold text-xs shadow-sm flex items-center gap-1.5 transition-colors ${
                          isReviewer
                            ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                            : "bg-slate-200 text-slate-400 cursor-not-allowed"
                        }`}
                        title={
                          !isReviewer
                            ? "Current active role lacks 'reviewer' capability required to approve."
                            : ""
                        }
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        {approveMutation.isPending
                          ? "Approving..."
                          : "Approve Action Proposal"}
                      </button>

                      <button
                        onClick={() => rejectMutation.mutate(selectedAction.id)}
                        disabled={!isReviewer || rejectMutation.isPending}
                        className="px-3 py-2 rounded-md border border-rose-300 text-rose-700 hover:bg-rose-50 text-xs font-semibold"
                      >
                        Reject / Cancel
                      </button>

                      {!isReviewer && (
                        <span className="text-[11px] text-amber-800 bg-amber-50 px-2 py-1 rounded border border-amber-200">
                          Controls disabled: switch to <strong>Reviewer</strong> role in header to approve.
                        </span>
                      )}
                    </div>
                  </>
                )}

                {selectedAction.status === "APPROVED" && (
                  <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-md flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold text-emerald-900 block">
                        Action Approved by {selectedAction.approval?.approved_by}
                      </span>
                      <span className="text-[11px] text-emerald-700">
                        Expires in 15 minutes. Ready for operations executor claim.
                      </span>
                    </div>

                    <Link
                      href={`/actions/${selectedAction.id}`}
                      className="px-4 py-2 rounded-md bg-emerald-600 text-white font-bold text-xs shadow-sm hover:bg-emerald-700"
                    >
                      Proceed to Execution & Read-back
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
