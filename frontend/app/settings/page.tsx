"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatusBadge } from "@/components/ui/status-badge";
import { UnavailableStateCard } from "@/components/ui/unavailable-state";
import {
  Settings,
  Database,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Lock,
  Layers,
  Cpu,
  FileText,
  Server,
  Activity,
} from "lucide-react";
import { ConnectorSummary } from "@/types/api";

export default function SettingsConnectorsPage() {
  const queryClient = useQueryClient();
  const [appMode, setAppMode] = useState<"DEMO" | "LIVE">(apiClient.getMode());
  const [resetStatus, setResetStatus] = useState<string | null>(null);

  useEffect(() => {
    return apiClient.subscribe((nextMode) => {
      setAppMode(nextMode);
    });
  }, []);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["connectors"],
    queryFn: () => apiClient.getConnectors(),
  });

  const connectors = data?.items || [];
  const isLive = appMode === "LIVE";

  const handleToggleMode = () => {
    const next = appMode === "DEMO" ? "LIVE" : "DEMO";
    setAppMode(next);
    apiClient.setMode(next);
    queryClient.invalidateQueries();
  };

  const handleResetData = () => {
    apiClient.resetDemoData();
    setResetStatus("In-memory demo scenario reset to baseline.");
    setTimeout(() => setResetStatus(null), 3000);
    refetch();
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
              Settings & Connectors
            </h1>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-200 text-slate-800">
              System Topology
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Integration health, connector configurations, safe masked parameters, and mode controls.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleToggleMode}
            className={`px-3 py-1.5 rounded-md font-mono text-xs font-bold border transition-colors ${
              appMode === "DEMO"
                ? "bg-slate-900 text-sky-400 border-slate-700 hover:bg-slate-800"
                : "bg-emerald-600 text-white border-emerald-700 hover:bg-emerald-700"
            }`}
          >
            Mode: {appMode} (Click to Switch)
          </button>
        </div>
      </div>

      {resetStatus && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-md text-emerald-900 text-xs flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{resetStatus}</span>
        </div>
      )}

      {/* Security & Credentials Policy Callout */}
      <div className="p-4 bg-slate-100 border border-slate-200 rounded-lg text-xs text-slate-700 flex items-start gap-3">
        <Lock className="w-5 h-5 text-slate-600 shrink-0 mt-0.5" />
        <div className="space-y-1 leading-relaxed">
          <span className="font-bold text-slate-900">
            Secret Sanitization & Zero-Leakage Guarantee:
          </span>
          <p>
            Client applications never receive raw API tokens, server private keys, or internal database credentials. Public client variables (`NEXT_PUBLIC_*`) contain only safe origin URLs. Secret parameters remain strictly server-side.
          </p>
        </div>
      </div>

      {isLive && (error || connectors.length === 0) && (
        <UnavailableStateCard
          title="Connector Registry Telemetry Unavailable"
          endpoint="GET /api/connectors"
          statusCode={404}
          errorCode="NOT_FOUND"
          message="The connector health and telemetry registry route is pending backend deployment (scheduled for Codex Milestone M1). In DEMO mode, adapter statuses for FalkorDB, LLM, Jira, Transcripts, and Workload mock are displayed with safe masked details."
          onRetry={() => refetch()}
        />
      )}

      {/* Connectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {connectors.map((conn) => {
          return (
            <div
              key={conn.id}
              className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4"
            >
              <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                      {conn.type}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                        conn.mode === "MOCK"
                          ? "bg-slate-100 text-slate-700 border-slate-300"
                          : "bg-emerald-50 text-emerald-800 border-emerald-300"
                      }`}
                    >
                      {conn.mode} MODE
                    </span>
                  </div>
                  <h3 className="font-bold text-sm text-slate-900">
                    {conn.title}
                  </h3>
                </div>

                <StatusBadge status={conn.health} size="sm" />
              </div>

              {/* Safe Masked Details */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs font-mono space-y-1.5">
                <span className="font-bold text-slate-700 block text-[11px]">
                  Configured Properties (Safe Masked View):
                </span>
                {Object.entries(conn.safe_details).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-[11px]">
                    <span className="text-slate-500">{k}:</span>
                    <span className="font-semibold text-slate-800">{v}</span>
                  </div>
                ))}
              </div>

              {/* Missing Requirements or Warnings */}
              {conn.missing_configuration_keys.length > 0 ? (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs space-y-1">
                  <span className="font-bold text-amber-900 block text-[11px] flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    Required for Live Execution:
                  </span>
                  <ul className="list-disc list-inside text-amber-800 text-[11px] space-y-0.5">
                    {conn.missing_configuration_keys.map((key, i) => (
                      <li key={i}>{key}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Adapter healthy and verified against local schema.</span>
                </div>
              )}

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-100">
                <span>Write Dispatch: {conn.write_enabled ? "ENABLED" : "DISABLED"}</span>
                <span>Checked: {new Date(conn.checked_at).toLocaleTimeString()}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Demo Scenario Reset Panel */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="font-bold text-sm text-slate-900">
            Reset Demo Scenario State
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Restores in-memory promises, receipts, allocations, and approval states to clean seed baseline.
          </p>
        </div>

        <button
          onClick={handleResetData}
          className="px-3.5 py-2 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs flex items-center gap-1.5 shadow-sm transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Demo State
        </button>
      </div>
    </div>
  );
}
