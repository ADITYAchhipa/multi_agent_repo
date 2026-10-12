import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/providers/query-provider";
import { AppShell } from "@/components/shell/app-shell";

export const metadata: Metadata = {
  title: "PromiseOps + PromiseSeal — Operational Decision Console",
  description:
    "Delivery margin protection, contract scope alignment, workload verification, and cryptographic PromiseSeal receipt attestation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased min-h-screen">
        <QueryProvider>
          <AppShell>{children}</AppShell>
        </QueryProvider>
      </body>
    </html>
  );
}
