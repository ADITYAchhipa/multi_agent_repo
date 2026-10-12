import React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  HelpCircle,
  ShieldAlert,
  ShieldCheck,
  XCircle,
  FileQuestion,
  RefreshCw,
  Slash,
} from "lucide-react";
import { PromiseState, ScopeStatus, ReceiptStanding, VerificationIntegrity } from "@/types/api";

type BadgeType =
  | PromiseState
  | ScopeStatus
  | ReceiptStanding
  | VerificationIntegrity
  | "FEASIBLE"
  | "INFEASIBLE"
  | "AT_RISK"
  | "READY"
  | "NEEDS_APPROVAL"
  | "APPROVED"
  | "EXECUTING"
  | "SUCCEEDED"
  | "FAILED"
  | "CANCELLED"
  | "BLOCKED"
  | "FRESH"
  | "AGING"
  | "STALE";

interface StatusBadgeProps {
  status: BadgeType | string;
  className?: string;
  size?: "sm" | "md";
}

export function StatusBadge({ status, className = "", size = "md" }: StatusBadgeProps) {
  const sizeClasses =
    size === "sm" ? "px-2 py-0.5 text-xs font-medium" : "px-2.5 py-1 text-xs font-semibold";

  let bg = "bg-slate-100";
  let text = "text-slate-800";
  let border = "border-slate-300";
  let icon = <HelpCircle className="w-3.5 h-3.5 mr-1" />;
  let label = status;

  switch (status) {
    // Promise States
    case "PROPOSED":
      bg = "bg-sky-50";
      text = "text-sky-800";
      border = "border-sky-300";
      icon = <Clock className="w-3.5 h-3.5 mr-1 text-sky-600" />;
      label = "PROPOSED (UNCONFIRMED)";
      break;

    case "NEEDS_REVIEW":
      bg = "bg-amber-50";
      text = "text-amber-800";
      border = "border-amber-300";
      icon = <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />;
      label = "NEEDS REVIEW";
      break;

    case "CONFIRMED":
      bg = "bg-emerald-50";
      text = "text-emerald-800";
      border = "border-emerald-300";
      icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
      label = "CONFIRMED";
      break;

    case "DISPUTED":
      bg = "bg-rose-50";
      text = "text-rose-800";
      border = "border-rose-300";
      icon = <ShieldAlert className="w-3.5 h-3.5 mr-1 text-rose-600" />;
      label = "DISPUTED";
      break;

    case "SUPERSEDED":
      bg = "bg-slate-100";
      text = "text-slate-700";
      border = "border-slate-300";
      icon = <RefreshCw className="w-3.5 h-3.5 mr-1 text-slate-500" />;
      label = "SUPERSEDED";
      break;

    case "FULFILLED":
      bg = "bg-emerald-50";
      text = "text-emerald-800";
      border = "border-emerald-300";
      icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
      label = "FULFILLED";
      break;

    case "REJECTED":
      bg = "bg-rose-50";
      text = "text-rose-800";
      border = "border-rose-300";
      icon = <XCircle className="w-3.5 h-3.5 mr-1 text-rose-600" />;
      label = "REJECTED";
      break;

    // Scope status
    case "IN_SCOPE":
      bg = "bg-emerald-50";
      text = "text-emerald-800";
      border = "border-emerald-300";
      icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
      label = "IN SCOPE";
      break;

    case "OUT_OF_SCOPE":
      bg = "bg-rose-50";
      text = "text-rose-800";
      border = "border-rose-300";
      icon = <Slash className="w-3.5 h-3.5 mr-1 text-rose-600" />;
      label = "OUT OF SCOPE";
      break;

    case "POSSIBLE_OUT_OF_SCOPE":
      bg = "bg-amber-50";
      text = "text-amber-800";
      border = "border-amber-300";
      icon = <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />;
      label = "POSSIBLE OUT OF SCOPE";
      break;

    case "AMBIGUOUS":
    case "INSUFFICIENT_EVIDENCE":
      bg = "bg-slate-100";
      text = "text-slate-800";
      border = "border-slate-300";
      icon = <FileQuestion className="w-3.5 h-3.5 mr-1 text-slate-600" />;
      label = status === "AMBIGUOUS" ? "AMBIGUOUS SCOPE" : "INSUFFICIENT EVIDENCE";
      break;

    // Verification & standing
    case "VALID":
      bg = "bg-emerald-50";
      text = "text-emerald-800";
      border = "border-emerald-300";
      icon = <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
      label = "INTEGRITY VALID";
      break;

    case "INVALID":
      bg = "bg-rose-50";
      text = "text-rose-800";
      border = "border-rose-300";
      icon = <ShieldAlert className="w-3.5 h-3.5 mr-1 text-rose-600" />;
      label = "INTEGRITY INVALID";
      break;

    case "UNSIGNED":
      bg = "bg-amber-50";
      text = "text-amber-800";
      border = "border-amber-300";
      icon = <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />;
      label = "UNSIGNED";
      break;

    case "ACTIVE":
      bg = "bg-emerald-50";
      text = "text-emerald-800";
      border = "border-emerald-300";
      icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
      label = "ACTIVE RECEIPT";
      break;

    case "REVOKED":
      bg = "bg-rose-50";
      text = "text-rose-800";
      border = "border-rose-300";
      icon = <XCircle className="w-3.5 h-3.5 mr-1 text-rose-600" />;
      label = "REVOKED";
      break;

    // Action status
    case "NEEDS_APPROVAL":
      bg = "bg-amber-50";
      text = "text-amber-800";
      border = "border-amber-300";
      icon = <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />;
      label = "NEEDS APPROVAL";
      break;

    case "APPROVED":
      bg = "bg-emerald-50";
      text = "text-emerald-800";
      border = "border-emerald-300";
      icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
      label = "APPROVED";
      break;

    case "SUCCEEDED":
      bg = "bg-emerald-50";
      text = "text-emerald-800";
      border = "border-emerald-300";
      icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
      label = "SUCCEEDED";
      break;

    case "EXECUTING":
      bg = "bg-sky-50";
      text = "text-sky-800";
      border = "border-sky-300";
      icon = <RefreshCw className="w-3.5 h-3.5 mr-1 text-sky-600 animate-spin" />;
      label = "EXECUTING";
      break;

    case "BLOCKED":
    case "FAILED":
      bg = "bg-rose-50";
      text = "text-rose-800";
      border = "border-rose-300";
      icon = <XCircle className="w-3.5 h-3.5 mr-1 text-rose-600" />;
      label = status;
      break;

    // Feasibility & Milestones
    case "FEASIBLE":
    case "READY":
      bg = "bg-emerald-50";
      text = "text-emerald-800";
      border = "border-emerald-300";
      icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
      label = status;
      break;

    case "INFEASIBLE":
    case "AT_RISK":
      bg = "bg-rose-50";
      text = "text-rose-800";
      border = "border-rose-300";
      icon = <AlertTriangle className="w-3.5 h-3.5 mr-1 text-rose-600" />;
      label = status;
      break;

    default:
      label = status;
      break;
  }

  return (
    <span
      className={`inline-flex items-center rounded-md border font-mono tracking-tight uppercase ${sizeClasses} ${bg} ${text} ${border} ${className}`}
    >
      {icon}
      <span>{label}</span>
    </span>
  );
}
