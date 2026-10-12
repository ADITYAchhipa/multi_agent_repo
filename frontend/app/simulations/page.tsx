"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  FlaskConical,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  Calendar,
  Layers,
  HelpCircle,
} from "lucide-react";
import { ScenarioResult } from "@/types/api";

export default function SimulationLabPage() {
  const [selectedScenarioId, setSelectedScenarioId] =
    useState<string>("scen-extra-capacity");

  const { data, isLoading } = useQuery({
    queryKey: ["simulations"],
    queryFn: () => apiClient.getSimulations(),
  });

  const scenarios = data?.results || [];
  const selectedScenario =
    scenarios.find((s) => s.id === selectedScenarioId) || scenarios[0];

  return (
    <div className="space-y-6">
      {/* Page Title & Context */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
              Simulation Lab / Flight Simulator
            </h1>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-200 text-slate-800">
              Counterfactual Planner
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Compare delivery options, capacity allocations, costs, and exposure without altering live systems.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded bg-amber-50 text-amber-900 border border-amber-200 font-mono">
            HYPOTHETICAL SANDBOX — LIVE GRAPH UNCHANGED
          </span>
        </div>
      </div>

      {/* Scenario Comparison Cards (3 Columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {scenarios.map((scenario) => {
          const isSelected = scenario.id === selectedScenarioId;
          const isAsRequested = scenario.type === "AS_REQUESTED";
          const isRenegotiate = scenario.type === "RENEGOTIATE_DATE_OR_SCOPE";
          const isExtraCapacity = scenario.type === "CHANGE_ORDER_OR_EXTRA_CAPACITY";

          return (
            <div
              key={scenario.id}
              onClick={() => setSelectedScenarioId(scenario.id)}
              className={`rounded-lg border p-5 cursor-pointer transition-all space-y-4 ${
                isSelected
                  ? "bg-white border-sky-600 shadow-md ring-1 ring-sky-600"
                  : "bg-white/80 border-slate-200 hover:border-slate-300 shadow-sm"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 block">
                    Scenario {scenario.id}
                  </span>
                  <h3 className="font-bold text-sm text-slate-900 mt-0.5">
                    {isAsRequested
                      ? "Plan A: As Requested (Friday 19:00)"
                      : isRenegotiate
                      ? "Plan B: Renegotiate to Monday"
                      : "Plan C: Add Internal Capacity (Ben 5h)"}
                  </h3>
                </div>
                <StatusBadge status={scenario.feasibility} size="sm" />
              </div>

              {/* High-level Feasibility Verdict */}
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs">
                {isAsRequested ? (
                  <p className="text-rose-700 font-medium leading-relaxed">
                    <strong>Infeasible:</strong> 5-hour capacity deficit before Friday deadline. Prerequisite ACME-102 blocked.
                  </p>
                ) : isRenegotiate ? (
                  <p className="text-amber-800 font-medium leading-relaxed">
                    <strong>Conditionally Feasible:</strong> Requires customer written agreement to shift date to Monday 16:00.
                  </p>
                ) : (
                  <p className="text-emerald-800 font-medium leading-relaxed">
                    <strong>Feasible & Authorizable:</strong> Ben 5h ($750) + Aria 3h fits before Friday deadline. Within reviewer authority.
                  </p>
                )}
              </div>

              {/* Calculations and Arithmetic */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 bg-slate-50 rounded border border-slate-200">
                  <span className="text-slate-500 text-[10px] block">Incremental Cost</span>
                  <span className="font-bold text-slate-900">
                    {isExtraCapacity ? "+USD 750 (F03)" : "USD 0"}
                  </span>
                </div>
                <div className="p-2 bg-slate-50 rounded border border-slate-200">
                  <span className="text-slate-500 text-[10px] block">Total Integration Cost</span>
                  <span className="font-bold text-slate-900">
                    {isExtraCapacity ? "USD 1,050 (F05)" : "USD 800 (F01)"}
                  </span>
                </div>
              </div>

              {/* Auditor Verdict */}
              <div className="flex items-center justify-between text-[11px] pt-2 border-t border-slate-100">
                <span className="text-slate-500">Auditor Verdict:</span>
                <span
                  className={`font-mono font-bold ${
                    scenario.auditor?.verdict === "APPROVED"
                      ? "text-emerald-700"
                      : scenario.auditor?.verdict === "CHALLENGED"
                      ? "text-amber-700"
                      : "text-rose-700"
                  }`}
                >
                  {scenario.auditor?.verdict || "PENDING"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Scenario Deep-Dive Inspector */}
      {selectedScenario && (
        <div className="bg-white rounded-lg border border-slate-300 shadow-sm p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">
                  Scenario Details: {selectedScenario.type}
                </h2>
                <StatusBadge status={selectedScenario.feasibility} size="md" />
              </div>
              <p className="text-xs text-slate-500 mt-1 font-mono">
                Digest: {selectedScenario.input_digest} &bull; Base Revision #
                {selectedScenario.base_graph_revision}
              </p>
            </div>

            {selectedScenario.feasibility === "FEASIBLE" && (
              <Link
                href="/actions"
                className="inline-flex items-center px-4 py-2 rounded-md bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs shadow-sm transition-colors"
              >
                Inspect Generated Action Proposal
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Link>
            )}
          </div>

          {/* Value Provenance Breakdown (Configured Inputs vs Deterministic Calculations vs Unknowns) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Column 1: Configured Inputs */}
            <div className="p-4 rounded-md border border-slate-200 bg-slate-50 space-y-2 text-xs">
              <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px] block">
                1. Configured Inputs
              </span>
              <ul className="space-y-1.5 text-slate-600 font-mono text-[11px]">
                {Object.entries(selectedScenario.inputs).map(([k, v]) => (
                  <li key={k} className="flex justify-between border-b border-slate-200/60 pb-1">
                    <span className="text-slate-500">{k}:</span>
                    <span className="font-semibold text-slate-800">{String(v)}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Column 2: Deterministic Calculations */}
            <div className="p-4 rounded-md border border-slate-200 bg-slate-50 space-y-2 text-xs">
              <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px] block">
                2. Deterministic Formulas
              </span>
              <div className="space-y-2">
                {selectedScenario.calculations.map((calc) => (
                  <div
                    key={calc.calculation_id}
                    className="p-2 bg-white rounded border border-slate-200 text-[11px]"
                  >
                    <div className="flex justify-between font-mono font-bold text-slate-800">
                      <span>Formula {calc.formula_id}</span>
                      <span>
                        {calc.currency} {calc.amount}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500 block mt-0.5">
                      Status: {calc.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Column 3: Assumptions & Unknowns */}
            <div className="p-4 rounded-md border border-slate-200 bg-slate-50 space-y-2 text-xs">
              <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px] block">
                3. Assumptions & Unknowns
              </span>
              <div className="space-y-1.5 text-[11px]">
                {selectedScenario.assumptions.map((asm) => (
                  <div
                    key={asm.id}
                    className="p-2 rounded bg-white border border-slate-200"
                  >
                    <span className="font-bold text-slate-700 block">
                      [{asm.kind}] {asm.description}
                    </span>
                  </div>
                ))}
                {selectedScenario.missing_inputs.length > 0 && (
                  <div className="p-2 bg-rose-50 border border-rose-200 rounded text-rose-800">
                    <span className="font-bold block">Missing Authoritative Inputs:</span>
                    {selectedScenario.missing_inputs.join(", ")}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Schedule Breakdown */}
          <div className="space-y-3">
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-sky-600" />
              Proposed Execution Schedule & Capacity Slots
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">Task ID</th>
                    <th className="py-2.5 px-3">Assigned Resource</th>
                    <th className="py-2.5 px-3">Slot Window</th>
                    <th className="py-2.5 px-3">Allocated Hours</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {selectedScenario.schedule.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 font-bold text-slate-900">
                        {item.issue_id}
                      </td>
                      <td className="py-2.5 px-3 text-slate-800">
                        {item.person_name || item.person_id}
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">
                        {item.start && item.end
                          ? `${new Date(item.start).toLocaleDateString()} ${new Date(
                              item.start
                            ).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })} – ${new Date(item.end).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}`
                          : "Unscheduled"}
                      </td>
                      <td className="py-2.5 px-3 font-bold text-slate-900">
                        {item.hours}h
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Auditor Findings & Constraint Checks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-200">
            <div className="space-y-2">
              <span className="font-bold text-xs text-slate-900 block">
                Independent Auditor Challenge:
              </span>
              <ul className="space-y-1 text-xs text-slate-700 list-disc list-inside bg-slate-50 p-3 rounded border border-slate-200">
                {selectedScenario.auditor?.findings.map((f, i) => (
                  <li key={i} className="leading-relaxed">
                    {f}
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-2">
              <span className="font-bold text-xs text-slate-900 block">
                Policy Verdicts:
              </span>
              <div className="space-y-1.5">
                {selectedScenario.policy_checks.map((pol) => (
                  <div
                    key={pol.rule_id}
                    className="p-2.5 rounded border border-slate-200 bg-slate-50 text-xs flex items-center justify-between"
                  >
                    <div>
                      <span className="font-mono font-bold text-slate-800 block">
                        {pol.rule_id}
                      </span>
                      <span className="text-[11px] text-slate-600">
                        {pol.reason}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        pol.outcome === "PASS"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {pol.outcome}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
