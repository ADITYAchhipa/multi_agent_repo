"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  HelpCircle,
  FileQuestion,
  Users,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Filter,
} from "lucide-react";
import { KnowledgeFinding } from "@/types/api";
import { UnavailableStateCard } from "@/components/ui/unavailable-state";

export default function KnowledgeHealthPage() {
  const [filterCategory, setFilterCategory] = useState<string>("ALL");
  const isLive = apiClient.getMode() === "LIVE";

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["knowledge"],
    queryFn: () => apiClient.getKnowledgeHealth(),
  });

  const findings = data?.findings || [];
  const counts = data?.counts || {
    nodes: isLive ? 0 : 54,
    edges: isLive ? 0 : 88,
    stale_sources: isLive ? 0 : 1,
    open_conflicts: isLive ? 0 : 1,
    unresolved_promises: isLive ? 0 : 1,
    open_findings: isLive ? 0 : 4,
  };

  const filteredFindings =
    filterCategory === "ALL"
      ? findings
      : findings.filter((f) => f.category === filterCategory);

  const quarantinedFindings = findings.filter(
    (f) => f.status === "QUARANTINED"
  );
  const openFindings = findings.filter((f) => f.status === "OPEN");

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
              Knowledge Health & Firewall
            </h1>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">
              {counts.open_findings} Active Findings
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Graph Quality Firewall gates corrupt entities, unverified quotes, ambiguous duplicates, and ontology violations.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
          <span>Graph Head: {isLive && !data ? "N/A" : `Rev #${data?.graph_revision || 12}`}</span>
          <span>&bull;</span>
          <span>Nodes: {counts.nodes}</span>
          <span>&bull;</span>
          <span>Edges: {counts.edges}</span>
        </div>
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-slate-500 space-y-2 bg-white rounded-lg border border-slate-200 p-8 shadow-sm">
          <div className="w-6 h-6 border-2 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-medium">Loading knowledge health telemetry...</p>
        </div>
      ) : isLive && (error || !data) ? (
        <UnavailableStateCard
          title="Knowledge Firewall Telemetry Unavailable"
          endpoint="GET /api/health/knowledge"
          statusCode={404}
          errorCode="NOT_FOUND"
          message="The Knowledge Health and Graph Quality Firewall route has not yet been deployed on the active backend (scheduled for Codex Milestone M1). In DEMO mode, quarantine monitoring for orphaned nodes, ambiguous entities, and stale sources is fully accessible."
          onRetry={() => refetch()}
        />
      ) : null}

      {!isLoading && (
        <>
          {/* Metric Cards Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-tight">
            Quarantined Records
          </span>
          <div className="text-2xl font-bold text-rose-700">
            {quarantinedFindings.length}
          </div>
          <p className="text-[11px] text-slate-500">
            Isolated outside active query projections.
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-tight">
            Open Conflicts
          </span>
          <div className="text-2xl font-bold text-amber-700">
            {counts.open_conflicts}
          </div>
          <p className="text-[11px] text-slate-500">
            Contradictory source statements requiring review.
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-tight">
            Ambiguous Identity Candidates
          </span>
          <div className="text-2xl font-bold text-slate-900">1</div>
          <p className="text-[11px] text-slate-500">
            Duplicate Person match unmerged without ID.
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-tight">
            Stale Historical Sources
          </span>
          <div className="text-2xl font-bold text-slate-900">
            {counts.stale_sources}
          </div>
          <p className="text-[11px] text-slate-500">
            100-day-old adapter incident context.
          </p>
        </div>
      </div>

      {/* Category Filter Bar */}
      <div className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-sm flex flex-wrap items-center gap-2 text-xs">
        <span className="font-semibold text-slate-600 mr-2">Filter Category:</span>
        <button
          onClick={() => setFilterCategory("ALL")}
          className={`px-2.5 py-1 rounded font-medium transition-colors ${
            filterCategory === "ALL"
              ? "bg-sky-600 text-white font-bold"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          All ({findings.length})
        </button>
        <button
          onClick={() => setFilterCategory("ORPHAN_NODE")}
          className={`px-2.5 py-1 rounded font-medium transition-colors ${
            filterCategory === "ORPHAN_NODE"
              ? "bg-sky-600 text-white font-bold"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Orphan Nodes
        </button>
        <button
          onClick={() => setFilterCategory("UNSUPPORTED_RELATION")}
          className={`px-2.5 py-1 rounded font-medium transition-colors ${
            filterCategory === "UNSUPPORTED_RELATION"
              ? "bg-sky-600 text-white font-bold"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Unsupported Relations
        </button>
        <button
          onClick={() => setFilterCategory("DUPLICATE_CANDIDATE")}
          className={`px-2.5 py-1 rounded font-medium transition-colors ${
            filterCategory === "DUPLICATE_CANDIDATE"
              ? "bg-sky-600 text-white font-bold"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Identity Ambiguities
        </button>
        <button
          onClick={() => setFilterCategory("STALE_SOURCE")}
          className={`px-2.5 py-1 rounded font-medium transition-colors ${
            filterCategory === "STALE_SOURCE"
              ? "bg-sky-600 text-white font-bold"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Stale Sources
        </button>
      </div>

      {/* Quarantine & Findings List */}
      <div className="space-y-4">
        {filteredFindings.map((finding) => {
          const isQuarantined = finding.status === "QUARANTINED";
          return (
            <div
              key={finding.id}
              className={`bg-white rounded-lg border p-5 shadow-sm space-y-3 ${
                isQuarantined ? "border-rose-300" : "border-slate-200"
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${
                        finding.severity === "HIGH"
                          ? "bg-rose-100 text-rose-800"
                          : finding.severity === "MEDIUM"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {finding.severity} SEVERITY
                    </span>
                    <span className="text-[10px] font-mono font-semibold text-slate-500">
                      {finding.category}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      Detected: {new Date(finding.detected_at).toLocaleString()}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-slate-900">
                    {finding.title}
                  </h3>
                </div>

                <StatusBadge status={finding.status} size="sm" />
              </div>

              <p className="text-xs text-slate-700 leading-relaxed">
                {finding.description}
              </p>

              {/* Recommendation Box */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs space-y-1">
                <span className="font-bold text-slate-800 block text-[11px]">
                  Firewall Recommendation:
                </span>
                <p className="text-slate-600 text-[11px] leading-relaxed">
                  {finding.recommendation}
                </p>
              </div>

              {/* Affected Entities */}
              <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500 pt-1 border-t border-slate-100">
                <span>Affected Entity IDs:</span>
                <span className="font-bold text-slate-800">
                  {finding.entity_ids.join(", ")}
                </span>
              </div>
            </div>
          );
        })}
        </div>
        </>
      )}
    </div>
  );
}
