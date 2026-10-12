"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
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
} from "lucide-react";
import { PromiseState, PromiseSummary } from "@/types/api";

export default function PromiseInboxPage() {
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [customerFilter, setCustomerFilter] = useState<string>("ALL");

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

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-mono">
            Triage Confidence: STRICT EVIDENCE REQUIRED
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
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
                          {promise.deadline?.original_text || "Unresolved"}
                        </span>
                        {promise.deadline?.instant && (
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
    </div>
  );
}
