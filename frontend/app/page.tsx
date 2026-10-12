"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  AlertTriangle,
  ArrowRight,
  Clock,
  DollarSign,
  FileText,
  HelpCircle,
  Network,
  ShieldAlert,
  ShieldCheck,
  TrendingDown,
  Users,
  CheckCircle2,
  Info,
} from "lucide-react";

export default function OverviewPage() {
  const { data: promisesData, isLoading: promisesLoading } = useQuery({
    queryKey: ["promises"],
    queryFn: () => apiClient.getPromises(),
  });

  const { data: knowledgeData } = useQuery({
    queryKey: ["knowledge"],
    queryFn: () => apiClient.getKnowledgeHealth(),
  });

  const { data: actionsData } = useQuery({
    queryKey: ["actions"],
    queryFn: () => apiClient.getActions(),
  });

  const promises = promisesData?.items || [];
  const proposedPromises = promises.filter((p) => p.current_state === "PROPOSED");
  const unconfirmedCount = proposedPromises.length;
  const highRiskCount = promises.filter((p) =>
    p.risk_flags.some((f) => f.includes("OUT_OF_SCOPE") || f.includes("DEFICIT"))
  ).length;

  return (
    <div className="space-y-6">
      {/* Page Title & Operational Context */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
              Operations Command
            </h1>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-200 text-slate-800">
              Northstar Systems
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Real-time delivery margin protection, scope reconciliation, and PromiseSeal audit head.
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <Link
            href="/promises/promise-loyalty"
            className="inline-flex items-center px-3 py-1.5 rounded-md bg-sky-600 text-white font-medium hover:bg-sky-700 shadow-sm transition-colors"
          >
            Investigate Friday Risk
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Link>
          <Link
            href="/simulations"
            className="inline-flex items-center px-3 py-1.5 rounded-md bg-white border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 transition-colors"
          >
            Open Flight Simulator
          </Link>
        </div>
      </div>

      {/* Primary Operational Question Card (Core Product Outcome) */}
      <div className="bg-white rounded-lg border border-slate-300 shadow-sm p-5 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <span className="inline-flex items-center text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 uppercase tracking-wide">
              <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />
              Active Delivery Decision Alert
            </span>
            <h2 className="text-base font-bold text-slate-900">
              “We promised Acme loyalty integration by Friday. Is it in scope, can we deliver it with available capacity, what is at risk, and what is the safest next action?”
            </h2>
          </div>
          <div className="text-right shrink-0">
            <span className="text-xs font-mono text-slate-500 block">Customer: Acme Retail</span>
            <span className="text-xs font-mono text-slate-500 block">Deadline: Fri 19:00 UTC</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2 border-t border-slate-100">
          <div className="p-3 rounded-md bg-slate-50 border border-slate-200">
            <span className="text-[11px] font-semibold text-slate-500 block uppercase">1. Scope Standing</span>
            <div className="mt-1 flex items-center justify-between">
              <span className="text-xs font-bold text-rose-700">POSSIBLE OUT OF SCOPE</span>
              <Info className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <p className="text-[11px] text-slate-600 mt-1">
              Clause C2 explicitly excludes loyalty. Change Order CO-1 is PROPOSED (unapproved).
            </p>
          </div>

          <div className="p-3 rounded-md bg-slate-50 border border-slate-200">
            <span className="text-[11px] font-semibold text-slate-500 block uppercase">2. Capacity Deficit</span>
            <div className="mt-1 flex items-center justify-between">
              <span className="text-xs font-bold text-rose-700">5-Hour Deficit (F04)</span>
              <TrendingDown className="w-3.5 h-3.5 text-rose-600" />
            </div>
            <p className="text-[11px] text-slate-600 mt-1">
              Task requires 8h; Aria has only 3h free before deadline. Prerequisites blocked.
            </p>
          </div>

          <div className="p-3 rounded-md bg-slate-50 border border-slate-200">
            <span className="text-[11px] font-semibold text-slate-500 block uppercase">3. Exposure at Risk</span>
            <div className="mt-1 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900">USD 40,000 (F02)</span>
              <DollarSign className="w-3.5 h-3.5 text-amber-600" />
            </div>
            <p className="text-[11px] text-slate-600 mt-1">
              Delivery milestone blocked by missing acceptance test and written acceptance.
            </p>
          </div>

          <div className="p-3 rounded-md bg-slate-50 border border-slate-200">
            <span className="text-[11px] font-semibold text-slate-500 block uppercase">4. Recommended Action</span>
            <div className="mt-1 flex items-center justify-between">
              <span className="text-xs font-bold text-sky-700">Reserve Option (F03)</span>
              <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
            </div>
            <p className="text-[11px] text-slate-600 mt-1">
              Reserve Ben&apos;s 5h option ($750). Clarify commitment before customer dispatch.
            </p>
          </div>
        </div>
      </div>

      {/* KPI Grid with Provenance and Formula Links */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <Link
          href="/promises"
          className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:border-slate-300 transition-colors block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-tight">
              Unconfirmed Candidates
            </span>
            <Clock className="w-4 h-4 text-sky-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">{unconfirmedCount}</span>
            <span className="text-xs font-medium text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
              1 Oral Quote
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Oral meeting claims pending reviewer confirmation under PromiseSeal protocol.
          </p>
        </Link>

        {/* Metric 2 */}
        <Link
          href="/promises/promise-loyalty"
          className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:border-slate-300 transition-colors block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-tight">
              Delivery Milestone At Risk
            </span>
            <DollarSign className="w-4 h-4 text-amber-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">USD 40,000</span>
            <span className="text-[10px] font-mono font-semibold text-amber-700 bg-amber-50 px-1 py-0.5 rounded border border-amber-200">
              AT_RISK (F02)
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Milestone blocked until acceptance testing complete. Not a realized loss.
          </p>
        </Link>

        {/* Metric 3 */}
        <Link
          href="/simulations"
          className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:border-slate-300 transition-colors block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-tight">
              Unpriced Integration Work
            </span>
            <FileText className="w-4 h-4 text-slate-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">USD 800</span>
            <span className="text-[10px] font-mono font-semibold text-slate-700 bg-slate-100 px-1 py-0.5 rounded border border-slate-200">
              ESTIMATE (F01)
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            8h task estimate @ Aria $100/hr base rate. Excluded from signed contract.
          </p>
        </Link>

        {/* Metric 4 */}
        <Link
          href="/knowledge"
          className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:border-slate-300 transition-colors block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-tight">
              Knowledge Firewall
            </span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">
              {knowledgeData?.counts.open_findings || 4}
            </span>
            <span className="text-[10px] font-mono font-semibold text-rose-700 bg-rose-50 px-1 py-0.5 rounded border border-rose-200">
              2 QUARANTINED
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            1 orphan task, 1 rejected relation, 1 ambiguous person, 1 stale context.
          </p>
        </Link>
      </div>

      {/* Main Two-Column Layout: Active Risk Radar & Recent PromiseSeal Events */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Promises & Milestones Overview (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Promises Table */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-slate-900">
                  Tracked Commitments & Promises
                </h3>
                <p className="text-xs text-slate-500">
                  Authoritative status from FalkorDB graph assertions
                </p>
              </div>
              <Link
                href="/promises"
                className="text-xs font-medium text-sky-600 hover:text-sky-800 flex items-center gap-1"
              >
                View all ({promises.length})
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-4">Deliverable / Quote</th>
                    <th className="py-2.5 px-3">State</th>
                    <th className="py-2.5 px-3">Scope Status</th>
                    <th className="py-2.5 px-3">Deadline</th>
                    <th className="py-2.5 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-normal">
                  {promisesLoading ? (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-slate-500">
                        Loading verified promises...
                      </td>
                    </tr>
                  ) : (
                    promises.map((promise) => (
                      <tr
                        key={promise.id}
                        className="hover:bg-slate-50/80 transition-colors"
                      >
                        <td className="py-3 px-4 max-w-xs">
                          <Link
                            href={`/promises/${promise.id}`}
                            className="font-medium text-slate-900 hover:text-sky-600 hover:underline block"
                          >
                            {promise.deliverable}
                          </Link>
                          <span className="text-[11px] text-slate-500 font-mono">
                            {promise.customer_name} &bull; v{promise.revision}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <StatusBadge status={promise.current_state} size="sm" />
                        </td>
                        <td className="py-3 px-3">
                          <StatusBadge status={promise.scope_status} size="sm" />
                        </td>
                        <td className="py-3 px-3 font-mono text-[11px] text-slate-600">
                          {promise.deadline?.original_text || "Unspecified"}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link
                            href={`/promises/${promise.id}`}
                            className="inline-flex items-center px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-[11px]"
                          >
                            Receipt
                            <ArrowRight className="w-3 h-3 ml-1" />
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Billing & Milestones Readiness */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-sm text-slate-900">
                  Billing Milestones & Commercial Governance
                </h3>
                <p className="text-xs text-slate-500">
                  Milestone invoicing requires verifiable acceptance evidence, not task completion alone.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500">
                Rule R28 Enforced
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Delivery Milestone */}
              <div className="p-4 rounded-md border border-amber-200 bg-amber-50/30 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">
                    POS System Delivery Milestone
                  </span>
                  <StatusBadge status="AT_RISK" size="sm" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-slate-900">USD 40,000</span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Target: Fri 19:00 UTC
                  </span>
                </div>
                <div className="text-[11px] space-y-1 text-slate-600 border-t border-amber-200/60 pt-2">
                  <div className="flex items-center text-rose-700">
                    <AlertTriangle className="w-3.5 h-3.5 mr-1 shrink-0" />
                    <span>ACME-103 acceptance testing incomplete</span>
                  </div>
                  <div className="flex items-center text-rose-700">
                    <AlertTriangle className="w-3.5 h-3.5 mr-1 shrink-0" />
                    <span>Written customer acceptance missing</span>
                  </div>
                </div>
              </div>

              {/* Kickoff Milestone */}
              <div className="p-4 rounded-md border border-emerald-200 bg-emerald-50/30 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">
                    Kickoff & Provisioning Milestone
                  </span>
                  <StatusBadge status="READY" size="sm" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-slate-900">USD 10,000</span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Completed: 2026-10-09
                  </span>
                </div>
                <div className="text-[11px] space-y-1 text-slate-600 border-t border-emerald-200/60 pt-2">
                  <div className="flex items-center text-emerald-700">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1 shrink-0" />
                    <span>Kickoff minutes signed & verified</span>
                  </div>
                  <div className="flex items-center text-emerald-700">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1 shrink-0" />
                    <span>Ready for billing generation</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Account Context Box */}
            <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600 flex items-start gap-2">
              <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-800">
                  Separate Commercial Account Context:
                </span>{" "}
                Acme Retail renewal opportunity is USD 180,000. Under accounting policy, renewal opportunity is never summed into milestone exposure or cost calculations.
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: PromiseSeal Attestation & Action Pipeline (1 col) */}
        <div className="space-y-6">
          {/* PromiseSeal Verification Card */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-600" />
                <h3 className="font-bold text-sm text-slate-900">
                  PromiseSeal Attestation
                </h3>
              </div>
              <span className="text-[10px] font-mono bg-sky-50 text-sky-700 px-1.5 py-0.5 rounded border border-sky-200">
                v1 ACTIVE
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded bg-slate-50 border border-slate-200 font-mono text-[11px] space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-500">Receipt ID:</span>
                  <span className="font-semibold text-slate-800">receipt-loyalty-v1</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Signing Algorithm:</span>
                  <span className="font-semibold text-slate-800">Ed25519</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Key Identifier:</span>
                  <span className="font-semibold text-slate-800">key-demo-2026</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Payload Digest:</span>
                  <span className="font-semibold text-slate-800 truncate max-w-[120px]">
                    e4f3a748...
                  </span>
                </div>
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-900 text-[11px] space-y-1">
                <div className="font-bold flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Legal / Commercial Distinction
                </div>
                <p className="text-amber-800 leading-relaxed">
                  Cryptographic verification proves payload integrity and service signature. It does not certify speaker authority, customer assent, or contractual enforceability.
                </p>
              </div>

              <Link
                href="/promises/promise-loyalty"
                className="w-full inline-flex items-center justify-center py-2 px-3 rounded-md bg-white border border-slate-300 text-slate-800 font-medium hover:bg-slate-50 transition-colors text-xs"
              >
                Inspect Canonical Receipt & Test Tamper
              </Link>
            </div>
          </div>

          {/* Action Approval Queue Summary */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-sm text-slate-900">
                Approval Queue Status
              </h3>
              <span className="text-xs font-mono font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                1 PENDING
              </span>
            </div>

            <div className="p-3 rounded-md border border-slate-200 bg-slate-50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-slate-900">
                  action-reserve-ben
                </span>
                <StatusBadge status="NEEDS_APPROVAL" size="sm" />
              </div>
              <p className="text-[11px] text-slate-600">
                Reserve Ben Ortiz optional 5-hour Friday slot (09:00–14:00) on Workload Mock adapter.
              </p>
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-1 border-t border-slate-200">
                <span>Cost Ceiling: USD 750</span>
                <span>Role: reviewer</span>
              </div>
            </div>

            <Link
              href="/actions"
              className="w-full inline-flex items-center justify-center py-2 px-3 rounded-md bg-sky-600 text-white font-medium hover:bg-sky-700 transition-colors text-xs"
            >
              Open Approval Queue
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
