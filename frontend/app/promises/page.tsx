"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Search,
  Filter,
  ArrowUpDown,
  AlertCircle,
  FileQuestion,
  ArrowRight,
  ShieldAlert,
  Clock,
  Sparkles,
  ExternalLink,
  UploadCloud,
  FileUp,
  Plus,
  CheckCircle2,
  X,
  FileText,
} from "lucide-react";
import { PromiseState, PromiseSummary } from "@/types/api";

export default function PromiseInboxPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [customerFilter, setCustomerFilter] = useState<string>("ALL");

  // Source upload modal state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadText, setUploadText] = useState(
    "Meeting with Acme Retail leadership on 2026-10-12:\nWe will deliver the loyalty integration by Friday at no extra charge.\n"
  );
  const [uploadSourceType, setUploadSourceType] = useState<
    "NOTES" | "TRANSCRIPT" | "CONTRACT"
  >("NOTES");
  const [uploadSourceKey, setUploadSourceKey] = useState("meeting-acme-loyalty");
  const [uploadFeedback, setUploadFeedback] = useState<string | null>(null);
  const [inspectedResult, setInspectedResult] = useState<{
    operationId: string;
    sourceId: string;
  } | null>(null);

  // Close upload modal on Escape key
  React.useEffect(() => {
    if (!uploadModalOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setUploadModalOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [uploadModalOpen]);

  const { data: operationData, isLoading: isOperationLoading } = useQuery({
    queryKey: ["operation", inspectedResult?.operationId],
    queryFn: () => apiClient.getOperation(inspectedResult!.operationId),
    enabled: !!inspectedResult,
  });

  const { data: sourceDetailData, isLoading: isSourceLoading } = useQuery({
    queryKey: ["sourceDetail", inspectedResult?.sourceId],
    queryFn: () => apiClient.getSource(inspectedResult!.sourceId),
    enabled: !!inspectedResult,
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      const blob = new Blob([uploadText], { type: "text/plain" });
      return apiClient.uploadSource({
        file: blob,
        filename: "notes.txt",
        sourceType: uploadSourceType,
        accessLabel: "PUBLIC_DEMO",
        sourceKey: uploadSourceKey.trim() || undefined,
      });
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["promises"] });
      setUploadModalOpen(false);
      if ("operation_id" in res) {
        setInspectedResult({
          operationId: res.operation_id,
          sourceId: res.source_id,
        });
      }
      setUploadFeedback(
        `Source document ingested successfully (Operation: ${
          "operation_id" in res ? res.operation_id : "NO_CHANGE"
        }). FalkorDB extracted literal commitment into a signed PROPOSED receipt.`
      );
      setTimeout(() => setUploadFeedback(null), 8000);
    },
    onError: (err: any) => {
      const isForbidden = err?.status === 403 || err?.code === "ROLE_FORBIDDEN";
      setUploadFeedback(
        isForbidden
          ? "Upload rejected (403): Source ingestion requires 'admin' role. Switch persona to Admin in Settings."
          : `Upload failed: ${err.message || "Failed to ingest source"}`
      );
    },
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["promises", statusFilter, customerFilter],
    queryFn: () =>
      apiClient.getPromises({
        status: statusFilter,
        customer_id: customerFilter === "ALL" ? undefined : customerFilter,
      }),
  });

  const allPromises = data?.items || [];

  const filteredPromises = allPromises.filter((p) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchText =
        p.deliverable.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q) ||
        (p.customer_name && p.customer_name.toLowerCase().includes(q));
      if (!matchText) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
              Promise Inbox
            </h1>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-200 text-slate-800">
              {allPromises.length} Tracked Records
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Review proposed meeting promises, contract scope conflicts, and state transitions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setUploadModalOpen(true)}
            className="inline-flex items-center px-3 py-1.5 rounded-md bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs shadow-sm transition-colors"
          >
            <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
            Ingest Source Document
          </button>
        </div>
      </div>

      {uploadFeedback && (
        <div
          className={`p-3 rounded-md text-xs font-medium flex items-center gap-2 ${
            uploadFeedback.includes("failed") || uploadFeedback.includes("rejected")
              ? "bg-rose-50 border border-rose-300 text-rose-900"
              : "bg-emerald-50 border border-emerald-300 text-emerald-900"
          }`}
        >
          {uploadFeedback.includes("failed") || uploadFeedback.includes("rejected") ? (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          )}
          <span>{uploadFeedback}</span>
        </div>
      )}

      {/* Live Ingestion & Extraction Result Inspector */}
      {inspectedResult && (
        <div className="bg-white rounded-lg border border-sky-300 shadow-md p-5 space-y-4 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-sky-600" />
              <div>
                <h3 className="font-bold text-sm text-slate-900">
                  Source Ingestion &amp; Extraction Inspection
                </h3>
                <p className="text-xs text-slate-500 font-mono">
                  Verified outputs from GET /api/operations/{inspectedResult.operationId} &amp; GET /api/sources/{inspectedResult.sourceId}
                </p>
              </div>
            </div>
            <button
              onClick={() => setInspectedResult(null)}
              className="text-slate-400 hover:text-slate-600 p-1 rounded"
              title="Dismiss inspection panel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            {/* Operation info */}
            <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1.5">
              <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider">
                Operation Telemetry
              </span>
              <div className="flex justify-between">
                <span className="text-slate-500">Operation ID:</span>
                <span className="font-semibold text-slate-800">{inspectedResult.operationId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Status:</span>
                <span className="font-bold text-emerald-700">
                  {operationData?.operation.status || "COMPLETED"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Phase:</span>
                <span className="font-semibold text-sky-700">
                  {operationData?.operation.phase || "PUBLISHED"}
                </span>
              </div>
            </div>

            {/* Source info */}
            <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1.5">
              <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider">
                Source Document Projection
              </span>
              <div className="flex justify-between">
                <span className="text-slate-500">Source ID:</span>
                <span className="font-semibold text-slate-800">{inspectedResult.sourceId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Source Type:</span>
                <span className="font-semibold text-slate-800">
                  {sourceDetailData?.source.source_type || "NOTES"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Content SHA-256:</span>
                <span className="text-slate-700 truncate max-w-[180px]">
                  {sourceDetailData?.version.source_hash || "..."}
                </span>
              </div>
            </div>
          </div>

          {/* Snippets / Evidence Quotes */}
          {sourceDetailData?.snippets && sourceDetailData.snippets.length > 0 && (
            <div className="border border-slate-200 rounded p-3 bg-slate-50 space-y-2">
              <span className="text-[11px] font-bold text-slate-700 block font-mono">
                Extracted Commitment Quotations ({sourceDetailData.snippets.length})
              </span>
              <div className="space-y-2">
                {sourceDetailData.snippets.map((snip, idx) => (
                  <div key={idx} className="p-2.5 bg-white border border-slate-200 rounded text-xs space-y-1">
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                      <span>Ref: {snip.evidence_ref_id}</span>
                      <span className="font-bold text-emerald-700">{snip.verification}</span>
                    </div>
                    <p className="italic text-slate-800 font-medium">
                      &ldquo;{snip.quote}&rdquo;
                    </p>
                    {snip.start_offset !== null && snip.end_offset !== null && (
                      <span className="text-[10px] font-mono text-slate-400 block">
                        Character Offsets: {snip.start_offset} - {snip.end_offset}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              aria-label="Search promises by deliverable or ID"
              placeholder="Search deliverable, promise ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-md border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              aria-label="Filter by lifecycle state"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full py-1.5 px-2.5 text-xs rounded-md border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:border-sky-500 font-medium text-slate-700"
            >
              <option value="ALL">All Lifecycle States</option>
              <option value="PROPOSED">PROPOSED (Unconfirmed)</option>
              <option value="NEEDS_REVIEW">NEEDS_REVIEW</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="DISPUTED">DISPUTED</option>
              <option value="SUPERSEDED">SUPERSEDED</option>
              <option value="FULFILLED">FULFILLED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
          </div>

          {/* Customer Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 shrink-0">Customer:</span>
            <select
              aria-label="Filter by customer"
              value={customerFilter}
              onChange={(e) => setCustomerFilter(e.target.value)}
              className="w-full py-1.5 px-2.5 text-xs rounded-md border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:border-sky-500 font-medium text-slate-700"
            >
              <option value="ALL">All Customers</option>
              <option value="customer-acme">Acme Retail (customer-acme)</option>
            </select>
          </div>
        </div>

        {/* Quick Filter Badges */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100 text-[11px]">
          <span className="text-slate-500 font-medium mr-1">Quick Filters:</span>
          <button
            onClick={() => setStatusFilter("PROPOSED")}
            className={`px-2 py-0.5 rounded border transition-colors ${
              statusFilter === "PROPOSED"
                ? "bg-sky-600 text-white border-sky-600 font-semibold"
                : "bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200"
            }`}
          >
            PROPOSED (Needs Confirmation)
          </button>
          <button
            onClick={() => setStatusFilter("DISPUTED")}
            className={`px-2 py-0.5 rounded border transition-colors ${
              statusFilter === "DISPUTED"
                ? "bg-rose-600 text-white border-rose-600 font-semibold"
                : "bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200"
            }`}
          >
            DISPUTED (Contradictory Sources)
          </button>
          <button
            onClick={() => setStatusFilter("CONFIRMED")}
            className={`px-2 py-0.5 rounded border transition-colors ${
              statusFilter === "CONFIRMED"
                ? "bg-emerald-600 text-white border-emerald-600 font-semibold"
                : "bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200"
            }`}
          >
            CONFIRMED
          </button>
          {(statusFilter !== "ALL" || searchQuery || customerFilter !== "ALL") && (
            <button
              onClick={() => {
                setStatusFilter("ALL");
                setSearchQuery("");
                setCustomerFilter("ALL");
              }}
              className="px-2 py-0.5 rounded text-sky-700 hover:underline font-medium ml-auto"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-500 space-y-2">
            <div className="w-6 h-6 border-2 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs">Loading promises from graph ledger...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center space-y-2">
            <AlertCircle className="w-8 h-8 text-rose-600 mx-auto" />
            <h3 className="text-sm font-bold text-slate-900">
              Failed to load promises
            </h3>
            <p className="text-xs text-slate-500">
              {error instanceof Error ? error.message : "Network error"}
            </p>
          </div>
        ) : filteredPromises.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <FileQuestion className="w-10 h-10 text-slate-400 mx-auto" />
            <h3 className="text-sm font-bold text-slate-900">
              No matching promises found
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No records match your current filter parameters. Try clearing your filters or selecting a different lifecycle state.
            </p>
            <button
              onClick={() => {
                setStatusFilter("ALL");
                setSearchQuery("");
                setCustomerFilter("ALL");
              }}
              className="inline-flex items-center px-3 py-1.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Promise & Deliverable</th>
                  <th className="py-3 px-3">State</th>
                  <th className="py-3 px-3">Scope Standing</th>
                  <th className="py-3 px-3">Customer & Project</th>
                  <th className="py-3 px-3">Deadline</th>
                  <th className="py-3 px-3">Freshness</th>
                  <th className="py-3 px-4 text-right">Receipt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPromises.map((promise) => {
                  const isProposed = promise.current_state === "PROPOSED";
                  const isDisputed = promise.current_state === "DISPUTED";

                  return (
                    <tr
                      key={promise.id}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        isProposed
                          ? "bg-sky-50/30"
                          : isDisputed
                          ? "bg-rose-50/30"
                          : ""
                      }`}
                    >
                      <td className="py-3 px-4 max-w-sm">
                        <Link
                          href={`/promises/${promise.id}`}
                          className="font-semibold text-slate-900 hover:text-sky-600 hover:underline block"
                        >
                          {promise.deliverable}
                        </Link>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[11px] font-mono text-slate-500">
                            {promise.id}
                          </span>
                          <span className="text-[11px] font-mono text-slate-400">
                            rev #{promise.revision}
                          </span>
                          {promise.open_conflict_ids.length > 0 && (
                            <span className="inline-flex items-center text-[10px] font-bold text-rose-700 bg-rose-50 px-1 py-0.2 rounded border border-rose-200">
                              <ShieldAlert className="w-3 h-3 mr-0.5" />
                              CONFLICT OPEN
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-3">
                        <StatusBadge status={promise.current_state} size="sm" />
                      </td>

                      <td className="py-3 px-3">
                        <StatusBadge status={promise.scope_status} size="sm" />
                      </td>

                      <td className="py-3 px-3 font-mono text-[11px]">
                        <span className="font-semibold text-slate-800 block">
                          {promise.customer_name || "Acme Retail"}
                        </span>
                        <span className="text-slate-500">{promise.project_id}</span>
                      </td>

                      <td className="py-3 px-3 font-mono text-[11px]">
                        <span className="font-medium text-slate-800 block">
                          {typeof promise.deadline === "string"
                            ? promise.deadline
                            : promise.deadline?.original_text ||
                              promise.deadline?.instant ||
                              "Unresolved"}
                        </span>
                        {typeof promise.deadline === "object" && promise.deadline?.instant && (
                          <span className="text-slate-500 text-[10px]">
                            {new Date(promise.deadline.instant).toLocaleDateString()}
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                            promise.freshness.level === "FRESH"
                              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                              : "bg-amber-50 text-amber-800 border-amber-200"
                          }`}
                        >
                          {promise.freshness.level}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/promises/${promise.id}`}
                          className="inline-flex items-center px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-800 font-medium text-xs transition-colors"
                        >
                          Review Receipt
                          <ArrowRight className="w-3 h-3 ml-1" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Protocol Notice Footer */}
      <div className="p-3 bg-slate-100 border border-slate-200 rounded-md text-xs text-slate-600 flex items-start gap-2">
        <Clock className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-slate-800">
            Lifecycle Transition Rule (PromiseSeal v1 §4):
          </span>{" "}
          Unconfirmed extractions enter as <span className="font-mono font-semibold">PROPOSED</span>. Confirmation requires an authenticated reviewer action and creates an immutable audit event and successor receipt version. An extracted statement is never automatically a confirmed commitment.
        </div>
      </div>

      {/* Ingest Source Document Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg border border-slate-200 shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                  <UploadCloud className="w-4 h-4 text-sky-600" />
                  Ingest Source Document
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Direct live extraction into FalkorDB graph & PromiseSeal proposal
                </p>
              </div>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Source Type
                  </label>
                  <select
                    value={uploadSourceType}
                    onChange={(e) =>
                      setUploadSourceType(
                        e.target.value as "NOTES" | "TRANSCRIPT" | "CONTRACT"
                      )
                    }
                    className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-2.5 bg-white text-slate-800 font-medium focus:outline-none focus:border-sky-500"
                  >
                    <option value="NOTES">Meeting Notes (NOTES)</option>
                    <option value="TRANSCRIPT">Meeting Transcript (TRANSCRIPT)</option>
                    <option value="CONTRACT">Contract Document (CONTRACT)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Source Key / Ref
                  </label>
                  <input
                    type="text"
                    value={uploadSourceKey}
                    onChange={(e) => setUploadSourceKey(e.target.value)}
                    placeholder="e.g. meeting-acme-loyalty"
                    className="w-full text-xs rounded-md border border-slate-300 py-1.5 px-2.5 bg-white text-slate-800 font-medium focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-700">
                    Document Text (contains literal commitment)
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      setUploadText(
                        `Meeting with Acme Retail leadership on 2026-10-12:\nWe will deliver the loyalty integration by Friday at no extra charge.\n`
                      )
                    }
                    className="text-[11px] text-sky-600 hover:text-sky-800 font-medium"
                  >
                    Load Sample
                  </button>
                </div>
                <textarea
                  rows={5}
                  value={uploadText}
                  onChange={(e) => setUploadText(e.target.value)}
                  placeholder="Paste meeting notes or conversation text..."
                  className="w-full text-xs font-mono rounded-md border border-slate-300 p-2.5 bg-slate-50 focus:bg-white text-slate-800 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="p-2.5 rounded-md bg-amber-50 border border-amber-200 text-[11px] text-amber-900 leading-relaxed">
                <span className="font-semibold">Live Integration Note:</span> Uploading invokes the backend&apos;s literal commitment extractor. Extracted commitments are cryptographically signed with the runtime Ed25519 key and entered into the FalkorDB ledger with state <span className="font-mono font-bold">PROPOSED</span>.
              </div>
            </div>

            <div className="px-5 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setUploadModalOpen(false)}
                className="px-3 py-1.5 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={uploadMutation.isPending || !uploadText.trim()}
                onClick={() => uploadMutation.mutate()}
                className="inline-flex items-center px-3.5 py-1.5 rounded-md text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 disabled:opacity-50 transition-colors shadow-sm"
              >
                {uploadMutation.isPending ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin mr-1.5" />
                    Ingesting...
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
                    Ingest &amp; Extract
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
