# Real-Time Systems
Brief implementations of real-time scheduling algorithms with accompanying plots and a Streamlit dashboard.

## Recent Updates
- Shared task-input validation now clamps unsafe period, computation, deadline, phase, and resource values before they reach the schedulers.
- Streamlit navigation is now Explorer-first: choose a family (EDF, EDD, RM, DM), then choose a variant (Uniprocessor, Global, Partitioned).
- Sidebar task-set controls are dynamic: enabling a parameter reveals its default-value control.
- Resource-aware protocol options (None, PIP, PCP, NPP) are available wherever resource simulation applies.
- Schedule plots now reuse a cached figure helper in the interactive pages, which makes reruns feel faster.
- PNG export now surfaces clearer failures instead of silently dropping downloads when image export is unavailable.
- Compare Mode now uses the shared algorithm registry from the core utilities, keeping the page definitions aligned.
- Added a dedicated Slack Stealing page with sidebar controls for periodic EDF tasks and aperiodic jobs.
- Slack Stealing now includes a stats panel with KPI metrics and per-aperiodic-job outcomes.
- Legacy flat algorithm pages were archived under `legacy_pages/` to keep the main sidebar focused.
- Added mixed-criticality support in Algorithm Explorer with static and adaptive modes.
- Task sets can now include criticality labels (`low/medium/high` or `A..Z`) and per-task `C-LO` / `C-HI` budgets.
- Adaptive mixed-criticality mode now performs an explicit LO->HI mode switch and drops low-criticality jobs after switch.

## Dashboard
The Streamlit dashboard lets you build custom task sets, check schedulability tests,
and generate schedules with hoverable job and resource details. Schedules can be
exported as PNG, and task sets as CSV.

### Navigation
- `pages/00_Algorithm_Explorer.py`: Main workflow for scheduling experiments
- `pages/01_Task_Set_Builder.py`: Task-set authoring and CSV export
- `pages/02_Compare_Mode.py`: Compare multiple algorithms across shared or unique task sets
- `pages/06_Cyclic_Executive.py`, `pages/10_Time_Demand.py`, `pages/11_Priority_Inversion.py`, `pages/15_Slack_Stealing.py`: Specialized analysis pages

### Slack Stealing page
- `pages/15_Slack_Stealing.py` demonstrates idle-time slack reclamation.
- Periodic jobs are scheduled with EDF first.
- Ready aperiodic jobs execute only when no periodic job is runnable.
- The page supports CSV export for periodic and aperiodic inputs, plus PNG schedule export.
- A Slack Stats panel reports total slack used, completion ratio, response/waiting times, and deadline misses.
- A detailed table shows per-aperiodic-job execution and completion outcomes.

### Slack Stealing walkthrough
Use this quick setup to see slack reclamation behavior:

- Periodic tasks
	- T1: phase 0, period 5, computation 1, deadline 5
	- T2: phase 0, period 10, computation 2, deadline 10
- Aperiodic jobs
	- AP1: release 1, computation 2, relative deadline 8
	- AP2: release 6, computation 1, relative deadline 6
- Time range
	- Start 0, End 20, Tick 1

Expected behavior:
- Periodic EDF jobs run whenever ready.
- Aperiodic jobs run in gaps where no periodic job is ready.
- AP1 starts shortly after release when the first idle window appears.
- AP2 is served in a later slack window after periodic demand is cleared.

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

## Structure
```
real-time-systems/
├── cyclic-executive/      # Cyclic executive frame sizing and schedules
├── dm-pcp/                # Deadline Monotonic with Priority Ceiling Protocol
├── dm-pip/                # Deadline Monotonic with Priority Inheritance Protocol
├── edf/                   # Earliest Deadline First scheduling
├── global-rm/             # Global RM on multiple processors
├── legacy_pages/          # Archived legacy Streamlit algorithm pages
├── priority-inversion/    # Priority inversion examples and debugging
├── rm-dm-basics/          # RM/DM basics and Lehoczky's counterexample
├── rm-npp/                # Rate Monotonic with Non-Preemptive Protocol
├── rm-pip/                # Rate Monotonic with Priority Inheritance Protocol
├── time-demand-analysis/  # Time-demand analysis for a selected task
├── pages/                 # Streamlit pages (Explorer + specialized tools)
├── rt_utils.py            # Scheduling logic and plot helpers
├── st_helpers.py          # Streamlit UI helpers
├── streamlit_app.py       # Dashboard landing page
└── requirements.txt       # Dashboard dependencies
```

Each algorithm folder contains a focused script (or set of scripts) for the named
method, plus any pre-generated schedule images and a short README describing the
contents.