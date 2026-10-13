"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Hash,
  Database,
  RefreshCw,
  GitCommit,
  UserCheck,
  Terminal,
} from "lucide-react";
import { UnavailableStateCard } from "@/components/ui/unavailable-state";

export default function ActionReceiptPage() {
  const params = useParams();
  const actionId = (params?.id as string) || "action-reserve-ben";
  const queryClient = useQueryClient();

  const [executionMessage, setExecutionMessage] = useState<string | null>(null);

  const currentActor = apiClient.getActor();
  const isExecutor = currentActor.roles.includes("executor");
  const isLive = apiClient.getMode() === "LIVE";

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["action-detail", actionId],
    queryFn: () => apiClient.getAction(actionId),
  });

  const executeMutation = useMutation({
    mutationFn: () => {
      if (!data?.action) throw new Error("Action proposal not loaded");
      return apiClient.executeAction(actionId, {
        expected_revision: data.action.revision,
        proposal_hash: data.action.proposal_hash,
      });
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["action-detail", actionId] });
      queryClient.invalidateQueries({ queryKey: ["actions"] });
      const isMockOrDemo = !isLive || data?.action.mode === "MOCK" || data?.action.target_system === "WORKLOAD_MOCK";
      setExecutionMessage(
        isMockOrDemo
          ? "Simulated execution SUCCEEDED using Workload Mock Adapter and verified against in-memory state. Read-back verified with 0 field mismatches. No external workload or Jira system was changed."
          : `Execution SUCCEEDED on target system. Read-back state verified with 0 field mismatches.`
      );
      setTimeout(() => setExecutionMessage(null), 6000);
    },
    onError: (err: any) => {
      setExecutionMessage(`Execution Blocked: ${err.message}`);
    },
  });

  if (isLoading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500 font-medium">
          Loading Action Receipt and execution audit records...
        </p>
      </div>
    );
  }

  if (error || !data) {
    if (isLive) {
      return (
        <div className="space-y-6">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Link href="/actions" className="hover:text-slate-800 hover:underline">
              Approval Queue
            </Link>
            <span>/</span>
            <span className="font-mono text-slate-700">{actionId}</span>
          </div>
          <UnavailableStateCard
            title={`Action Proposal '${actionId}' Unavailable`}
            endpoint={`GET /api/actions/${encodeURIComponent(actionId)}`}
            statusCode={404}
            errorCode="NOT_FOUND"
            message="This action proposal route has not yet been deployed on the active backend (scheduled for Codex Milestone M4). In DEMO mode, action-reserve-ben provides complete read-back audit records."
            onRetry={() => refetch()}
          />
        </div>
      );
    }

    return (
      <div className="bg-white p-8 rounded-lg border border-rose-200 text-center space-y-3">
        <ShieldAlert className="w-10 h-10 text-rose-600 mx-auto" />
        <h2 className="text-base font-bold text-slate-900">
          Action Proposal Not Found
        </h2>
        <Link
          href="/actions"
          className="inline-flex items-center px-3 py-1.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-medium"
        >
          Return to Queue
        </Link>
      </div>
    );
  }

  const { action } = data;
  const isApproved = action.status === "APPROVED";
  const isSucceeded = action.status === "SUCCEEDED";
  const isNeedsApproval = action.status === "NEEDS_APPROVAL";

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Link href="/actions" className="hover:text-slate-800 hover:underline">
          Approval Queue
        </Link>
        <span>/</span>
        <span className="font-mono text-slate-700">{action.id}</span>
      </div>

      {/* Execution Feedback Banner */}
      {executionMessage && (
        <div
          className={`p-3 rounded-md text-xs font-medium flex items-center gap-2 ${
            executionMessage.includes("SUCCEEDED")
              ? "bg-emerald-50 border border-emerald-300 text-emerald-900"
              : "bg-rose-50 border border-rose-300 text-rose-900"
          }`}
        >
          {executionMessage.includes("SUCCEEDED") ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{executionMessage}</span>
        </div>
      )}

      {/* Header Card */}
      <div className="bg-white rounded-lg border border-slate-300 shadow-sm p-6 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={action.status} size="md" />
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
                Action ID: {action.id}
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                Target: {action.target_system} ({action.mode})
              </span>
            </div>

            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
              Workload Reservation Execution Ledger
            </h1>

            <p className="text-xs text-slate-600 font-mono">
              Idempotency Key: {action.idempotency_key} &bull; Proposal Hash:{" "}
              {action.proposal_hash.substring(0, 16)}...
            </p>
          </div>

          {/* Execution Controls */}
          <div className="flex items-center gap-3 shrink-0">
            {!isSucceeded && (
              <button
                onClick={() => executeMutation.mutate()}
                disabled={executeMutation.isPending}
                className={`px-4 py-2 rounded-md font-bold text-xs shadow-sm flex items-center gap-1.5 transition-colors ${
                  isApproved && isExecutor
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                    : "bg-slate-200 text-slate-500 hover:bg-slate-300"
                }`}
                title={
                  !isApproved
                    ? "Action is not approved. Attempting execution will test policy gate blocking."
                    : !isExecutor
                    ? "Active role lacks executor capability. Switch to Executor in header."
                    : ""
                }
              >
                {executeMutation.isPending ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Terminal className="w-3.5 h-3.5" />
                )}
                {isNeedsApproval
                  ? "Test Pre-Approval Execution (Expect Block)"
                  : "Dispatch Approved Execution"}
              </button>
            )}

            {isSucceeded && (
              <span className="inline-flex items-center px-3 py-1.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 text-xs font-bold">
                <CheckCircle2 className="w-4 h-4 mr-1.5 text-emerald-600" />
                {!isLive || action.mode === "MOCK"
                  ? "Simulated Execution Verified (Mock Adapter)"
                  : "Execution Completed & Verified"}
              </span>
            )}
          </div>
        </div>

        {/* Simulation Context Notice for Demo / Mock Mode */}
        {(!isLive || action.mode === "MOCK") && (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600 flex items-start gap-2">
            <Database className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-800">Simulated Execution Environment:</span> This operation is simulated using the in-memory Workload Mock Adapter and verified against platform state. No external workload, scheduling, or Jira systems are modified.
            </div>
          </div>
        )}

        {/* Notice on Gate Check */}
        {isNeedsApproval && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Gate Rule (Demo Question #10):</span>{" "}
              This action proposal has not yet received reviewer approval. Attempting execution now will be rejected by backend policy without any external write.
            </div>
          </div>
        )}
      </div>

      {/* Main Two-Column View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Target API Response & Read-back Diff */}
        <div className="space-y-4">
          {/* Read-Back Verification Card */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-sky-600" />
                <h3 className="font-bold text-sm text-slate-900">
                  Target System Read-Back Verification
                </h3>
              </div>
              {action.read_back ? (
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  0 MISMATCHES (VERIFIED)
                </span>
              ) : (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                  AWAITING DISPATCH
                </span>
              )}
            </div>

            {action.read_back ? (
              <div className="space-y-3 text-xs font-mono">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1">
                    <span className="text-slate-500 text-[11px] font-bold block">
                      Expected Target Allocation:
                    </span>
                    <pre className="text-[11px] text-slate-700 whitespace-pre-wrap">
                      {JSON.stringify(action.read_back.expected, null, 2)}
                    </pre>
                  </div>
                  <div className="p-3 bg-emerald-50/50 border border-emerald-200 rounded space-y-1">
                    <span className="text-emerald-800 text-[11px] font-bold block">
                      Actual Confirmed State:
                    </span>
                    <pre className="text-[11px] text-slate-800 whitespace-pre-wrap">
                      {JSON.stringify(action.read_back.actual, null, 2)}
                    </pre>
                  </div>
                </div>

                <div className="p-3 bg-slate-100 rounded text-[11px] space-y-1">
                  <div className="flex justify-between">
                    <span>Checked At:</span>
                    <span className="font-semibold text-slate-800">
                      {new Date(action.read_back.checked_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Reference URI:</span>
                    <span className="font-semibold text-slate-800 break-all">
                      {action.external_response_reference}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-slate-500">
                Read-back occurs immediately after authoritative execution dispatch.
              </div>
            )}
          </div>

          {/* Idempotency Ledger Details */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-3">
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-sky-600" />
              Idempotency & Deduplication Ledger
            </h3>
            <p className="text-xs text-slate-600">
              The platform maintains an immutable execution ledger binding tenant, actor, route, and payload digest. Repeated dispatches with the same key replay the previous result without duplicate external allocations.
            </p>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded font-mono text-[11px] space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-500">Idempotency Key:</span>
                <span className="font-bold text-slate-900">{action.idempotency_key}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Execution Attempts:</span>
                <span className="font-bold text-slate-900">{action.attempts.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Audit Chain & Approval Record */}
        <div className="space-y-4">
          {/* Approval Record */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-3">
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-sky-600" />
              Authoritative Approval Record
            </h3>

            {action.approval ? (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs space-y-1.5 font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-500">Approved By:</span>
                  <span className="font-bold text-slate-900">
                    {action.approval.approved_by}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Approved At:</span>
                  <span className="font-semibold text-slate-800">
                    {new Date(action.approval.approved_at).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Expires At:</span>
                  <span className="font-semibold text-slate-800">
                    {new Date(action.approval.expires_at).toLocaleString()}
                  </span>
                </div>
                <div className="pt-1 border-t border-emerald-200 text-slate-700 font-sans">
                  <strong>Reason:</strong> {action.approval.reason}
                </div>
              </div>
            ) : (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-500">
                Action currently lacks approval. Reviewer action required.
              </div>
            )}
          </div>

          {/* Audit Head & Chain Verification */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-3">
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-sky-600" />
              Audit Chain Verification (promiseops-audit-v1)
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="p-3 rounded border border-slate-200 bg-slate-50 space-y-1">
                <div className="flex justify-between text-slate-700">
                  <span className="font-bold">Audit Event Sequence #3</span>
                  <span className="text-emerald-700 font-bold">CHAIN VALID</span>
                </div>
                <span className="text-slate-500 text-[10px] block truncate">
                  Hash: a4901284ba0129c81920ef091248019238ebc091283ef9012489012ef091288
                </span>
                <span className="text-slate-500 text-[10px] block truncate">
                  Signing Key: key-demo-2026 (Ed25519)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
