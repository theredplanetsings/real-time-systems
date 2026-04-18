# Verification Guide

## Quick Start

1. Install runtime dependencies:

```bash
pip install -r requirements.txt
```

2. Install dev/test dependencies:

```bash
pip install -r requirements-dev.txt
```

3. Run all tests:

```bash
pytest -q
```

4. Run the fast core subset when iterating:

```bash
make quick-test
```

5. Run focused suites for changed areas:

```bash
pytest -q tests/test_compare_metrics.py
pytest -q tests/test_scheduling_math.py
pytest -q tests/test_schedulability_core.py
pytest -q tests/test_streamlit_smoke.py
```

## Scope Of Tests

- Core schedulability checks for EDF, RM, DM, and global EDF thresholds.
- Protocol behavior checks for None, PIP, PCP, and NPP execution paths.
- Compare metrics checks for run summaries and miss-detail tables.
- Cyclic executive checks for frame candidate generation and schedule frame bounds.

## Manual Verification

1. Launch app:

```bash
streamlit run streamlit_app.py
```

2. Verify pages render:
- Algorithm Explorer
- Compare Mode
- Task Set Builder
- Slack Stealing
- Benchmark Suite

3. Verify exports:
- Task Set Builder CSV export
- Task Set Builder JSON export
- Task Set Builder scenario bundle JSON export
- Compare Mode PNG export
- Dashboard home page cards and local run command block

## CI Verification

CI runs on pushes and pull requests for Python 3.10, 3.11, and 3.12.
The workflow installs dependencies and runs `pytest -q`.