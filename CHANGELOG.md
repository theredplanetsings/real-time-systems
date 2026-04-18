# Changelog

## Unreleased

- Refreshed the dashboard home page with data-driven sections and sparkline previews.
- Added Task Set Builder presets, JSON import/export, seeded generation, hyperperiod warnings, and scenario snapshots.
- Added Compare Mode deadline miss detail table and JSON task-set export.
- Added Cyclic Executive support to Compare Mode with automatic frame-size selection.
- Added a benchmark suite page for runtime and miss comparisons across canned workloads.
- Added mixed-workload analysis for baseline EDF versus slack stealing.
- Added mixed-criticality support in Algorithm Explorer with static and adaptive modes.
- Added nested/non-nested resource access controls to Priority Inversion and Compare Mode.
- Added dynamic sidebar controls, shared validation, cached plot helpers, and clearer PNG export errors.
- Added a GitHub Actions CI workflow, dev tooling config, verification guide, and contribution guide.
- Refreshed the dashboard home page contrast for improved readability.
- Hardened compare-metrics horizon normalization to handle invalid/non-numeric inputs safely.
- Counted compare-mode jobs using non-empty IDs only for cleaner summary totals.
- Added fail-fast computation-time validation in utilisation and density helpers.
- Normalized invalid global processor counts to a safe minimum of 1 in schedulability summaries.
- Stabilized task editor IDs to sequential 1..N values for deterministic job naming.
- Expanded smoke coverage to include the dashboard home page.
