import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import OverviewPage from "@/app/page";
import { TestWrapper } from "./test-utils";

describe("Overview / Operations Command Page", () => {
  it("renders the primary operational decision question clearly", async () => {
    render(
      <TestWrapper>
        <OverviewPage />
      </TestWrapper>
    );

    expect(
      await screen.findByText(/We promised Acme loyalty integration by Friday/i)
    ).toBeInTheDocument();
  });

  it("distinguishes milestone exposure at risk from realized loss and shows calculation F02", async () => {
    render(
      <TestWrapper>
        <OverviewPage />
      </TestWrapper>
    );

    // Should render USD 40,000 with AT_RISK badge
    const amounts = await screen.findAllByText(/USD 40,000/i);
    expect(amounts.length).toBeGreaterThan(0);
    expect(screen.getByText(/AT_RISK \(F02\)/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Milestone blocked until acceptance testing complete. Not a realized loss./i)
    ).toBeInTheDocument();
  });

  it("displays separate account context without combining renewal into loss or milestone exposure", async () => {
    render(
      <TestWrapper>
        <OverviewPage />
      </TestWrapper>
    );

    expect(
      await screen.findByText(/Separate Commercial Account Context/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/renewal opportunity is never summed into milestone exposure/i)
    ).toBeInTheDocument();
  });
});
