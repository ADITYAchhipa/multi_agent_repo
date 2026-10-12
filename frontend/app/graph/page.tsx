"use client";

import React, { useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
} from "@xyflow/react";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Network,
  Filter,
  Eye,
  Info,
  Maximize2,
  List,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { GraphNode, GraphEdge, GraphPath } from "@/types/api";

// Custom node rendering logic
const NODE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  Customer: { bg: "#ffffff", border: "#0284c7", text: "#0369a1" },
  Contract: { bg: "#ffffff", border: "#475569", text: "#334155" },
  ContractClause: { bg: "#ffffff", border: "#64748b", text: "#475569" },
  Promise: { bg: "#ffffff", border: "#1481ee", text: "#0969d6" },
  PromiseSealReceipt: { bg: "#f0fdf4", border: "#16a34a", text: "#15803d" },
  JiraIssue: { bg: "#ffffff", border: "#0f172a", text: "#0f172a" },
  Person: { bg: "#ffffff", border: "#0284c7", text: "#0369a1" },
  Milestone: { bg: "#fffbeb", border: "#d97706", text: "#b45309" },
  AcceptanceRequirement: { bg: "#fef2f2", border: "#dc2626", text: "#b91c1c" },
  ActionProposal: { bg: "#f0f7ff", border: "#0969d6", text: "#0753ab" },
};

export default function GraphExplorerPage() {
  const [selectedPathId, setSelectedPathId] = useState<string>("ALL");
  const [selectedLabel, setSelectedLabel] = useState<string>("ALL");
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"canvas" | "list">("canvas");

  const { data, isLoading } = useQuery({
    queryKey: ["graph"],
    queryFn: () => apiClient.getGraph(),
  });

  const rawNodes = useMemo(() => data?.nodes ?? [], [data?.nodes]);
  const rawEdges = useMemo(() => data?.edges ?? [], [data?.edges]);
  const paths = useMemo(() => data?.paths ?? [], [data?.paths]);

  const activePath = useMemo(
    () => paths.find((p) => p.path_id === selectedPathId),
    [paths, selectedPathId]
  );

  // Position nodes deterministically in layers
  const initialNodes: Node[] = useMemo(() => {
    const layerMap: Record<string, number> = {
      Customer: 0,
      Contract: 1,
      ContractClause: 2,
      Promise: 2,
      PromiseSealReceipt: 3,
      JiraIssue: 4,
      Person: 5,
      Milestone: 3,
      AcceptanceRequirement: 4,
      ActionProposal: 5,
    };

    const countsInLayer: Record<number, number> = {};

    return rawNodes.map((n) => {
      const layer = layerMap[n.label] ?? 3;
      const count = countsInLayer[layer] || 0;
      countsInLayer[layer] = count + 1;

      const colors = NODE_COLORS[n.label] || {
        bg: "#ffffff",
        border: "#cbd5e1",
        text: "#0f172a",
      };

      const isHighlighted =
        selectedPathId === "ALL" ||
        (activePath && activePath.node_ids.includes(n.id));

      return {
        id: n.id,
        position: { x: layer * 220 + 40, y: count * 110 + 60 },
        data: {
          label: (
            <div className="p-2 space-y-1 text-left">
              <span className="text-[9px] font-mono font-bold uppercase tracking-wider block opacity-70">
                {n.label}
              </span>
              <span className="font-bold text-xs block leading-tight">
                {n.display_name}
              </span>
              {n.status && (
                <span className="inline-block text-[9px] font-mono px-1 py-0.2 rounded bg-slate-100 text-slate-700 border border-slate-200">
                  {n.status}
                </span>
              )}
            </div>
          ),
          rawNode: n,
        },
        style: {
          backgroundColor: colors.bg,
          border: `2px solid ${isHighlighted ? colors.border : "#e2e8f0"}`,
          color: colors.text,
          width: 180,
          borderRadius: 6,
          boxShadow: isHighlighted
            ? "0 2px 6px -1px rgba(0,0,0,0.1)"
            : "none",
          opacity: isHighlighted ? 1 : 0.35,
          cursor: "pointer",
        },
      };
    });
  }, [rawNodes, selectedPathId, activePath]);

  const initialEdges: Edge[] = useMemo(() => {
    return rawEdges.map((e) => {
      const isPathEdge =
        selectedPathId === "ALL" ||
        (activePath && activePath.edge_ids.includes(e.id));

      const isHypothetical = e.scenario_only;
      const isConflict = e.status === "CONFLICT";

      return {
        id: e.id,
        source: e.from_id,
        target: e.to_id,
        label: e.type,
        animated: isHypothetical,
        style: {
          stroke: isConflict
            ? "#dc2626"
            : isHypothetical
            ? "#0284c7"
            : isPathEdge
            ? "#0f172a"
            : "#cbd5e1",
          strokeWidth: isPathEdge ? 2 : 1,
          strokeDasharray: isHypothetical ? "4 4" : undefined,
          opacity: isPathEdge ? 1 : 0.3,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isConflict ? "#dc2626" : isHypothetical ? "#0284c7" : "#0f172a",
        },
        data: {
          rawEdge: e,
        },
      };
    });
  }, [rawEdges, selectedPathId, activePath]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const selectedNodeData = rawNodes.find((n) => n.id === selectedEntityId);
  const selectedEdgeData = rawEdges.find((e) => e.id === selectedEdgeId);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
              Graph Explorer
            </h1>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-200 text-slate-800">
              FalkorDB Provenance (Revision #12)
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Traverse verifiable business relationships, contract links, task dependencies, and scenario overlays.
          </p>
        </div>

        {/* View Switcher (Desktop Canvas vs Mobile/Accessible Relationship List) */}
        <div className="flex items-center gap-2">
          <div className="bg-slate-200 p-0.5 rounded-md flex text-xs">
            <button
              onClick={() => setViewMode("canvas")}
              className={`px-3 py-1 rounded font-medium transition-colors ${
                viewMode === "canvas"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Interactive Canvas
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`px-3 py-1 rounded font-medium flex items-center gap-1 transition-colors ${
                viewMode === "list"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <List className="w-3.5 h-3.5" />
              Relationship List
            </button>
          </div>
        </div>
      </div>

      {/* Control Bar: Path Highlighting & Entity Filters */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-600 shrink-0" />
            <span className="font-semibold text-slate-700">Proof Path:</span>
            <select
              value={selectedPathId}
              onChange={(e) => setSelectedPathId(e.target.value)}
              className="py-1 px-2.5 rounded border border-slate-300 bg-slate-50 font-mono text-xs focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All Active Edges</option>
              <option value="PTH1">PTH1: Transcript Quote &rarr; PromiseSeal v1</option>
              <option value="PTH2">PTH2: Contract Scope Exclusion (Clause C2)</option>
              <option value="PTH3">PTH3: Jira ACME-101 &rarr; Blocked ACME-102</option>
            </select>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-600">
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-slate-900 inline-block" />
            Stored Fact
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-rose-600 inline-block" />
            Conflict
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 border-t border-sky-600 border-dashed inline-block" />
            Hypothetical Scenario Edge
          </span>
        </div>
      </div>

      {/* Canvas View */}
      {viewMode === "canvas" ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* React Flow Viewport (3 cols) */}
          <div className="lg:col-span-3 bg-white rounded-lg border border-slate-300 shadow-sm h-[600px] relative overflow-hidden">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={(_, n) => {
                setSelectedEntityId(n.id);
                setSelectedEdgeId(null);
              }}
              onEdgeClick={(_, e) => {
                setSelectedEdgeId(e.id);
                setSelectedEntityId(null);
              }}
              fitView
              minZoom={0.2}
              maxZoom={1.5}
            >
              <Background color="#cbd5e1" gap={16} size={1} />
              <Controls showInteractive={false} />
              <MiniMap
                nodeColor="#cbd5e1"
                maskColor="rgba(248, 250, 252, 0.7)"
                className="rounded border border-slate-300"
              />
            </ReactFlow>
          </div>

          {/* Side Panel: Selected Node / Edge Details (1 col) */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 space-y-3">
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700 border-b border-slate-100 pb-2">
                Entity / Provenance Inspector
              </h3>

              {selectedNodeData ? (
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-slate-500 block">
                      {selectedNodeData.label}
                    </span>
                    <h4 className="font-bold text-slate-900 text-sm">
                      {selectedNodeData.display_name}
                    </h4>
                    <span className="font-mono text-slate-500 text-[11px] block mt-0.5">
                      ID: {selectedNodeData.id}
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-slate-50 border border-slate-200 font-mono text-[11px] space-y-1">
                    <span className="font-bold text-slate-700 block">
                      Node Properties:
                    </span>
                    <pre className="text-[10px] whitespace-pre-wrap text-slate-600">
                      {JSON.stringify(selectedNodeData.properties, null, 2)}
                    </pre>
                  </div>

                  <div className="text-[11px] text-slate-500 font-mono">
                    Sources: {selectedNodeData.source_ref_ids.join(", ") || "None"}
                  </div>
                </div>
              ) : selectedEdgeData ? (
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-slate-500 block">
                      Edge Relationship
                    </span>
                    <h4 className="font-bold text-slate-900 text-sm">
                      {selectedEdgeData.type}
                    </h4>
                  </div>

                  <div className="p-2.5 rounded bg-slate-50 border border-slate-200 font-mono text-[11px] space-y-1">
                    <div>From: {selectedEdgeData.from_id}</div>
                    <div>To: {selectedEdgeData.to_id}</div>
                    <div>Status: {selectedEdgeData.status}</div>
                    <div>Provenance: {selectedEdgeData.provenance_kind}</div>
                    <div>
                      Hypothetical: {selectedEdgeData.scenario_only ? "YES" : "NO"}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500">
                  Click any graph node or relationship edge to inspect verifiable provenance and properties.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Accessible Relationship List View (Mobile & Screen Readers) */
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 space-y-4">
          <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-3">
            Authoritative Relationship Catalog (FalkorDB Triplets)
          </h3>

          <div className="space-y-2">
            {rawEdges.map((edge) => (
              <div
                key={edge.id}
                className="p-3 rounded border border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs font-mono"
              >
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900">{edge.from_id}</span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-800 text-[10px] font-bold">
                    &minus;[{edge.type}]&minus;&gt;
                  </span>
                  <span className="font-bold text-slate-900">{edge.to_id}</span>
                </div>

                <div className="flex items-center gap-2 text-[11px]">
                  <span className="text-slate-500">{edge.provenance_kind}</span>
                  <StatusBadge status={edge.status} size="sm" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
