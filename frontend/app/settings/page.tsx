"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, DEMO_CREDENTIALS } from "@/lib/api-client";
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
  UserCheck,
  RefreshCw,
  KeyRound,
  Hash,
  AlertCircle,
} from "lucide-react";
import { ConnectorSummary, SessionInfo, AuditVerifyResponse } from "@/types/api";

export default function SettingsConnectorsPage() {
  const queryClient = useQueryClient();
  const [appMode, setAppMode] = useState<"DEMO" | "LIVE">(apiClient.getMode());
  const [resetStatus, setResetStatus] = useState<string | null>(null);
  const [authFeedback, setAuthFeedback] = useState<string | null>(null);

  useEffect(() => {
    return apiClient.subscribe((nextMode) => {
      setAppMode(nextMode);
    });
  }, []);

  const { data: sessionData, isLoading: isSessionLoading, refetch: refetchSession } = useQuery({
    queryKey: ["session", appMode],
    queryFn: () => apiClient.getSession(),
  });

  const switchRoleMutation = useMutation({
    mutationFn: async (role: "admin" | "reviewer" | "executor" | "viewer") => {
      if (appMode === "LIVE") {
        const cred = DEMO_CREDENTIALS[role];
        const res = await apiClient.bootstrapSession(cred);
        apiClient.setActor(role);
        return res;
      } else {
        apiClient.setActor(role);
        return apiClient.getSession();
      }
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries();
      setAuthFeedback(`Authenticated as ${res.actor.id} (${res.actor.roles.join(", ")})`);
      setTimeout(() => setAuthFeedback(null), 4000);
    },
    onError: (err: any) => {
      setAuthFeedback(`Auth error: ${err.message || "Failed to switch identity"}`);
    },
  });

  const {
    data: auditData,
    isLoading: isAuditLoading,
    error: auditError,
    refetch: refetchAudit,
  } = useQuery({
    queryKey: ["auditVerify", appMode],
    queryFn: () => apiClient.getAuditVerification(),
    enabled: appMode === "LIVE",
  });

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
    queryClient.invalidateQueries();
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
              Settings &amp; Connectors
            </h1>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-200 text-slate-800">
              System Topology
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Integration health, cryptographic audit chain, session authentication, and mode controls.
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

      {authFeedback && (
        <div
          className={`p-3 rounded-md text-xs flex items-center gap-2 font-medium ${
            authFeedback.includes("error")
              ? "bg-rose-50 border border-rose-300 text-rose-900"
              : "bg-emerald-50 border border-emerald-300 text-emerald-900"
          }`}
        >
          {authFeedback.includes("error") ? (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          )}
          <span>{authFeedback}</span>
        </div>
      )}

      {/* Live Session & Identity Card */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-sky-600" />
              Active Session &amp; Identity Bootstrap
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              PromiseSeal actor identity, role authorizations, and authenticated session state
            </p>
          </div>
          <button
            onClick={() => refetchSession()}
            className="inline-flex items-center text-xs text-slate-600 hover:text-slate-900 border border-slate-200 hover:bg-slate-50 px-2 py-1 rounded"
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            Refresh Session
          </button>
        </div>

        {isSessionLoading ? (
          <div className="py-4 text-center text-xs text-slate-500">
            Checking session info...
          </div>
        ) : sessionData ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Actor ID:</span>
                <span className="font-semibold text-slate-800">{sessionData.actor.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Name / Description:</span>
                <span className="font-semibold text-slate-800">{sessionData.actor.name || "Default Actor"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Roles Granted:</span>
                <span className="font-bold text-emerald-700">{sessionData.actor.roles.join(", ")}</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Tenant ID:</span>
                <span className="font-semibold text-slate-800">{sessionData.tenant_id || "tenant-demo"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Session Mode:</span>
                <span className="font-bold text-sky-700">{sessionData.mode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Expires At:</span>
                <span className="text-slate-700">{new Date(sessionData.expires_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
        ) : null}

        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-600 font-semibold mr-1">Switch Persona (Live Cookie Bootstrap):</span>
          {(["reviewer", "admin", "executor", "viewer"] as const).map((role) => {
            const isSelected = sessionData?.actor.id?.includes(role) || sessionData?.actor.roles.includes(role);
            return (
              <button
                key={role}
                disabled={switchRoleMutation.isPending}
                onClick={() => switchRoleMutation.mutate(role)}
                className={`px-2.5 py-1 text-xs rounded border transition-colors capitalize ${
                  isSelected
                    ? "bg-sky-600 text-white border-sky-600 font-bold"
                    : "bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300"
                }`}
              >
                {role}
              </button>
            );
          })}
        </div>
      </div>

      {/* Live Cryptographic Audit Chain Verification Card */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Cryptographic Audit Chain Verification (PromiseSeal v1 §5)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Verifies immutable SHA-256 hash chaining and Ed25519 signatures across the entire audit log
            </p>
          </div>
          {isLive && (
            <button
              onClick={() => refetchAudit()}
              disabled={isAuditLoading}
              className="inline-flex items-center text-xs text-sky-600 hover:text-sky-800 border border-sky-200 hover:bg-sky-50 px-2.5 py-1 rounded font-medium"
            >
              <RefreshCw className={`w-3 h-3 mr-1 ${isAuditLoading ? "animate-spin" : ""}`} />
              Re-verify Chain
            </button>
          )}
        </div>

        {isLive ? (
          isAuditLoading ? (
            <div className="py-6 text-center text-xs text-slate-500 space-y-2">
              <div className="w-5 h-5 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto" />
              <p>Traversing audit ledger and verifying SHA-256 sequence integrity...</p>
            </div>
          ) : auditError ? (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800">
              Audit verification query failed: {auditError instanceof Error ? auditError.message : "Error"}
            </div>
          ) : auditData ? (
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded font-mono text-xs">
                  <span className="text-slate-500 block text-[11px]">Chain Result</span>
                  <span
                    className={`text-sm font-bold inline-flex items-center gap-1 mt-1 ${
                      auditData.chain_result === "VALID"
                        ? "text-emerald-700"
                        : "text-rose-700"
                    }`}
                  >
                    <ShieldCheck className="w-4 h-4" />
                    {auditData.chain_result}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded font-mono text-xs">
                  <span className="text-slate-500 block text-[11px]">Sequences Verified</span>
                  <span className="text-sm font-bold text-slate-800 mt-1 block">
                    #{auditData.checked_range.from_sequence} &rarr; #{auditData.checked_range.to_sequence}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded font-mono text-xs">
                  <span className="text-slate-500 block text-[11px]">Checkpoint Status</span>
                  <span className="text-sm font-bold text-slate-800 mt-1 block">
                    {auditData.checkpoint.available ? "Available & Trusted" : "Rolling Sequence Check"}
                  </span>
                </div>
              </div>

              {auditData.checks && auditData.checks.length > 0 && (
                <div className="border border-slate-200 rounded overflow-hidden">
                  <div className="bg-slate-50 px-3 py-1.5 border-b border-slate-200 text-[11px] font-semibold text-slate-600 uppercase font-mono">
                    Audit Checks ({auditData.checks.length} entries)
                  </div>
                  <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs font-mono">
                    {auditData.checks.map((chk, i) => (
                      <div key={i} className="px-3 py-2 flex items-center justify-between hover:bg-slate-50">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400">Seq #{chk.sequence}</span>
                          <span className="font-bold text-slate-800">{chk.code}</span>
                          {chk.actor_id && (
                            <span className="text-slate-500 text-[11px]">by {chk.actor_id}</span>
                          )}
                        </div>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            chk.result === "PASS" || chk.result === "VALID"
                              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                              : "bg-rose-50 text-rose-800 border border-rose-200"
                          }`}
                        >
                          {chk.result}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null
        ) : (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600 space-y-1">
            <p className="font-semibold text-slate-800">
              DEMO Mode — Simulated Audit Log
            </p>
            <p>
              Switch to <span className="font-bold text-emerald-700">LIVE</span> mode to execute real cryptographic hash chain validation against the backend&apos;s FalkorDB audit ledger via <code className="font-mono bg-slate-200 px-1 py-0.5 rounded">GET /api/audit/verify</code>.
            </p>
          </div>
        )}
      </div>

      {/* Security &amp; Credentials Policy Callout */}
      <div className="p-4 bg-slate-100 border border-slate-200 rounded-lg text-xs text-slate-700 flex items-start gap-3">
        <Lock className="w-5 h-5 text-slate-600 shrink-0 mt-0.5" />
        <div className="space-y-1 leading-relaxed">
          <span className="font-bold text-slate-900">
            Secret Sanitization &amp; Zero-Leakage Guarantee:
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
