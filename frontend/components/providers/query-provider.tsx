"use client";

import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 20000, // 20s default freshness
            gcTime: 60000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: false, // Do not auto-retry mutations without idempotency safety
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
