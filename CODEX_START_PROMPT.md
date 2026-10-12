# Initial Codex Prompt — PromiseOps + PromiseSeal

Read `PROMISEOPS_PROMISESEAL_CODEX_BUILD_SPEC.md` completely before editing code. It is the detailed source of truth. Do not start by generating the UI.

1. Inspect the existing repository, current working tree, source code, manifests, README, environment examples, Docker setup, tests, and git status. Preserve useful existing work.
2. Compare the repo against the specification. Write `docs/IMPLEMENTATION_NOTES.md` with (a) what already exists, (b) what is missing, (c) real constraints, and (d) any necessary deviations. Do not silently change the chosen stack or product direction.
3. Verify the current version/docs for each external dependency before pinning it. Use only the repositories selected by the spec; do not add more frameworks/repos unless you can name the concrete blocker they solve.
4. Implement in the exact phased order in §16. First deliver a runnable FalkorDB-backed core with a deterministic seed dataset and tests. No frontend polish until source ingest, graph queries, PromiseSeal verification, scenario math, and the action state machine work.
5. Keep mock mode end-to-end complete. Do not fabricate live Microsoft Teams, Jira, or workload API access. If credentials or the workload API contract are missing, leave live mode disabled and document the exact required environment/config fields.
6. Use FalkorDB for real business relationship traversal, source provenance, promise version history, conflicts, scenarios, and audit references. Build only vetted parameterized Cypher templates. Do not let the LLM write arbitrary Cypher or bypass backend policy.
7. Build PromiseSeal as a versioned, signed service receipt with a reproducible canonical payload, SHA-256 digest, Ed25519 signature, verifier, and append-only transition history. Do not claim a signature proves a statement is true or that the receipt is legally binding. Do not store private keys in the graph or client.
8. Keep the Promise Compiler, Graph Investigator, Margin Investigator, Counterfactual Planner, and Adversarial Auditor outputs typed and validated. Business arithmetic and final authorization are deterministic backend code, not LLM decisions.
9. Never execute a Jira/workload write before server-side approval and policy checks. Recheck evidence freshness before executing, then read the external state back and log whether it matches. If the real workload API schema is unknown, use `MockWorkloadAdapter`; do not invent endpoints or fields.
10. Test every phase against the acceptance criteria and preserve exact logs/results. Finish with setup instructions, architecture, connector prerequisites, benchmark results, limitations, and an end-to-end demo smoke test.

Do not mark an item complete unless the implementation and its test have actually been run. If time is limited, cut optional features and protect the core workflow.
