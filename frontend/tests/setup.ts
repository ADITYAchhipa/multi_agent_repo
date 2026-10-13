import "@testing-library/jest-dom";

class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (typeof window !== "undefined") {
  window.ResizeObserver = window.ResizeObserver || MockResizeObserver;
}

