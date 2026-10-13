"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQueryClient, useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Inbox,
  FlaskConical,
  CheckSquare,
  Network,
  Activity,
  Settings,
  ShieldCheck,
  UserCheck,
  RotateCcw,
  Menu,
  X,
  Building2,
  Database,
  ExternalLink,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [appMode, setAppMode] = useState<"DEMO" | "LIVE">(apiClient.getMode());
  const [activeRole, setActiveRole] = useState<
    "reviewer" | "executor" | "admin" | "viewer"
  >("reviewer");
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const { data: actionsData } = useQuery({
    queryKey: ["actions"],
    queryFn: () => apiClient.getActions(),
  });

  const pendingActionsCount = (actionsData?.items || []).filter(
    (a) => a.status === "NEEDS_APPROVAL" || a.status === "PROPOSED"
  ).length;

  useEffect(() => {
    return apiClient.subscribe((nextMode) => {
      setAppMode(nextMode);
    });
  }, []);

  const handleRoleChange = (role: "reviewer" | "executor" | "admin" | "viewer") => {
    setActiveRole(role);
    apiClient.setActor(role);
    queryClient.invalidateQueries();
  };

  const handleModeToggle = () => {
    const nextMode = appMode === "DEMO" ? "LIVE" : "DEMO";
    setAppMode(nextMode);
    apiClient.setMode(nextMode);
    queryClient.invalidateQueries();
  };

  const handleReset = () => {
    apiClient.resetDemoData();
    queryClient.invalidateQueries();
    setResetMessage("Demo scenario state reset to baseline.");
    setTimeout(() => setResetMessage(null), 3000);
    if (typeof window !== "undefined" && window.location) {
      window.location.reload();
    }
  };

  const navItems = [
    {
      name: "Operations Command",
      href: "/",
      icon: LayoutDashboard,
      badge: "ACTIVE",
    },
    {
      name: "Promise Inbox",
      href: "/promises",
      icon: Inbox,
      badge: "1 PROPOSED",
    },
    {
      name: "Simulation Lab",
      href: "/simulations",
      icon: FlaskConical,
      badge: "3 SCENARIOS",
    },
    {
      name: "Approval Queue",
      href: "/actions",
      icon: CheckSquare,
      badge: `${pendingActionsCount} PENDING`,
    },
    {
      name: "Graph Explorer",
      href: "/graph",
      icon: Network,
      badge: null,
    },
    {
      name: "Knowledge Health",
      href: "/knowledge",
      icon: Activity,
      badge: "4 FINDINGS",
    },
    {
      name: "Connectors & Settings",
      href: "/settings",
      icon: Settings,
      badge: null,
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Top Banner: Environment Context, Demo Status, Active Actor & Mode */}
      <header className="bg-slate-900 text-slate-100 border-b border-slate-800 text-xs px-4 py-2 flex flex-wrap items-center justify-between gap-2 z-30">
        <div className="flex flex-wrap items-center gap-2">
          {appMode === "DEMO" ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-amber-500 text-slate-950 font-bold tracking-wider uppercase text-[10px]">
              DEMO DATA
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-500 text-slate-950 font-bold tracking-wider uppercase text-[10px]">
              LIVE BACKEND
            </span>
          )}

          <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono text-[10px]">
            <Database className="w-3 h-3 mr-1 text-slate-400" />
            WORKLOAD MOCK MODE
          </span>

          <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono text-[10px]">
            <Building2 className="w-3 h-3 mr-1 text-slate-400" />
            Northstar Systems / Acme Retail
          </span>

          <span className="hidden md:inline-flex text-slate-400 font-mono text-[11px]">
            Anchor: 2026-10-12 (Eval: Fri 09:00 UTC)
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Active Persona / Actor Switcher */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-2 py-1 rounded border border-slate-700">
            <UserCheck className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-slate-400 font-medium mr-1 hidden sm:inline">Role:</span>
            <select
              value={activeRole}
              onChange={(e) =>
                handleRoleChange(
                  e.target.value as "reviewer" | "executor" | "admin" | "viewer"
                )
              }
              className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer text-xs"
              aria-label="Active actor role selection"
            >
              <option value="reviewer" className="bg-slate-900 text-white">
                Aria Chen (Reviewer)
              </option>
              <option value="executor" className="bg-slate-900 text-white">
                Casey Rao (Executor)
              </option>
              <option value="admin" className="bg-slate-900 text-white">
                System Admin
              </option>
              <option value="viewer" className="bg-slate-900 text-white">
                Read-only Stakeholder
              </option>
            </select>
          </div>

          {/* Mode Switcher */}
          <button
            onClick={handleModeToggle}
            className={`px-2 py-1 rounded font-mono font-medium border text-[11px] transition-colors ${
              appMode === "DEMO"
                ? "bg-slate-800 text-sky-300 border-sky-600/50 hover:bg-slate-700"
                : "bg-emerald-950 text-emerald-300 border-emerald-600 hover:bg-emerald-900"
            }`}
            title="Toggle between DEMO fixtures and LIVE API backend"
          >
            {appMode === "DEMO" ? "Switch to LIVE" : "Switch to DEMO"}
          </button>

          {/* Reset Demo State */}
          {appMode === "DEMO" && (
            <button
              onClick={handleReset}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1 text-[11px]"
              title="Reset in-memory scenario state to clean baseline"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reset</span>
            </button>
          )}
        </div>
      </header>

      {resetMessage && (
        <div className="bg-sky-600 text-white text-xs px-4 py-1.5 text-center font-medium animate-in fade-in">
          {resetMessage}
        </div>
      )}

      <div className="flex flex-1 min-h-[calc(100vh-38px)]">
        {/* Left Desktop Sidebar */}
        <aside className="w-64 bg-slate-900 text-slate-200 border-r border-slate-800 hidden md:flex flex-col shrink-0">
          {/* Logo & Product Identification */}
          <div className="p-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-sky-600 flex items-center justify-center text-white font-bold">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h1 className="font-bold text-sm tracking-tight text-white flex items-center gap-1">
                  PromiseOps
                  <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-slate-800 text-sky-400 border border-slate-700">
                    SEAL
                  </span>
                </h1>
                <p className="text-[11px] text-slate-400">
                  Operational Decision Console
                </p>
              </div>
            </div>
          </div>

          {/* Nav Links */}
          <nav className="flex-1 p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-sky-600 text-white font-semibold shadow-sm"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        isActive
                          ? "bg-sky-700 text-white font-bold"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Sidebar Footer: Guarantee & Protocol Trust */}
          <div className="p-3 border-t border-slate-800 text-[11px] text-slate-400 space-y-2">
            <div className="flex items-center justify-between text-slate-300">
              <span className="font-semibold">PromiseSeal v1</span>
              <span className="text-[10px] font-mono text-emerald-400">
                Ed25519
              </span>
            </div>
            <p className="text-[10px] leading-relaxed text-slate-400">
              Cryptographic receipt attestation binds statement bytes to
              canonical history. Distinct from legal confirmation.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-500">
              Graph Revision: #12
            </div>
          </div>
        </aside>

        {/* Mobile Header / Navigation Trigger */}
        <div className="md:hidden bg-slate-900 border-b border-slate-800 p-3 flex items-center justify-between w-full fixed bottom-0 z-40">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-sky-400" />
            <span className="font-bold text-xs text-white">PromiseOps</span>
          </div>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1 rounded bg-slate-800 text-slate-200 border border-slate-700"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Mobile Drawer Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-x-0 top-0 bottom-14 bg-slate-950/95 z-40 p-4 flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-sky-400" />
                  <span className="font-bold text-xs text-white uppercase tracking-wider">Navigation Menu</span>
                </div>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded bg-slate-800 text-slate-200 border border-slate-700"
                  aria-label="Close Navigation Menu"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <nav className="space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive =
                    item.href === "/"
                      ? pathname === "/"
                      : pathname.startsWith(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center justify-between px-3 py-2.5 rounded-md text-sm font-medium ${
                        isActive
                          ? "bg-sky-600 text-white font-bold"
                          : "text-slate-200 hover:bg-slate-800"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon className="w-5 h-5" />
                        <span>{item.name}</span>
                      </div>
                      {item.badge && (
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>
            <div className="p-4 border-t border-slate-800 text-xs text-slate-400">
              <p>PromiseOps Console — Mobile Layout Mode</p>
            </div>
          </div>
        )}

        {/* Main Content Pane */}
        <main className="flex-1 overflow-x-hidden p-4 md:p-6 pb-20 md:pb-6">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
