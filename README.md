# Real-Time Systems
Brief implementations of real-time scheduling algorithms with accompanying plots and a Streamlit dashboard.

## Dashboard
The Streamlit dashboard lets you build custom task sets, check schedulability tests,
and generate schedules with hoverable job and resource details. Schedules can be
exported as PNG, and task sets as CSV.

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
├── priority-inversion/    # Priority inversion examples and debugging
├── rm-dm-basics/          # RM/DM basics and Lehoczky's counterexample
├── rm-npp/                # Rate Monotonic with Non-Preemptive Protocol
├── rm-pip/                # Rate Monotonic with Priority Inheritance Protocol
├── time-demand-analysis/  # Time-demand analysis for a selected task
├── pages/                 # Streamlit pages for each algorithm
├── rt_utils.py            # Scheduling logic and plot helpers
├── st_helpers.py          # Streamlit UI helpers
├── streamlit_app.py       # Dashboard landing page
└── requirements.txt       # Dashboard dependencies
```

Each algorithm folder contains a focused script (or set of scripts) for the named
method, plus any pre-generated schedule images and a short README describing the
contents.