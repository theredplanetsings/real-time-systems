# Real-Time Systems

[![Tests](https://github.com/theredplanetsings/real-time-systems/workflows/tests/badge.svg)](https://github.com/theredplanetsings/real-time-systems/actions/workflows/tests.yml)

Real-time scheduling examples, analysis pages, and interactive plots in a Streamlit dashboard.

## Dashboard
The app supports task-set authoring, schedulability checks, schedule generation, and CSV/PNG export. It also covers several non-obvious workflow pages beyond the main explorer.

The dashboard home page now includes a styled hero, data-driven navigation cards, compact sparkline previews, and a Recent Updates panel generated from a single source list.
The latest home-page pass also tightened the colour palette so text and controls are easier to read.

### Main Pages
- `pages/00_Algorithm_Explorer.py`: Primary workflow for EDF, EDD, RM, and DM variants.
- `pages/01_Task_Set_Builder.py`: Standalone task-set authoring with presets, seeded generation, snapshots, and CSV/JSON export.
- `pages/02_Compare_Mode.py`: Side-by-side comparison across multiple algorithms and task sets.
- `pages/16_Mixed_Workload_Analysis.py`: Periodic EDF baseline versus slack stealing for mixed periodic/aperiodic workloads.
- `pages/17_Benchmark_Suite.py`: Runtime and deadline-miss benchmark comparisons across canned scenarios.

### Specialised Analyses
- `pages/06_Cyclic_Executive.py`: Frame-size search and cyclic executive schedule generation.
- `pages/10_Time_Demand.py`: Time-demand analysis for a selected task.
- `pages/11_Priority_Inversion.py`: Resource-sharing demo with protocol options.
- `pages/15_Slack_Stealing.py`: Idle-time reclamation for periodic EDF plus aperiodic jobs.

### Key Behaviours
- Shared validation clamps unsafe phase, period, computation, deadline, resource, and mixed-criticality values before simulation.
- Algorithm Explorer supports mixed-criticality task sets with static or adaptive mode.
- Compare Mode uses the shared algorithm registry, cached plots, miss-detail reporting, and CSV/JSON task-set export.
- Compare Mode now supports nested/non-nested resource access options for uniprocessor and partitioned runs.
- Resource-aware protocols are available where they apply: None, PIP, PCP, and NPP.
- Legacy flat pages remain archived under `legacy_pages/`.

## Algorithm Input/Output Examples

These examples use the same canonical task shape used across pages:

```text
Task = (id, phase, period, computation, deadline)
```

Example task set:

```text
T1 = (1, 0, 4, 1, 4)
T2 = (2, 0, 5, 2, 5)
T3 = (3, 0, 20, 4, 20)
```

- EDF:
	Input: periodic tasks with explicit deadlines.
	Output: dynamic-priority timeline, deadline-miss report, utilisation summary.
- RM:
	Input: periodic tasks where fixed priorities come from shorter periods.
	Output: fixed-priority schedule, response-time intuition via timeline, miss report.
- DM:
	Input: periodic tasks where fixed priorities come from shorter relative deadlines.
	Output: fixed-priority deadline-driven schedule, miss report, protocol-aware resource blocking details when enabled.
- Cyclic Executive:
	Input: periodic tasks plus optional frame size (or auto-search).
	Output: selected feasible frame size and per-frame dispatch table.
- Time-Demand Analysis:
	Input: a fixed-priority task set and a selected task under analysis.
	Output: iterative demand-vs-time table and schedulable/unschedulable verdict for that task.
- Priority Inversion page:
	Input: tasks with shared resources, selected protocol (None/PIP/PCP/NPP), and nested/non-nested resource access.
	Output: protocol effect timeline showing blocking/inheritance/ceiling behavior.
- Slack Stealing:
	Input: periodic EDF baseline and aperiodic arrivals.
	Output: reclaimed slack timeline and aperiodic completion improvements compared with baseline.

## Changelog

Recent project updates are tracked in `CHANGELOG.md`.

## Recent Improvements (2026-04-15)

1. Added fail-fast validation in shared utilisation and density math for non-positive task periods/deadlines.
2. Normalized negative compare-metrics horizons to zero for more predictable run summaries and miss-detail tables.
3. Switched compare miss-details output to deterministic natural job ordering (e.g., 2.0 before 10.0).
4. Added a `make quick-test` shortcut for running the highest-signal core test subset.
5. Expanded verification guidance with fast-path and focused-suite test commands.
6. Updated contributor workflow guidance to use `make quick-test` during iteration and keep commits tightly scoped.
7. Standardized algorithm family/variant ordering to deterministic sorted lists for consistent UI selection behavior.
8. Added smoke coverage to assert all configured Streamlit page paths exist before page execution checks.
9. Broadened hyperperiod helper typing to accept generic iterables (for tuple/list parity).

### PNG Export Notes
- PNG export uses Plotly + Kaleido and requires a Chrome/Chromium runtime.
- For Streamlit Cloud deployments, this repository includes `packages.txt` with `chromium` so PNG downloads work after redeploy.

### Mixed-Criticality (SMC/AMC)
- Enable **Include criticality** in Algorithm Explorer.
- Choose a scale:
	- `Low/Medium/High`
	- `A-Z`
- Choose a mode:
	- `static`: mixed-criticality priorities/budgets are applied without mode switch.
	- `adaptive`: starts in LO mode and switches to HI mode when a HI-criticality job exceeds `C-LO`; low-criticality jobs are then dropped.
- Configure default `C-LO` and `C-HI` from the sidebar and fine-tune per task in the table.
- Schedules now show explicit LO->HI mode-switch markers and a mixed-criticality stats panel (switch count/time and HI-mode execution time).
- Task input validation now auto-corrects invalid criticality labels and enforces `C-LO >= 1` and `C-HI >= C-LO`, with warnings.

Live app: https://real-time.streamlit.app/

### Run locally
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Run tests
```bash
pip install -r requirements-dev.txt
python3 -m pytest -q tests
# or
make test
# fast core subset
make quick-test
```

### Available Make targets
```bash
make help      # Show all available make targets
make fmt       # Auto-format code
make lint      # Check code quality
```

## Structure
```
real-time-systems/
├── .github/workflows/      # CI workflow definitions
├── CONTRIBUTING.md         # Contribution guidelines
├── Makefile                # Common developer commands
├── README.md               # Project overview and usage
├── compare_utils.py        # Compare-mode summary helpers
├── cyclic-executive/      # Cyclic executive frame sizing and schedules
├── dm-pcp/                # Deadline Monotonic with Priority Ceiling Protocol
├── dm-pip/                # Deadline Monotonic with Priority Inheritance Protocol
├── docs/                  # Verification and contributor guidance
├── edf/                   # Earliest Deadline First scheduling
├── global-rm/             # Global RM on multiple processors
├── legacy_pages/          # Archived legacy Streamlit algorithm pages
│   ├── 02_EDF.py
│   ├── 03_EDD.py
│   ├── 04_RM.py
│   ├── 05_DM.py
│   ├── 07_Global_RM.py
│   ├── 08_Global_EDF.py
│   ├── 09_Global_DM.py
│   ├── 12_Partitioned_EDF.py
│   ├── 13_Partitioned_RM.py
│   └── 14_Partitioned_DM.py
├── pages/                 # Active Streamlit pages
│   ├── 00_Algorithm_Explorer.py
│   ├── 01_Task_Set_Builder.py
│   ├── 02_Compare_Mode.py
│   ├── 06_Cyclic_Executive.py
│   ├── 10_Time_Demand.py
│   ├── 11_Priority_Inversion.py
│   ├── 15_Slack_Stealing.py
│   ├── 16_Mixed_Workload_Analysis.py
│   └── 17_Benchmark_Suite.py
├── priority-inversion/    # Priority inversion examples and debugging
├── pyproject.toml         # Ruff/Black configuration
├── requirements-dev.txt   # Development and lint/test dependencies
├── requirements.txt       # Runtime dependencies
├── rm-dm-basics/          # RM/DM basics and Lehoczky's counterexample
├── rm-npp/                # Rate Monotonic with Non-Preemptive Protocol
├── rm-pip/                # Rate Monotonic with Priority Inheritance Protocol
├── tests/                 # Automated test suite
├── time-demand-analysis/  # Time-demand analysis for a selected task
├── streamlit_app.py       # Dashboard landing page
├── st_helpers.py          # Shared Streamlit page helpers
├── rt_utils.py            # Scheduling logic and plot helpers
├── scheduling_math.py     # Shared scheduling math helpers
└── (see folders above for algorithm-specific scripts and notes)
```

Each algorithm folder contains a focused script (or set of scripts) for the named
method, plus any pre-generated schedule images and a short README describing the
contents.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) file for details.

## Development

For detailed development setup, workflow, and contribution guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md) and [CONTRIBUTING.md](CONTRIBUTING.md).