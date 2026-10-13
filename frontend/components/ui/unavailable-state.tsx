"use client";

import React from "react";
import { AlertCircle, ServerOff, ArrowRight, RotateCcw, Info } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface UnavailableStateCardProps {
  title: string;
  endpoint: string;
  statusCode?: number;
  errorCode?: string;
  message?: string;
  milestoneStatus?: string;
  onRetry?: () => void;
  compact?: boolean;
}

export function UnavailableStateCard({
  title,
  endpoint,
  statusCode = 404,
  errorCode = "NOT_FOUND",
  message = "This endpoint has not yet been deployed on the active backend.",
  milestoneStatus = "Pending backend implementation",
  onRetry,
  compact = false,
}: UnavailableStateCardProps) {
  const isLive = apiClient.getMode() === "LIVE";

  if (compact) {
    return (
      <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-md text-xs text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-bold">
          <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span>{title} ({errorCode} {statusCode})</span>
        </div>
        <p className="text-[11px] text-amber-800">
          Route <code className="font-mono bg-amber-100 px-1 py-0.2 rounded">{endpoint}</code>: {message}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-slate-300 shadow-sm p-6 space-y-4">
      <div className="flex items-start gap-4">
        <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 shrink-0">
          <ServerOff className="w-6 h-6 text-amber-700" />
        </div>
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-bold text-slate-900">{title}</h3>
            <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
              HTTP {statusCode} &bull; {errorCode}
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              {milestoneStatus}
            </span>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            {message}
          </p>

          <div className="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs font-mono space-y-1 text-slate-700">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Documented Route:</span>
              <span className="font-bold text-slate-900">{endpoint}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Specification:</span>
              <span>docs/API_CONTRACTS.md</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Live Backend State:</span>
              <span className="text-amber-700 font-semibold">Unimplemented by Codex backend</span>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500">
          <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span>
            {isLive
              ? "Switch to DEMO mode in the top banner to inspect full synthetic flows."
              : "Demo fixtures available."}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center px-2.5 py-1.5 rounded-md border border-slate-300 text-slate-700 hover:bg-slate-50 font-medium transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" />
              Retry Query
            </button>
          )}
          {isLive && (
            <button
              onClick={() => {
                apiClient.setMode("DEMO");
                window.location.reload();
              }}
              className="inline-flex items-center px-3 py-1.5 rounded-md bg-sky-600 text-white font-medium hover:bg-sky-700 transition-colors shadow-sm"
            >
              Switch to DEMO Mode
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
