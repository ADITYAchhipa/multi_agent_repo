import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/ui/status-badge";

describe("StatusBadge Component", () => {
  it("renders PROPOSED state with clear unconfirmed label", () => {
    render(<StatusBadge status="PROPOSED" />);
    expect(screen.getByText(/PROPOSED \(UNCONFIRMED\)/i)).toBeInTheDocument();
  });

  it("renders CONFIRMED state with appropriate label", () => {
    render(<StatusBadge status="CONFIRMED" />);
    expect(screen.getByText("CONFIRMED")).toBeInTheDocument();
  });

  it("renders DISPUTED state with distinctive label", () => {
    render(<StatusBadge status="DISPUTED" />);
    expect(screen.getByText("DISPUTED")).toBeInTheDocument();
  });

  it("renders Scope Status with unambiguous text", () => {
    render(<StatusBadge status="POSSIBLE_OUT_OF_SCOPE" />);
    expect(screen.getByText("POSSIBLE OUT OF SCOPE")).toBeInTheDocument();
  });

  it("renders Verification Integrity status correctly", () => {
    render(<StatusBadge status="VALID" />);
    expect(screen.getByText("INTEGRITY VALID")).toBeInTheDocument();
  });
});
